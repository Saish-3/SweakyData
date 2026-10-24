import os
import json
import logging
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Default configurations
DEFAULT_OLLAMA_MODEL = os.getenv("GEMMA_MODEL", "gemma4:e4b")
DEFAULT_API_MODEL = os.getenv("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_genai_client():
    """Returns Google GenAI client if GEMINI_API_KEY is available."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key.strip():
        try:
            from google import genai
            from google.genai import types
            return genai.Client(api_key=api_key.strip(), http_options=types.HttpOptions(timeout=30000))
        except Exception as e:
            logger.warning(f"Could not initialize google-genai client: {e}")
    return None


def get_backend_info() -> Dict[str, Any]:
    """
    Checks active LLM provider:
    1. Google GenAI API (Gemma 4 hosted)
    2. Local Ollama (if running)
    3. Offline Fallback
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key.strip():
        return {
            "provider": "google_genai",
            "model": os.getenv("GEMMA_MODEL_ID", DEFAULT_API_MODEL),
            "status": "Online (Gemma 4 API)",
            "key_present": True,
        }

    # Check Ollama
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        resp = requests.get(url, timeout=1.5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {
                "provider": "ollama",
                "model": DEFAULT_OLLAMA_MODEL,
                "status": "Online (Local Ollama)",
                "models": models,
                "key_present": False,
            }
    except Exception:
        pass

    return {
        "provider": "fallback",
        "model": "offline-forensic-engine",
        "status": "Offline (Raw Forensic Proofs)",
        "key_present": False,
    }


def get_model_name() -> str:
    """Returns the configured model name."""
    info = get_backend_info()
    return info.get("model", DEFAULT_API_MODEL)


def check_ollama_status() -> Dict[str, Any]:
    """Backward compatibility helper for Ollama status."""
    info = get_backend_info()
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        resp = requests.get(url, timeout=1.5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {
                "available": True,
                "models": models,
                "current_model": get_model_name(),
                "model_installed": True if models else False,
            }
    except Exception:
        pass
    return {
        "available": False,
        "models": [],
        "current_model": get_model_name(),
        "model_installed": False,
    }


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Attempts to parse JSON from raw text, stripping code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return None


def _ask_genai_api(prompt: str, client, model_id: str) -> Optional[Dict[str, Any]]:
    """Invokes Gemma 4 via Google GenAI SDK with JSON mode."""
    from google.genai import types
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )
    for attempt in range(2):
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            parsed = _extract_json_from_text(resp.text or "")
            if parsed and isinstance(parsed, dict):
                return parsed
        except Exception as e:
            logger.warning(f"Google GenAI API attempt {attempt + 1} error: {e}")
            break
    return None


def _ask_ollama(prompt: str, model_name: str) -> Optional[Dict[str, Any]]:
    """Invokes local Ollama endpoint with JSON format."""
    endpoint = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2},
    }
    for attempt in range(2):
        try:
            resp = requests.post(endpoint, json=payload, timeout=25.0)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                parsed = _extract_json_from_text(content)
                if parsed and isinstance(parsed, dict):
                    return parsed
        except Exception:
            break
    return None


def ask_gemma(prompt: str, fallback_evidence_id: str = "E?", fallback_summary: str = "") -> Dict[str, Any]:
    """
    Unified Gemma interface:
    - Queries Google GenAI API (Gemma 4: gemma-4-26b-a4b-it) when GEMINI_API_KEY is configured.
    - Otherwise queries local Ollama if active.
    - Falls back safely to deterministic evidence facts if offline.
    """
    client = get_genai_client()
    model_id = os.getenv("GEMMA_MODEL_ID", DEFAULT_API_MODEL)

    parsed_result = None

    # Priority 1: Google GenAI API (Gemma 4)
    if client is not None:
        parsed_result = _ask_genai_api(prompt, client, model_id)

    # Priority 2: Ollama Local
    if parsed_result is None:
        parsed_result = _ask_ollama(prompt, os.getenv("GEMMA_MODEL", DEFAULT_OLLAMA_MODEL))

    if parsed_result and isinstance(parsed_result, dict):
        return {
            "evidence_id": parsed_result.get("evidence_id", fallback_evidence_id),
            "explanation": parsed_result.get("explanation", fallback_summary[:120]),
            "severity": str(parsed_result.get("severity", "medium")).lower(),
            "hypothesis": parsed_result.get("hypothesis", "HYPOTHESIS: Identified pattern risks metric distortion."),
            "suggested_fix": parsed_result.get("suggested_fix", "Examine flagged columns prior to training."),
        }

    # Graceful fallback: return facts without crashing
    severity = "high" if "leakage" in prompt.lower() or "duplicate" in prompt.lower() else "medium"
    return {
        "evidence_id": fallback_evidence_id,
        "explanation": f"[Forensic Proof] {fallback_summary}" if fallback_summary else "Evidence proven deterministically by forensic checks.",
        "severity": severity,
        "hypothesis": "HYPOTHESIS: Deterministic findings indicate risk of metric distortion or leakage.",
        "suggested_fix": "Drop or isolate flagged columns and verify deduplication before model training.",
    }
