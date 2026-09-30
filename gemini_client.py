"""Shared Gemini helper used by qna, quiz, summary and learning-path modules.

Keeps the API key, model name and model fallback logic in one place.
"""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3-flash-preview,gemini-2.5-flash").split(",")
    if m.strip()
]

_client = None
_working_model = None  # remembers the last model that succeeded


class GeminiError(Exception):
    """Raised for configuration problems or when no model could answer."""


def api_key_configured() -> bool:
    return bool(API_KEY) and API_KEY != "your_api_key_here"


def _get_client():
    global _client
    if not api_key_configured():
        raise GeminiError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env and paste your key "
            "from Google AI Studio, then restart the server."
        )
    if _client is None:
        _client = genai.Client(api_key=API_KEY)
    return _client


def _is_model_missing(err: Exception) -> bool:
    msg = str(err)
    return "404" in msg or "NOT_FOUND" in msg or "no longer available" in msg


def generate(prompt: str, json_output: bool = False) -> str:
    """Send a prompt to Gemini and return the response text.

    If a model has been retired (404), the next model in the fallback list is tried.
    """
    global _working_model
    client = _get_client()
    config = types.GenerateContentConfig(response_mime_type="application/json") if json_output else None

    candidates = []
    for m in [_working_model, PRIMARY_MODEL, *FALLBACK_MODELS]:
        if m and m not in candidates:
            candidates.append(m)

    last_error = None
    for model in candidates:
        try:
            response = client.models.generate_content(model=model, contents=prompt, config=config)
            text = (response.text or "").strip()
            if not text:
                raise GeminiError("Gemini returned an empty response (it may have been blocked by safety filters).")
            _working_model = model
            return text
        except Exception as err:  # noqa: BLE001
            last_error = err
            if _is_model_missing(err):
                continue  # try next model
            raise
    raise GeminiError(
        f"None of the configured Gemini models are available ({', '.join(candidates)}). "
        f"Set GEMINI_MODEL in .env to a current model. Last error: {last_error}"
    )
