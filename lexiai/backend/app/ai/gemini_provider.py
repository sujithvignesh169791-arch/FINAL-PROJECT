import os
import json
import logging
import time
from typing import List, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import settings
from app.schemas.analysis import LegalAnalysisResult
from app.ai.prompts import (
    LEGAL_ANALYSIS_SYSTEM_INSTRUCTION,
    LEGAL_ANALYSIS_PROMPT,
    LEGAL_CHUNK_ANALYSIS_PROMPT,
    LEGAL_COMBINE_PROMPT,
    RAG_SYSTEM_INSTRUCTION,
    RAG_QUERY_PROMPT
)

logger = logging.getLogger(__name__)

class GeminiProviderError(Exception):
    """Base exception for Gemini provider errors."""
    pass

class GeminiConfigurationError(GeminiProviderError):
    """Raised when Gemini API is improperly configured."""
    pass

class GeminiAPIError(GeminiProviderError):
    """Raised when Gemini API call fails."""
    pass

def get_gemini_client() -> genai.Client:
    """
    Initializes and returns the official Google Gen AI Client using the backend GEMINI_API_KEY.
    Does not log secrets or expose the API key.
    """
    api_key = (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
    if not api_key:
        logger.error("Gemini API key is missing from environment.")
        raise GeminiConfigurationError("GEMINI_API_KEY is not configured in backend environment.")
    
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60.0)
    )

def _retry_api_call(func, max_retries: int = 3, initial_delay: float = 1.0):
    """
    Executes a callable with exponential backoff for transient failures (rate limits, timeouts, 5xx).
    """
    delay = initial_delay
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except APIError as e:
            last_exception = e
            status_code = getattr(e, "code", None)
            # Retry on rate limit (429) or server errors (500, 503)
            if status_code in (429, 500, 503) and attempt < max_retries:
                logger.warning(
                    f"Transient Gemini API error ({status_code}) on attempt {attempt}/{max_retries}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
                delay *= 2.0
            else:
                logger.error(f"Gemini API call failed with status {status_code}: {e.message}")
                raise GeminiAPIError(f"Gemini API error: {e.message}") from e
        except Exception as e:
            last_exception = e
            logger.error(f"Unexpected error during Gemini call on attempt {attempt}: {str(e)[:150]}")
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0
            else:
                raise GeminiAPIError(f"Gemini service error: {str(e)[:150]}") from e

    raise GeminiAPIError(f"Gemini request failed after {max_retries} attempts: {last_exception}")

def analyze_legal_text_structured(
    text: str,
    model_name: Optional[str] = None
) -> LegalAnalysisResult:
    """
    Executes structured document legal analysis with Pydantic validation using the official GenAI SDK.
    """
    client = get_gemini_client()
    active_model = model_name or settings.GEMINI_MODEL

    logger.info(f"Submitting legal document analysis ({len(text)} chars) to model: {active_model}")

    config = types.GenerateContentConfig(
        system_instruction=LEGAL_ANALYSIS_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=LegalAnalysisResult,
        temperature=0.1,
    )

    prompt = LEGAL_ANALYSIS_PROMPT.format(text=text)

    def _call():
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=config
        )
        if response.parsed and isinstance(response.parsed, LegalAnalysisResult):
            return response.parsed
        if response.text:
            data = json.loads(response.text)
            return LegalAnalysisResult.model_validate(data)
        raise GeminiAPIError("Empty or unparsable response received from Gemini.")

    return _retry_api_call(_call)

def analyze_chunk_structured(
    chunk_text: str,
    chunk_index: int,
    total_chunks: int,
    model_name: Optional[str] = None
) -> LegalAnalysisResult:
    """
    Analyzes an individual chunk of a large legal document.
    """
    client = get_gemini_client()
    active_model = model_name or settings.GEMINI_MODEL

    logger.info(f"Analyzing document chunk {chunk_index}/{total_chunks} ({len(chunk_text)} chars)")

    config = types.GenerateContentConfig(
        system_instruction=LEGAL_ANALYSIS_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=LegalAnalysisResult,
        temperature=0.1,
    )

    prompt = LEGAL_CHUNK_ANALYSIS_PROMPT.format(
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        chunk_text=chunk_text
    )

    def _call():
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=config
        )
        if response.parsed and isinstance(response.parsed, LegalAnalysisResult):
            return response.parsed
        if response.text:
            data = json.loads(response.text)
            return LegalAnalysisResult.model_validate(data)
        raise GeminiAPIError(f"Empty response for chunk {chunk_index}.")

    return _retry_api_call(_call)

def combine_chunk_analyses_structured(
    chunk_results: List[LegalAnalysisResult],
    model_name: Optional[str] = None
) -> LegalAnalysisResult:
    """
    Consolidates multiple chunk-level analyses into a unified structured legal analysis.
    """
    client = get_gemini_client()
    active_model = model_name or settings.GEMINI_MODEL

    logger.info(f"Consolidating {len(chunk_results)} chunk analyses into final document analysis.")

    # Convert chunk outputs into clean JSON snippets for consolidation
    chunk_summaries_text = json.dumps(
        [res.model_dump(exclude_unset=True) for res in chunk_results],
        indent=2
    )

    config = types.GenerateContentConfig(
        system_instruction=LEGAL_ANALYSIS_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=LegalAnalysisResult,
        temperature=0.1,
    )

    prompt = LEGAL_COMBINE_PROMPT.format(chunk_summaries=chunk_summaries_text)

    def _call():
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=config
        )
        if response.parsed and isinstance(response.parsed, LegalAnalysisResult):
            return response.parsed
        if response.text:
            data = json.loads(response.text)
            return LegalAnalysisResult.model_validate(data)
        raise GeminiAPIError("Failed to consolidate chunk analyses into final output.")

    return _retry_api_call(_call)

def generate_embeddings(
    texts: List[str],
    model_name: Optional[str] = None
) -> List[List[float]]:
    """
    Generates vector embeddings for a list of texts using the official SDK.
    Validates output dimensions and ensures vector presence.
    """
    if not texts:
        return []

    client = get_gemini_client()
    active_model = model_name or settings.GEMINI_EMBEDDING_MODEL

    logger.info(f"Generating embeddings for {len(texts)} text snippets using model {active_model}")

    def _call():
        response = client.models.embed_content(
            model=active_model,
            contents=texts
        )
        embeddings = []
        if hasattr(response, "embeddings") and response.embeddings:
            for emb in response.embeddings:
                if hasattr(emb, "values") and emb.values:
                    embeddings.append(list(emb.values))
        elif hasattr(response, "embedding") and response.embedding:
            embeddings.append(list(response.embedding.values))

        if len(embeddings) != len(texts):
            raise GeminiAPIError(
                f"Embedding count mismatch: expected {len(texts)}, received {len(embeddings)}"
            )
        return embeddings

    return _retry_api_call(_call)

def generate_grounded_answer(
    question: str,
    context: str,
    chat_history: Optional[List[dict]] = None,
    model_name: Optional[str] = None
) -> str:
    """
    Generates a legally grounded answer to a user query strictly using retrieved context.
    Adheres to untrusted data policies and prompt injection protection.
    """
    client = get_gemini_client()
    active_model = model_name or settings.GEMINI_MODEL

    logger.info(f"Generating grounded RAG answer for query (context size: {len(context)} chars)")

    config = types.GenerateContentConfig(
        system_instruction=RAG_SYSTEM_INSTRUCTION,
        temperature=0.2,
    )

    prompt = RAG_QUERY_PROMPT.format(
        context=context if context.strip() else "[No relevant document excerpts found]",
        question=question
    )

    contents = []
    if chat_history:
        for msg in chat_history[-6:]:  # Keep recent history
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.get("content", ""))]
            ))

    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    ))

    def _call():
        response = client.models.generate_content(
            model=active_model,
            contents=contents,
            config=config
        )
        if response and response.text:
            return response.text.strip()
        return "Based on the available document evidence, there is insufficient information to answer this question."

    return _retry_api_call(_call)
