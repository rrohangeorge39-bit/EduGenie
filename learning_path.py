"""Personalised learning path with Gemini."""
from gemini_client import generate


def get_learning_recommendations(topic: str) -> str:
    prompt = f"""
You are an AI tutor. The student wants to learn about: {topic}.
Suggest a structured and adaptive learning path including key topics, order of learning,
estimated time for each level, and resources (videos, articles, or books).
Include beginner, intermediate, and advanced levels if needed.
Format the answer in Markdown with headings and bullet points.
"""
    try:
        return generate(prompt)
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Error occurred: {e}"
