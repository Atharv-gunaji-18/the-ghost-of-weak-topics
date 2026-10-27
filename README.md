# 👻 The Ghost of Weak Topics

> **An adaptive, beginner-friendly AI-powered educational chatbot and revision assistant powered by Gemma 4, Streamlit, and SQLite.**

---

## 📖 1. Project Overview & Problem Statement

Students frequently repeat identical mistakes across quizzes because knowledge gaps and conceptual misconceptions linger unnoticed. **The Ghost of Weak Topics** is a friendly, spirited AI study companion designed to:
- Track quiz performance question-by-question in **Python, DSA, Mathematics, Computer Science, and Basic Science**.
- Automatically detect weak topics using a pedagogical threshold rule.
- Explain why specific answers were incorrect and guide students toward the right solution.
- Generate personalized, time-budgeted revision sessions to eliminate academic gaps.

---

## 🗂️ 2. Project Folder Structure

```text
ghost-of-weak-topics/
├── server.py               # FastAPI full-stack website server & REST API powered by Gemma 4
├── app.py                  # Streamlit multipage application & UI
├── static/                 # Modern responsive website frontend
│   ├── index.html          # Single-Page Web Application UI
│   ├── style.css           # Custom dark cosmic purple & spectral cyan theme
│   └── app.js              # Full-featured client engine, REST integration & dynamic charts
├── chatbot.py              # Gemma 4 AI client & ghost persona via Ollama
├── quiz_engine.py          # Dynamic & curated MCQ generation, scoring & answer validation
├── weak_topic_analyzer.py  # Gap detection engine (<50%, 50-74%, >=75%, 3-attempt rule)
├── revision_planner.py     # 6-stage personalized revision planner
├── database.py             # SQLite persistence layer for students, attempts & questions
├── requirements.txt        # Python dependency manifest
├── README.md               # Complete setup, hardware & troubleshooting documentation
├── .env.example            # Environment configuration template
├── .gitignore              # Files excluded from git tracking
└── tests/
    └── test_core.py        # Automated unit tests for scoring, rules & persistence
```

---

## 🧠 3. Weak Topic Detection Rules

The engine calculates topic accuracy strictly from recorded database answers (never fabricating results):

| Accuracy Range | Classification | Ghost Badge | Reliability Condition |
| :--- | :--- | :--- | :--- |
| **< 50%** | Needs attention | 🔴 `Needs attention` | Requires &ge; 3 attempts |
| **50% – 74.9%** | Improving | 🟡 `Improving` | Requires &ge; 3 attempts |
| **&ge; 75%** | Strong (Mastered) | 🟢 `Strong` | Requires &ge; 3 attempts |
| **Any %** | Uncalibrated | ⚪ `Not enough data` | When attempts &lt; 3 |

---

## 🤖 4. AI Model: Gemma 4 Setup & Compatibility

This application uses Google’s **Gemma 4** open-weights model family running locally via **Ollama**.

### Gemma 4 Variants & Hardware Requirements:

| Variant Tag | Description | Model Download | Minimum RAM / VRAM | Recommended Machine |
| :--- | :--- | :--- | :--- | :--- |
| **`gemma4:e2b`** *(Recommended)* | Edge 2B Lightweight | ~2.5 GB | 4 GB RAM / CPU | Any modern laptop |
| **`gemma4:e4b`** / `gemma4` | Edge 4B Standard | ~4.5 GB | 8 GB RAM / CPU | Standard dev laptops |
| **`gemma4:12b`** | Workstation 12B | ~9.0 GB | 16 GB RAM / 8GB VRAM | High-end laptop or PC |
| **`gemma4:26b`** | Mixture-of-Experts | ~18 GB | 24 GB RAM / GPU | High-spec workstation |

> [!NOTE]
> For standard laptops without a dedicated GPU, **`gemma4:e2b`** is the recommended default. It provides low latency, crisp reasoning, and consumes minimal system resources.

---

## 🚀 5. Installation & Setup Guide (Windows PowerShell in VS Code)

### Step 1: Install Ollama
Download and install Ollama from [ollama.com/download/windows](https://ollama.com/download/windows) or run via Windows Package Manager:
```powershell
winget install Ollama.Ollama
```
Ensure the Ollama application is running (an icon appears in the Windows system tray).

### Step 2: Download Gemma 4
Open Windows PowerShell in VS Code and pull the lightweight Gemma 4 Edge model:
```powershell
ollama pull gemma4:e2b
```
*(Or pull the standard 4B model with `ollama pull gemma4`).*

Verify that the model is loaded and available:
```powershell
ollama list
```
You should see `gemma4:e2b` listed under `NAME`.

### Step 3: Clone or Open the Project
Open VS Code and navigate to the project directory:
```powershell
cd "C:\Users\VTU CS19\.gemini\antigravity\scratch\ghost-of-weak-topics"
```

### Step 4: Create & Activate Python Virtual Environment
```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 5: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default configuration inside `.env`:
```ini
OLLAMA_BASE_URL=http://localhost:11434
GEMMA_MODEL=gemma4:e2b
DB_PATH=ghost_tutor.db
MODEL_TIMEOUT=60
```

---

## 🧪 6. Running Unit Tests

Run the full test suite verifying answer keys, scoring, weak-topic classification thresholds, and persistence:
```powershell
pytest tests/test_core.py -v
```
All tests should pass:
```text
tests/test_core.py::test_evaluate_answer_correct PASSED
tests/test_core.py::test_evaluate_answer_incorrect PASSED
tests/test_core.py::test_topic_status_insufficient_attempts PASSED
tests/test_core.py::test_topic_status_needs_attention PASSED
tests/test_core.py::test_topic_status_improving PASSED
tests/test_core.py::test_topic_status_strong PASSED
tests/test_core.py::test_revision_prioritizes_weak_over_strong PASSED
tests/test_core.py::test_ai_question_validation PASSED
...
```

---

## 🌟 7. Launching the Applications

You can run the project in two flexible modes:

### Mode A: Modern Full-Stack Website (Recommended)
Powered by FastAPI with Gemma 4 backend and dynamic animated single-page frontend:
```powershell
python server.py
```
Open your browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

### Mode B: Streamlit Multipage Application
```powershell
python -m streamlit run app.py
```
Open your browser at:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🎮 8. Feature Walkthrough & Verification

1. **🏠 Home Tab:**
   - View your scholar profile and overall accuracy.
   - Switch or create new student profiles from the sidebar.
2. **👻 Chat with Ghost:**
   - Engage with the Ghost Tutor in real-time.
   - Click one of the quick chips like *"Explain Recursion"* or ask for a hint on a difficult concept.
3. **📝 Take a Quiz:**
   - Select a subject (e.g. *Python*, *DSA*, *Mathematics*, *Computer Science*, *Science*), topic, and difficulty.
   - Click *"💡 Ask Ghost for a Hint"* if you are unsure before submitting.
   - Submit answers to receive immediate educational explanations.
   - Click *"👻 Ask Ghost Why I Was Wrong"* for mistake breakdowns.
4. **🔍 My Weak Topics:**
   - View your topics categorized into 🔴 *Needs attention*, 🟡 *Improving*, 🟢 *Strong*, and ⚪ *Calibrating*.
   - Review recent mistaken questions with their full step-by-step explanations.
5. **📅 Revision Planner:**
   - Choose your study time (15, 30, 45, or 60 minutes).
   - Generate a 6-stage revision session with:
     1. Short Concept Explanation
     2. Two Worked Examples
     3. Five Practice Drills
     4. Feedback on Mistakes
     5. Final Mini-Quiz (3 questions)
     6. Progress Summary & SQLite saving
6. **📊 Progress Dashboard:**
   - Inspect interactive Plotly charts showing accuracy by topic and score progression over time.

---

## 🔧 9. Troubleshooting Guide

### Issue 1: "Could not connect to Ollama server at http://localhost:11434"
- **Cause:** Ollama service is not running.
- **Fix:** Start Ollama from your Windows Start menu or run:
  ```powershell
  ollama serve
  ```

### Issue 2: "Configured Gemma model 'gemma4:e2b' was not found"
- **Cause:** The model has not been pulled yet.
- **Fix:** Run the following command in PowerShell:
  ```powershell
  ollama pull gemma4:e2b
  ```

### Issue 3: "Execution of scripts is disabled on this system"
- **Cause:** Windows PowerShell script execution policy restricts `Activate.ps1`.
- **Fix:** Run this command in your active PowerShell session before activating:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```

### Issue 4: What if I don't have Ollama running yet?
- **Behavior:** The application will display a clear warning banner with setup instructions, but will **never crash**.
- All quizzes, scoring, analytics, and revision planning remain **100% operational** using the built-in curated question vault until Gemma 4 is downloaded!

---

## 📜 10. License & Ethics

Built for educational purposes. Follows ethical AI guidelines:
- Never marks answers correct solely based on AI assertions.
- Validates answer keys objectively.
- Stores progress locally in SQLite without exposing personal data or credentials.
