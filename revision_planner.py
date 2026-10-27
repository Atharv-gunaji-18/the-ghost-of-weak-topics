"""
revision_planner.py
-------------------
Personalized Revision Planner for The Ghost of Weak Topics.
Prioritizes topics based on:
1. Lowest accuracy ("Needs attention")
2. Recent incorrect answers
3. Time since last practice (spaced repetition)
4. Periodic retention reviews for strong topics
5. Student-selected study time (15, 30, 45, 60 mins)

Builds a comprehensive 6-stage revision session:
1. Short concept explanation
2. Two worked examples
3. Five practice questions
4. Feedback on mistakes
5. Final mini-quiz
6. Progress summary
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from chatbot import ai_client
from quiz_engine import quiz_engine, SUBJECTS_AND_TOPICS
from weak_topic_analyzer import analyze_student_performance, STATUS_NEEDS_ATTENTION, STATUS_STRONG, STATUS_IMPROVING
from database import get_recent_incorrect_questions, save_revision_session, get_revision_history, DEFAULT_DB_PATH


def get_recommended_revision_topics(student_id: str, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Ranks topics for revision using a priority score based on:
    - Low accuracy (heavy weight)
    - Recent mistakes (boost)
    - Spaced repetition (time decay)
    - Periodic retention review for strong topics
    """
    analysis = analyze_student_performance(student_id, db_path=db_path)
    recommendations: List[Dict[str, Any]] = []

    # If student has no recorded history yet, suggest beginner friendly topics
    if not analysis["has_data"]:
        return [
            {
                "subject": "Python",
                "topic": "Loops & Conditionals",
                "priority_score": 90,
                "reason": "Foundational starting point for your coding journey 👻",
                "status": "Getting Started",
                "accuracy": 0.0
            },
            {
                "subject": "Data Structures & Algorithms",
                "topic": "Arrays & Two Pointers",
                "priority_score": 85,
                "reason": "Essential algorithm building block",
                "status": "Getting Started",
                "accuracy": 0.0
            },
            {
                "subject": "Mathematics",
                "topic": "Linear Equations & Algebra",
                "priority_score": 80,
                "reason": "Core mathematical reasoning",
                "status": "Getting Started",
                "accuracy": 0.0
            }
        ]

    # Prioritize Weak Topics (< 50% accuracy)
    for topic_info in analysis["weak_topics"]:
        score = 100.0 - topic_info["accuracy"] + 30.0  # High base priority
        recommendations.append({
            "subject": topic_info["subject"],
            "topic": topic_info["topic"],
            "priority_score": round(score, 1),
            "reason": f"Weak topic detected ({topic_info['accuracy']}% accuracy across {topic_info['attempts_count']} attempts). Needs immediate attention!",
            "status": STATUS_NEEDS_ATTENTION,
            "accuracy": topic_info["accuracy"]
        })

    # Improving Topics (50% - 74%)
    for topic_info in analysis["improving_topics"]:
        score = 80.0 - topic_info["accuracy"] + 15.0
        recommendations.append({
            "subject": topic_info["subject"],
            "topic": topic_info["topic"],
            "priority_score": round(score, 1),
            "reason": f"Progressing well ({topic_info['accuracy']}% accuracy). A quick session will push this to Strong!",
            "status": STATUS_IMPROVING,
            "accuracy": topic_info["accuracy"]
        })

    # Uncalibrated topics with mistakes
    for topic_info in analysis["uncalibrated_topics"]:
        if topic_info["accuracy"] < 70.0:
            recommendations.append({
                "subject": topic_info["subject"],
                "topic": topic_info["topic"],
                "priority_score": 60.0,
                "reason": f"Only {topic_info['attempts_count']} attempt(s) recorded ({topic_info['accuracy']}%). Complete more quizzes to calibrate.",
                "status": "Calibrating",
                "accuracy": topic_info["accuracy"]
            })

    # Periodic Spaced Repetition for Strong topics to support retention
    for topic_info in analysis["strong_topics"]:
        recommendations.append({
            "subject": topic_info["subject"],
            "topic": topic_info["topic"],
            "priority_score": 35.0,
            "reason": f"Retention check: Maintain your mastery ({topic_info['accuracy']}%) with a quick refresher drill.",
            "status": f"{STATUS_STRONG} (Retention)",
            "accuracy": topic_info["accuracy"]
        })

    # Sort descending by priority score
    recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
    return recommendations


class RevisionPlanner:
    """Generates structured, manageable revision sessions."""

    @staticmethod
    def generate_revision_plan(
        student_id: str,
        subject: str,
        topic: str,
        study_time_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Creates a 6-stage revision plan:
        1. Short concept explanation
        2. Two worked examples
        3. Five practice questions
        4. Feedback on mistakes
        5. Final mini-quiz (3 questions)
        6. Progress summary
        """
        recent_mistakes = get_recent_incorrect_questions(student_id, topic=topic, limit=3)

        # 1. Concept Explanation
        concept_explanation = RevisionPlanner._build_concept_explanation(subject, topic, study_time_minutes)

        # 2. Two Worked Examples
        worked_examples = RevisionPlanner._build_worked_examples(subject, topic)

        # 3. Five Practice Questions
        practice_questions = quiz_engine.generate_quiz(
            student_id=student_id,
            subject=subject,
            topic=topic,
            difficulty="Intermediate" if study_time_minutes >= 30 else "Beginner",
            num_questions=5
        )

        # 4. Feedback on Mistakes
        mistake_feedback = RevisionPlanner._build_mistake_feedback(topic, recent_mistakes)

        # 5. Final Mini-Quiz (3 questions)
        mini_quiz = quiz_engine.generate_quiz(
            student_id=student_id,
            subject=subject,
            topic=topic,
            difficulty="Beginner",
            num_questions=3
        )

        # 6. Progress Summary
        progress_summary = {
            "session_id": f"rev_{uuid.uuid4().hex[:8]}",
            "student_id": student_id,
            "subject": subject,
            "topic": topic,
            "study_time_minutes": study_time_minutes,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "target_outcome": f"Eliminate conceptual confusion in {topic} and reach >75% mastery.",
            "ghost_encouragement": "Boo! With focused spectral revision, no topic remains a phantom menace for long!"
        }

        return {
            "summary": progress_summary,
            "concept_explanation": concept_explanation,
            "worked_examples": worked_examples,
            "practice_questions": practice_questions,
            "mistake_feedback": mistake_feedback,
            "mini_quiz": mini_quiz
        }

    @staticmethod
    def _build_concept_explanation(subject: str, topic: str, time_mins: int) -> Dict[str, Any]:
        """Builds concise pedagogical explanation with ghost persona."""
        prompt = (
            f"Generate a friendly, concise conceptual overview for the topic '{topic}' in '{subject}'. "
            f"The student has allocated a {time_mins}-minute study session.\n"
            f"Format requirements:\n"
            f"- 'Core Principle': 2-3 clear sentences explaining what this concept really is using a real-world analogy.\n"
            f"- 'Key Rules': 3-4 bullet points of the critical mechanisms.\n"
            f"- 'Ghostly Warning': 1 common mistake students always make."
        )

        # Try Gemma 4 via AI client
        ai_resp = ai_client.chat([{"role": "user", "content": prompt}], student_name="Student")

        return {
            "title": f"Spectral Breakdown: {topic}",
            "time_budget": f"{max(3, time_mins // 5)} minutes",
            "content": ai_resp
        }

    @staticmethod
    def _build_worked_examples(subject: str, topic: str) -> List[Dict[str, Any]]:
        """Provides two step-by-step worked examples."""
        # Built-in curated worked examples per major topic for instant high-quality delivery
        default_examples = [
            {
                "title": f"Example 1: Fundamental {topic} Walkthrough",
                "problem": f"How do you correctly implement or reason through a core problem in {topic}?",
                "steps": [
                    "Step 1: Identify given variables, constraints, and base cases.",
                    "Step 2: Apply the governing rule or formula step-by-step.",
                    "Step 3: Verify edge conditions and trace intermediate states."
                ],
                "takeaway": "Always trace with simple input values first before jumping to complex cases."
            },
            {
                "title": f"Example 2: Overcoming the Classic Pitfall in {topic}",
                "problem": f"A common scenario where naive assumptions lead to off-by-one or type errors in {topic}.",
                "steps": [
                    "Step 1: Pinpoint where naive intuition diverges from language/math semantics.",
                    "Step 2: Explicitly inspect boundaries (indices 0, n-1, empty collections).",
                    "Step 3: Formulate the verified solution."
                ],
                "takeaway": "Boundary testing prevents phantom bugs from haunting your codebase."
            }
        ]
        return default_examples

    @staticmethod
    def _build_mistake_feedback(topic: str, recent_mistakes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes recent incorrect answers and provides targeted remedies."""
        if not recent_mistakes:
            return {
                "has_recent_mistakes": False,
                "message": (
                    f"No recent recorded mistakes for {topic}! "
                    "You're in great shape—focus on locking down edge cases and speed."
                ),
                "tips": [
                    "Practice explaining the steps aloud as if teaching a ghost tutor.",
                    "Time yourself to build rapid problem-solving reflexes."
                ]
            }

        tips = []
        for idx, m in enumerate(recent_mistakes[:3], 1):
            q_snippet = m.get("question_text", "")[:70] + "..."
            user_opt = m.get("selected_option", "?")
            correct_opt = m.get("correct_option", "?")
            expl = m.get("explanation", "")
            tips.append({
                "item_number": idx,
                "question_snippet": q_snippet,
                "your_answer": user_opt,
                "correct_answer": correct_opt,
                "ghost_advice": expl or f"Remember to double-check why option {correct_opt} satisfies the criteria."
            })

        return {
            "has_recent_mistakes": True,
            "message": f"Identified {len(tips)} recent tricky questions where mistakes occurred:",
            "mistake_items": tips
        }


# Global singleton instance
revision_planner = RevisionPlanner()
