"""EduGenie - FastAPI backend.

Run with:  uvicorn main:app --reload
"""
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import gemini_client
from explanation_module import explain_topic
from learning_path import get_learning_recommendations
from qna import answer_question_with_gemini
from quiz_module import generate_quiz
from summary_module import summarize_text

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="EduGenie", description="Gemini-powered learning assistant")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class TopicRequest(BaseModel):
    topic: str = ""


class TextRequest(BaseModel):
    text: str = ""


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(content={"error": message}, status_code=400)


# ---------- Frontend ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_key_configured": gemini_client.api_key_configured(),
        "gemini_model": gemini_client.PRIMARY_MODEL,
    }


# ---------- Q&A - GET ----------
@app.get("/qa")
def answer_question(question: str = Query(..., min_length=1)):
    answer = answer_question_with_gemini(question.strip())
    return {"answer": answer}


# ---------- Explanation - POST ----------
@app.post("/explain")
@app.post("/explain/", include_in_schema=False)
def explain_api(payload: TopicRequest):
    topic = payload.topic.strip()
    if not topic:
        return bad_request("Please provide a topic.")
    explanation = explain_topic(topic)
    return {"topic": topic, "explanation": explanation}


# ---------- Summarization - POST ----------
@app.post("/summarize")
@app.post("/summarize/", include_in_schema=False)
def summarize_api(payload: TextRequest):
    text = payload.text.strip()
    if not text:
        return bad_request("Please provide text to summarize.")
    return {"summary": summarize_text(text)}


# ---------- Quiz generation - POST ----------
@app.post("/quiz")
@app.post("/quiz/", include_in_schema=False)
def quiz_api(payload: TextRequest):
    text = payload.text.strip()
    if not text:
        return bad_request("Please provide text or a topic for the quiz.")
    try:
        quiz = generate_quiz(text)
    except Exception as e:  # noqa: BLE001
        return JSONResponse(content={"error": f"Quiz generation failed: {e}"}, status_code=502)
    print("Generated quiz:", quiz)  # DEBUG
    return JSONResponse(content={"quiz": quiz})


# ---------- Learning recommendations - GET ----------
@app.get("/learn/recommendations")
def learning_recommendation_api(topic: str = Query(..., min_length=1)):
    recommendation = get_learning_recommendations(topic.strip())
    return {"topic": topic.strip(), "recommendation": recommendation}
