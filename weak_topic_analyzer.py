"""
weak_topic_analyzer.py
----------------------
Core analytical engine for detecting student learning gaps and topic proficiencies.
Applies the pedagogical thresholds:
- < 50% accuracy: Needs attention 🔴
- 50–74% accuracy: Improving 🟡
- >= 75% accuracy: Strong 🟢
- < 3 attempts: "Not enough data" ⚪

Strictly calculates metrics from recorded database attempts without fabricating data.
"""

from typing import Dict, Any, List, Optional
from database import (
    get_student_topic_stats,
    get_student_quiz_attempts,
    get_recent_incorrect_questions,
    DEFAULT_DB_PATH
)

# Threshold constants per project specification
MIN_ATTEMPTS_REQUIRED = 3
ACCURACY_WEAK_THRESHOLD = 50.0       # Below 50%: Needs attention
ACCURACY_STRONG_THRESHOLD = 75.0     # 75% or above: Strong (50-74%: Improving)

STATUS_NEEDS_ATTENTION = "Needs attention"
STATUS_IMPROVING = "Improving"
STATUS_STRONG = "Strong"
STATUS_NOT_ENOUGH_DATA = "Not enough data"


def classify_topic_status(accuracy: float, attempts_count: int) -> Dict[str, Any]:
    """
    Classifies a topic based on accuracy and minimum attempt threshold.

    Rules:
    - Below 3 attempts: 'Not enough data'
    - >= 3 attempts:
        - < 50%: 'Needs attention'
        - 50% - 74.9%: 'Improving'
        - >= 75%: 'Strong'
    """
    if attempts_count < MIN_ATTEMPTS_REQUIRED:
        remaining = MIN_ATTEMPTS_REQUIRED - attempts_count
        return {
            "status": STATUS_NOT_ENOUGH_DATA,
            "badge": "⚪ Not enough data",
            "color": "#9E9E9E",
            "is_reliable": False,
            "description": f"Need {remaining} more attempt{'s' if remaining > 1 else ''} for reliable classification."
        }

    if accuracy < ACCURACY_WEAK_THRESHOLD:
        return {
            "status": STATUS_NEEDS_ATTENTION,
            "badge": "🔴 Needs attention",
            "color": "#FF4B4B",
            "is_reliable": True,
            "description": f"Accuracy ({accuracy:.1f}%) is below 50%. Immediate revision recommended."
        }
    elif accuracy < ACCURACY_STRONG_THRESHOLD:
        return {
            "status": STATUS_IMPROVING,
            "badge": "🟡 Improving",
            "color": "#FFAA00",
            "is_reliable": True,
            "description": f"Accuracy ({accuracy:.1f}%) is between 50% and 74%. Solid progress, keep practicing."
        }
    else:
        return {
            "status": STATUS_STRONG,
            "badge": "🟢 Strong",
            "color": "#00CC96",
            "is_reliable": True,
            "description": f"Accuracy ({accuracy:.1f}%) is 75% or higher. Mastery achieved!"
        }


def analyze_student_performance(student_id: str, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Performs comprehensive analysis of the student's quiz history.
    Calculates overall statistics and categorizes every practiced topic.
    """
    raw_stats = get_student_topic_stats(student_id, db_path=db_path)
    attempts = get_student_quiz_attempts(student_id, limit=200, db_path=db_path)

    total_quizzes = len(attempts)
    total_questions = sum(a["total_questions"] for a in attempts)
    total_correct = sum(a["score"] for a in attempts)
    overall_accuracy = (total_correct / total_questions * 100.0) if total_questions > 0 else 0.0

    topic_reports: List[Dict[str, Any]] = []
    weak_topics: List[Dict[str, Any]] = []
    improving_topics: List[Dict[str, Any]] = []
    strong_topics: List[Dict[str, Any]] = []
    uncalibrated_topics: List[Dict[str, Any]] = []

    for item in raw_stats:
        subject = item["subject"]
        topic = item["topic"]
        attempts_count = int(item["attempts_count"])
        q_count = int(item["total_questions"])
        correct_count = int(item["total_correct"])
        accuracy = float(item["accuracy"]) if item["accuracy"] is not None else 0.0
        last_practiced = item["last_practiced"]

        classification = classify_topic_status(accuracy, attempts_count)

        report = {
            "subject": subject,
            "topic": topic,
            "attempts_count": attempts_count,
            "total_questions": q_count,
            "total_correct": correct_count,
            "accuracy": round(accuracy, 1),
            "last_practiced": last_practiced,
            "status": classification["status"],
            "badge": classification["badge"],
            "color": classification["color"],
            "is_reliable": classification["is_reliable"],
            "description": classification["description"]
        }

        topic_reports.append(report)

        if classification["status"] == STATUS_NEEDS_ATTENTION:
            weak_topics.append(report)
        elif classification["status"] == STATUS_IMPROVING:
            improving_topics.append(report)
        elif classification["status"] == STATUS_STRONG:
            strong_topics.append(report)
        else:
            uncalibrated_topics.append(report)

    # Sort weak topics by lowest accuracy first
    weak_topics.sort(key=lambda x: x["accuracy"])
    strong_topics.sort(key=lambda x: x["accuracy"], reverse=True)

    # Fetch recent mistakes
    recent_mistakes = get_recent_incorrect_questions(student_id, limit=6, db_path=db_path)

    return {
        "student_id": student_id,
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_accuracy": round(overall_accuracy, 1),
        "topic_reports": topic_reports,
        "weak_topics": weak_topics,
        "improving_topics": improving_topics,
        "strong_topics": strong_topics,
        "uncalibrated_topics": uncalibrated_topics,
        "recent_mistakes": recent_mistakes,
        "has_data": total_quizzes > 0
    }
