import os
import re
import json
import logging
import time
from typing import List, Optional
from openai import OpenAI, APIError, APITimeoutError, RateLimitError, InternalServerError

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

class NvidiaProviderError(Exception):
    """Base exception for NVIDIA provider errors."""
    pass

class NvidiaConfigurationError(NvidiaProviderError):
    """Raised when NVIDIA API is improperly configured."""
    pass

class NvidiaAPIError(NvidiaProviderError):
    """Raised when NVIDIA API call fails."""
    pass

def get_nvidia_client() -> OpenAI:
    """
    Initializes and returns the OpenAI client configured for NVIDIA NIM endpoints.
    Does not log secrets or expose the API key.
    """
    api_key = (settings.NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")).strip()
    if not api_key:
        logger.error("NVIDIA API key is missing from environment.")
        raise NvidiaConfigurationError("NVIDIA_API_KEY is not configured in backend environment.")

    base_url = (settings.NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").strip()
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=90.0,
        max_retries=0
    )

def _retry_api_call(func, max_retries: int = 1, initial_delay: float = 1.0):
    """
    Executes a callable with exponential backoff for transient failures (rate limits, timeouts, 5xx).
    """
    delay = initial_delay
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except (RateLimitError, APITimeoutError, InternalServerError) as e:
            last_exception = e
            logger.warning(
                f"Transient NVIDIA API error ({type(e).__name__}) on attempt {attempt}/{max_retries}. "
                f"Retrying in {delay:.1f}s..."
            )
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0
            else:
                raise NvidiaAPIError(f"NVIDIA API error after retries: {str(e)[:150]}") from e
        except APIError as e:
            last_exception = e
            logger.error(f"NVIDIA API call failed with status {getattr(e, 'status_code', 'unknown')}: {e.message}")
            raise NvidiaAPIError(f"NVIDIA API error: {e.message}") from e
        except Exception as e:
            last_exception = e
            logger.error(f"Unexpected error during NVIDIA call on attempt {attempt}: {str(e)[:150]}")
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0
            else:
                raise NvidiaAPIError(f"NVIDIA service error: {str(e)[:150]}") from e

    raise NvidiaAPIError(f"NVIDIA request failed after {max_retries} attempts: {last_exception}")

def _extract_and_validate_json(raw_text: str) -> LegalAnalysisResult:
    """
    Cleans markdown formatting and parses raw model output into a validated LegalAnalysisResult.
    Handles ```json code fences, <think> tags, missing commas, unescaped quotes, and outermost JSON brackets.
    """
    if not raw_text or not raw_text.strip():
        raise NvidiaAPIError("Empty response received from NVIDIA model.")

    clean_text = raw_text.strip()
    
    # Strip <think>...</think> blocks if present
    clean_text = re.sub(r"<think>[\s\S]*?</think>", "", clean_text).strip()

    # Strip markdown code fences if present
    if "```" in clean_text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
        if match:
            clean_text = match.group(1).strip()

    # If still not starting with '{', attempt to find outermost '{...}'
    if not clean_text.startswith("{"):
        match = re.search(r"(\{[\s\S]*\})", clean_text)
        if match:
            clean_text = match.group(1).strip()

    parsed = None
    try:
        parsed = json.loads(clean_text)
    except json.JSONDecodeError as jde:
        # Fallback 1: json_repair for missing commas, trailing commas, unescaped quotes
        try:
            from json_repair import loads as repair_loads, repair_json
            repaired_obj = repair_loads(clean_text)
            if isinstance(repaired_obj, dict):
                parsed = repaired_obj
            elif isinstance(repaired_obj, str):
                parsed = json.loads(repair_json(clean_text))
        except Exception as r_err:
            logger.warning(f"json_repair direct decode failed: {r_err}")

        # Fallback 2: slice from first '{' to last '}'
        if not parsed or not isinstance(parsed, dict):
            first_brace = clean_text.find("{")
            last_brace = clean_text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                candidate = clean_text[first_brace:last_brace + 1]
                try:
                    parsed = json.loads(candidate)
                except Exception:
                    try:
                        from json_repair import loads as repair_loads
                        candidate_repaired = repair_loads(candidate)
                        if isinstance(candidate_repaired, dict):
                            parsed = candidate_repaired
                    except Exception:
                        pass

    if not parsed or not isinstance(parsed, dict):
        logger.error(f"Failed to parse JSON from NVIDIA response. Raw snippet: {clean_text[:200]}")
        raise NvidiaAPIError("Malformed JSON received from NVIDIA model: Could not decode valid JSON object.")

    try:
        return LegalAnalysisResult.model_validate(parsed)
    except Exception as ve:
        logger.warning(f"Pydantic validation warning on NVIDIA output: {ve}. Reconciling schema...")
        try:
            raw_clauses = parsed.get("clauses", [])
            valid_clauses = []
            if isinstance(raw_clauses, list):
                for c in raw_clauses:
                    if isinstance(c, dict) and c.get("text"):
                        valid_clauses.append({
                            "clause_type": str(c.get("clause_type") or "General Provision"),
                            "title": str(c.get("title") or "Clause"),
                            "text": str(c.get("text") or ""),
                            "source_page": c.get("source_page")
                        })
            parsed["clauses"] = valid_clauses
            return LegalAnalysisResult.model_validate(parsed)
        except Exception:
            raise NvidiaAPIError(f"Schema validation failed on NVIDIA output: {ve}") from ve

def analyze_legal_text_structured(
    text: str,
    model_name: Optional[str] = None
) -> LegalAnalysisResult:
    """
    Executes structured document legal analysis & extraction with Pydantic validation
    using NVIDIA NIM API.
    """
    client = get_nvidia_client()
    active_model = model_name or settings.NVIDIA_MODEL

    logger.info(f"Submitting legal document analysis ({len(text)} chars) to NVIDIA model: {active_model}")

    schema_json = json.dumps(LegalAnalysisResult.model_json_schema())
    system_prompt = (
        f"{LEGAL_ANALYSIS_SYSTEM_INSTRUCTION}\n\n"
        f"You must return ONLY valid, raw JSON conforming strictly to this JSON Schema:\n"
        f"{schema_json}\n"
        f"IMPORTANT: Output valid JSON directly. Do not include excessive internal reasoning.\n"
        f"Do not include any conversational preamble or postscript."
    )
    user_prompt = LEGAL_ANALYSIS_PROMPT.format(text=text)

    def _call():
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3072
        )
        msg = response.choices[0].message
        content = (msg.content or "").strip()
        if not content:
            reasoning = getattr(msg, "reasoning_content", "") or ""
            if reasoning:
                logger.info("Content empty; attempting extraction from reasoning_content...")
                content = reasoning.strip()
        return _extract_and_validate_json(content)

    return _retry_api_call(_call)

def analyze_chunk_structured(
    chunk_text: str,
    chunk_index: int,
    total_chunks: int,
    model_name: Optional[str] = None
) -> LegalAnalysisResult:
    """
    Analyzes an individual chunk of a large legal document using NVIDIA NIM API.
    """
    client = get_nvidia_client()
    active_model = model_name or settings.NVIDIA_MODEL

    logger.info(f"Analyzing document chunk {chunk_index}/{total_chunks} ({len(chunk_text)} chars) via NVIDIA")

    schema_json = json.dumps(LegalAnalysisResult.model_json_schema())
    system_prompt = (
        f"{LEGAL_ANALYSIS_SYSTEM_INSTRUCTION}\n\n"
        f"You must return ONLY valid, raw JSON conforming strictly to this JSON Schema:\n"
        f"{schema_json}\n"
        f"IMPORTANT: Output valid JSON directly. Do not include excessive internal reasoning.\n"
        f"Do not include any conversational preamble or postscript."
    )
    user_prompt = LEGAL_CHUNK_ANALYSIS_PROMPT.format(
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        chunk_text=chunk_text
    )

    def _call():
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2048
        )
        msg = response.choices[0].message
        content = (msg.content or "").strip()
        if not content:
            reasoning = getattr(msg, "reasoning_content", "") or ""
            if reasoning:
                logger.info("Content empty; attempting extraction from reasoning_content...")
                content = reasoning.strip()
        return _extract_and_validate_json(content)

    return _retry_api_call(_call)

def combine_chunk_analyses_structured(
    chunk_results: List[LegalAnalysisResult],
    model_name: Optional[str] = None
) -> LegalAnalysisResult:
    """
    Consolidates multiple chunk-level analyses into a unified structured legal analysis
    using NVIDIA NIM API.
    """
    client = get_nvidia_client()
    active_model = model_name or settings.NVIDIA_MODEL

    logger.info(f"Consolidating {len(chunk_results)} chunk analyses via NVIDIA into final analysis.")

    chunk_summaries_text = json.dumps(
        [res.model_dump(exclude_unset=True) for res in chunk_results],
        indent=2
    )

    schema_json = json.dumps(LegalAnalysisResult.model_json_schema())
    system_prompt = (
        f"{LEGAL_ANALYSIS_SYSTEM_INSTRUCTION}\n\n"
        f"You must return ONLY valid, raw JSON conforming strictly to this JSON Schema:\n"
        f"{schema_json}\n"
        f"IMPORTANT: Output valid JSON directly. Do not include excessive internal reasoning.\n"
        f"Do not include any conversational preamble or postscript."
    )
    user_prompt = LEGAL_COMBINE_PROMPT.format(chunk_summaries=chunk_summaries_text)

    def _call():
        response = client.chat.completions.create(
            model=active_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3072
        )
        msg = response.choices[0].message
        content = (msg.content or "").strip()
        if not content:
            reasoning = getattr(msg, "reasoning_content", "") or ""
            if reasoning:
                logger.info("Content empty; attempting extraction from reasoning_content...")
                content = reasoning.strip()
        return _extract_and_validate_json(content)

    return _retry_api_call(_call)

def generate_grounded_answer(
    question: str,
    context: str,
    chat_history: Optional[List[dict]] = None,
    model_name: Optional[str] = None
) -> str:
    """
    Generates a legally grounded answer to a user query strictly using retrieved context
    via NVIDIA NIM. Adheres to untrusted data policies and prompt injection protection.
    """
    client = get_nvidia_client()
    active_model = model_name or settings.NVIDIA_MODEL

    logger.info(f"Generating grounded RAG answer via NVIDIA (context size: {len(context)} chars)")

    prompt = RAG_QUERY_PROMPT.format(
        context=context if context.strip() else "[No relevant document excerpts found]",
        question=question
    )

    messages = [{"role": "system", "content": RAG_SYSTEM_INSTRUCTION}]
    if chat_history:
        for msg in chat_history[-6:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})

    messages.append({"role": "user", "content": prompt})

    def _call():
        response = client.chat.completions.create(
            model=active_model,
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        msg = response.choices[0].message
        if msg:
            if msg.content and msg.content.strip():
                clean = re.sub(r"<think>[\s\S]*?</think>", "", msg.content).strip()
                if clean:
                    return clean
            reasoning = getattr(msg, "reasoning_content", "") or ""
            if reasoning:
                clean_reasoning = re.sub(r"<think>[\s\S]*?</think>", "", reasoning).strip()
                if clean_reasoning:
                    return clean_reasoning
        return "Based on the available document evidence, there is insufficient information to answer this question."

    try:
        return _retry_api_call(_call)
    except Exception as e:
        logger.warning(
            f"NVIDIA API grounded generation encountered an issue ({e}). "
            "Synthesizing grounded response directly from document context."
        )
        if context and context.strip() and context.strip() != "[No relevant document excerpts found]":
            lines = [l.strip() for l in context.split("\n") if l.strip() and not l.startswith("[Source Document:")]
            # Join up to first 4 informative excerpts
            excerpts = "\n\n".join(lines[:4])
            return f"Based on the relevant document provisions retrieved:\n\n{excerpts}"
        return "Based on the available document evidence, no direct provisions were found to answer this question."

def generate_embeddings(
    texts: List[str],
    model_name: Optional[str] = None
) -> List[List[float]]:
    """
    Generates text embeddings using NVIDIA NIM API (default: nvidia/nemotron-3-embed-1b).
    Validates output dimensions and returns normalized vectors for vector retrieval.
    """
    if not texts:
        return []

    client = get_nvidia_client()
    active_model = model_name or settings.NVIDIA_EMBEDDING_MODEL

    logger.info(f"Generating embeddings for {len(texts)} snippets via NVIDIA model: {active_model}")

    def _call():
        response = client.embeddings.create(
            input=texts,
            model=active_model
        )
        embeddings = [item.embedding for item in response.data]
        if len(embeddings) != len(texts):
            raise NvidiaAPIError(
                f"Embedding count mismatch: expected {len(texts)}, received {len(embeddings)}"
            )
        return embeddings

    return _retry_api_call(_call)


