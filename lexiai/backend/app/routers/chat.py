import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionResponse,
    ChatMessageResponse,
    SourceItem
)
from app.services.auth_service import get_current_user
from app.ai.rag_service import answer_legal_query
from app.ai.gemini_provider import GeminiConfigurationError, GeminiAPIError
from app.ai.nvidia_provider import NvidiaConfigurationError, NvidiaAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/query", response_model=ChatQueryResponse)
def query_chat(
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG-grounded legal chat query:
    1. Authenticate user.
    2. Enforce document authorization (restricts retrieval to documents owned by user).
    3. Retrieve relevant chunks using cosine similarity.
    4. Call Gemini with evidence-grounded prompt & prompt injection defense.
    5. Persist question, answer, and session in database.
    6. Return grounded answer, citations/sources, and session ID.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # If document_id is provided, verify it belongs to current_user
    if payload.document_id:
        doc = db.query(Document).filter(
            Document.id == payload.document_id,
            Document.user_id == current_user.id
        ).first()
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found or unauthorized access."
            )

    try:
        answer, sources, session_id = answer_legal_query(
            db=db,
            user_id=current_user.id,
            question=payload.question.strip(),
            document_id=payload.document_id,
            session_id=payload.session_id
        )

        source_items = [
            SourceItem(
                document_id=s.get("document_id", ""),
                document_name=s.get("document_name", "Document"),
                page_number=s.get("page_number"),
                chunk_index=s.get("chunk_index"),
                excerpt=s.get("excerpt", ""),
                score=s.get("score")
            )
            for s in sources
        ]

        return ChatQueryResponse(
            answer=answer,
            sources=source_items,
            session_id=session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GeminiConfigurationError as e:
        raise HTTPException(status_code=500, detail=f"Gemini configuration error: {str(e)}")
    except (GeminiAPIError, NvidiaAPIError) as e:
        logger.warning(f"AI provider transient failure in chat query ({e}). Generating fallback assistant response.")
        return ChatQueryResponse(
            answer="The AI inference provider experienced a transient timeout. Your document has been indexed; please try submitting your query again or refer to the Document Analysis tab for the complete extracted summary.",
            sources=[],
            session_id=payload.session_id or ""
        )
    except Exception as e:
        logger.error(f"Error handling chat query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat query: {str(e)}")

@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all chat sessions belonging to the authenticated user.
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()

    result = []
    for s in sessions:
        msgs = db.query(ChatMessage).filter(
            ChatMessage.session_id == s.id
        ).order_by(ChatMessage.created_at.asc()).all()

        result.append(ChatSessionResponse(
            id=s.id,
            title=s.title,
            document_id=s.document_id,
            created_at=s.created_at.isoformat() if s.created_at else None,
            messages=[
                ChatMessageResponse(
                    id=m.id,
                    session_id=m.session_id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at.isoformat() if m.created_at else None
                )
                for m in msgs
            ]
        ))
    return result

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve an individual chat session with full message history.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    msgs = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        document_id=session.document_id,
        created_at=session.created_at.isoformat() if session.created_at else None,
        messages=[
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat() if m.created_at else None
            )
            for m in msgs
        ]
    )
