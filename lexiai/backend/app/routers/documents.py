import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentJobResponse
from app.schemas.analysis import AnalysisResponse
from app.ai.legal_analysis import perform_document_analysis
from app.models.analysis import DocumentAnalysis
from app.services.auth_service import get_current_user
from app.services.document_service import process_document
from app.ai.gemini_provider import GeminiConfigurationError, GeminiAPIError
from app.ai.nvidia_provider import NvidiaConfigurationError, NvidiaAPIError

router = APIRouter(prefix="/documents", tags=["documents"])

# Ensure uploads directory is always anchored to backend folder
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = str(BACKEND_DIR / "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "application/octet-stream",
    "binary/octet-stream"
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}. Allowed: PDF, DOCX, TXT")

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # If extension is valid, allow it even if browser sends an unusual MIME
        pass

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (Max 50MB)")
        
    # Generate safe filename and save
    file_uuid = str(uuid.uuid4())
    safe_filename = f"{file_uuid}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
        
    # Create DB record
    db_doc = Document(
        user_id=current_user.id,
        filename=file.filename or "uploaded_document",
        file_type=ext.replace(".", ""),
        storage_url=file_path,
        upload_status="processing"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Run processing in background with document ID (creates its own DB session)
    background_tasks.add_task(process_document, db_doc.id)
    
    return db_doc

@router.get("", response_model=list[DocumentResponse])
def get_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.asc()).all()
    return docs

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/jobs/{job_id}", response_model=DocumentJobResponse)
def get_document_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == job_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Job/Document not found")
        
    msg = None
    if doc.upload_status == "failed":
        analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == doc.id).first()
        if analysis and analysis.processing_error:
            msg = analysis.processing_error
            
    return DocumentJobResponse(
        job_id=doc.id,
        document_id=doc.id,
        status=doc.upload_status,
        message=msg
    )

@router.post("/{document_id}/analyze", response_model=AnalysisResponse)
def analyze_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
    
    # If document processing is still pending, process it synchronously now
    if doc.upload_status != "completed":
        process_document(db, document_id)
        db.refresh(doc)
        
    try:
        analysis = perform_document_analysis(db, document_id, current_user.id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GeminiConfigurationError as e:
        raise HTTPException(status_code=500, detail=f"Gemini configuration error: {str(e)}")
    except GeminiAPIError as e:
        raise HTTPException(status_code=502, detail=f"Gemini API failure: {str(e)}")
    except NvidiaConfigurationError as e:
        raise HTTPException(status_code=500, detail=f"NVIDIA configuration error: {str(e)}")
    except NvidiaAPIError as e:
        raise HTTPException(status_code=502, detail=f"NVIDIA API failure: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{document_id}/analysis", response_model=AnalysisResponse)
def get_analysis(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
        
    analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).first()
    if not analysis or not analysis.summary:
        try:
            analysis = perform_document_analysis(db, document_id, current_user.id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except GeminiConfigurationError as e:
            raise HTTPException(status_code=500, detail=f"Gemini configuration error: {str(e)}")
        except GeminiAPIError as e:
            raise HTTPException(status_code=502, detail=f"Gemini API failure: {str(e)}")
        except NvidiaConfigurationError as e:
            raise HTTPException(status_code=500, detail=f"NVIDIA configuration error: {str(e)}")
        except NvidiaAPIError as e:
            raise HTTPException(status_code=502, detail=f"NVIDIA API failure: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis retrieval failed: {str(e)}")
        
    return analysis

@router.delete("/{document_id}")
def delete_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
    
    db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).delete()
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": "Document deleted successfully"}
