"""
app.py
------
Streamlit frontend for The Ghost of Weak Topics 👻
A beginner-friendly AI educational chatbot and adaptive tutor powered by Gemma 4.
"""

import os
import sys
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure local imports work reliably
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
from quiz_engine import quiz_engine, SUBJECTS_AND_TOPICS, DIFFICULTIES
from weak_topic_analyzer import (
    analyze_student_performance,
    STATUS_NEEDS_ATTENTION,
    STATUS_IMPROVING,
    STATUS_STRONG,
    STATUS_NOT_ENOUGH_DATA
)
from revision_planner import revision_planner, get_recommended_revision_topics

# Page configuration
st.set_page_config(
    page_title="The Ghost of Weak Topics 👻",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema
init_db()

# Custom Ghostly Dark Purple & Black CSS
CUSTOM_CSS = """
<style>
    /* Global Theme Overrides */
    .stApp {
        background: radial-gradient(circle at 15% 15%, #18092f 0%, #0c0417 60%, #06020c 100%);
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f061e !important;
        border-right: 1px solid rgba(167, 139, 250, 0.2);
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Spooky Ghost Gradient Header */
    .ghost-title {
        background: linear-gradient(135deg, #A78BFA 0%, #00F0FF 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .ghost-sub {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    /* Cards */
    .ghost-card {
        background: rgba(30, 16, 60, 0.65);
        border: 1px solid rgba(167, 139, 250, 0.25);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }

    .ghost-card-highlight {
        background: linear-gradient(145deg, rgba(45, 20, 85, 0.75), rgba(20, 9, 45, 0.85));
        border: 1px solid rgba(0, 240, 255, 0.4);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.15);
    }

    /* Metrics & Badges */
    .badge-weak {
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }

    .badge-improving {
        background-color: rgba(245, 158, 11, 0.2);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }

    .badge-strong {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }

    .badge-nodata {
        background-color: rgba(148, 163, 184, 0.2);
        color: #94A3B8;
        border: 1px solid rgba(148, 163, 184, 0.4);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6B21A8 0%, #4C1D95 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(167, 139, 250, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #7E22CE 0%, #581C87 100%) !important;
        border-color: #00F0FF !important;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.3) !important;
        transform: translateY(-1px);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(18, 8, 36, 0.7);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(167, 139, 250, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8 !important;
        font-weight: 600;
        border-radius: 6px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(126, 34, 206, 0.4) !important;
        color: #00F0FF !important;
        border-bottom: 2px solid #00F0FF !important;
    }

    /* Callout & Alerts */
    .ghost-alert-warning {
        background: rgba(245, 158, 11, 0.12);
        border-left: 4px solid #F59E0B;
        padding: 12px;
        border-radius: 4px;
        color: #FDE68A;
        margin-bottom: 1rem;
    }
    .ghost-alert-info {
        background: rgba(0, 240, 255, 0.1);
        border-left: 4px solid #00F0FF;
        padding: 12px;
        border-radius: 4px;
        color: #E0F2FE;
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Session state initialization
def init_session_state():
    if "student_id" not in st.session_state:
        st.session_state.student_id = "student_ghost_01"
    if "student_name" not in st.session_state:
        st.session_state.student_name = "Alex"
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "👻 *Boo! Greetings, brave scholar!* I am **The Ghost of Weak Topics**!\n\n"
                    "I lurk in the shadows of your textbooks to track down your academic fears in "
                    "**Python, DSA, Mathematics, Computer Science, and Science**.\n\n"
                    "Ask me anything, or jump into a quiz so we can discover your ghostly weak spots!"
                )
            }
        ]
    if "active_quiz" not in st.session_state:
        st.session_state.active_quiz = None
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_current_q" not in st.session_state:
        st.session_state.quiz_current_q = 0
    if "quiz_results" not in st.session_state:
        st.session_state.quiz_results = None
    if "active_revision_plan" not in st.session_state:
        st.session_state.active_revision_plan = None
    if "active_tab_index" not in st.session_state:
        st.session_state.active_tab_index = 0


init_session_state()

# Ensure active student exists in database
current_student = create_or_get_student(st.session_state.student_id, st.session_state.student_name)

# -------------------------------------------------------------
# Sidebar Configuration & Student Selector
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 👻 Ghost Tutor HQ")
    st.markdown(f"**Current Scholar:** `{st.session_state.student_name}`")

    # Profile switcher / creator
    with st.expander("👤 Student Profile", expanded=False):
        all_students = get_all_students()
        student_names = [s["name"] for s in all_students] if all_students else [st.session_state.student_name]
        
        sel_name = st.selectbox("Select Student Profile", options=student_names, index=0 if student_names else 0)
        new_name = st.text_input("Or register new student name:", placeholder="e.g. Maya")
        if st.button("Switch / Register", use_container_width=True):
            if new_name.strip():
                new_id = f"std_{uuid.uuid4().hex[:6]}"
                create_or_get_student(new_id, new_name.strip())
                st.session_state.student_id = new_id
                st.session_state.student_name = new_name.strip()
                st.rerun()
            elif sel_name:
                matched = next((s for s in all_students if s["name"] == sel_name), None)
                if matched:
                    st.session_state.student_id = matched["student_id"]
                    st.session_state.student_name = matched["name"]
                    st.rerun()

    st.markdown("---")

    # Real-time Gemma 4 Model Status Check
    st.markdown("### 🔮 Gemma 4 Status")
    model_check = ai_client.check_connection()

    if model_check["available"]:
        st.success(f"**Gemma 4 Active** 🟢\n`{ai_client.model_name}` connected via Ollama.")
    else:
        st.warning(
            f"**Model Status:** `{model_check['status']}`\n\n"
            f"{model_check['message']}\n\n"
            f"**Setup Command:**\n```powershell\n{model_check['setup_command']}\n```"
        )
        st.caption("ℹ️ Quizzes and analytical features are fully functional using the built-in verified question vault!")

    st.markdown("---")
    st.markdown("### 📜 Weak Topic Rules")
    st.markdown(
        """
        - 🔴 **< 50% Accuracy:** Needs attention
        - 🟡 **50–74% Accuracy:** Improving
        - 🟢 **>= 75% Accuracy:** Strong
        - ⚪ **< 3 Attempts:** Not enough data
        """
    )
    st.caption("Ghostly accuracy is computed separately per topic using recorded answers only.")

# -------------------------------------------------------------
# Main Application Header
# -------------------------------------------------------------
st.markdown('<div class="ghost-title">The Ghost of Weak Topics 👻</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ghost-sub">Your spectral AI tutor tracking misconceptions, conquering weak topics, '
    'and illuminating your path to academic mastery.</div>',
    unsafe_allow_html=True
)

# Tabs
tabs = st.tabs([
    "🏠 Home",
    "👻 Chat with Ghost",
    "📝 Take a Quiz",
    "🔍 My Weak Topics",
    "📅 Revision Planner",
    "📊 Progress Dashboard"
])

# -------------------------------------------------------------
# TAB 1: HOME
# -------------------------------------------------------------
with tabs[0]:
    st.markdown("### Welcome, Scholar of the Living Realm! 🕯️")
    
    col_welcome, col_stats = st.columns([1.6, 1.0])
    with col_welcome:
        st.markdown(
            """
            <div class="ghost-card-highlight">
                <h4 style="color:#00F0FF; margin-top:0;">Meet Your Spectral Study Companion</h4>
                <p>
                    Every student repeats mistakes because misconceptions linger in the dark.
                    <strong>The Ghost of Weak Topics</strong> is here to shine a lantern on those elusive gaps!
                </p>
                <ul>
                    <li><strong>Adaptive Quizzes:</strong> Practice with 4-choice questions in Python, DSA, Math, CS, and Science.</li>
                    <li><strong>Rigorous Gap Detection:</strong> Topics are analyzed across your answers with our 3-attempt calibration rule.</li>
                    <li><strong>Targeted Revision:</strong> Generate customized revision sessions tailored to your available time.</li>
                    <li><strong>Spooky Ghost Chat:</strong> Ask questions, request hints, and discover why tricky choices failed.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Fetch live performance metrics
    perf = analyze_student_performance(st.session_state.student_id)

    with col_stats:
        st.markdown(
            f"""
            <div class="ghost-card">
                <h4 style="color:#A78BFA; margin-top:0;">Spectral Pulse: {st.session_state.student_name}</h4>
                <p style="font-size:1.6rem; font-weight:800; margin:0; color:#00F0FF;">
                    {perf['overall_accuracy']}% <span style="font-size:0.9rem; color:#94A3B8; font-weight:normal;">Overall Accuracy</span>
                </p>
                <hr style="border-color:rgba(167,139,250,0.2); margin:10px 0;">
                <p style="margin:4px 0;">🎯 <strong>Quizzes Completed:</strong> {perf['total_quizzes']}</p>
                <p style="margin:4px 0;">🔴 <strong>Weak Topics:</strong> {len(perf['weak_topics'])}</p>
                <p style="margin:4px 0;">🟡 <strong>Improving Topics:</strong> {len(perf['improving_topics'])}</p>
                <p style="margin:4px 0;">🟢 <strong>Strong Topics:</strong> {len(perf['strong_topics'])}</p>
                <p style="margin:4px 0;">⚪ <strong>Calibrating (&lt;3 attempts):</strong> {len(perf['uncalibrated_topics'])}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("#### Quick Spectral Portals")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        st.info("🎯 **Test Your Knowledge**\n\nChoose a subject and launch an adaptive quiz.")
    with btn_col2:
        st.warning("🔍 **Inspect Learning Gaps**\n\nReview weak topics and uncalibrated subjects.")
    with btn_col3:
        st.success("📅 **Launch Revision Session**\n\nFollow a 6-stage personalized study plan.")


# -------------------------------------------------------------
# TAB 2: CHAT WITH GHOST
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### 👻 Converse with the Ghost Tutor")
    st.markdown("Ask anything about Python, DSA, Mathematics, CS, or Science. The Ghost explains concepts in simple, spirited terms!")

    # Subject Context Filter
    col_chat_subj, col_chat_chips = st.columns([1, 2])
    with col_chat_subj:
        chat_subject = st.selectbox(
            "Subject Focus:",
            options=["General Knowledge"] + list(SUBJECTS_AND_TOPICS.keys()),
            key="chat_subject_select"
        )

    # Prompt suggestions
    st.markdown("**Quick Invocations:**")
    chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
    quick_prompt = None
    if chip_col1.button("👻 Explain Recursion", use_container_width=True):
        quick_prompt = "Explain recursion in programming like I'm a beginner, using a spooky ghost mirror analogy!"
    if chip_col2.button("💡 Give me a Hint", use_container_width=True):
        quick_prompt = "I'm confused about when to use a hash map (dictionary) vs a list. Can you give me a subtle conceptual hint?"
    if chip_col3.button("🐛 Why did this fail?", use_container_width=True):
        quick_prompt = "In Python, why does `def func(x=[]): x.append(1)` cause unexpected behavior across function calls?"
    if chip_col4.button("📐 Newton's 3rd Law", use_container_width=True):
        quick_prompt = "Explain Newton's Third Law with a fun ghostly example of floating and pushing objects!"

    # Render Chat History
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            avatar = "👻" if msg["role"] == "assistant" else "🧑‍🎓"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # User input handler
    user_input = st.chat_input("Whisper your question into the spectral mist...") or quick_prompt

    if user_input:
        # Append user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant", avatar="👻"):
            with st.spinner("The Ghost of Weak Topics is consulting the ancient scrolls..."):
                ghost_reply = ai_client.chat(
                    messages=st.session_state.chat_messages,
                    student_name=st.session_state.student_name
                )
                st.markdown(ghost_reply)

        st.session_state.chat_messages.append({"role": "assistant", "content": ghost_reply})


# -------------------------------------------------------------
# TAB 3: TAKE A QUIZ
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### 📝 Adaptive Ghost Quiz")
    st.markdown("Test your skills against spectral challenges. Questions adapt to your chosen topic and difficulty.")

    # Quiz Configuration Panel
    if st.session_state.active_quiz is None:
        with st.form("quiz_config_form"):
            col_subj, col_top, col_diff = st.columns(3)
            with col_subj:
                quiz_subj = st.selectbox("Subject:", options=list(SUBJECTS_AND_TOPICS.keys()))
            with col_top:
                topics_avail = quiz_engine.get_topics_for_subject(quiz_subj)
                quiz_top = st.selectbox("Topic:", options=topics_avail)
            with col_diff:
                quiz_diff = st.selectbox("Difficulty:", options=DIFFICULTIES)

            num_q = st.slider("Number of Questions:", min_value=3, max_value=7, value=5)

            start_quiz_btn = st.form_submit_button("👻 Awaken Quiz Questions")

            if start_quiz_btn:
                with st.spinner("Summoning questions from the ethereal vault..."):
                    questions = quiz_engine.generate_quiz(
                        student_id=st.session_state.student_id,
                        subject=quiz_subj,
                        topic=quiz_top,
                        difficulty=quiz_diff,
                        num_questions=num_q
                    )
                    st.session_state.active_quiz = {
                        "subject": quiz_subj,
                        "topic": quiz_top,
                        "difficulty": quiz_diff,
                        "questions": questions,
                        "total": len(questions)
                    }
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_current_q = 0
                    st.session_state.quiz_results = None
                    st.rerun()

    # Active Quiz Playing Interface
    else:
        active = st.session_state.active_quiz
        questions = active["questions"]
        q_idx = st.session_state.quiz_current_q
        current_q = questions[q_idx]

        st.markdown(
            f"**Subject:** `{active['subject']}` | **Topic:** `{active['topic']}` | "
            f"**Difficulty:** `{active['difficulty']}` | **Source:** `{current_q.get('source', 'Vault')}`"
        )
        st.progress((q_idx + 1) / active["total"], text=f"Question {q_idx + 1} of {active['total']}")

        st.markdown(
            f"""
            <div class="ghost-card">
                <h4 style="color:#00F0FF; margin-top:0;">Question {q_idx + 1}:</h4>
                <p style="font-size:1.15rem; font-weight:500;">{current_q['question']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Options
        options = current_q["options"]
        opt_keys = ["A", "B", "C", "D"]
        opt_labels = [f"{k}: {options.get(k, '')}" for k in opt_keys]

        # Use radio button
        prev_choice = st.session_state.quiz_answers.get(q_idx, None)
        selected_label = st.radio(
            "Select your answer:",
            options=opt_labels,
            index=opt_keys.index(prev_choice) if prev_choice in opt_keys else None,
            key=f"q_radio_{q_idx}"
        )

        col_act1, col_act2, col_act3 = st.columns([1, 1, 1.2])

        # Ghost Hint Button
        with col_act1:
            if st.button("💡 Ask Ghost for a Hint", key=f"hint_btn_{q_idx}"):
                with st.spinner("The ghost whispers a secret..."):
                    hint_text = ai_client.get_hint(current_q["question"], options, active["topic"])
                    st.info(f"👻 **Ghost Hint:**\n\n{hint_text}")

        with col_act2:
            if q_idx > 0:
                if st.button("⬅️ Previous Question"):
                    st.session_state.quiz_current_q -= 1
                    st.rerun()

        with col_act3:
            if selected_label:
                selected_key = selected_label.split(":")[0].strip()
                st.session_state.quiz_answers[q_idx] = selected_key

            is_last = (q_idx == active["total"] - 1)
            btn_text = "🏁 Submit Full Quiz" if is_last else "Next Question ➡️"

            if st.button(btn_text, key="next_or_submit"):
                if q_idx not in st.session_state.quiz_answers:
                    st.warning("Please choose an answer before proceeding!")
                else:
                    if is_last:
                        # Finalize Quiz
                        with st.spinner("Evaluating your spectral performance..."):
                            results = QuizEngine.finalize_quiz_attempt(
                                student_id=st.session_state.student_id,
                                subject=active["subject"],
                                topic=active["topic"],
                                difficulty=active["difficulty"],
                                questions=questions,
                                student_answers=st.session_state.quiz_answers
                            )
                            st.session_state.quiz_results = results
                            st.session_state.active_quiz = None
                            st.rerun()
                    else:
                        st.session_state.quiz_current_q += 1
                        st.rerun()

        # Instant check helper
        if q_idx in st.session_state.quiz_answers:
            user_sel = st.session_state.quiz_answers[q_idx]
            correct_ans = current_q["correct_answer"]
            with st.expander("🔍 Inspect Question Feedback", expanded=False):
                if user_sel == correct_ans:
                    st.success(f"🟢 **Option {user_sel} is Correct!**\n\n{current_q['explanation']}")
                else:
                    st.error(f"🔴 **Option {user_sel} is Incorrect.** (Correct: Option {correct_ans})\n\n{current_q['explanation']}")
                    if st.button("👻 Ask Ghost Why I Was Wrong", key=f"why_wrong_{q_idx}"):
                        with st.spinner("Consulting the spectral archives for mistake analysis..."):
                            detailed_why = ai_client.explain_incorrect_answer(
                                question_text=current_q["question"],
                                selected_key=user_sel,
                                selected_text=options.get(user_sel, ""),
                                correct_key=correct_ans,
                                correct_text=options.get(correct_ans, ""),
                                topic=active["topic"]
                            )
                            st.markdown(detailed_why)

        # Cancel / Restart Quiz option
        if st.button("❌ Abandon Quiz", key="abandon_quiz"):
            st.session_state.active_quiz = None
            st.session_state.quiz_answers = {}
            st.rerun()

    # Completed Quiz Results Display
    if st.session_state.quiz_results is not None:
        res = st.session_state.quiz_results
        st.markdown("---")
        st.markdown("### 🏆 Quiz Completed!")
        
        acc = res["accuracy"]
        score_color = "#00CC96" if acc >= 75 else ("#FFAA00" if acc >= 50 else "#FF4B4B")

        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.markdown(
                f"""
                <div class="ghost-card" style="text-align:center;">
                    <h3 style="margin-top:0; color:{score_color}; font-size:2.2rem;">{res['score']} / {res['total_questions']}</h3>
                    <p style="font-size:1.3rem; font-weight:700; margin:0; color:#F8FAFC;">{acc}% Accuracy</p>
                    <p style="color:#94A3B8; margin-top:8px;">{res['subject']} &bull; {res['topic']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with res_col2:
            if acc >= 75:
                st.balloons()
                st.success("👻 **Spooktacular Mastery!** The ghost is thoroughly impressed with your understanding!")
            elif acc >= 50:
                st.warning("👻 **Solid Progress!** You're escaping the phantom clutches, but a quick revision will cement this topic.")
            else:
                st.error("👻 **Phantom Menace Detected!** This topic needs immediate revision. Check the Revision Planner to banish these doubts!")

        # Detailed Question Review
        st.markdown("#### Question-by-Question Breakdown")
        for idx, q_rev in enumerate(res["questions"], 1):
            is_c = q_rev["is_correct"]
            icon = "🟢" if is_c else "🔴"
            user_opt = q_rev["selected_option"]
            corr_opt = q_rev["correct_option"]
            opts = q_rev["options"]

            with st.expander(f"{icon} Question {idx}: {q_rev['question'][:65]}...", expanded=not is_c):
                st.markdown(f"**Full Question:** {q_rev['question']}")
                for k, v in opts.items():
                    marker = "✅ (Correct)" if k == corr_opt else ("❌ (Your Choice)" if k == user_opt and not is_c else "")
                    st.markdown(f"- **{k}:** {v} `{marker}`")
                st.markdown(f"**Explanation:** {q_rev['explanation']}")

        if st.button("👻 Start Another Quiz", key="another_quiz_btn"):
            st.session_state.quiz_results = None
            st.rerun()


# -------------------------------------------------------------
# TAB 4: MY WEAK TOPICS
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### 🔍 Ghostly Weak Topic Radar")
    st.markdown("Automatic detection of knowledge gaps based on your recorded quiz answers.")

    # Status Rule explanation
    st.markdown(
        """
        <div class="ghost-card" style="border-left:4px solid #A78BFA;">
            <strong>Pedagogical Rules:</strong><br>
            🔴 <span class="badge-weak">Needs attention</span>: Accuracy &lt; 50% &bull;
            🟡 <span class="badge-improving">Improving</span>: Accuracy 50%–74% &bull;
            🟢 <span class="badge-strong">Strong</span>: Accuracy &ge; 75% &bull;
            ⚪ <span class="badge-nodata">Not enough data</span>: Minimum 3 attempts required for reliable classification.
        </div>
        """,
        unsafe_allow_html=True
    )

    analysis = analyze_student_performance(st.session_state.student_id)

    if not analysis["has_data"]:
        st.info("👻 No quizzes completed yet! Head over to **'Take a Quiz'** to calibrate your knowledge.")
    else:
        # Category Tabs
        cat_tabs = st.tabs([
            f"All ({len(analysis['topic_reports'])})",
            f"🔴 Needs Attention ({len(analysis['weak_topics'])})",
            f"🟡 Improving ({len(analysis['improving_topics'])})",
            f"🟢 Strong ({len(analysis['strong_topics'])})",
            f"⚪ Calibrating ({len(analysis['uncalibrated_topics'])})"
        ])

        def render_topic_cards(topics_list):
            if not topics_list:
                st.caption("No topics currently in this category.")
                return

            for item in topics_list:
                badge_class = (
                    "badge-weak" if item["status"] == STATUS_NEEDS_ATTENTION else (
                        "badge-improving" if item["status"] == STATUS_IMPROVING else (
                            "badge-strong" if item["status"] == STATUS_STRONG else "badge-nodata"
                        )
                    )
                )

                st.markdown(
                    f"""
                    <div class="ghost-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:#F8FAFC;">{item['topic']} <span style="font-size:0.85rem; color:#94A3B8;">({item['subject']})</span></h4>
                            <span class="{badge_class}">{item['badge']}</span>
                        </div>
                        <p style="margin:8px 0; color:#CBD5E1;">{item['description']}</p>
                        <div style="display:flex; gap:20px; font-size:0.9rem; color:#94A3B8;">
                            <span>📊 <strong>Accuracy:</strong> {item['accuracy']}%</span>
                            <span>🎯 <strong>Attempts:</strong> {item['attempts_count']}</span>
                            <span>📝 <strong>Questions:</strong> {item['total_correct']}/{item['total_questions']} correct</span>
                            <span>🕒 <strong>Last Practiced:</strong> {item['last_practiced'][:10] if item['last_practiced'] else 'N/A'}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with cat_tabs[0]:
            render_topic_cards(analysis["topic_reports"])
        with cat_tabs[1]:
            render_topic_cards(analysis["weak_topics"])
        with cat_tabs[2]:
            render_topic_cards(analysis["improving_topics"])
        with cat_tabs[3]:
            render_topic_cards(analysis["strong_topics"])
        with cat_tabs[4]:
            render_topic_cards(analysis["uncalibrated_topics"])

        # Recent Mistakes Section
        if analysis["recent_mistakes"]:
            st.markdown("#### 🧟 Recent Ghostly Pitfalls (Incorrect Answers)")
            for m in analysis["recent_mistakes"]:
                with st.expander(f"🔴 [{m['subject']}] {m['question_text'][:70]}..."):
                    st.markdown(f"**Question:** {m['question_text']}")
                    st.markdown(f"- **Your Answer:** Option {m['selected_option']}")
                    st.markdown(f"- **Correct Answer:** Option {m['correct_option']}")
                    st.markdown(f"**Explanation:** {m['explanation']}")


# -------------------------------------------------------------
# TAB 5: REVISION PLANNER
# -------------------------------------------------------------
with tabs[4]:
    st.markdown("### 📅 Personalized Spectral Revision Planner")
    st.markdown(
        "Builds a manageable, time-budgeted study session focusing on your weak topics, "
        "recent mistakes, and periodic spaced repetition for retention."
    )

    recommended = get_recommended_revision_topics(st.session_state.student_id)

    col_rev_cfg1, col_rev_cfg2, col_rev_cfg3 = st.columns([1.5, 1, 1])

    with col_rev_cfg1:
        # Display top recommended topics
        topic_options = [f"{r['subject']} - {r['topic']} ({r['status']})" for r in recommended]
        chosen_opt = st.selectbox("Select Target Topic for Revision:", options=topic_options)

    with col_rev_cfg2:
        study_time = st.select_slider(
            "Available Study Time:",
            options=[15, 30, 45, 60],
            value=30,
            format_func=lambda x: f"{x} Minutes"
        )

    with col_rev_cfg3:
        st.markdown("<br>", unsafe_allow_html=True)
        gen_plan_btn = st.button("👻 Conjure Revision Plan", use_container_width=True)

    if gen_plan_btn and chosen_opt:
        # Extract subject and topic
        selected_rec = next(r for r in recommended if f"{r['subject']} - {r['topic']} ({r['status']})" == chosen_opt)
        with st.spinner(f"Crafting {study_time}-minute ghostly revision plan for {selected_rec['topic']}..."):
            plan = revision_planner.generate_revision_plan(
                student_id=st.session_state.student_id,
                subject=selected_rec["subject"],
                topic=selected_rec["topic"],
                study_time_minutes=study_time
            )
            st.session_state.active_revision_plan = plan
            st.session_state.revision_mini_answers = {}
            st.rerun()

    # Active Revision Session Display (6 Required Stages)
    if st.session_state.active_revision_plan is not None:
        plan = st.session_state.active_revision_plan
        summary = plan["summary"]

        st.markdown("---")
        st.markdown(
            f"""
            <div class="ghost-card-highlight">
                <h3 style="color:#00F0FF; margin-top:0;">
                    Spectral Revision Session: {summary['topic']} ({summary['study_time_minutes']} Mins)
                </h3>
                <p style="color:#CBD5E1; margin:0;"><strong>Goal:</strong> {summary['target_outcome']}</p>
                <p style="color:#A78BFA; font-style:italic; margin:4px 0;">{summary['ghost_encouragement']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        rev_stage_tabs = st.tabs([
            "1. Concept Breakdown 📜",
            "2. Worked Examples 🧪",
            "3. Practice Drills (5) 🎯",
            "4. Feedback on Mistakes 💡",
            "5. Final Mini-Quiz 🏁",
            "6. Progress Summary 📈"
        ])

        # Stage 1: Concept Explanation
        with rev_stage_tabs[0]:
            concept = plan["concept_explanation"]
            st.markdown(f"#### {concept['title']} `(Target: {concept['time_budget']})`")
            st.markdown(concept["content"])

        # Stage 2: Worked Examples
        with rev_stage_tabs[1]:
            st.markdown("#### Step-by-Step Problem Walkthroughs")
            for ex in plan["worked_examples"]:
                with st.expander(f"🧪 {ex['title']}", expanded=True):
                    st.markdown(f"**Problem Scenario:** {ex['problem']}")
                    st.markdown("**Logical Steps:**")
                    for s in ex["steps"]:
                        st.markdown(f"- {s}")
                    st.info(f"💡 **Key Takeaway:** {ex['takeaway']}")

        # Stage 3: Five Practice Questions
        with rev_stage_tabs[2]:
            st.markdown("#### 🎯 Five Focused Practice Drills")
            for idx, pq in enumerate(plan["practice_questions"], 1):
                with st.expander(f"Drill {idx}: {pq['question'][:65]}...", expanded=(idx == 1)):
                    st.markdown(f"**Question:** {pq['question']}")
                    for k, v in pq["options"].items():
                        st.markdown(f"- **{k}:** {v}")
                    if st.button(f"Reveal Solution for Drill {idx}", key=f"drill_reveal_{idx}"):
                        st.success(f"🟢 **Answer: Option {pq['correct_answer']}**\n\n{pq['explanation']}")

        # Stage 4: Feedback on Mistakes
        with rev_stage_tabs[3]:
            fb = plan["mistake_feedback"]
            st.markdown("#### 💡 Targeted Guidance on Past Pitfalls")
            st.markdown(fb["message"])
            if fb.get("has_recent_mistakes"):
                for itm in fb.get("mistake_items", []):
                    st.warning(
                        f"**Item {itm['item_number']}:** {itm['question_snippet']}\n\n"
                        f"- Your Choice: `{itm['your_answer']}` | Correct: `{itm['correct_answer']}`\n\n"
                        f"**Ghost Advice:** {itm['ghost_advice']}"
                    )
            else:
                for tip in fb.get("tips", []):
                    st.info(f"✨ {tip}")

        # Stage 5: Final Mini-Quiz (3 questions)
        with rev_stage_tabs[4]:
            st.markdown("#### 🏁 Final Verification Mini-Quiz")
            st.markdown("Test your retention right now with these 3 quick checks!")

            if "revision_mini_answers" not in st.session_state:
                st.session_state.revision_mini_answers = {}

            mini_q_list = plan["mini_quiz"]
            with st.form("mini_quiz_form"):
                for idx, mq in enumerate(mini_q_list):
                    st.markdown(f"**Mini-Question {idx + 1}:** {mq['question']}")
                    options_str = [f"{k}: {v}" for k, v in mq["options"].items()]
                    sel = st.radio(
                        f"Your answer for Q{idx+1}:",
                        options=options_str,
                        key=f"mini_radio_{idx}"
                    )
                    if sel:
                        st.session_state.revision_mini_answers[idx] = sel.split(":")[0].strip()
                    st.markdown("---")

                submit_mini = st.form_submit_button("Submit Mini-Quiz")

                if submit_mini:
                    correct_mini = 0
                    for idx, mq in enumerate(mini_q_list):
                        u_ans = st.session_state.revision_mini_answers.get(idx, "")
                        if u_ans == mq["correct_answer"]:
                            correct_mini += 1

                    # Save revision session to SQLite
                    save_revision_session(
                        revision_id=summary["session_id"],
                        student_id=st.session_state.student_id,
                        subject=summary["subject"],
                        topic=summary["topic"],
                        study_time_minutes=summary["study_time_minutes"],
                        plan_dict=plan,
                        mini_quiz_score=correct_mini,
                        mini_quiz_total=len(mini_q_list)
                    )

                    st.session_state.mini_quiz_finished = {
                        "score": correct_mini,
                        "total": len(mini_q_list)
                    }
                    st.rerun()

            if "mini_quiz_finished" in st.session_state:
                res_mini = st.session_state.mini_quiz_finished
                st.success(
                    f"🎉 **Mini-Quiz Score: {res_mini['score']} / {res_mini['total']}**! "
                    "Session successfully saved to your spectral history."
                )

        # Stage 6: Progress Summary
        with rev_stage_tabs[5]:
            st.markdown("#### 📈 Revision Session Summary")
            st.markdown(
                f"""
                - **Subject:** `{summary['subject']}`
                - **Topic:** `{summary['topic']}`
                - **Study Duration:** `{summary['study_time_minutes']} minutes`
                - **Generated At:** `{summary['generated_at']}`
                - **Spectral Verdict:** Your dedication has banished another layer of academic fog!
                """
            )
            if st.button("Close Revision Session"):
                st.session_state.active_revision_plan = None
                if "mini_quiz_finished" in st.session_state:
                    del st.session_state["mini_quiz_finished"]
                st.rerun()


# -------------------------------------------------------------
# TAB 6: PROGRESS DASHBOARD
# -------------------------------------------------------------
with tabs[5]:
    st.markdown("### 📊 Spectral Analytics & Progress Dashboard")
    st.markdown("Comprehensive visual insights into your mastery, accuracy trends, and quiz history.")

    perf = analyze_student_performance(st.session_state.student_id)
    attempts = get_student_quiz_attempts(st.session_state.student_id, limit=100)

    # KPI Top Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Quizzes", perf["total_quizzes"])
    with kpi2:
        st.metric("Overall Accuracy", f"{perf['overall_accuracy']}%")
    with kpi3:
        st.metric("Weak Topics", len(perf["weak_topics"]))
    with kpi4:
        st.metric("Strong Topics", len(perf["strong_topics"]))

    if not perf["has_data"]:
        st.info("👻 No quizzes recorded yet! Complete your first quiz to generate visual charts.")
    else:
        st.markdown("---")
        chart_col1, chart_col2 = st.columns(2)

        # Plotly Chart 1: Topic Accuracy Bar Chart
        with chart_col1:
            st.markdown("#### 🎯 Topic Accuracy Breakdown")
            df_topics = pd.DataFrame(perf["topic_reports"])
            if not df_topics.empty:
                # Assign colors based on threshold
                color_map = {
                    STATUS_NEEDS_ATTENTION: "#EF4444",
                    STATUS_IMPROVING: "#F59E0B",
                    STATUS_STRONG: "#10B981",
                    STATUS_NOT_ENOUGH_DATA: "#94A3B8"
                }

                fig_bar = px.bar(
                    df_topics,
                    x="accuracy",
                    y="topic",
                    color="status",
                    orientation="h",
                    color_discrete_map=color_map,
                    labels={"accuracy": "Accuracy (%)", "topic": "Topic", "status": "Status"},
                    range_x=[0, 100]
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#E2E8F0",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # Plotly Chart 2: Accuracy Over Time
        with chart_col2:
            st.markdown("#### 📈 Attempt History Trend")
            df_attempts = pd.DataFrame(attempts)
            if not df_attempts.empty:
                df_attempts["attempt_num"] = range(len(df_attempts), 0, -1)
                df_attempts = df_attempts.sort_values("completed_at")

                fig_line = px.line(
                    df_attempts,
                    x="completed_at",
                    y="accuracy",
                    markers=True,
                    labels={"completed_at": "Timestamp", "accuracy": "Accuracy (%)"},
                    range_y=[0, 100]
                )
                fig_line.update_traces(line_color="#00F0FF", marker=dict(size=8, color="#A78BFA"))
                fig_line.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#E2E8F0"
                )
                st.plotly_chart(fig_line, use_container_width=True)

        # Recent Attempts Table
        st.markdown("#### 📜 Recent Quiz Log")
        if not df_attempts.empty:
            display_df = df_attempts[["completed_at", "subject", "topic", "difficulty", "score", "total_questions", "accuracy"]].copy()
            display_df.columns = ["Date & Time", "Subject", "Topic", "Difficulty", "Score", "Total Qs", "Accuracy (%)"]
            st.dataframe(display_df, use_container_width=True)

        # Previous Revision Sessions
        st.markdown("#### 📚 Completed Revision Sessions")
        rev_history = get_revision_history(st.session_state.student_id, limit=5)
        if rev_history:
            for r in rev_history:
                score_badge = f"{r['mini_quiz_score']}/{r['mini_quiz_total']}" if r['mini_quiz_score'] is not None else "Not completed"
                st.markdown(
                    f"- **{r['completed_at'][:16]}** &bull; `{r['subject']}`: **{r['topic']}** "
                    f"({r['study_time_minutes']} mins) | Mini-Quiz: `{score_badge}`"
                )
        else:
            st.caption("No revision sessions logged yet.")
