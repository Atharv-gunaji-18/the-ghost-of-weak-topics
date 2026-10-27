"""
quiz_engine.py
--------------
Adaptive Quiz System for The Ghost of Weak Topics.
Handles question bank management, dynamic AI generation via Gemma 4,
answer evaluation, scoring, and history tracking with repetition avoidance.
"""

import uuid
import random
from typing import Dict, Any, List, Optional, Tuple
from chatbot import ai_client
from database import save_quiz_attempt, get_recent_question_texts, DEFAULT_DB_PATH

# Curated subjects and sub-topics
SUBJECTS_AND_TOPICS = {
    "Python": [
        "Variables & Data Types",
        "Loops & Conditionals",
        "Functions & Scope",
        "Dictionaries & Sets",
        "OOP & Classes",
        "List Comprehensions",
        "Exception Handling"
    ],
    "Data Structures & Algorithms": [
        "Arrays & Two Pointers",
        "Linked Lists",
        "Stacks & Queues",
        "Binary Search",
        "Trees & BSTs",
        "Graph Traversal (BFS/DFS)",
        "Dynamic Programming Basics"
    ],
    "Mathematics": [
        "Linear Equations & Algebra",
        "Calculus & Derivatives",
        "Probability & Combinatorics",
        "Matrices & Linear Algebra",
        "Geometry & Trigonometry"
    ],
    "Computer Science": [
        "OS Processes & Threads",
        "Computer Networks & TCP/IP",
        "Databases & SQL",
        "Computer Architecture & CPU",
        "Cybersecurity Basics"
    ],
    "Basic Science": [
        "Newton's Laws & Mechanics",
        "Chemical Bonding & Reactions",
        "Cell Biology & Genetics",
        "Thermodynamics & Heat",
        "Optics & Light Waves"
    ]
}

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]

# Verified foundational question bank for instant reliability and offline/startup support
CURATED_QUESTION_BANK: List[Dict[str, Any]] = [
    # Python - Variables & Data Types
    {
        "subject": "Python",
        "topic": "Variables & Data Types",
        "difficulty": "Beginner",
        "question": "In Python, which of the following data types is immutable?",
        "options": {
            "A": "list",
            "B": "dict",
            "C": "tuple",
            "D": "set"
        },
        "correct_answer": "C",
        "explanation": "Tuples cannot be modified after creation, making them immutable. Lists, dictionaries, and sets are mutable."
    },
    {
        "subject": "Python",
        "topic": "Variables & Data Types",
        "difficulty": "Intermediate",
        "question": "What is the output of bool([]) in Python?",
        "options": {
            "A": "True",
            "B": "False",
            "C": "None",
            "D": "Raises ValueError"
        },
        "correct_answer": "B",
        "explanation": "In Python, empty collections (such as empty lists, dictionaries, tuples, and sets) evaluate to False in a boolean context."
    },
    {
        "subject": "Python",
        "topic": "Variables & Data Types",
        "difficulty": "Advanced",
        "question": "What does sys.getrefcount(x) return relative to the actual number of references to object x?",
        "options": {
            "A": "The exact reference count",
            "B": "One less than the reference count",
            "C": "One greater than the reference count because passing x to the function creates a temporary reference",
            "D": "Always 0 for small integers"
        },
        "correct_answer": "C",
        "explanation": "Passing an object into sys.getrefcount(x) temporarily increases its reference count by 1 during the function execution."
    },
    # Python - Loops & Conditionals
    {
        "subject": "Python",
        "topic": "Loops & Conditionals",
        "difficulty": "Beginner",
        "question": "When does the 'else' block of a for loop in Python execute?",
        "options": {
            "A": "Only if the loop encounters an error",
            "B": "When the loop completes normally without encountering a break statement",
            "C": "Before the first iteration of the loop begins",
            "D": "Whenever a break statement is executed"
        },
        "correct_answer": "B",
        "explanation": "A loop's 'else' clause executes only when the loop terminates naturally after iterating through all items, never after a break."
    },
    {
        "subject": "Python",
        "topic": "Loops & Conditionals",
        "difficulty": "Intermediate",
        "question": "What will be printed by: for i in range(1, 6, 2): print(i, end=' ')?",
        "options": {
            "A": "1 2 3 4 5",
            "B": "1 3 5",
            "C": "2 4 6",
            "D": "1 3"
        },
        "correct_answer": "B",
        "explanation": "range(start, stop, step) starts at 1, increments by 2, and stops before 6, producing 1, 3, 5."
    },
    # Python - Functions & Scope
    {
        "subject": "Python",
        "topic": "Functions & Scope",
        "difficulty": "Beginner",
        "question": "Which keyword is used to modify a variable defined outside the current local function scope?",
        "options": {
            "A": "extern",
            "B": "global",
            "C": "outer",
            "D": "static"
        },
        "correct_answer": "B",
        "explanation": "The 'global' keyword allows a function to bind a variable name to the module-level scope for re-assignment."
    },
    {
        "subject": "Python",
        "topic": "Functions & Scope",
        "difficulty": "Intermediate",
        "question": "Why is using a mutable default argument like def append_to(item, target=[]): dangerous in Python?",
        "options": {
            "A": "It causes a compilation SyntaxError",
            "B": "The default list is evaluated once when the function is defined, so modifications persist across calls",
            "C": "Python will automatically convert the list to an immutable tuple",
            "D": "It throws an TypeError on the second call"
        },
        "correct_answer": "B",
        "explanation": "Default argument expressions are evaluated once when the function definition is executed, so mutable objects are shared across all calls."
    },
    # Python - Dictionaries & Sets
    {
        "subject": "Python",
        "topic": "Dictionaries & Sets",
        "difficulty": "Beginner",
        "question": "What is the average time complexity for looking up a key in a Python dictionary?",
        "options": {
            "A": "O(N)",
            "B": "O(log N)",
            "C": "O(1)",
            "D": "O(N^2)"
        },
        "correct_answer": "C",
        "explanation": "Python dictionaries use hash tables, offering O(1) average time complexity for lookups, insertions, and deletions."
    },
    # Python - OOP & Classes
    {
        "subject": "Python",
        "topic": "OOP & Classes",
        "difficulty": "Beginner",
        "question": "What is the primary role of the __init__ method in a Python class?",
        "options": {
            "A": "To allocate raw memory for a new object before creation",
            "B": "To initialize the attributes of an instantiated object",
            "C": "To destroy an object when garbage collected",
            "D": "To define static class-level constants"
        },
        "correct_answer": "B",
        "explanation": "The __init__ method acts as the constructor initializer, receiving self to configure attributes on newly created instances."
    },
    # DSA - Arrays & Two Pointers
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Arrays & Two Pointers",
        "difficulty": "Beginner",
        "question": "What is the time complexity of accessing an element in an array by its index?",
        "options": {
            "A": "O(N)",
            "B": "O(1)",
            "C": "O(log N)",
            "D": "O(N log N)"
        },
        "correct_answer": "B",
        "explanation": "Arrays store items contiguously in memory, enabling instant index address computation in O(1) constant time."
    },
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Arrays & Two Pointers",
        "difficulty": "Intermediate",
        "question": "To find two numbers in a sorted array that sum to a target T, what is the optimal two-pointer time complexity?",
        "options": {
            "A": "O(N^2)",
            "B": "O(N log N)",
            "C": "O(N)",
            "D": "O(1)"
        },
        "correct_answer": "C",
        "explanation": "Using left and right pointers moving inward based on the comparison of the current sum with T solves the problem in O(N) time with O(1) auxiliary space."
    },
    # DSA - Linked Lists
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Linked Lists",
        "difficulty": "Beginner",
        "question": "What is the time complexity to insert a new node at the head of a singly linked list with a known head reference?",
        "options": {
            "A": "O(N)",
            "B": "O(log N)",
            "C": "O(1)",
            "D": "O(N^2)"
        },
        "correct_answer": "C",
        "explanation": "Inserting at the head merely requires pointing the new node's next to the old head and updating head, which is O(1)."
    },
    # DSA - Stacks & Queues
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Stacks & Queues",
        "difficulty": "Beginner",
        "question": "Which principle governs the order of operations in a standard Stack data structure?",
        "options": {
            "A": "FIFO (First In, First Out)",
            "B": "LIFO (Last In, First Out)",
            "C": "LILO (Last In, Last Out)",
            "D": "Priority-based"
        },
        "correct_answer": "B",
        "explanation": "A stack operates on LIFO (Last In, First Out): the most recently pushed item is the first one popped."
    },
    # DSA - Binary Search
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Binary Search",
        "difficulty": "Beginner",
        "question": "What fundamental condition must a dataset satisfy before Binary Search can be applied?",
        "options": {
            "A": "It must contain only unique positive integers",
            "B": "The elements must be sorted in monotonic order",
            "C": "The data must be stored in a Linked List",
            "D": "The size must be an exact power of 2"
        },
        "correct_answer": "B",
        "explanation": "Binary search divides the search space in half at each step by comparing the target with the median element, requiring sorted order."
    },
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Binary Search",
        "difficulty": "Intermediate",
        "question": "What is the worst-case time complexity of Binary Search on a sorted array of N elements?",
        "options": {
            "A": "O(1)",
            "B": "O(N)",
            "C": "O(log N)",
            "D": "O(N log N)"
        },
        "correct_answer": "C",
        "explanation": "Each iteration cuts the remaining elements in half, leading to at most floor(log2(N)) + 1 comparisons, or O(log N)."
    },
    # DSA - Trees & BSTs
    {
        "subject": "Data Structures & Algorithms",
        "topic": "Trees & BSTs",
        "difficulty": "Beginner",
        "question": "Which tree traversal of a Binary Search Tree (BST) visits nodes in strictly ascending sorted order?",
        "options": {
            "A": "Pre-order Traversal",
            "B": "In-order Traversal",
            "C": "Post-order Traversal",
            "D": "Level-order Traversal"
        },
        "correct_answer": "B",
        "explanation": "In-order traversal visits (Left Subtree -> Root -> Right Subtree). For any BST, this produces sorted ascending values."
    },
    # Mathematics - Linear Equations & Algebra
    {
        "subject": "Mathematics",
        "topic": "Linear Equations & Algebra",
        "difficulty": "Beginner",
        "question": "If 3x + 7 = 22, what is the value of x?",
        "options": {
            "A": "3",
            "B": "5",
            "C": "7",
            "D": "15"
        },
        "correct_answer": "B",
        "explanation": "Subtract 7 from both sides: 3x = 15. Divide by 3: x = 5."
    },
    {
        "subject": "Mathematics",
        "topic": "Linear Equations & Algebra",
        "difficulty": "Intermediate",
        "question": "What is the slope of a line that is perpendicular to a line with slope m = 4?",
        "options": {
            "A": "4",
            "B": "-4",
            "C": "-1/4",
            "D": "1/4"
        },
        "correct_answer": "C",
        "explanation": "Two perpendicular non-vertical lines have slopes that are negative reciprocals of each other: m2 = -1/m1 = -1/4."
    },
    # Mathematics - Calculus & Derivatives
    {
        "subject": "Mathematics",
        "topic": "Calculus & Derivatives",
        "difficulty": "Beginner",
        "question": "What is the derivative of f(x) = x^3 with respect to x?",
        "options": {
            "A": "3x",
            "B": "3x^2",
            "C": "x^2",
            "D": "3x^4 / 4"
        },
        "correct_answer": "B",
        "explanation": "Using the power rule d/dx [x^n] = n * x^(n-1), the derivative of x^3 is 3 * x^2."
    },
    # Mathematics - Probability & Combinatorics
    {
        "subject": "Mathematics",
        "topic": "Probability & Combinatorics",
        "difficulty": "Beginner",
        "question": "What is the probability of rolling an even number on a standard, fair 6-sided die?",
        "options": {
            "A": "1/6",
            "B": "1/3",
            "C": "1/2",
            "D": "2/3"
        },
        "correct_answer": "C",
        "explanation": "The even outcomes are {2, 4, 6}, which are 3 favorable outcomes out of 6 total possibilities: 3/6 = 1/2."
    },
    # Computer Science - OS Processes & Threads
    {
        "subject": "Computer Science",
        "topic": "OS Processes & Threads",
        "difficulty": "Beginner",
        "question": "What is the primary difference between a process and a thread?",
        "options": {
            "A": "Processes cannot execute code; only threads can",
            "B": "Threads within the same process share memory address space, whereas processes have independent address spaces",
            "C": "A thread always has its own independent heap and file descriptor table",
            "D": "Processes run exclusively on hardware while threads run inside browsers"
        },
        "correct_answer": "B",
        "explanation": "A process has its own isolated memory space. Threads exist within a process and share code, data, and resources."
    },
    {
        "subject": "Computer Science",
        "topic": "OS Processes & Threads",
        "difficulty": "Intermediate",
        "question": "Which of the following is NOT one of Coffman's four conditions required for a Deadlock to occur?",
        "options": {
            "A": "Mutual Exclusion",
            "B": "Hold and Wait",
            "C": "Preemption of Resources",
            "D": "Circular Wait"
        },
        "correct_answer": "C",
        "explanation": "Deadlock requires 'No Preemption'. If resources can be preempted, circular deadlock cannot hold indefinitely."
    },
    # Computer Science - Computer Networks & TCP/IP
    {
        "subject": "Computer Science",
        "topic": "Computer Networks & TCP/IP",
        "difficulty": "Beginner",
        "question": "At which OSI model layer does the IP (Internet Protocol) operate?",
        "options": {
            "A": "Data Link Layer (Layer 2)",
            "B": "Network Layer (Layer 3)",
            "C": "Transport Layer (Layer 4)",
            "D": "Application Layer (Layer 7)"
        },
        "correct_answer": "B",
        "explanation": "The Internet Protocol (IP) handles logical addressing and packet routing at Layer 3 (Network Layer)."
    },
    # Computer Science - Databases & SQL
    {
        "subject": "Computer Science",
        "topic": "Databases & SQL",
        "difficulty": "Beginner",
        "question": "Which SQL clause is used to filter records resulting from an aggregate GROUP BY query?",
        "options": {
            "A": "WHERE",
            "B": "HAVING",
            "C": "ORDER BY",
            "D": "FILTER BY"
        },
        "correct_answer": "B",
        "explanation": "WHERE filters individual rows before aggregation; HAVING filters aggregated groups created by GROUP BY."
    },
    # Basic Science - Newton's Laws & Mechanics
    {
        "subject": "Basic Science",
        "topic": "Newton's Laws & Mechanics",
        "difficulty": "Beginner",
        "question": "According to Newton's Second Law of Motion, what is the formula connecting Force (F), Mass (m), and Acceleration (a)?",
        "options": {
            "A": "F = m / a",
            "B": "F = m * a",
            "C": "F = a / m",
            "D": "F = 1/2 * m * a^2"
        },
        "correct_answer": "B",
        "explanation": "Newton's second law states that Force equals Mass multiplied by Acceleration (F = ma)."
    },
    # Basic Science - Chemical Bonding & Reactions
    {
        "subject": "Basic Science",
        "topic": "Chemical Bonding & Reactions",
        "difficulty": "Beginner",
        "question": "Which type of chemical bond is formed when electrons are shared between two non-metal atoms?",
        "options": {
            "A": "Ionic bond",
            "B": "Covalent bond",
            "C": "Metallic bond",
            "D": "Hydrogen bond"
        },
        "correct_answer": "B",
        "explanation": "A covalent bond involves the sharing of valence electron pairs between atoms, typically non-metals."
    }
]


class QuizEngine:
    """Orchestrates adaptive quiz generation, answer verification, and scoring."""

    def __init__(self):
        self.curated_bank = CURATED_QUESTION_BANK

    def get_topics_for_subject(self, subject: str) -> List[str]:
        """Returns available topics for a subject."""
        return SUBJECTS_AND_TOPICS.get(subject, ["General Concepts"])

    def generate_question(
        self,
        student_id: str,
        subject: str,
        topic: str,
        difficulty: str = "Beginner"
    ) -> Dict[str, Any]:
        """
        Generates a question using Gemma 4 via AI client if available,
        avoiding recently asked questions. Falls back gracefully to curated bank.
        """
        # Fetch recent questions to prevent repetition
        recent_questions = get_recent_question_texts(student_id, topic, limit=20)

        # 1. Try dynamic AI generation with Gemma 4
        ai_question = ai_client.generate_quiz_question_ai(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            avoid_questions=recent_questions
        )

        if ai_question:
            ai_question["source"] = f"Gemma 4 ({ai_client.model_name})"
            ai_question["subject"] = subject
            ai_question["topic"] = topic
            ai_question["difficulty"] = difficulty
            return ai_question

        # 2. Select from curated bank matching subject and topic
        candidates = [
            q for q in self.curated_bank
            if q["subject"] == subject and q["topic"] == topic
        ]

        # Filter out questions student has already seen recently if alternatives exist
        unseen_candidates = [
            q for q in candidates
            if q["question"] not in recent_questions
        ]
        pool = unseen_candidates if unseen_candidates else candidates

        if not pool:
            # Fallback to broader subject match
            subject_pool = [q for q in self.curated_bank if q["subject"] == subject]
            pool = subject_pool if subject_pool else self.curated_bank

        chosen = random.choice(pool).copy()
        chosen["source"] = "Ghost Vault (Curated Bank)"
        chosen["subject"] = subject
        chosen["topic"] = topic
        chosen["difficulty"] = difficulty
        return chosen

    def generate_quiz(
        self,
        student_id: str,
        subject: str,
        topic: str,
        difficulty: str = "Beginner",
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generates a multi-question quiz ensuring unique questions.
        """
        quiz_questions: List[Dict[str, Any]] = []
        seen_texts = set(get_recent_question_texts(student_id, topic, limit=15))

        for idx in range(num_questions):
            # Attempt to get question
            q = self.generate_question(student_id, subject, topic, difficulty)

            # Avoid adding the same question twice in the single quiz
            attempts = 0
            while q["question"] in seen_texts and attempts < 3:
                q = self.generate_question(student_id, subject, topic, difficulty)
                attempts += 1

            q["q_idx"] = idx
            q["question_id"] = f"{uuid.uuid4().hex[:8]}_{idx}"
            seen_texts.add(q["question"])
            quiz_questions.append(q)

        return quiz_questions

    @staticmethod
    def evaluate_answer(
        question_data: Dict[str, Any],
        selected_option: str
    ) -> Tuple[bool, str]:
        """
        Objectively validates student answer against the verified answer key.
        Never marks correct solely because of arbitrary text claims.
        """
        clean_selected = str(selected_option).strip().upper()
        correct_answer = str(question_data.get("correct_answer", "")).strip().upper()

        is_correct = (clean_selected == correct_answer)
        explanation = question_data.get("explanation", "No explanation available.")

        return is_correct, explanation

    @staticmethod
    def finalize_quiz_attempt(
        student_id: str,
        subject: str,
        topic: str,
        difficulty: str,
        questions: List[Dict[str, Any]],
        student_answers: Dict[int, str],
        db_path: str = DEFAULT_DB_PATH
    ) -> Dict[str, Any]:
        """
        Evaluates the full quiz, computes score and accuracy, and persists to SQLite.
        """
        attempt_id = f"attempt_{uuid.uuid4().hex[:12]}"
        total_questions = len(questions)
        score = 0
        recorded_questions: List[Dict[str, Any]] = []

        for idx, q in enumerate(questions):
            selected = student_answers.get(idx, "")
            is_correct, explanation = QuizEngine.evaluate_answer(q, selected)
            if is_correct:
                score += 1

            q_record = q.copy()
            q_record["selected_option"] = selected
            q_record["is_correct"] = is_correct
            q_record["explanation"] = explanation
            recorded_questions.append(q_record)

        accuracy = (score / total_questions * 100.0) if total_questions > 0 else 0.0

        # Save to SQLite database
        save_quiz_attempt(
            attempt_id=attempt_id,
            student_id=student_id,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            score=score,
            total_questions=total_questions,
            questions_data=recorded_questions,
            db_path=db_path
        )

        return {
            "attempt_id": attempt_id,
            "student_id": student_id,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "score": score,
            "total_questions": total_questions,
            "accuracy": round(accuracy, 1),
            "questions": recorded_questions
        }


# Global singleton instance
quiz_engine = QuizEngine()
