# EduGenie – Gemini-powered learning assistant

FastAPI backend + HTML/CSS/JS frontend. Features: Q&A, concept explanation (local LaMini-Flan-T5),
summarization, quiz generation, and learning paths (Gemini).

## Quick start
    python -m venv venv
    venv\Scripts\activate          # Windows   (macOS/Linux: source venv/bin/activate)
    pip install -r requirements.txt
    copy .env.example .env         # macOS/Linux: cp .env.example .env   -> then paste your GEMINI_API_KEY
    uvicorn main:app --reload
Open http://127.0.0.1:8000  (API docs: http://127.0.0.1:8000/docs)

## Structure
    main.py               FastAPI app + routes
    gemini_client.py      Shared Gemini client (API key, model fallback)
    explanation_module.py Local LaMini-Flan-T5 explanations (Gemini fallback)
    qna.py                Question answering
    quiz_module.py        Quiz generation (JSON -> validated list)
    summary_module.py     Summarization
    learning_path.py      Learning recommendations
    templates/index.html  Frontend page
    static/style.css      Styling
    static/app.js         Frontend logic
    smoke_test.py         End-to-end API check
