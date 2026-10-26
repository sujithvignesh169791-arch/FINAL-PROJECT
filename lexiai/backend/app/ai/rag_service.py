import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.models.document import Document
from app.models.analysis import DocumentAnalysis
from app.models.chat import ChatSession, ChatMessage
from app.ai import gemini_provider, nvidia_provider

logger = logging.getLogger(__name__)

def get_ai_provider():
    provider_name = (settings.AI_PROVIDER or "auto").strip().lower()
    if provider_name == "nvidia":
        return nvidia_provider
    elif provider_name == "gemini":
        gemini_key = (settings.GEMINI_API_KEY or "").strip()
        if (not gemini_key or "mock" in gemini_key or "test" in gemini_key) and (settings.NVIDIA_API_KEY or "").strip():
            return nvidia_provider
        return gemini_provider
    else:
        if (settings.NVIDIA_API_KEY or "").strip():
            return nvidia_provider
        return gemini_provider

def generate_embeddings(
    texts: List[str],
    model_name: Optional[str] = None
) -> List[List[float]]:
    return get_ai_provider().generate_embeddings(texts, model_name=model_name)

def generate_grounded_answer(
    question: str,
    context: str,
    chat_history: Optional[List[dict]] = None,
    model_name: Optional[str] = None
) -> str:
    return get_ai_provider().generate_grounded_answer(
        question=question,
        context=context,
        chat_history=chat_history,
        model_name=model_name
    )

def get_collection_name():
    provider_name = (settings.AI_PROVIDER or "auto").strip().lower()
    return f"lexiai_documents_{provider_name}"

_chroma_client: Optional[chromadb.PersistentClient] = None

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Returns a persistent ChromaDB client anchored to CHROMA_PERSIST_DIR.
    Ensures vector data survives server restarts.
    """
    global _chroma_client
    if _chroma_client is None:
        persist_dir = settings.CHROMA_PERSIST_DIR
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client

def get_document_collection():
    """
    Returns or creates the Chroma collection for legal documents.
    Uses cosine similarity for normalized vector search.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=get_collection_name(),
        metadata={"hnsw:space": "cosine"}
    )

def chunk_document_text(
    pages: Optional[List[Dict[str, Any]]],
    full_text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Splits document text into logically structured chunks by paragraphs, headings,
    and legal clauses, preserving page numbers whenever available.
    """
    chunks: List[Dict[str, Any]] = []
    chunk_idx = 0

    if pages and len(pages) > 0:
        for p in pages:
            page_num = p.get("page_number", 1)
            text = (p.get("text") or "").strip()
            if not text:
                continue

            # Split page text by paragraph breaks or clause markers
            paragraphs = re.split(r"\n\s*\n|(?<=\.)\n(?=[A-Z0-9\(\[])", text)
            current_chunk = ""

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                if len(current_chunk) + len(para) + 1 <= chunk_size:
                    current_chunk = f"{current_chunk}\n{para}".strip()
                else:
                    if current_chunk:
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "page_number": page_num,
                            "text": current_chunk
                        })
                        chunk_idx += 1

                    # If a single paragraph exceeds chunk_size, split with overlap
                    if len(para) > chunk_size:
                        start = 0
                        while start < len(para):
                            end = start + chunk_size
                            part = para[start:end].strip()
                            if part:
                                chunks.append({
                                    "chunk_index": chunk_idx,
                                    "page_number": page_num,
                                    "text": part
                                })
                                chunk_idx += 1
                            start += (chunk_size - chunk_overlap)
                        current_chunk = ""
                    else:
                        current_chunk = para

            if current_chunk:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "text": current_chunk
                })
                chunk_idx += 1
    else:
        # Fallback to splitting full_text
        text = full_text.strip()
        if not text:
            return []

        paragraphs = re.split(r"\n\s*\n", text)
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) + 1 <= chunk_size:
                current_chunk = f"{current_chunk}\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": 1,
                        "text": current_chunk
                    })
                    chunk_idx += 1
                if len(para) > chunk_size:
                    start = 0
                    while start < len(para):
                        end = start + chunk_size
                        part = para[start:end].strip()
                        if part:
                            chunks.append({
                                "chunk_index": chunk_idx,
                                "page_number": 1,
                                "text": part
                            })
                            chunk_idx += 1
                        start += (chunk_size - chunk_overlap)
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append({
                "chunk_index": chunk_idx,
                "page_number": 1,
                "text": current_chunk
            })

    return chunks

def has_indexed_chunks(document_id: str) -> bool:
    """
    Checks if chunks for this document are already stored in ChromaDB.
    Prevents duplicate embeddings and redundant API costs.
    """
    try:
        coll = get_document_collection()
        results = coll.get(where={"document_id": document_id}, limit=1)
        return bool(results and results.get("ids") and len(results["ids"]) > 0)
    except Exception as e:
        logger.warning(f"Error checking indexed chunks for doc {document_id}: {e}")
        return False

def delete_document_chunks(document_id: str) -> None:
    """
    Removes all chunks associated with a document ID from ChromaDB.
    """
    try:
        coll = get_document_collection()
        coll.delete(where={"document_id": document_id})
        logger.info(f"Deleted vector chunks for document {document_id}")
    except Exception as e:
        logger.warning(f"Failed to delete chunks for {document_id}: {e}")

def index_document_chunks(
    document_id: str,
    user_id: str,
    filename: str,
    pages: Optional[List[Dict[str, Any]]],
    full_text: str,
    force: bool = False
) -> int:
    """
    Extracts chunks, generates embeddings using Gemini, and saves to ChromaDB.
    Avoids re-embedding if chunks already exist unless force=True.
    """
    if not force and has_indexed_chunks(document_id):
        logger.info(f"Document {document_id} is already indexed in vector database. Skipping.")
        return 0

    if force:
        delete_document_chunks(document_id)

    chunks = chunk_document_text(
        pages=pages,
        full_text=full_text,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    if not chunks:
        logger.warning(f"No chunks extracted from document {document_id}")
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts)

    ids = [f"{document_id}_{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "user_id": user_id,
            "filename": filename,
            "page_number": int(c.get("page_number") or 1),
            "chunk_index": int(c["chunk_index"])
        }
        for c in chunks
    ]

    coll = get_document_collection()
    coll.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logger.info(f"Successfully indexed {len(chunks)} chunks for document '{filename}' ({document_id})")
    return len(chunks)

def retrieve_relevant_chunks(
    user_id: str,
    query: str,
    document_id: Optional[str] = None,
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Searches ChromaDB for relevant chunks matching the query embedding.
    Enforces authorization: only returns chunks belonging to user_id.
    If document_id is provided, restricts search to that document.
    """
    k = top_k or settings.TOP_K_CHUNKS

    # Generate query embedding
    query_embeddings = generate_embeddings([query])
    if not query_embeddings:
        return []

    # Build authorization and scoping filter
    if document_id:
        filter_criteria = {
            "$and": [
                {"user_id": user_id},
                {"document_id": document_id}
            ]
        }
    else:
        filter_criteria = {"user_id": user_id}

    coll = get_document_collection()
    res = coll.query(
        query_embeddings=query_embeddings,
        n_results=k,
        where=filter_criteria
    )

    chunks = []
    if res and res.get("documents") and len(res["documents"]) > 0:
        docs = res["documents"][0]
        metas = res["metadatas"][0] if res.get("metadatas") else []
        distances = res["distances"][0] if res.get("distances") else []

        for i, doc_text in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else None
            # For cosine space, similarity = 1 - distance
            score = round(1.0 - dist, 4) if dist is not None else None

            chunks.append({
                "document_id": meta.get("document_id", ""),
                "document_name": meta.get("filename", "Document"),
                "page_number": meta.get("page_number", 1),
                "chunk_index": meta.get("chunk_index", 0),
                "excerpt": doc_text,
                "score": score
            })

    return chunks

def answer_legal_query(
    db: Session,
    user_id: str,
    question: str,
    document_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    Complete RAG workflow:
    1. Authenticate & verify ownership.
    2. Auto-index document chunks if not yet indexed.
    3. Retrieve top-K relevant chunks with user-level isolation.
    4. Send grounded prompt to Gemini with prompt injection defense.
    5. Save chat session and messages to database.
    6. Return (answer, sources, session_id).
    """
    # 1. Verify document authorization if document_id is provided
    target_doc = None
    if document_id:
        target_doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        if not target_doc:
            raise ValueError("Document not found or unauthorized access.")

        # Ensure document is indexed into vector store
        if not has_indexed_chunks(document_id):
            analysis = db.query(DocumentAnalysis).filter(
                DocumentAnalysis.document_id == document_id
            ).first()
            if analysis and analysis.extracted_text:
                index_document_chunks(
                    document_id=document_id,
                    user_id=user_id,
                    filename=target_doc.filename,
                    pages=analysis.page_text,
                    full_text=analysis.extracted_text
                )

    # 2. Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(
        user_id=user_id,
        query=question,
        document_id=document_id
    )

    # 3. Format context string
    if not chunks:
        answer = "Based on the available document evidence, there is insufficient information to answer this question."
        sources = []
    else:
        context_parts = []
        for c in chunks:
            context_parts.append(
                f"[Source Document: {c['document_name']}, Page: {c['page_number']}]\n{c['excerpt']}"
            )
        context_str = "\n\n---\n\n".join(context_parts)

        # 4. Handle Chat History
        chat_history = []
        if session_id:
            prior_msgs = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).all()
            for msg in prior_msgs:
                chat_history.append({"role": msg.role, "content": msg.content})

        # 5. Generate Grounded Gemini Answer
        answer = generate_grounded_answer(
            question=question,
            context=context_str,
            chat_history=chat_history
        )
        sources = chunks

    # 6. Persist Chat Session & Messages
    session = None
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

    if not session:
        title = question[:40] + ("..." if len(question) > 40 else "")
        session = ChatSession(
            user_id=user_id,
            document_id=document_id,
            title=title
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=question
    )
    # Save assistant message
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer
    )
    db.add(user_msg)
    db.add(ai_msg)
    db.commit()

    return answer, sources, session.id
