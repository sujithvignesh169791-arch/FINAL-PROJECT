import os
import uuid
import threading
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
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
from app.ai.rag_service import delete_document_chunks
from app.ai.gemini_provider import GeminiConfigurationError, GeminiAPIError
from app.ai.nvidia_provider import NvidiaConfigurationError, NvidiaAPIError

router = APIRouter(prefix="/documents", tags=["documents"])

# Ensure uploads directory is always anchored to backend folder
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = str(BACKEND_DIR / "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory concurrency tracking to prevent duplicate concurrent analyses
_analyzing_documents: set[str] = set()
_analyzing_lock = threading.Lock()

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
        pass

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (Max 50MB)")
        
    file_uuid = str(uuid.uuid4())
    safe_filename = f"{file_uuid}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
        
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
    
    background_tasks.add_task(process_document, db_doc.id)
    db_doc.file_size = len(file_content)
    return db_doc

@router.get("", response_model=list[DocumentResponse])
def get_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    for d in docs:
        if d.storage_url and os.path.exists(d.storage_url):
            try:
                d.file_size = os.path.getsize(d.storage_url)
            except Exception:
                d.file_size = None
    return docs

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.storage_url and os.path.exists(doc.storage_url):
        try:
            doc.file_size = os.path.getsize(doc.storage_url)
        except Exception:
            doc.file_size = None
    return doc

@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")

    if not doc.storage_url or not os.path.exists(doc.storage_url):
        raise HTTPException(status_code=404, detail="Original document file not found on server")

    return FileResponse(
        path=doc.storage_url,
        filename=doc.filename,
        media_type="application/octet-stream"
    )

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
    
    # Concurrency check: avoid duplicate parallel analyses for the same document
    with _analyzing_lock:
        if document_id in _analyzing_documents:
            # Wait briefly for in-flight analysis to finish rather than duplicating
            for _ in range(20):
                time.sleep(0.5)
                db.refresh(doc)
                existing = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).first()
                if existing and existing.summary:
                    return existing
                if document_id not in _analyzing_documents:
                    break
        _analyzing_documents.add(document_id)

    try:
        if doc.upload_status != "completed":
            process_document(db, document_id)
            db.refresh(doc)
            
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
    finally:
        with _analyzing_lock:
            _analyzing_documents.discard(document_id)

@router.get("/{document_id}/analysis", response_model=AnalysisResponse)
def get_analysis(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
        
    analysis = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).first()
    
    # Return persisted analysis immediately if ready
    if analysis and analysis.summary:
        return analysis

    # If document upload/text extraction failed, report error
    if doc.upload_status == "failed":
        err_msg = analysis.processing_error if analysis else "Document processing failed."
        raise HTTPException(status_code=400, detail=f"Text extraction failed: {err_msg}")

    # Prevent concurrent duplicate requests from running parallel analyses
    with _analyzing_lock:
        if document_id in _analyzing_documents:
            # Another request is actively generating analysis, wait briefly or return existing
            for _ in range(15):
                time.sleep(0.5)
                existing = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).first()
                if existing and existing.summary:
                    return existing
                if document_id not in _analyzing_documents:
                    break
            existing = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).first()
            if existing and existing.summary:
                return existing
            raise HTTPException(status_code=409, detail="Analysis is already actively running for this document.")
        _analyzing_documents.add(document_id)

    try:
        # If document text extraction hasn't completed yet, run extraction first
        if doc.upload_status != "completed":
            process_document(db, document_id)
            db.refresh(doc)

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
        raise HTTPException(status_code=500, detail=f"Analysis retrieval failed: {str(e)}")
    finally:
        with _analyzing_lock:
            _analyzing_documents.discard(document_id)

@router.delete("/{document_id}")
def delete_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")

    # Clean up uploaded file on disk
    if doc.storage_url and os.path.exists(doc.storage_url):
        try:
            os.remove(doc.storage_url)
        except Exception:
            pass

    # Clean up vector database chunks
    try:
        delete_document_chunks(document_id)
    except Exception:
        pass

    db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id).delete()
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": "Document deleted successfully"}
