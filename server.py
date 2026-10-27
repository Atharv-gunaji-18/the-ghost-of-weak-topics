"""
server.py
---------
FastAPI web server for The Ghost of Weak Topics website.
Serves RESTful API endpoints powered by Gemma 4 backend and delivers the frontend website.
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import (
    init_db,
    create_or_get_student,
    get_all_students,
    get_student_quiz_attempts,
    save_revision_session,
    get_revision_history
)
from chatbot import ai_client, GEMMA_MODEL, OLLAMA_BASE_URL
from quiz_engine import quiz_engine, QuizEngine, SUBJECTS_AND_TOPICS, DIFFICULTIES
from weak_topic_analyzer import (
    analyze_student_performance,
    STATUS_NEEDS_ATTENTION,
    STATUS_IMPROVING,
    STATUS_STRONG,
    STATUS_NOT_ENOUGH_DATA
)
from revision_planner import revision_planner, get_recommended_revision_topics

# Initialize SQLite database
init_db()

app = FastAPI(
    title="The Ghost of Weak Topics 👻",
    description="Full-stack educational website powered by Gemma 4 via Ollama",
    version="2.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)


# -------------------------------------------------------------
# Pydantic Request Models
# -------------------------------------------------------------
class StudentRequest(BaseModel):
    name: str
    student_id: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    student_name: str = "Learner"
    subject: Optional[str] = None


class HintRequest(BaseModel):
    question_text: str
    options: Dict[str, str]
    topic: str


class ExplainMistakeRequest(BaseModel):
    question_text: str
    selected_key: str
    selected_text: str
    correct_key: str
    correct_text: str
    topic: str


class QuizGenerateRequest(BaseModel):
    student_id: str
    subject: str
    topic: str
    difficulty: str = "Beginner"
    num_questions: int = Field(default=5, ge=1, le=10)


class QuizSubmitRequest(BaseModel):
    student_id: str
    subject: str
    topic: str
    difficulty: str
    questions: List[Dict[str, Any]]
    answers: Dict[int, str]


class RevisionGenerateRequest(BaseModel):
    student_id: str
    subject: str
    topic: str
    study_time_minutes: int = 30


class RevisionSaveRequest(BaseModel):
    revision_id: str
    student_id: str
    subject: str
    topic: str
    study_time_minutes: int
    plan: Dict[str, Any]
    mini_quiz_score: Optional[int] = None
    mini_quiz_total: Optional[int] = None


# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------
@app.get("/api/status")
async def get_gemma_status():
    """Returns real-time status of Gemma 4 connection via Ollama."""
    check = ai_client.check_connection(force_refresh=True)
    return {
        "status": check["status"],
        "available": check["available"],
        "model": check["model"],
        "message": check["message"],
        "installed_models": check["installed_models"],
        "setup_command": check["setup_command"],
        "backend": "Gemma 4 via Ollama",
        "ollama_url": OLLAMA_BASE_URL
    }


@app.get("/api/subjects")
async def get_subjects():
    """Returns available subjects, topics, and difficulties."""
    return {
        "subjects": SUBJECTS_AND_TOPICS,
        "difficulties": DIFFICULTIES
    }


@app.get("/api/students")
async def get_students():
    """Returns registered student profiles."""
    students = get_all_students()
    if not students:
        # Create default initial student
        default_student = create_or_get_student("student_ghost_01", "Alex")
        students = [default_student]
    return {"students": students}


@app.post("/api/students")
async def register_student(req: StudentRequest):
    """Creates or updates a student profile."""
    sid = req.student_id or f"std_{uuid.uuid4().hex[:6]}"
    student = create_or_get_student(sid, req.name.strip())
    return {"student": student}


@app.post("/api/chat")
async def chat_with_ghost(req: ChatRequest):
    """Sends student conversation history to Gemma 4."""
    response_text = ai_client.chat(req.messages, student_name=req.student_name)
    return {
        "role": "assistant",
        "content": response_text,
        "model": ai_client.model_name
    }


@app.post("/api/chat/hint")
async def request_hint(req: HintRequest):
    """Generates a ghostly pedagogical hint from Gemma 4."""
    hint_text = ai_client.get_hint(req.question_text, req.options, req.topic)
    return {"hint": hint_text}


@app.post("/api/chat/explain")
async def explain_mistake(req: ExplainMistakeRequest):
    """Generates a detailed mistake breakdown from Gemma 4."""
    explanation = ai_client.explain_incorrect_answer(
        question_text=req.question_text,
        selected_key=req.selected_key,
        selected_text=req.selected_text,
        correct_key=req.correct_key,
        correct_text=req.correct_text,
        topic=req.topic
    )
    return {"explanation": explanation}


@app.post("/api/quiz/generate")
async def generate_quiz(req: QuizGenerateRequest):
    """Generates an adaptive quiz for the student."""
    questions = quiz_engine.generate_quiz(
        student_id=req.student_id,
        subject=req.subject,
        topic=req.topic,
        difficulty=req.difficulty,
        num_questions=req.num_questions
    )
    return {
        "subject": req.subject,
        "topic": req.topic,
        "difficulty": req.difficulty,
        "total_questions": len(questions),
        "questions": questions
    }


@app.post("/api/quiz/submit")
async def submit_quiz(req: QuizSubmitRequest):
    """Evaluates quiz answers, updates student database, and calculates accuracy."""
    results = QuizEngine.finalize_quiz_attempt(
        student_id=req.student_id,
        subject=req.subject,
        topic=req.topic,
        difficulty=req.difficulty,
        questions=req.questions,
        student_answers={int(k): v for k, v in req.answers.items()}
    )
    return results


@app.get("/api/weak-topics/{student_id}")
async def get_weak_topics(student_id: str):
    """Analyzes student performance using the strict threshold rules."""
    analysis = analyze_student_performance(student_id)
    return analysis


@app.get("/api/revision/recommendations/{student_id}")
async def get_revision_recommendations(student_id: str):
    """Calculates prioritized revision recommendations."""
    recommendations = get_recommended_revision_topics(student_id)
    return {"recommendations": recommendations}


@app.post("/api/revision/generate")
async def generate_revision_session(req: RevisionGenerateRequest):
    """Generates a comprehensive 6-stage revision session."""
    plan = revision_planner.generate_revision_plan(
        student_id=req.student_id,
        subject=req.subject,
        topic=req.topic,
        study_time_minutes=req.study_time_minutes
    )
    return plan


@app.post("/api/revision/save")
async def save_revision(req: RevisionSaveRequest):
    """Persists completed revision session to SQLite."""
    save_revision_session(
        revision_id=req.revision_id,
        student_id=req.student_id,
        subject=req.subject,
        topic=req.topic,
        study_time_minutes=req.study_time_minutes,
        plan_dict=req.plan,
        mini_quiz_score=req.mini_quiz_score,
        mini_quiz_total=req.mini_quiz_total
    )
    return {"status": "saved", "revision_id": req.revision_id}


@app.get("/api/dashboard/{student_id}")
async def get_dashboard_data(student_id: str):
    """Returns KPI metrics and quiz attempts history for visual graphs."""
    analysis = analyze_student_performance(student_id)
    attempts = get_student_quiz_attempts(student_id, limit=50)
    revisions = get_revision_history(student_id, limit=10)
    return {
        "analysis": analysis,
        "attempts": attempts,
        "revisions": revisions
    }


# -------------------------------------------------------------
# Static Website Delivery
# -------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serves the main website homepage."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "Ghost of Weak Topics API is running. Frontend static files loading..."})


if __name__ == "__main__":
    import uvicorn
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    port = int(os.environ.get("PORT", "8000"))
    print(f"[Ghost Tutor] The Ghost of Weak Topics web server starting on http://localhost:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
