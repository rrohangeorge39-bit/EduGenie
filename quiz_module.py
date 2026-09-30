"""Quiz generation with Gemini (3 MCQs, 4 options each, returned as a Python list)."""
import json
import random
import re

from gemini_client import generate


def clean_json_block(text: str) -> str:
    """Remove Markdown ```json code fences if the model added them."""
    return re.sub(r"```(?:json)?\s*\n?(.*?)```", r"\1", text, flags=re.DOTALL).strip()


def _normalise(items) -> list:
    """Validate the model output and make sure 'answer' exactly matches one option."""
    if isinstance(items, dict):
        items = items.get("questions") or items.get("quiz") or [items]
    if not isinstance(items, list):
        raise ValueError("Quiz JSON is not a list.")

    quiz = []
    for item in items:
        question = str(item.get("question", "")).strip()
        options = [str(o).strip() for o in item.get("options", [])]
        answer = str(item.get("answer", "")).strip()
        if not question or len(options) != 4:
            continue

        # Accept "A"/"B"/"C"/"D" or "A) text" style answers as well as exact text.
        if answer not in options:
            letter = re.match(r"^\(?([A-Da-d])[\).:]?(\s|$)", answer)
            if letter:
                answer = options[ord(letter.group(1).upper()) - 65]
            else:
                lowered = {o.lower(): o for o in options}
                answer = lowered.get(answer.lower(), "")
        if answer not in options:
            continue

        random.shuffle(options)  # LLMs love putting the answer at B; shuffle it
        quiz.append({"question": question, "options": options, "answer": answer})

    if not quiz:
        raise ValueError("The model did not return any valid questions.")
    return quiz[:3]


def generate_quiz(text: str) -> list:
    prompt = f"""
You are a quiz generator.

From the following passage or topic, create 3 multiple-choice questions.
If only a short topic is given (for example "Solar System"), use your own knowledge of that topic.
Each question must include:
- A "question"
- A list of exactly 4 "options" (plain text, do NOT prefix them with A/B/C/D)
- A correct "answer" that must exactly match one of the options.

Format your output as valid JSON only, like this:
[
  {{
    "question": "What is ...?",
    "options": ["Option one", "Option two", "Option three", "Option four"],
    "answer": "Option two"
  }}
]

Passage:
{text}
"""
    raw = generate(prompt, json_output=True)
    cleaned = clean_json_block(raw)
    try:
        return _normalise(json.loads(cleaned))
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse quiz JSON: {e}. Raw output: {cleaned[:300]}") from e
