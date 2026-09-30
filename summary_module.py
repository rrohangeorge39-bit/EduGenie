"""Summarization with Gemini."""
from gemini_client import generate


def summarize_text(text: str) -> str:
    try:
        prompt = (
            "Summarize the following text in simple language. Keep the key points, "
            "remove redundancy, and stay concise:\n\n"
            f"{text}"
        )
        return generate(prompt)
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Error in Summary: {e}"
