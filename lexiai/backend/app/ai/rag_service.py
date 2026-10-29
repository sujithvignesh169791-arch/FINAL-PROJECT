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

# Track active dimensions to route collections correctly without dimension mismatch errors
_last_used_user_dim: Optional[int] = None
_last_used_corpus_dim: Optional[int] = None
_chroma_client: Optional[chromadb.PersistentClient] = None

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

def get_user_collection_name(dimension: Optional[int] = None) -> str:
    """
    Returns dimension-aware collection name for private user documents:
    e.g. lexiai_documents_nvidia_2048 or lexiai_documents_nvidia_768
    """
    global _last_used_user_dim
    provider_name = (settings.AI_PROVIDER or "auto").strip().lower()
    dim = dimension or _last_used_user_dim
    if not dim:
        # Fallback to provider defaults or existing collections
        dim = 2048 if provider_name == "nvidia" else 768
    return f"{settings.USER_DOCUMENTS_COLLECTION_PREFIX}_{provider_name}_{dim}"

def get_public_corpus_collection_name(dimension: Optional[int] = None) -> str:
    """
    Returns dimension-aware collection name for the public legal corpus:
    e.g. lexiai_public_corpus_nvidia_2048 or lexiai_public_corpus_nvidia_768
    """
    global _last_used_corpus_dim
    provider_name = (settings.AI_PROVIDER or "auto").strip().lower()
    dim = dimension or _last_used_corpus_dim
    if not dim:
        dim = 2048 if provider_name == "nvidia" else 768
    return f"{settings.PUBLIC_CORPUS_COLLECTION_PREFIX}_{provider_name}_{dim}"

def get_collection_name():
    """Backwards compatibility helper."""
    return get_user_collection_name()

def get_document_collection(dimension: Optional[int] = None):
    """
    Returns or creates the Chroma collection for private user documents.
    Uses cosine similarity for normalized vector search.
    """
    client = get_chroma_client()
    coll_name = get_user_collection_name(dimension)
    return client.get_or_create_collection(
        name=coll_name,
        metadata={"hnsw:space": "cosine"}
    )

def get_public_corpus_collection(dimension: Optional[int] = None):
    """
    Returns or creates the Chroma collection for public research corpus documents.
    Completely isolated from private user documents.
    """
    client = get_chroma_client()
    coll_name = get_public_corpus_collection_name(dimension)
    return client.get_or_create_collection(
        name=coll_name,
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

def has_indexed_chunks(document_id: str, dimension: Optional[int] = None) -> bool:
    """
    Checks if chunks for this user document are already stored in ChromaDB.
    If dimension is specified, checks that specific dimension's collection.
    """
    try:
        client = get_chroma_client()
        provider_name = (settings.AI_PROVIDER or "auto").strip().lower()

        if dimension:
            coll_name = get_user_collection_name(dimension)
            try:
                c = client.get_collection(coll_name)
                res = c.get(where={"document_id": document_id}, limit=1)
                return bool(res and res.get("ids") and len(res["ids"]) > 0)
            except Exception:
                return False

        for coll_meta in client.list_collections():
            if coll_meta.name.startswith(f"{settings.USER_DOCUMENTS_COLLECTION_PREFIX}_{provider_name}") or \
               coll_meta.name == f"lexiai_documents_{provider_name}":
                try:
                    c = client.get_collection(coll_meta.name)
                    res = c.get(where={"document_id": document_id}, limit=1)
                    if res and res.get("ids") and len(res["ids"]) > 0:
                        return True
                except Exception:
                    pass
        return False
    except Exception as e:
        logger.warning(f"Error checking indexed chunks for doc {document_id}: {e}")
        return False

def delete_document_chunks(document_id: str) -> None:
    """
    Removes all chunks associated with a document ID from all user document collections.
    """
    try:
        client = get_chroma_client()
        provider_name = (settings.AI_PROVIDER or "auto").strip().lower()
        for coll_meta in client.list_collections():
            if coll_meta.name.startswith(f"{settings.USER_DOCUMENTS_COLLECTION_PREFIX}_{provider_name}") or \
               coll_meta.name == f"lexiai_documents_{provider_name}":
                try:
                    c = client.get_collection(coll_meta.name)
                    c.delete(where={"document_id": document_id})
                    logger.info(f"Deleted vector chunks for document {document_id} from {coll_meta.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete chunks from {coll_meta.name}: {e}")
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
    Extracts chunks, generates embeddings, and saves to the user ChromaDB collection.
    Avoids re-embedding if chunks already exist unless force=True.
    """
    global _last_used_user_dim

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
    if not embeddings or not embeddings[0]:
        logger.warning(f"Empty embeddings generated for document {document_id}")
        return 0

    dim = len(embeddings[0])
    _last_used_user_dim = dim

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

    coll = get_document_collection(dimension=dim)
    coll.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logger.info(f"Successfully indexed {len(chunks)} chunks in '{coll.name}' for document '{filename}' ({document_id})")
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
    global _last_used_user_dim
    k = top_k or settings.TOP_K_CHUNKS

    query_embeddings = generate_embeddings([query])
    if not query_embeddings or not query_embeddings[0]:
        return []

    dim = len(query_embeddings[0])
    _last_used_user_dim = dim

    if document_id:
        filter_criteria = {
            "$and": [
                {"user_id": user_id},
                {"document_id": document_id}
            ]
        }
    else:
        filter_criteria = {"user_id": user_id}

    coll = get_document_collection(dimension=dim)
    try:
        res = coll.query(
            query_embeddings=query_embeddings,
            n_results=k,
            where=filter_criteria
        )
    except Exception as e:
        logger.warning(f"Error querying user collection {coll.name}: {e}")
        return []

    chunks = []
    if res and res.get("documents") and len(res["documents"]) > 0:
        docs = res["documents"][0]
        metas = res["metadatas"][0] if res.get("metadatas") else []
        distances = res["distances"][0] if res.get("distances") else []

        for i, doc_text in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else None
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

# ==========================================
# PUBLIC RESEARCH CORPUS INGESTION & SEARCH
# ==========================================

def has_indexed_public_chunks(corpus_id: str) -> bool:
    """
    Checks if a public research corpus document is already indexed in the public Chroma collection.
    """
    try:
        client = get_chroma_client()
        provider_name = (settings.AI_PROVIDER or "auto").strip().lower()
        for coll_meta in client.list_collections():
            if coll_meta.name.startswith(f"{settings.PUBLIC_CORPUS_COLLECTION_PREFIX}_{provider_name}"):
                try:
                    c = client.get_collection(coll_meta.name)
                    res = c.get(where={"corpus_id": corpus_id}, limit=1)
                    if res and res.get("ids") and len(res["ids"]) > 0:
                        return True
                except Exception:
                    pass
        return False
    except Exception as e:
        logger.warning(f"Error checking indexed public chunks for {corpus_id}: {e}")
        return False

def index_public_corpus_chunks(
    corpus_id: str,
    corpus_type: str,
    title: str,
    filename: str,
    court: str,
    year: str,
    citation: str,
    full_text: str,
    verdict: Optional[str] = None,
    force: bool = False
) -> int:
    """
    Extracts chunks from a public legal document (CUAD contract or Indian Court judgment),
    embeds them, and saves to the separate public research ChromaDB collection.
    """
    global _last_used_corpus_dim

    if not force and has_indexed_public_chunks(corpus_id):
        logger.info(f"Public corpus item '{title}' ({corpus_id}) is already indexed. Skipping.")
        return 0

    chunks = chunk_document_text(
        pages=None,
        full_text=full_text,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    if not chunks:
        return 0

    # For long public contracts or judgments, index up to top 15 most representative chunks to optimize storage
    selected_chunks = chunks[:15]
    texts = [c["text"] for c in selected_chunks]

    embeddings = generate_embeddings(texts)
    if not embeddings or not embeddings[0]:
        return 0

    dim = len(embeddings[0])
    _last_used_corpus_dim = dim

    coll = get_public_corpus_collection(dimension=dim)
    ids = [f"pub_{corpus_id}_{c['chunk_index']}" for c in selected_chunks]
    metadatas = [
        {
            "corpus_id": corpus_id,
            "corpus_type": corpus_type,
            "title": title[:200],
            "filename": filename,
            "court": court[:100],
            "year": str(year),
            "citation": citation[:100],
            "verdict": verdict or "",
            "chunk_index": int(c["chunk_index"])
        }
        for c in selected_chunks
    ]

    coll.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    logger.info(f"Successfully indexed {len(selected_chunks)} public chunks for '{title}' into '{coll.name}'")
    return len(selected_chunks)

def retrieve_public_corpus_chunks(
    query: str,
    corpus_type: Optional[str] = None,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Retrieves relevant public research chunks (CUAD commercial contracts or Supreme Court judgments)
    matching the query embedding from the separate public collection.
    """
    global _last_used_corpus_dim

    query_embeddings = generate_embeddings([query])
    if not query_embeddings or not query_embeddings[0]:
        return []

    dim = len(query_embeddings[0])
    _last_used_corpus_dim = dim

    coll = get_public_corpus_collection(dimension=dim)
    kwargs = {
        "query_embeddings": query_embeddings,
        "n_results": top_k
    }
    if corpus_type:
        kwargs["where"] = {"corpus_type": corpus_type}

    try:
        res = coll.query(**kwargs)
    except Exception as e:
        logger.warning(f"Error querying public collection {coll.name}: {e}")
        return []

    chunks = []
    if res and res.get("documents") and len(res["documents"]) > 0:
        docs = res["documents"][0]
        metas = res["metadatas"][0] if res.get("metadatas") else []
        distances = res["distances"][0] if res.get("distances") else []

        for i, doc_text in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else None
            score = round(1.0 - dist, 4) if dist is not None else None

            chunks.append({
                "corpus_id": meta.get("corpus_id", ""),
                "corpus_type": meta.get("corpus_type", ""),
                "title": meta.get("title", ""),
                "filename": meta.get("filename", ""),
                "court": meta.get("court", ""),
                "year": meta.get("year", ""),
                "citation": meta.get("citation", ""),
                "verdict": meta.get("verdict", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "excerpt": doc_text,
                "score": score
            })

    return chunks

# ==========================================
# RAG WORKFLOW & GROUNDED GENERATION
# ==========================================

def answer_legal_query(
    db: Session,
    user_id: str,
    question: str,
    document_id: Optional[str] = None,
    session_id: Optional[str] = None,
    include_public_corpus: bool = False
) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    Complete RAG workflow:
    1. Authenticate & verify ownership.
    2. Auto-index private document chunks if not yet indexed.
    3. Retrieve top-K relevant chunks with user-level isolation.
    4. Optionally augment with relevant public corpus research (Supreme Court precedents / contracts).
    5. Send grounded prompt to active AI provider with prompt injection defense.
    6. Save chat session and messages to database.
    7. Return (answer, sources, session_id).
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

    # 2. Retrieve relevant user document chunks
    user_chunks = retrieve_relevant_chunks(
        user_id=user_id,
        query=question,
        document_id=document_id
    )

    # If document_id was requested but no chunks were found in active collection (e.g. model/dim switch),
    # index into active collection and re-query
    if document_id and not user_chunks and target_doc:
        analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id
        ).first()
        if analysis and analysis.extracted_text:
            index_document_chunks(
                document_id=document_id,
                user_id=user_id,
                filename=target_doc.filename,
                pages=analysis.page_text,
                full_text=analysis.extracted_text,
                force=True
            )
            user_chunks = retrieve_relevant_chunks(
                user_id=user_id,
                query=question,
                document_id=document_id
            )

    # 3. Retrieve relevant public corpus chunks if permitted or needed
    public_chunks: List[Dict[str, Any]] = []
    if include_public_corpus:
        # Determine if query mentions cases/precedents/contracts
        try:
            public_chunks = retrieve_public_corpus_chunks(query=question, top_k=2)
        except Exception as e:
            logger.warning(f"Public corpus retrieval error: {e}")

    # 4. Format context string
    all_sources = []
    context_parts = []

    for c in user_chunks:
        context_parts.append(
            f"[Source Document: {c['document_name']}, Page: {c['page_number']}]\n{c['excerpt']}"
        )
        all_sources.append(c)

    for p in public_chunks:
        cite_str = f" | Citation: {p['citation']}" if p.get("citation") else ""
        context_parts.append(
            f"[Public Precedent: {p['title']} | Court: {p['court']} ({p['year']}){cite_str} | File: {p['filename']}]\n{p['excerpt']}"
        )
        all_sources.append({
            "document_id": p.get("corpus_id", ""),
            "document_name": f"{p.get('title')} ({p.get('citation') or p.get('filename')})",
            "page_number": 1,
            "chunk_index": p.get("chunk_index", 0),
            "excerpt": p.get("excerpt", ""),
            "score": p.get("score")
        })

    if not context_parts:
        answer = "Based on the available document evidence, there is insufficient information to answer this question."
        sources = []
    else:
        context_str = "\n\n---\n\n".join(context_parts)

        # 5. Handle Chat History
        chat_history = []
        if session_id:
            prior_msgs = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).all()
            for msg in prior_msgs:
                chat_history.append({"role": msg.role, "content": msg.content})

        # 6. Generate Grounded Answer
        answer = generate_grounded_answer(
            question=question,
            context=context_str,
            chat_history=chat_history
        )
        sources = all_sources

    # 7. Persist Chat Session & Messages
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
