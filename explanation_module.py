"""Concept explanation using the local LaMini-Flan-T5-783M model.

The model (~3 GB) is downloaded from Hugging Face on first use and cached.
If it cannot be loaded (no internet, not enough RAM, missing torch), the module
falls back to Gemini so the feature keeps working.
"""
import os
import threading

from gemini_client import generate

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "MBZUAI/LaMini-Flan-T5-783M")

_lock = threading.Lock()
_tokenizer = None
_model = None


def _load_model():
    global _tokenizer, _model
    if _model is not None:
        return
    with _lock:
        if _model is not None:
            return
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        print(f"Loading local model {LOCAL_MODEL_NAME} (first run downloads it)...")
        _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL_NAME)
        _model.eval()
        print("Local model ready.")


def explain_topic(topic: str) -> str:
    input_text = f"Explain the concept of '{topic}' in a simple and clear way for a school student."

    try:
        import torch

        _load_model()
        inputs = _tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = _model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                do_sample=True,
            )
        explanation = _tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        if explanation:
            return explanation
    except Exception as e:  # noqa: BLE001
        print(f"[explain] Local model unavailable, falling back to Gemini: {e}")

    try:
        return generate(input_text + " Keep it under 120 words.")
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Error in Explanation: {e}"
