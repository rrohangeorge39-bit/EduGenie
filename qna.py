"""Question answering with Gemini."""
from gemini_client import generate


def answer_question_with_gemini(question: str) -> str:
    try:
        prompt = (
            "You are EduGenie, a friendly and accurate tutor. "
            "Answer the student's question clearly and concisely (a few sentences unless more is needed).\n\n"
            f"Question: {question}"
        )
        return generate(prompt)
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Error in QnA: {e}"
