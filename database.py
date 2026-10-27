"""
database.py
-----------
SQLite persistence layer for The Ghost of Weak Topics educational assistant.
Handles student profiles, quiz attempts, question-level responses, and revision history.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_DB_PATH = os.environ.get("DB_PATH", "ghost_tutor.db")


_INITIALIZED_DBS = set()


def _ensure_schema(db_path: str) -> None:
    """Helper to initialize schema using raw connection to avoid recursion."""
    if db_path in _INITIALIZED_DBS:
        return
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            attempt_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            question_id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            selected_option TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(attempt_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revision_history (
            revision_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            study_time_minutes INTEGER NOT NULL,
            plan_json TEXT NOT NULL,
            mini_quiz_score INTEGER,
            mini_quiz_total INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_student_topic ON quiz_attempts(student_id, topic)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_student_topic ON quiz_questions(student_id, topic)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_correctness ON quiz_questions(student_id, is_correct)")
    conn.commit()
    conn.close()
    _INITIALIZED_DBS.add(db_path)


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a database connection with row factory enabled and auto-initializes tables."""
    _ensure_schema(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes SQLite schema for student progress and quiz tracking."""
    _ensure_schema(db_path)



def create_or_get_student(student_id: str, name: str, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Retrieves or creates a student profile."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()

    now = datetime.now().isoformat()
    if row:
        cursor.execute("UPDATE students SET last_active = ?, name = ? WHERE student_id = ?", (now, name, student_id))
        conn.commit()
        student = dict(row)
        student["name"] = name
        student["last_active"] = now
    else:
        cursor.execute(
            "INSERT INTO students (student_id, name, created_at, last_active) VALUES (?, ?, ?, ?)",
            (student_id, name, now, now)
        )
        conn.commit()
        student = {"student_id": student_id, "name": name, "created_at": now, "last_active": now}

    conn.close()
    return student


def get_all_students(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns a list of all registered students."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY last_active DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_quiz_attempt(
    attempt_id: str,
    student_id: str,
    subject: str,
    topic: str,
    difficulty: str,
    score: int,
    total_questions: int,
    questions_data: List[Dict[str, Any]],
    db_path: str = DEFAULT_DB_PATH
) -> None:
    """
    Saves a completed quiz attempt and its individual question responses atomically.
    """
    accuracy = (score / total_questions * 100.0) if total_questions > 0 else 0.0
    now = datetime.now().isoformat()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO quiz_attempts (
                attempt_id, student_id, subject, topic, difficulty, score, total_questions, accuracy, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (attempt_id, student_id, subject, topic, difficulty, score, total_questions, accuracy, now))

        for idx, q in enumerate(questions_data):
            row_id = f"qq_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
                INSERT INTO quiz_questions (
                    question_id, attempt_id, student_id, subject, topic, difficulty,
                    question_text, option_a, option_b, option_c, option_d,
                    correct_option, selected_option, is_correct, explanation, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row_id,
                attempt_id,
                student_id,
                subject,
                topic,
                difficulty,
                q.get("question", ""),
                q.get("options", {}).get("A", ""),
                q.get("options", {}).get("B", ""),
                q.get("options", {}).get("C", ""),
                q.get("options", {}).get("D", ""),
                q.get("correct_answer", "").strip().upper(),
                q.get("selected_option", "").strip().upper(),
                1 if q.get("is_correct") else 0,
                q.get("explanation", ""),
                now
            ))

        cursor.execute("UPDATE students SET last_active = ? WHERE student_id = ?", (now, student_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_student_quiz_attempts(
    student_id: str,
    subject: Optional[str] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Fetches quiz attempts for a student ordered by recent first."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if subject:
        cursor.execute("""
            SELECT * FROM quiz_attempts
            WHERE student_id = ? AND subject = ?
            ORDER BY completed_at DESC
            LIMIT ?
        """, (student_id, subject, limit))
    else:
        cursor.execute("""
            SELECT * FROM quiz_attempts
            WHERE student_id = ?
            ORDER BY completed_at DESC
            LIMIT ?
        """, (student_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_topic_stats(student_id: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Computes topic-level statistics from recorded question answers:
    - attempts_count: Number of quiz attempts on this topic
    - total_questions: Total questions answered
    - total_correct: Total correct answers
    - accuracy: (total_correct / total_questions) * 100
    - last_practiced: Timestamp of most recent attempt
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            subject,
            topic,
            COUNT(DISTINCT attempt_id) AS attempts_count,
            COUNT(*) AS total_questions,
            SUM(is_correct) AS total_correct,
            ROUND(100.0 * SUM(is_correct) / COUNT(*), 1) AS accuracy,
            MAX(timestamp) AS last_practiced
        FROM quiz_questions
        WHERE student_id = ?
        GROUP BY subject, topic
        ORDER BY accuracy ASC, attempts_count DESC
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_question_texts(
    student_id: str,
    topic: str,
    limit: int = 25,
    db_path: str = DEFAULT_DB_PATH
) -> List[str]:
    """Retrieves recent question texts for a topic to avoid repeating them."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question_text
        FROM quiz_questions
        WHERE student_id = ? AND topic = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (student_id, topic, limit))
    rows = cursor.fetchall()
    conn.close()
    return [r["question_text"] for r in rows]


def get_recent_incorrect_questions(
    student_id: str,
    topic: Optional[str] = None,
    limit: int = 10,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieves questions the student answered incorrectly."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if topic:
        cursor.execute("""
            SELECT * FROM quiz_questions
            WHERE student_id = ? AND topic = ? AND is_correct = 0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (student_id, topic, limit))
    else:
        cursor.execute("""
            SELECT * FROM quiz_questions
            WHERE student_id = ? AND is_correct = 0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (student_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_revision_session(
    revision_id: str,
    student_id: str,
    subject: str,
    topic: str,
    study_time_minutes: int,
    plan_dict: Dict[str, Any],
    mini_quiz_score: Optional[int] = None,
    mini_quiz_total: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> None:
    """Stores a generated revision plan and completed session results."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO revision_history (
            revision_id, student_id, subject, topic, study_time_minutes,
            plan_json, mini_quiz_score, mini_quiz_total, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        revision_id,
        student_id,
        subject,
        topic,
        study_time_minutes,
        json.dumps(plan_dict),
        mini_quiz_score,
        mini_quiz_total,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_revision_history(
    student_id: str,
    limit: int = 15,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieves previous revision sessions for a student."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM revision_history
        WHERE student_id = ?
        ORDER BY completed_at DESC
        LIMIT ?
    """, (student_id, limit))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        try:
            item["plan"] = json.loads(item["plan_json"])
        except Exception:
            item["plan"] = {}
        results.append(item)
    return results


def clear_student_data(student_id: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """Cleans up data for a student (useful for testing or profile reset)."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quiz_questions WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM quiz_attempts WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM revision_history WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()


# Ensure default database schema is initialized on first import
try:
    init_db(DEFAULT_DB_PATH)
except Exception:
    pass

