import difflib
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.analysis import DocumentAnalysis
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/comparison", tags=["comparison"])

class CompareRequest(BaseModel):
    doc_a_id: str
    doc_b_id: str

@router.post("")
def compare_documents(
    payload: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compares two database documents, returning additions, deletions, and side-by-side diffs.
    """
    doc_a = db.query(Document).filter(Document.id == payload.doc_a_id, Document.user_id == current_user.id).first()
    doc_b = db.query(Document).filter(Document.id == payload.doc_b_id, Document.user_id == current_user.id).first()

    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found or unauthorized.")

    analysis_a = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == doc_a.id).first()
    analysis_b = db.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == doc_b.id).first()

    text_a = (analysis_a.extracted_text or "") if analysis_a else ""
    text_b = (analysis_b.extracted_text or "") if analysis_b else ""

    lines_a = [l.strip() for l in text_a.splitlines() if l.strip()][:100]
    lines_b = [l.strip() for l in text_b.splitlines() if l.strip()][:100]

    matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
    
    additions = []
    deletions = []
    modifications = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            modifications.append({
                "original": " ".join(lines_a[i1:i2])[:200],
                "modified": " ".join(lines_b[j1:j2])[:200]
            })
        elif tag == "delete":
            deletions.append(" ".join(lines_a[i1:i2])[:200])
        elif tag == "insert":
            additions.append(" ".join(lines_b[j1:j2])[:200])

    return {
        "doc_a": {
            "id": doc_a.id,
            "filename": doc_a.filename
        },
        "doc_b": {
            "id": doc_b.id,
            "filename": doc_b.filename
        },
        "additions_count": len(additions),
        "deletions_count": len(deletions),
        "modifications_count": len(modifications),
        "additions": additions[:10],
        "deletions": deletions[:10],
        "modifications": modifications[:10],
        "text_a_sample": "\n\n".join(lines_a[:8]),
        "text_b_sample": "\n\n".join(lines_b[:8]),
    }
