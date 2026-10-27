/**
 * The Ghost of Weak Topics 👻
 * Single-Page Web Application Frontend Engine
 * Communicates with the FastAPI backend powered by Gemma 4
 */

// Application State
const state = {
    studentId: localStorage.getItem("ghost_student_id") || "student_ghost_01",
    studentName: localStorage.getItem("ghost_student_name") || "Alex",
    currentView: "home",
    subjects: {},
    gemmaStatus: null,
    
    // Chat state
    chatHistory: [
        {
            role: "assistant",
            content: "👻 **Boo! Greetings, scholar!** I am **The Ghost of Weak Topics**.\n\nAsk me anything about **Python, DSA, Mathematics, Computer Science, or Science**. I break difficult concepts into simple, spirited analogies!"
        }
    ],

    // Active Quiz state
    activeQuiz: null,
    quizIndex: 0,
    quizAnswers: {},
    quizSubmitted: false,

    // Revision Plan state
    activeRevisionPlan: null,
    activeRevisionStage: 1,
    miniQuizAnswers: {},

    // Analytics Cache
    dashboardData: null
};

// =========================================================
// Initialization
// =========================================================
document.addEventListener("DOMContentLoaded", async () => {
    updateStudentDisplay();
    await checkGemmaStatus();
    await fetchSubjects();
    await refreshHomeKPIs();

    // Check periodically for model status
    setInterval(checkGemmaStatus, 30000);
});

function updateStudentDisplay() {
    const el = document.getElementById("navStudentName");
    if (el) el.textContent = state.studentName;
}

// =========================================================
// Navigation & Views
// =========================================================
function navigate(viewName) {
    state.currentView = viewName;

    // Update nav buttons
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.view === viewName);
    });

    // Update view panels
    document.querySelectorAll(".view-panel").forEach(panel => {
        panel.classList.toggle("active", panel.id === `view-${viewName}`);
    });

    // View specific hooks
    if (viewName === "home") {
        refreshHomeKPIs();
    } else if (viewName === "weak-topics") {
        loadWeakTopics();
    } else if (viewName === "revision") {
        loadRevisionRecommendations();
    } else if (viewName === "dashboard") {
        loadDashboard();
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

// =========================================================
// Gemma 4 Status Check
// =========================================================
async function checkGemmaStatus() {
    const pill = document.getElementById("modelStatusPill");
    const statusText = document.getElementById("modelStatusText");
    const banner = document.getElementById("gemmaNoticeBanner");

    try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error("Status check failed");
        const data = await res.json();
        state.gemmaStatus = data;

        const dot = pill.querySelector(".status-dot");

        if (data.available) {
            dot.className = "status-dot pulsing";
            statusText.textContent = `Gemma 4 (${data.model}) Active 🟢`;
            banner.classList.add("hidden");
        } else {
            dot.className = "status-dot offline";
            statusText.textContent = `Gemma 4 Offline (Vault Active) ⚪`;

            // Display helpful setup banner
            document.getElementById("bannerTitle").textContent = "Gemma 4 Not Detected";
            document.getElementById("bannerMsg").textContent = data.message;
            document.getElementById("bannerCmd").textContent = data.setup_command;
            banner.classList.remove("hidden");
        }
    } catch (err) {
        statusText.textContent = "Backend Connecting...";
    }
}

function dismissBanner() {
    document.getElementById("gemmaNoticeBanner").classList.add("hidden");
}

// =========================================================
// Subjects & Metadata Fetch
// =========================================================
async function fetchSubjects() {
    try {
        const res = await fetch("/api/subjects");
        const data = await res.json();
        state.subjects = data.subjects || {};

        // Populate quiz subject dropdown
        const subjSelect = document.getElementById("quizSubject");
        subjSelect.innerHTML = "";
        for (const subj of Object.keys(state.subjects)) {
            const opt = document.createElement("option");
            opt.value = subj;
            opt.textContent = subj;
            subjSelect.appendChild(opt);
        }

        updateQuizTopics();
    } catch (err) {
        console.error("Failed to load subjects:", err);
    }
}

function updateQuizTopics() {
    const subj = document.getElementById("quizSubject").value;
    const topicSelect = document.getElementById("quizTopic");
    topicSelect.innerHTML = "";

    const topics = state.subjects[subj] || ["General Concepts"];
    for (const t of topics) {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t;
        topicSelect.appendChild(opt);
    }
}

// =========================================================
// Home View KPIs
// =========================================================
async function refreshHomeKPIs() {
    try {
        const res = await fetch(`/api/weak-topics/${state.studentId}`);
        const data = await res.json();

        document.getElementById("kpiQuizzes").textContent = data.total_quizzes || 0;
        document.getElementById("kpiAccuracy").textContent = `${data.overall_accuracy || 0}%`;
        document.getElementById("kpiWeak").textContent = data.weak_topics ? data.weak_topics.length : 0;
        document.getElementById("kpiStrong").textContent = data.strong_topics ? data.strong_topics.length : 0;
    } catch (err) {
        console.warn("Could not load KPIs:", err);
    }
}

// =========================================================
// Ghost Chatbot
// =========================================================
function handleChatKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function sendQuickPrompt(promptText) {
    const input = document.getElementById("chatInput");
    input.value = promptText;
    sendChatMessage();
}

async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    const subject = document.getElementById("chatSubjectSelect").value;

    // Append user message
    state.chatHistory.push({ role: "user", content: text });
    renderChatMessages();

    // Scroll to bottom
    const win = document.getElementById("chatWindow");
    win.scrollTop = win.scrollHeight;

    // Show loading assistant placeholder
    const loadingId = "loading_msg_" + Date.now();
    state.chatHistory.push({
        role: "assistant",
        content: "👻 *The Ghost is floating through the spectral library...*",
        id: loadingId
    });
    renderChatMessages();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messages: state.chatHistory.filter(m => m.id !== loadingId),
                student_name: state.studentName,
                subject: subject
            })
        });

        const data = await res.json();
        // Replace loading placeholder
        const itemIdx = state.chatHistory.findIndex(m => m.id === loadingId);
        if (itemIdx !== -1) {
            state.chatHistory[itemIdx] = { role: "assistant", content: data.content };
        }
    } catch (err) {
        const itemIdx = state.chatHistory.findIndex(m => m.id === loadingId);
        if (itemIdx !== -1) {
            state.chatHistory[itemIdx] = {
                role: "assistant",
                content: "👻 *Ectoplasmic interference! Connection lost with Gemma 4 backend.*"
            };
        }
    }

    renderChatMessages();
    win.scrollTop = win.scrollHeight;
}

function clearChat() {
    state.chatHistory = [
        {
            role: "assistant",
            content: "👻 *Spectral memory cleared.* Ask me another question whenever you are ready!"
        }
    ];
    renderChatMessages();
}

function renderChatMessages() {
    const win = document.getElementById("chatWindow");
    win.innerHTML = "";

    state.chatHistory.forEach(msg => {
        const isGhost = msg.role === "assistant";
        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${msg.role}`;

        const avatar = document.createElement("div");
        avatar.className = "msg-avatar";
        avatar.textContent = isGhost ? "👻" : "🧑‍🎓";

        const content = document.createElement("div");
        content.className = "msg-content";
        content.innerHTML = parseMarkdown(msg.content);

        bubble.appendChild(avatar);
        bubble.appendChild(content);
        win.appendChild(bubble);
    });
}

// =========================================================
// Adaptive Quiz Engine
// =========================================================
async function startQuiz() {
    const subject = document.getElementById("quizSubject").value;
    const topic = document.getElementById("quizTopic").value;
    const difficulty = document.getElementById("quizDifficulty").value;
    const count = parseInt(document.getElementById("quizCount").value, 10);

    showToast("Summoning questions from the ethereal vault... 👻");

    try {
        const res = await fetch("/api/quiz/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: state.studentId,
                subject: subject,
                topic: topic,
                difficulty: difficulty,
                num_questions: count
            })
        });

        const data = await res.json();
        state.activeQuiz = data;
        state.quizIndex = 0;
        state.quizAnswers = {};
        state.quizSubmitted = false;

        document.getElementById("quizSetupCard").classList.add("hidden");
        document.getElementById("quizResultCard").classList.add("hidden");
        document.getElementById("quizActiveContainer").classList.remove("hidden");

        // Set pills
        document.getElementById("quizPillSubject").textContent = data.subject;
        document.getElementById("quizPillTopic").textContent = data.topic;
        document.getElementById("quizPillDiff").textContent = data.difficulty;

        renderCurrentQuestion();
    } catch (err) {
        showToast("Error summoning questions. Check server connection.", "error");
    }
}

function renderCurrentQuestion() {
    const quiz = state.activeQuiz;
    const qIdx = state.quizIndex;
    const currentQ = quiz.questions[qIdx];

    document.getElementById("quizPillSource").textContent = currentQ.source || "Gemma 4";
    document.getElementById("quizProgressText").textContent = `Question ${qIdx + 1} of ${quiz.total_questions}`;
    document.getElementById("quizProgressBar").style.width = `${((qIdx + 1) / quiz.total_questions) * 100}%`;

    document.getElementById("currentQuestionText").textContent = currentQ.question;

    // Render Options A, B, C, D
    const optionsContainer = document.getElementById("optionsList");
    optionsContainer.innerHTML = "";

    const selectedOption = state.quizAnswers[qIdx];

    ["A", "B", "C", "D"].forEach(key => {
        const optText = currentQ.options[key] || "";
        const item = document.createElement("div");
        item.className = "option-item" + (selectedOption === key ? " selected" : "");
        item.onclick = () => selectOption(key);

        const keyBadge = document.createElement("div");
        keyBadge.className = "option-key";
        keyBadge.textContent = key;

        const textSpan = document.createElement("div");
        textSpan.className = "option-text";
        textSpan.textContent = optText;

        item.appendChild(keyBadge);
        item.appendChild(textSpan);
        optionsContainer.appendChild(item);
    });

    // Reset feedback & hint boxes for this question
    document.getElementById("hintBox").classList.add("hidden");
    document.getElementById("instantFeedbackBox").classList.add("hidden");
    document.getElementById("whyWrongResponse").classList.add("hidden");
    document.getElementById("btnAskWhy").classList.add("hidden");

    // Button states
    document.getElementById("btnPrevQ").disabled = (qIdx === 0);
    const isLast = (qIdx === quiz.total_questions - 1);
    document.getElementById("btnNextQ").textContent = isLast ? "🏁 Submit Full Quiz" : "Next Question ➡️";
}

function selectOption(key) {
    state.quizAnswers[state.quizIndex] = key;
    renderCurrentQuestion();

    // Check instant feedback
    const currentQ = state.activeQuiz.questions[state.quizIndex];
    const isCorrect = (key.trim().toUpperCase() === currentQ.correct_answer.trim().toUpperCase());

    const fbBox = document.getElementById("instantFeedbackBox");
    const fbTitle = document.getElementById("feedbackTitle");
    const fbDesc = document.getElementById("feedbackExplanation");
    const btnWhy = document.getElementById("btnAskWhy");

    fbBox.className = "feedback-box " + (isCorrect ? "correct" : "incorrect");
    fbBox.classList.remove("hidden");

    if (isCorrect) {
        fbTitle.innerHTML = `🟢 Option ${key} is Correct!`;
        fbDesc.textContent = currentQ.explanation;
        btnWhy.classList.add("hidden");
    } else {
        fbTitle.innerHTML = `🔴 Option ${key} is Incorrect (Correct Answer: Option ${currentQ.correct_answer})`;
        fbDesc.textContent = currentQ.explanation;
        btnWhy.classList.remove("hidden");
    }
}

async function askHintForCurrentQuestion() {
    const currentQ = state.activeQuiz.questions[state.quizIndex];
    const hintBox = document.getElementById("hintBox");
    const hintContent = document.getElementById("hintContent");

    hintBox.classList.remove("hidden");
    hintContent.textContent = "👻 The Ghost is whispering a subtle clue...";

    try {
        const res = await fetch("/api/chat/hint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question_text: currentQ.question,
                options: currentQ.options,
                topic: state.activeQuiz.topic
            })
        });
        const data = await res.json();
        hintContent.innerHTML = parseMarkdown(data.hint);
    } catch (err) {
        hintContent.textContent = "Think about the underlying constraints and edge boundaries!";
    }
}

async function askWhyWrong() {
    const currentQ = state.activeQuiz.questions[state.quizIndex];
    const userKey = state.quizAnswers[state.quizIndex];
    const corrKey = currentQ.correct_answer;
    const whyBox = document.getElementById("whyWrongResponse");

    whyBox.classList.remove("hidden");
    whyBox.textContent = "👻 Ghost Tutor is analyzing why this trap was tempting...";

    try {
        const res = await fetch("/api/chat/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question_text: currentQ.question,
                selected_key: userKey,
                selected_text: currentQ.options[userKey] || "",
                correct_key: corrKey,
                correct_text: currentQ.options[corrKey] || "",
                topic: state.activeQuiz.topic
            })
        });
        const data = await res.json();
        whyBox.innerHTML = parseMarkdown(data.explanation);
    } catch (err) {
        whyBox.textContent = "Option " + corrKey + " is strictly required by the fundamental rules of this topic.";
    }
}

function prevQuestion() {
    if (state.quizIndex > 0) {
        state.quizIndex--;
        renderCurrentQuestion();
    }
}

async function nextOrSubmitQuestion() {
    if (state.quizAnswers[state.quizIndex] === undefined) {
        showToast("Please choose an answer option before moving on!", "warning");
        return;
    }

    const quiz = state.activeQuiz;
    const isLast = (state.quizIndex === quiz.total_questions - 1);

    if (isLast) {
        // Finalize Quiz
        showToast("Evaluating your spectral results... 🏆");
        try {
            const res = await fetch("/api/quiz/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    student_id: state.studentId,
                    subject: quiz.subject,
                    topic: quiz.topic,
                    difficulty: quiz.difficulty,
                    questions: quiz.questions,
                    answers: state.quizAnswers
                })
            });

            const results = await res.json();
            renderQuizResults(results);
        } catch (err) {
            showToast("Failed to record quiz results.", "error");
        }
    } else {
        state.quizIndex++;
        renderCurrentQuestion();
    }
}

function abandonQuiz() {
    if (confirm("Are you sure you want to abandon this quiz attempt?")) {
        restartQuizUI();
    }
}

function restartQuizUI() {
    state.activeQuiz = null;
    state.quizIndex = 0;
    state.quizAnswers = {};
    document.getElementById("quizActiveContainer").classList.add("hidden");
    document.getElementById("quizResultCard").classList.add("hidden");
    document.getElementById("quizSetupCard").classList.remove("hidden");
    refreshHomeKPIs();
}

function renderQuizResults(results) {
    document.getElementById("quizActiveContainer").classList.add("hidden");
    const resultCard = document.getElementById("quizResultCard");
    resultCard.classList.remove("hidden");

    const acc = results.accuracy;
    document.getElementById("resScore").textContent = `${results.score} / ${results.total_questions}`;
    document.getElementById("resAccuracy").textContent = `${acc}%`;

    const statusEl = document.getElementById("resStatus");
    const iconEl = document.getElementById("resultIcon");
    const titleEl = document.getElementById("resultTitle");
    const subEl = document.getElementById("resultSubtitle");

    if (acc >= 75) {
        statusEl.textContent = "🟢 Strong";
        statusEl.style.color = "var(--strong-green)";
        iconEl.textContent = "🏆";
        titleEl.textContent = "Spooktacular Mastery!";
        subEl.textContent = `You scored ${acc}%. The Ghost is deeply impressed with your grasp on ${results.topic}!`;
    } else if (acc >= 50) {
        statusEl.textContent = "🟡 Improving";
        statusEl.style.color = "var(--improving-amber)";
        iconEl.textContent = "🕯️";
        titleEl.textContent = "Solid Progress!";
        subEl.textContent = `Accuracy: ${acc}%. You're making progress—a short revision session will push you to mastery.`;
    } else {
        statusEl.textContent = "🔴 Needs Attention";
        statusEl.style.color = "var(--weak-red)";
        iconEl.textContent = "🧟";
        titleEl.textContent = "Phantom Menace Detected!";
        subEl.textContent = `Accuracy: ${acc}%. This is a weak topic. Head to the Revision Planner to banish these doubts!`;
    }

    // Question Breakdown List
    const breakdownContainer = document.getElementById("resultQuestionsBreakdown");
    breakdownContainer.innerHTML = "<h4 style='margin-bottom:1rem;'>Detailed Question Breakdown</h4>";

    results.questions.forEach((q, idx) => {
        const item = document.createElement("div");
        item.className = "card card-glass";
        item.style.marginBottom = "0.75rem";

        const isC = q.is_correct;
        const icon = isC ? "🟢" : "🔴";

        item.innerHTML = `
            <div style="font-weight:700; margin-bottom:0.4rem;">
                ${icon} Question ${idx + 1}: ${q.question}
            </div>
            <div style="font-size:0.9rem; color:var(--text-muted); margin-bottom:0.4rem;">
                Your Answer: <strong>Option ${q.selected_option}</strong> &bull; Correct: <strong>Option ${q.correct_option}</strong>
            </div>
            <div style="font-size:0.88rem; background:rgba(0,0,0,0.3); padding:0.6rem; border-radius:6px;">
                ${q.explanation}
            </div>
        `;
        breakdownContainer.appendChild(item);
    });
}

// =========================================================
// Weak Topics Radar
// =========================================================
let currentWeakTopicsData = null;

async function loadWeakTopics() {
    try {
        const res = await fetch(`/api/weak-topics/${state.studentId}`);
        const data = await res.json();
        currentWeakTopicsData = data;

        document.getElementById("countAll").textContent = data.topic_reports ? data.topic_reports.length : 0;
        document.getElementById("countWeak").textContent = data.weak_topics ? data.weak_topics.length : 0;
        document.getElementById("countImproving").textContent = data.improving_topics ? data.improving_topics.length : 0;
        document.getElementById("countStrong").textContent = data.strong_topics ? data.strong_topics.length : 0;
        document.getElementById("countUncalibrated").textContent = data.uncalibrated_topics ? data.uncalibrated_topics.length : 0;

        renderFilteredTopics(data.topic_reports || []);
        renderRecentPitfalls(data.recent_mistakes || []);
    } catch (err) {
        console.error("Failed to load weak topics:", err);
    }
}

function filterWeakTopics(filterType, btnEl) {
    document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
    if (btnEl) btnEl.classList.add("active");

    if (!currentWeakTopicsData) return;

    if (filterType === "weak") {
        renderFilteredTopics(currentWeakTopicsData.weak_topics);
    } else if (filterType === "improving") {
        renderFilteredTopics(currentWeakTopicsData.improving_topics);
    } else if (filterType === "strong") {
        renderFilteredTopics(currentWeakTopicsData.strong_topics);
    } else if (filterType === "uncalibrated") {
        renderFilteredTopics(currentWeakTopicsData.uncalibrated_topics);
    } else {
        renderFilteredTopics(currentWeakTopicsData.topic_reports);
    }
}

function renderFilteredTopics(topics) {
    const container = document.getElementById("topicCardsContainer");
    container.innerHTML = "";

    if (!topics || topics.length === 0) {
        container.innerHTML = "<p style='color:var(--text-muted); grid-column:span 2;'>No topics in this category.</p>";
        return;
    }

    topics.forEach(t => {
        const card = document.createElement("div");
        card.className = "topic-card";

        let badgeBg = "var(--nodata-bg)";
        let badgeColor = "var(--nodata-gray)";

        if (t.status === "Needs attention") {
            badgeBg = "var(--weak-bg)"; badgeColor = "var(--weak-red)";
        } else if (t.status === "Improving") {
            badgeBg = "var(--improving-bg)"; badgeColor = "var(--improving-amber)";
        } else if (t.status === "Strong") {
            badgeBg = "var(--strong-bg)"; badgeColor = "var(--strong-green)";
        }

        card.innerHTML = `
            <div>
                <div class="topic-card-header">
                    <div>
                        <div class="topic-card-title">${t.topic}</div>
                        <div class="topic-card-subject">${t.subject}</div>
                    </div>
                    <span class="badge-status" style="background:${badgeBg}; color:${badgeColor};">${t.badge}</span>
                </div>
                <p style="font-size:0.85rem; color:var(--text-sub); margin-bottom:0.5rem;">${t.description}</p>
                <div class="topic-accuracy-bar">
                    <div class="topic-accuracy-fill" style="width:${t.accuracy}%; background:${badgeColor};"></div>
                </div>
                <div class="topic-meta-row">
                    <span>📊 ${t.accuracy}% Accuracy</span>
                    <span>🎯 ${t.attempts_count} Attempts</span>
                    <span>📝 ${t.total_correct}/${t.total_questions}</span>
                </div>
            </div>
            <button class="btn btn-sm btn-outline" style="width:100%; margin-top:0.5rem;" onclick="jumpToRevise('${t.subject}', '${t.topic}')">
                📅 Revise This Topic
            </button>
        `;
        container.appendChild(card);
    });
}

function renderRecentPitfalls(mistakes) {
    const container = document.getElementById("recentPitfallsContainer");
    container.innerHTML = "";

    if (!mistakes || mistakes.length === 0) {
        container.innerHTML = "<p style='color:var(--text-muted);'>No recent mistakes recorded! Keep conquering your subjects.</p>";
        return;
    }

    mistakes.forEach(m => {
        const item = document.createElement("div");
        item.className = "card card-glass";
        item.style.marginBottom = "0.75rem";
        item.innerHTML = `
            <div style="font-weight:700; color:#F87171; margin-bottom:0.25rem;">
                🔴 [${m.subject}] ${m.topic}: ${m.question_text}
            </div>
            <div style="font-size:0.88rem; color:var(--text-muted); margin-bottom:0.3rem;">
                Your Answer: <strong>Option ${m.selected_option}</strong> &bull; Correct: <strong>Option ${m.correct_option}</strong>
            </div>
            <div style="font-size:0.85rem; color:var(--text-sub); background:rgba(0,0,0,0.3); padding:0.5rem; border-radius:4px;">
                ${m.explanation}
            </div>
        `;
        container.appendChild(item);
    });
}

function jumpToRevise(subject, topic) {
    navigate("revision");
    setTimeout(() => {
        const select = document.getElementById("revTopicSelect");
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].text.includes(topic)) {
                select.selectedIndex = i;
                break;
            }
        }
    }, 100);
}

// =========================================================
// Revision Planner (6 Stages)
// =========================================================
async function loadRevisionRecommendations() {
    try {
        const res = await fetch(`/api/revision/recommendations/${state.studentId}`);
        const data = await res.json();
        const select = document.getElementById("revTopicSelect");
        select.innerHTML = "";

        data.recommendations.forEach(r => {
            const opt = document.createElement("option");
            opt.value = JSON.stringify({ subject: r.subject, topic: r.topic });
            opt.textContent = `${r.subject} - ${r.topic} (${r.status}) [Priority: ${r.priority_score}]`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Could not load recommendations:", err);
    }
}

async function generateRevisionPlan() {
    const topicVal = document.getElementById("revTopicSelect").value;
    if (!topicVal) return;

    const parsed = JSON.parse(topicVal);
    const timeMins = parseInt(document.getElementById("revTimeSelect").value, 10);

    showToast(`Conjuring ${timeMins}-min revision session for ${parsed.topic}... 📜`);

    try {
        const res = await fetch("/api/revision/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: state.studentId,
                subject: parsed.subject,
                topic: parsed.topic,
                study_time_minutes: timeMins
            })
        });

        const plan = await res.json();
        state.activeRevisionPlan = plan;
        state.miniQuizAnswers = {};

        renderRevisionSession(plan);
    } catch (err) {
        showToast("Error generating revision plan.", "error");
    }
}

function renderRevisionSession(plan) {
    const container = document.getElementById("revisionPlanContainer");
    container.classList.remove("hidden");

    document.getElementById("planTopicHeader").textContent = `Revision Session: ${plan.summary.topic}`;
    document.getElementById("planGoalText").textContent = plan.summary.target_outcome;
    document.getElementById("planTimeBadge").textContent = `${plan.summary.study_time_minutes} Mins`;

    // Stage 1: Concept
    document.getElementById("stage1Title").textContent = plan.concept_explanation.title;
    document.getElementById("stage1Body").innerHTML = parseMarkdown(plan.concept_explanation.content);

    // Stage 2: Worked Examples
    const exContainer = document.getElementById("stage2Examples");
    exContainer.innerHTML = "";
    plan.worked_examples.forEach((ex, idx) => {
        const card = document.createElement("div");
        card.className = "card card-glass";
        card.style.marginBottom = "1rem";
        card.innerHTML = `
            <h4 style="color:var(--cyan); margin-bottom:0.5rem;">🧪 ${ex.title}</h4>
            <p><strong>Problem Scenario:</strong> ${ex.problem}</p>
            <div style="margin:0.75rem 0;">
                <strong>Logical Steps:</strong>
                <ul style="margin-left:1.5rem; margin-top:0.3rem;">
                    ${ex.steps.map(s => `<li>${s}</li>`).join("")}
                </ul>
            </div>
            <div style="background:rgba(0,240,255,0.08); padding:0.6rem; border-radius:6px; font-size:0.9rem; color:var(--cyan);">
                💡 <strong>Key Takeaway:</strong> ${ex.takeaway}
            </div>
        `;
        exContainer.appendChild(card);
    });

    // Stage 3: Practice Drills
    const drillContainer = document.getElementById("stage3Drills");
    drillContainer.innerHTML = "";
    plan.practice_questions.forEach((pq, idx) => {
        const card = document.createElement("div");
        card.className = "card card-glass";
        card.style.marginBottom = "1rem";
        card.innerHTML = `
            <h4 style="margin-bottom:0.5rem;">🎯 Drill ${idx + 1}: ${pq.question}</h4>
            <div style="margin:0.75rem 0; font-size:0.95rem;">
                <div>A: ${pq.options.A}</div>
                <div>B: ${pq.options.B}</div>
                <div>C: ${pq.options.C}</div>
                <div>D: ${pq.options.D}</div>
            </div>
            <button class="btn btn-sm btn-outline" onclick="toggleDrillAnswer(${idx})">Reveal Solution</button>
            <div id="drillAns_${idx}" class="hidden" style="margin-top:0.6rem; background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.3); padding:0.6rem; border-radius:6px;">
                🟢 <strong>Correct Answer: Option ${pq.correct_answer}</strong><br>
                ${pq.explanation}
            </div>
        `;
        drillContainer.appendChild(card);
    });

    // Stage 4: Mistake Feedback
    const fbContainer = document.getElementById("stage4Feedback");
    const fb = plan.mistake_feedback;
    fbContainer.innerHTML = `
        <h4 style="color:#FBBF24; margin-bottom:0.5rem;">💡 Targeted Advice on Past Pitfalls</h4>
        <p>${fb.message}</p>
    `;
    if (fb.has_recent_mistakes) {
        fb.mistake_items.forEach(itm => {
            fbContainer.innerHTML += `
                <div style="background:rgba(245,158,11,0.1); border-left:3px solid #F59E0B; padding:0.75rem; margin-top:0.75rem; border-radius:4px;">
                    <div><strong>Pitfall ${itm.item_number}:</strong> ${itm.question_snippet}</div>
                    <div style="font-size:0.85rem; margin:0.3rem 0;">Your Answer: <code>${itm.your_answer}</code> | Correct: <code>${itm.correct_answer}</code></div>
                    <div style="font-size:0.88rem; color:#FDE68A;">${itm.ghost_advice}</div>
                </div>
            `;
        });
    } else {
        (fb.tips || []).forEach(t => {
            fbContainer.innerHTML += `<div style="margin-top:0.5rem;">✨ ${t}</div>`;
        });
    }

    // Stage 5: Mini-Quiz
    const mqContainer = document.getElementById("stage5Questions");
    mqContainer.innerHTML = "";
    plan.mini_quiz.forEach((mq, idx) => {
        const item = document.createElement("div");
        item.style.marginBottom = "1.25rem";
        item.innerHTML = `
            <div style="font-weight:600; margin-bottom:0.5rem;">Q${idx + 1}: ${mq.question}</div>
            <div style="display:flex; flex-direction:column; gap:0.4rem;">
                ${["A", "B", "C", "D"].map(k => `
                    <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
                        <input type="radio" name="mini_q_${idx}" value="${k}" onchange="selectMiniAnswer(${idx}, '${k}')">
                        <span><strong>${k}:</strong> ${mq.options[k]}</span>
                    </label>
                `).join("")}
            </div>
        `;
        mqContainer.appendChild(item);
    });

    // Stage 6: Progress Summary
    const sumContainer = document.getElementById("stage6Summary");
    sumContainer.innerHTML = `
        <p><strong>Subject:</strong> ${plan.summary.subject}</p>
        <p><strong>Topic:</strong> ${plan.summary.topic}</p>
        <p><strong>Duration:</strong> ${plan.summary.study_time_minutes} minutes</p>
        <p><strong>Generated At:</strong> ${plan.summary.generated_at}</p>
        <div style="margin-top:1rem; padding:1rem; background:rgba(167,139,250,0.15); border-radius:8px; border:1px solid var(--primary);">
            👻 <em>${plan.summary.ghost_encouragement}</em>
        </div>
    `;

    // Default to Stage 1
    switchStage(1);
}

function switchStage(stageNum, btnEl) {
    state.activeRevisionStage = stageNum;
    document.querySelectorAll(".stage-tab").forEach((btn, idx) => {
        btn.classList.toggle("active", (idx + 1) === stageNum);
    });
    document.querySelectorAll(".stage-content").forEach((panel, idx) => {
        panel.classList.toggle("active", (idx + 1) === stageNum);
    });
}

function toggleDrillAnswer(idx) {
    const el = document.getElementById(`drillAns_${idx}`);
    el.classList.toggle("hidden");
}

function selectMiniAnswer(qIdx, key) {
    state.miniQuizAnswers[qIdx] = key;
}

async function submitMiniQuiz() {
    const miniQuiz = state.activeRevisionPlan.mini_quiz;
    let score = 0;

    miniQuiz.forEach((mq, idx) => {
        if (state.miniQuizAnswers[idx] === mq.correct_answer) {
            score++;
        }
    });

    const scoreBox = document.getElementById("miniQuizScoreBox");
    scoreBox.className = "feedback-box " + (score >= 2 ? "correct" : "incorrect");
    scoreBox.classList.remove("hidden");
    scoreBox.innerHTML = `
        <div class="feedback-title">Mini-Quiz Score: ${score} / ${miniQuiz.length}</div>
        <div class="feedback-desc">
            ${score === miniQuiz.length ? "Flawless retention! This topic is now mastered." : "Good effort! Review the incorrect answers to solidify your understanding."}
        </div>
    `;

    // Save revision session in SQLite backend
    try {
        await fetch("/api/revision/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                revision_id: state.activeRevisionPlan.summary.session_id,
                student_id: state.studentId,
                subject: state.activeRevisionPlan.summary.subject,
                topic: state.activeRevisionPlan.summary.topic,
                study_time_minutes: state.activeRevisionPlan.summary.study_time_minutes,
                plan: state.activeRevisionPlan,
                mini_quiz_score: score,
                mini_quiz_total: miniQuiz.length
            })
        });
        showToast("Revision session permanently saved to your history! 📈");
    } catch (err) {
        console.error("Save revision failed:", err);
    }
}

// =========================================================
// Dashboard & Dynamic Canvas Charts
// =========================================================
async function loadDashboard() {
    try {
        const res = await fetch(`/api/dashboard/${state.studentId}`);
        const data = await res.json();
        state.dashboardData = data;

        drawTopicBarChart(data.analysis.topic_reports || []);
        drawTrendLineChart(data.attempts || []);
        renderQuizHistoryTable(data.attempts || []);
        renderRevisionHistoryLog(data.revisions || []);
    } catch (err) {
        console.error("Failed to load dashboard:", err);
    }
}

function drawTopicBarChart(topics) {
    const canvas = document.getElementById("topicBarCanvas");
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!topics || topics.length === 0) {
        ctx.fillStyle = "#94A3B8";
        ctx.font = "14px 'Plus Jakarta Sans'";
        ctx.textAlign = "center";
        ctx.fillText("No topic attempts recorded yet.", w / 2, h / 2);
        return;
    }

    const paddingLeft = 140;
    const paddingRight = 40;
    const paddingTop = 20;
    const paddingBottom = 30;
    const chartW = w - paddingLeft - paddingRight;
    const chartH = h - paddingTop - paddingBottom;

    const rowH = Math.min(36, chartH / topics.length);

    topics.slice(0, 7).forEach((t, idx) => {
        const y = paddingTop + (idx * rowH);
        const barW = (t.accuracy / 100) * chartW;

        // Label
        ctx.fillStyle = "#F8FAFC";
        ctx.font = "12px 'Plus Jakarta Sans'";
        ctx.textAlign = "right";
        ctx.fillText(t.topic.length > 16 ? t.topic.slice(0, 14) + ".." : t.topic, paddingLeft - 10, y + (rowH / 2) + 4);

        // Bar background track
        ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
        ctx.fillRect(paddingLeft, y + 4, chartW, rowH - 10);

        // Bar fill color by threshold
        let color = "#94A3B8";
        if (t.status === "Needs attention") color = "#EF4444";
        else if (t.status === "Improving") color = "#F59E0B";
        else if (t.status === "Strong") color = "#10B981";

        ctx.fillStyle = color;
        ctx.fillRect(paddingLeft, y + 4, barW, rowH - 10);

        // Percentage label
        ctx.fillStyle = "#CBD5E1";
        ctx.font = "11px 'Plus Jakarta Sans'";
        ctx.textAlign = "left";
        ctx.fillText(`${t.accuracy}%`, paddingLeft + barW + 8, y + (rowH / 2) + 4);
    });
}

function drawTrendLineChart(attempts) {
    const canvas = document.getElementById("trendLineCanvas");
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (!attempts || attempts.length === 0) {
        ctx.fillStyle = "#94A3B8";
        ctx.font = "14px 'Plus Jakarta Sans'";
        ctx.textAlign = "center";
        ctx.fillText("No attempts history to plot.", w / 2, h / 2);
        return;
    }

    const pad = 40;
    const chartW = w - (pad * 2);
    const chartH = h - (pad * 2);

    // Draw axes
    ctx.strokeStyle = "rgba(167, 139, 250, 0.2)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, pad);
    ctx.lineTo(pad, h - pad);
    ctx.lineTo(w - pad, h - pad);
    ctx.stroke();

    const chronological = attempts.slice().reverse().slice(-10);
    const stepX = chartW / Math.max(1, chronological.length - 1);

    ctx.beginPath();
    ctx.strokeStyle = "#00F0FF";
    ctx.lineWidth = 3;

    chronological.forEach((att, idx) => {
        const x = pad + (idx * stepX);
        const y = (h - pad) - ((att.accuracy / 100) * chartH);

        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Draw points
    chronological.forEach((att, idx) => {
        const x = pad + (idx * stepX);
        const y = (h - pad) - ((att.accuracy / 100) * chartH);

        ctx.fillStyle = "#A78BFA";
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "#CBD5E1";
        ctx.font = "10px 'Plus Jakarta Sans'";
        ctx.textAlign = "center";
        ctx.fillText(`${att.accuracy}%`, x, y - 10);
    });
}

function renderQuizHistoryTable(attempts) {
    const tbody = document.getElementById("quizHistoryTbody");
    tbody.innerHTML = "";

    if (!attempts || attempts.length === 0) {
        tbody.innerHTML = "<tr><td colspan='6' style='text-align:center; color:var(--text-muted);'>No quizzes recorded yet.</td></tr>";
        return;
    }

    attempts.forEach(a => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${a.completed_at ? a.completed_at.slice(0, 16).replace("T", " ") : "N/A"}</td>
            <td>${a.subject}</td>
            <td>${a.topic}</td>
            <td>${a.difficulty}</td>
            <td><strong>${a.score} / ${a.total_questions}</strong></td>
            <td><span style="color:${a.accuracy >= 75 ? 'var(--strong-green)' : (a.accuracy >= 50 ? 'var(--improving-amber)' : 'var(--weak-red)')}; font-weight:700;">${a.accuracy}%</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderRevisionHistoryLog(revisions) {
    const container = document.getElementById("revisionLogContainer");
    container.innerHTML = "";

    if (!revisions || revisions.length === 0) {
        container.innerHTML = "<p style='color:var(--text-muted);'>No revision sessions logged yet.</p>";
        return;
    }

    revisions.forEach(r => {
        const item = document.createElement("div");
        item.style.padding = "0.5rem 0";
        item.style.borderBottom = "1px solid rgba(167,139,250,0.1)";
        item.innerHTML = `
            🕒 <strong>${r.completed_at ? r.completed_at.slice(0, 16).replace("T", " ") : "N/A"}</strong> &bull;
            <code>${r.subject}</code>: <strong>${r.topic}</strong> (${r.study_time_minutes} mins) &bull;
            Mini-Quiz Score: <strong>${r.mini_quiz_score !== null ? `${r.mini_quiz_score}/${r.mini_quiz_total}` : 'N/A'}</strong>
        `;
        container.appendChild(item);
    });
}

// =========================================================
// Scholar Profile Modal
// =========================================================
async function openStudentModal() {
    const modal = document.getElementById("studentModal");
    modal.classList.remove("hidden");

    try {
        const res = await fetch("/api/students");
        const data = await res.json();
        const select = document.getElementById("studentSelect");
        select.innerHTML = "";

        data.students.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s.student_id;
            opt.textContent = s.name;
            if (s.student_id === state.studentId) opt.selected = true;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load students:", err);
    }
}

function closeStudentModal() {
    document.getElementById("studentModal").classList.add("hidden");
}

function onStudentSelectChange() {
    const select = document.getElementById("studentSelect");
    const selectedOption = select.options[select.selectedIndex];
    if (selectedOption) {
        document.getElementById("newStudentInput").value = "";
    }
}

async function saveStudentProfile() {
    const newName = document.getElementById("newStudentInput").value.trim();
    const select = document.getElementById("studentSelect");

    if (newName) {
        try {
            const res = await fetch("/api/students", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newName })
            });
            const data = await res.json();
            state.studentId = data.student.student_id;
            state.studentName = data.student.name;
        } catch (err) {
            showToast("Failed to create student.", "error");
            return;
        }
    } else if (select.value) {
        state.studentId = select.value;
        state.studentName = select.options[select.selectedIndex].textContent;
    }

    localStorage.setItem("ghost_student_id", state.studentId);
    localStorage.setItem("ghost_student_name", state.studentName);
    updateStudentDisplay();
    closeStudentModal();
    showToast(`Switched active scholar to ${state.studentName} 🧑‍🎓`);
    refreshHomeKPIs();
}

// =========================================================
// Utilities & Toast Notifications
// =========================================================
function showToast(msg, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function parseMarkdown(text) {
    if (!text) return "";
    let safe = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Code blocks
    safe = safe.replace(/```(?:[a-zA-Z]+)?\n([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
    // Inline code
    safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Bold
    safe = safe.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    // Italics
    safe = safe.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    // Bullet points
    safe = safe.replace(/^\s*-\s+(.*)$/gm, "<li>$1</li>");
    safe = safe.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");
    // Line breaks
    safe = safe.replace(/\n\n/g, "</p><p>");
    return `<p>${safe}</p>`;
}
