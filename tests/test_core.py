"""
tests/test_core.py
------------------
Unit test suite verifying scoring, weak-topic detection rules,
revision prioritization, and database persistence.
"""

import os
import sys
import tempfile
import pytest

# Ensure parent project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import (
    init_db,
    create_or_get_student,
    save_quiz_attempt,
    get_student_topic_stats,
    get_recent_question_texts
)
from weak_topic_analyzer import (
    classify_topic_status,
    analyze_student_performance,
    STATUS_NEEDS_ATTENTION,
    STATUS_IMPROVING,
    STATUS_STRONG,
    STATUS_NOT_ENOUGH_DATA
)
from quiz_engine import QuizEngine
from revision_planner import get_recommended_revision_topics


@pytest.fixture
def temp_db():
    """Provides a fresh temporary SQLite database path for isolated testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


# -------------------------------------------------------------
# 1. Scoring & Answer Key Validation Tests
# -------------------------------------------------------------
def test_evaluate_answer_correct():
    q = {
        "question": "What is 2 + 2?",
        "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
        "correct_answer": "B",
        "explanation": "2+2=4"
    }
    is_correct, explanation = QuizEngine.evaluate_answer(q, "B")
    assert is_correct is True
    assert "2+2=4" in explanation


def test_evaluate_answer_incorrect():
    q = {
        "question": "What is 2 + 2?",
        "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
        "correct_answer": "B",
        "explanation": "2+2=4"
    }
    is_correct, _ = QuizEngine.evaluate_answer(q, "A")
    assert is_correct is False


def test_evaluate_answer_case_insensitive_and_whitespace():
    q = {
        "question": "Test?",
        "options": {"A": "Yes", "B": "No", "C": "Maybe", "D": "Never"},
        "correct_answer": "C"
    }
    is_correct, _ = QuizEngine.evaluate_answer(q, " c ")
    assert is_correct is True


# -------------------------------------------------------------
# 2. Weak Topic Detection Rules Tests
# -------------------------------------------------------------
def test_topic_status_insufficient_attempts():
    """Fewer than 3 attempts must yield 'Not enough data' regardless of accuracy."""
    res_1 = classify_topic_status(accuracy=100.0, attempts_count=1)
    assert res_1["status"] == STATUS_NOT_ENOUGH_DATA
    assert res_1["is_reliable"] is False

    res_2 = classify_topic_status(accuracy=20.0, attempts_count=2)
    assert res_2["status"] == STATUS_NOT_ENOUGH_DATA
    assert res_2["is_reliable"] is False


def test_topic_status_needs_attention():
    """Accuracy < 50% with at least 3 attempts must be 'Needs attention'."""
    res = classify_topic_status(accuracy=49.9, attempts_count=3)
    assert res["status"] == STATUS_NEEDS_ATTENTION
    assert res["is_reliable"] is True


def test_topic_status_improving():
    """Accuracy 50% to 74.9% with at least 3 attempts must be 'Improving'."""
    res_50 = classify_topic_status(accuracy=50.0, attempts_count=3)
    assert res_50["status"] == STATUS_IMPROVING

    res_74 = classify_topic_status(accuracy=74.9, attempts_count=4)
    assert res_74["status"] == STATUS_IMPROVING


def test_topic_status_strong():
    """Accuracy >= 75% with at least 3 attempts must be 'Strong'."""
    res = classify_topic_status(accuracy=75.0, attempts_count=3)
    assert res["status"] == STATUS_STRONG

    res_100 = classify_topic_status(accuracy=100.0, attempts_count=5)
    assert res_100["status"] == STATUS_STRONG


# -------------------------------------------------------------
# 3. Database Persistence & Topic Aggregation Tests
# -------------------------------------------------------------
def test_save_and_retrieve_quiz_attempt(temp_db):
    student = create_or_get_student("std_1", "Alice", db_path=temp_db)
    assert student["name"] == "Alice"

    # Simulate 3 attempts for 'Loops' (2 wrong, 1 right -> 33% accuracy)
    for i in range(3):
        questions_data = [
            {
                "question_id": f"q_{i}",
                "q_idx": 0,
                "question": f"Question {i} about loops",
                "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                "correct_answer": "A",
                "selected_option": "A" if i == 0 else "B",
                "is_correct": (i == 0),
                "explanation": "Loops explanation"
            }
        ]
        save_quiz_attempt(
            attempt_id=f"att_{i}",
            student_id="std_1",
            subject="Python",
            topic="Loops & Conditionals",
            difficulty="Beginner",
            score=1 if i == 0 else 0,
            total_questions=1,
            questions_data=questions_data,
            db_path=temp_db
        )

    stats = get_student_topic_stats("std_1", db_path=temp_db)
    assert len(stats) == 1
    topic_stat = stats[0]
    assert topic_stat["topic"] == "Loops & Conditionals"
    assert topic_stat["attempts_count"] == 3
    assert topic_stat["total_questions"] == 3
    assert topic_stat["total_correct"] == 1
    assert round(topic_stat["accuracy"], 1) == 33.3


def test_avoid_repeating_questions(temp_db):
    create_or_get_student("std_rep", "Bob", db_path=temp_db)
    q_data = [{
        "question_id": "q_abc",
        "question": "What is Python?",
        "options": {"A": "Language", "B": "Snake", "C": "Food", "D": "Car"},
        "correct_answer": "A",
        "selected_option": "A",
        "is_correct": True,
        "explanation": "Language"
    }]
    save_quiz_attempt("att_rep_1", "std_rep", "Python", "General", "Beginner", 1, 1, q_data, db_path=temp_db)

    recent_texts = get_recent_question_texts("std_rep", "General", limit=10, db_path=temp_db)
    assert "What is Python?" in recent_texts


# -------------------------------------------------------------
# 4. Revision Prioritization Tests
# -------------------------------------------------------------
def test_revision_planner_recommendation_new_student(temp_db):
    """A student with no data receives beginner foundational recommendations."""
    recs = get_recommended_revision_topics("std_empty", db_path=temp_db)
    assert len(recs) > 0
    assert recs[0]["status"] == "Getting Started"


def test_revision_prioritizes_weak_over_strong(temp_db):
    """Verifies that a weak topic (<50% accuracy) is ranked above a strong topic (>=75%)."""
    create_or_get_student("std_prio", "Charlie", db_path=temp_db)

    # 3 attempts for 'Weak Topic' with 0% accuracy
    for i in range(3):
        save_quiz_attempt(
            attempt_id=f"att_w_{i}",
            student_id="std_prio",
            subject="Python",
            topic="OOP & Classes",
            difficulty="Beginner",
            score=0,
            total_questions=1,
            questions_data=[{
                "question_id": f"qw_{i}",
                "question": "What is self?",
                "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                "correct_answer": "A",
                "selected_option": "B",
                "is_correct": False,
                "explanation": "Self explanation"
            }],
            db_path=temp_db
        )

    # 3 attempts for 'Strong Topic' with 100% accuracy
    for i in range(3):
        save_quiz_attempt(
            attempt_id=f"att_s_{i}",
            student_id="std_prio",
            subject="Python",
            topic="Variables & Data Types",
            difficulty="Beginner",
            score=1,
            total_questions=1,
            questions_data=[{
                "question_id": f"qs_{i}",
                "question": "What is int?",
                "options": {"A": "Number", "B": "2", "C": "3", "D": "4"},
                "correct_answer": "A",
                "selected_option": "A",
                "is_correct": True,
                "explanation": "Int explanation"
            }],
            db_path=temp_db
        )

    recs = get_recommended_revision_topics("std_prio", db_path=temp_db)
    assert len(recs) >= 2
    # The first recommendation must be the weak topic
    assert recs[0]["topic"] == "OOP & Classes"
    assert recs[0]["status"] == STATUS_NEEDS_ATTENTION
    # The strong topic should still be included for spaced retention review
    strong_rec = next(r for r in recs if r["topic"] == "Variables & Data Types")
    assert "Strong" in strong_rec["status"]
    assert recs[0]["priority_score"] > strong_rec["priority_score"]


# -------------------------------------------------------------
# 5. Question Schema Validation Tests
# -------------------------------------------------------------
def test_ai_question_validation():
    from chatbot import ai_client

    # Valid JSON
    valid_json = """{
        "question": "What is the time complexity of binary search?",
        "options": {
            "A": "O(1)",
            "B": "O(log N)",
            "C": "O(N)",
            "D": "O(N^2)"
        },
        "correct_answer": "B",
        "explanation": "Binary search halves the space each step."
    }"""
    parsed = ai_client._parse_and_validate_question(valid_json)
    assert parsed is not None
    assert parsed["correct_answer"] == "B"
    assert parsed["options"]["B"] == "O(log N)"

    # Invalid: missing option D
    invalid_missing_opt = """{
        "question": "What is Python?",
        "options": {"A": "Lang", "B": "Snake", "C": "Both"},
        "correct_answer": "C",
        "explanation": "Python is both."
    }"""
    assert ai_client._parse_and_validate_question(invalid_missing_opt) is None

    # Invalid: duplicate options
    invalid_duplicate = """{
        "question": "What is 1+1?",
        "options": {"A": "2", "B": "2", "C": "3", "D": "4"},
        "correct_answer": "A",
        "explanation": "1+1=2"
    }"""
    assert ai_client._parse_and_validate_question(invalid_duplicate) is None

    # Invalid: wrong correct_answer key
    invalid_key = """{
        "question": "Sample?",
        "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
        "correct_answer": "Z",
        "explanation": "None"
    }"""
    assert ai_client._parse_and_validate_question(invalid_key) is None

