"""
chatbot.py
----------
Reusable AI client for The Ghost of Weak Topics powered by Gemma 4 via Ollama.
Maintains the ghost tutor's pedagogical persona, handles JSON extraction and question
validation, and handles offline/missing model states gracefully.
"""

import os
import json
import re
import time
import requests
from typing import Dict, Any, List, Optional, Tuple

# Configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma4:e2b")
MODEL_TIMEOUT = int(os.environ.get("MODEL_TIMEOUT", "60"))

GHOST_SYSTEM_PROMPT = """You are "The Ghost of Weak Topics" 👻, an ancient, witty, and deeply encouraging scholarly phantom from the Great Hall of Forgotten Knowledge.

Your mission:
Help mortal students conquer their academic fears and eliminate weak topics in Python, Data Structures & Algorithms (DSA), Mathematics, Computer Science, and Basic Science.

Your personality & pedagogical style:
1. Spooky yet warm: Use lighthearted ghost puns (e.g., "floating your way", "haunted by syntax", "spirited learner", "let's exorcise this bug!"), but keep explanations crystal clear.
2. Beginner-friendly: Break down complex topics into intuitive real-world metaphors and bite-sized steps. Never be condescending or excessively verbose.
3. Active learning: When a student asks for help, encourage their reasoning. When asked for a hint, give an intuitive clue without giving away the direct answer immediately.
4. Detailed mistake analysis: When explaining errors, explain WHY the incorrect path was tempting, why it fails, and the exact conceptual shift needed to arrive at the truth.
5. Format: Use markdown with bold highlights, bullet points, and syntax-highlighted code blocks where appropriate.
"""


class GemmaModelClient:
    """Handles communication with the local Gemma 4 model via Ollama."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model_name: str = GEMMA_MODEL, timeout: int = MODEL_TIMEOUT):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        self._cached_status: Optional[Dict[str, Any]] = None
        self._cached_status_time: float = 0.0
        self._cache_ttl_seconds: float = 10.0

    def check_connection(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Verifies if Ollama is running and whether the specified Gemma model is installed.
        Caches results for 10 seconds to avoid repeating socket connection timeouts.
        """
        now = time.time()
        if not force_refresh and self._cached_status and (now - self._cached_status_time < self._cache_ttl_seconds):
            return self._cached_status

        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=1.5)
            if resp.status_code != 200:
                result = {
                    "available": False,
                    "status": "error",
                    "model": self.model_name,
                    "message": f"Ollama returned HTTP status {resp.status_code}.",
                    "installed_models": [],
                    "setup_command": f"ollama pull {self.model_name}"
                }
                self._cached_status = result
                self._cached_status_time = now
                return result

            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            # Match model name or tag prefix (e.g. gemma4 or gemma4:e2b or gemma4:latest)
            matched = any(
                self.model_name == m or
                m.startswith(f"{self.model_name}:") or
                (self.model_name.startswith("gemma4") and "gemma4" in m)
                for m in models
            )

            if matched:
                result = {
                    "available": True,
                    "status": "ready",
                    "model": self.model_name,
                    "message": f"Ghost Tutor is active and floating on Gemma 4 ({self.model_name})! 👻",
                    "installed_models": models,
                    "setup_command": f"ollama run {self.model_name}"
                }
            else:
                result = {
                    "available": False,
                    "status": "model_missing",
                    "model": self.model_name,
                    "message": (
                        f"Ollama is running, but the configured Gemma model '{self.model_name}' "
                        f"was not found among installed models."
                    ),
                    "installed_models": models,
                    "setup_command": f"ollama pull {self.model_name}"
                }
            self._cached_status = result
            self._cached_status_time = now
            return result
        except requests.exceptions.ConnectionError:
            result = {
                "available": False,
                "status": "offline",
                "model": self.model_name,
                "message": (
                    f"Could not connect to Ollama server at {self.base_url}. "
                    "Make sure Ollama is installed and running."
                ),
                "installed_models": [],
                "setup_command": f"ollama run {self.model_name}"
            }
            self._cached_status = result
            self._cached_status_time = now
            return result
        except Exception as e:
            result = {
                "available": False,
                "status": "error",
                "model": self.model_name,
                "message": f"Unexpected error checking Gemma model: {str(e)}",
                "installed_models": [],
                "setup_command": f"ollama pull {self.model_name}"
            }
            self._cached_status = result
            self._cached_status_time = now
            return result

    def chat(self, messages: List[Dict[str, str]], student_name: str = "Learner") -> str:
        """
        Sends conversation history to Gemma 4 via Ollama /api/chat.
        Prepends the Ghost system prompt.
        """
        conn_check = self.check_connection()
        if not conn_check["available"]:
            return (
                f"👻 *A cold phantom chill sweeps the chamber...*\n\n"
                f"The Ghost Tutor cannot reach Gemma 4 right now:\n\n"
                f"> **Notice:** {conn_check['message']}\n\n"
                f"**To awaken Gemma 4, run this command in your PowerShell terminal:**\n"
                f"```powershell\n{conn_check['setup_command']}\n```\n"
                f"Once pulled, refresh this page to begin your ghostly tutorial!"
            )

        system_msg = {
            "role": "system",
            "content": f"{GHOST_SYSTEM_PROMPT}\nThe current student's name is: {student_name}."
        }

        # Build payload
        payload_messages = [system_msg] + messages

        payload = {
            "model": self.model_name,
            "messages": payload_messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                result = resp.json()
                content = result.get("message", {}).get("content", "")
                if content.strip():
                    return content.strip()
                return "👻 *The ghostly mist stirs, but no words echoed back... Please rephrase your question!*"
            else:
                return f"👻 *Ectoplasmic interference! Model returned HTTP {resp.status_code}: {resp.text}*"
        except requests.exceptions.Timeout:
            return "👻 *The ethereal connection timed out while consulting the spectral archives. Please try again with a shorter question!*"
        except Exception as e:
            return f"👻 *A mystical disturbance occurred:* {str(e)}"

    def get_hint(self, question_text: str, options: Dict[str, str], topic: str) -> str:
        """Generates a thoughtful, ghost-themed pedagogical hint without revealing the answer."""
        prompt = (
            f"You are tutoring a student on the topic '{topic}'.\n"
            f"Question: {question_text}\n"
            f"Options:\n"
            f"A: {options.get('A', '')}\n"
            f"B: {options.get('B', '')}\n"
            f"C: {options.get('C', '')}\n"
            f"D: {options.get('D', '')}\n\n"
            f"Provide a friendly, ghostly hint (2-3 sentences). "
            f"CRITICAL RULE: DO NOT reveal which option (A, B, C, or D) is correct, nor state the direct answer. "
            f"Instead, highlight the key underlying concept or give a small clue to trigger the student's own insight."
        )

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages)

    def explain_incorrect_answer(
        self,
        question_text: str,
        selected_key: str,
        selected_text: str,
        correct_key: str,
        correct_text: str,
        topic: str
    ) -> str:
        """Generates a detailed, spooky explanation of why the answer was incorrect."""
        prompt = (
            f"Subject/Topic: {topic}\n"
            f"Question: {question_text}\n"
            f"Student's chosen answer: Option {selected_key}: {selected_text}\n"
            f"True correct answer: Option {correct_key}: {correct_text}\n\n"
            f"Explain kindly and clearly in your ghost tutor voice:\n"
            f"1. Why the student's chosen answer ({selected_key}) is incorrect (what common misconception or trap led there).\n"
            f"2. Why the correct answer ({correct_key}) is true, with a simple analogy or quick code/math example.\n"
            f"3. A ghostly memory tip to never forget this rule again."
        )

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages)

    def generate_quiz_question_ai(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        avoid_questions: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Uses Gemma 4 to generate a new, non-repetitive multiple-choice question.
        Returns validated question dictionary or None if generation failed.
        """
        conn_check = self.check_connection()
        if not conn_check["available"]:
            return None

        avoid_clause = ""
        if avoid_questions:
            recent_sample = avoid_questions[-5:]
            avoid_clause = (
                "\nDo NOT repeat or closely rephrase any of these recent questions:\n- "
                + "\n- ".join(recent_sample)
            )

        prompt = f"""Generate a high-quality educational multiple choice question for a student.
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}{avoid_clause}

Requirements:
1. Question must be clear, unambiguous, and conceptually sound.
2. Provide exactly four options: A, B, C, D.
3. Only ONE option must be objectively correct. The other three must be plausible distractors.
4. Provide a clear, educational explanation of why the correct option is right.
5. Return ONLY a valid JSON object strictly matching this format, with no markdown fences, no surrounding commentary:
{{
    "question": "Clear question text here?",
    "options": {{
        "A": "Option text 1",
        "B": "Option text 2",
        "C": "Option text 3",
        "D": "Option text 4"
    }},
    "correct_answer": "A",
    "explanation": "Spooky-friendly educational explanation."
}}
"""

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.85
                    }
                },
                timeout=self.timeout
            )
            if resp.status_code != 200:
                return None

            raw_text = resp.json().get("response", "").strip()
            return self._parse_and_validate_question(raw_text)
        except Exception:
            return None

    def _parse_and_validate_question(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Strictly parses and validates question format:
        - Must contain question, options (A, B, C, D), correct_answer, and explanation.
        - Options must be distinct, non-empty.
        - correct_answer must strictly be 'A', 'B', 'C', or 'D'.
        """
        try:
            # Strip markdown code blocks if the model wrapped it
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

            # Find outer curly braces
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                return None

            data = json.loads(match.group(0))

            # Validate fields
            question = str(data.get("question", "")).strip()
            if not question or len(question) < 5:
                return None

            options = data.get("options")
            if not isinstance(options, dict):
                return None

            required_keys = {"A", "B", "C", "D"}
            if set(options.keys()) != required_keys:
                return None

            clean_options = {}
            for k in ["A", "B", "C", "D"]:
                val = str(options.get(k, "")).strip()
                if not val:
                    return None
                clean_options[k] = val

            # Check all 4 options are unique
            if len(set(clean_options.values())) != 4:
                return None

            correct = str(data.get("correct_answer", "")).strip().upper()
            if correct not in ["A", "B", "C", "D"]:
                return None

            explanation = str(data.get("explanation", "")).strip()
            if not explanation:
                explanation = f"Option {correct} is the correct answer."

            return {
                "question": question,
                "options": clean_options,
                "correct_answer": correct,
                "explanation": explanation
            }
        except Exception:
            return None


# Global singleton client
ai_client = GemmaModelClient()
