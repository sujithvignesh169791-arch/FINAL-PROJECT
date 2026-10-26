import os
import tempfile
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from pypdf import PdfReader
from dotenv import load_dotenv

from app.routers import auth, documents, chat, cases, risk, comparison
from app.db.session import engine
from app.db.base import Base
# Import all models to ensure they are registered with Base
from app.models.user import User
from app.models.document import Document
from app.models.analysis import DocumentAnalysis
from app.models.chat import ChatSession, ChatMessage
from app.core.config import settings

# Load environment variables
load_dotenv()

# Create tables for testing/local dev
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LEXIAI Backend API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        settings.FRONTEND_URL_PROD,
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase Client (Service Role Key recommended for backend writes)
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY", "")
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

# Include modular routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(comparison.router, prefix="/api/v1")


class DocumentProcessRequest(BaseModel):
    document_id: str
    file_path: str


# Background worker function to process PDF & Extract Risks
def process_document_background(document_id: str, file_path: str):
    if not supabase:
        print(f"Supabase client not initialized. Cannot process document: {document_id}")
        return

    try:
        print(f"Starting processing for document: {document_id}")

        # 1. Update status to 'processing'
        supabase.table("documents").update({"status": "processing"}).eq("id", document_id).execute()

        # 2. Download file from Supabase storage bucket 'documents'
        res = supabase.storage.from_("documents").download(file_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(res)
            temp_path = temp_file.name

        # 3. Extract text using PyPDF
        reader = PdfReader(temp_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        os.remove(temp_path)  # Clean up temp file

        # 4. Generate AI Summary & Risk Analysis using official Gemini provider
        from app.ai.gemini_provider import analyze_legal_text_structured
        ai_res = analyze_legal_text_structured(full_text[:15000])
        doc_summary = ai_res.executive_summary or "Legal summary generated."

        # 5. Insert analysis into risk_clauses table if supabase is active
        supabase.table("risk_clauses").insert({
            "document_id": document_id,
            "clause_text": "AI Risk Analysis generated from document review.",
            "risk_level": "medium",
            "is_verified": False
        }).execute()

        # 6. Update document record with summary and 'processed' status
        supabase.table("documents").update({
            "status": "processed",
            "summary": doc_summary
        }).eq("id", document_id).execute()

        print(f"Successfully processed document: {document_id}")

    except Exception as e:
        print(f"Error processing document {document_id}: {str(e)}")
        try:
            supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
        except Exception as inner_e:
            print(f"Failed to update error status for {document_id}: {inner_e}")


@app.post("/api/v1/documents/process")
def trigger_document_processing(payload: DocumentProcessRequest, background_tasks: BackgroundTasks):
    # Trigger background processing so HTTP request responds immediately
    background_tasks.add_task(process_document_background, payload.document_id, payload.file_path)
    return {"status": "success", "message": "Document processing started in background", "document_id": payload.document_id}


@app.get("/")
def read_root():
    return {"status": "ok", "app": "LEXIAI Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

