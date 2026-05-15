"""
HireIQ - Streamlit UI
"""

import streamlit as st
import tempfile
import os
from main import process_message
from utils.pdf_reader import extract_text_from_pdf
from graph import build_graph

st.set_page_config(
    page_title="HireIQ — TechNova Solutions",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
app = build_graph()

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    .status-card {
        background: #f8f9fa;
        border-left: 4px solid #0f3460;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }
    .step-complete { border-left-color: #28a745; }
    .step-active   { border-left-color: #ffc107; }
    .step-pending  { border-left-color: #dee2e6; color: #aaa; }
</style>
""", unsafe_allow_html=True)

DEFAULTS = {
    "messages":          [],
    "cv_path":           None,
    "cv_text":           None,
    "cv_received":       False,
    "person_type":       None,
    "job_role":          None,
    "email":             None,
    "name":              None,
    "interview_state":   None,
    "interview_result":  None,
    "client_question":   None,
    "rag_answer":        None,
    "preferred_time":    None,
    "guide_available":   None,
    "assigned_guide":    None,
    "visit_slot":        None,
    "current_node":      "",
    "error_count":       0,
    "conversation_done": False,
    "greeted":           False,
    "pending_day":       "",
    "pending_time":      "",
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

with st.sidebar:
    st.image("https://via.placeholder.com/200x60/0f3460/ffffff?text=TechNova", width=200)
    st.markdown("## 📎 Upload CV")
    st.caption("*For job applicants only*")

    uploaded_file = st.file_uploader(
        "Upload your CV (PDF only)",
        type=["pdf"],
        key="cv_uploader",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        cv_text = extract_text_from_pdf(tmp_path)
        if cv_text and len(cv_text.strip()) > 50:
            st.session_state.cv_path = tmp_path
            st.session_state.cv_text = cv_text
            st.session_state.cv_received = False
            st.success(f"✅ **{uploaded_file.name}** ready!")
        else:
            os.unlink(tmp_path)
            st.error("⚠️ Could not read this PDF. Please upload a text-based CV.")

    if st.session_state.cv_received:
        st.info("✅ CV loaded and ready")

    st.divider()
    st.markdown("### 📊 Application Status")

    def status_card(label, done, active=False):
        cls = "step-complete" if done else ("step-active" if active else "step-pending")
        icon = "✅" if done else ("🔄" if active else "⬜")
        st.markdown(
            f'<div class="status-card {cls}">{icon} {label}</div>',
            unsafe_allow_html=True
        )

    p = st.session_state
    iv = p.interview_state or {}

    status_card("CV Uploaded",        p.cv_received,
                active=not p.cv_received and p.person_type == "employee")
    status_card("Role Selected",      bool(p.job_role),
                active=p.cv_received and not p.job_role)
    status_card("Email Provided",     bool(p.email),
                active=bool(p.job_role) and not p.email)
    q_done = len(iv.get("answers_given", []))
    status_card(f"Interview ({q_done}/5)",
                p.conversation_done,
                active=bool(p.email) and not p.conversation_done)
    status_card("Result Emailed", p.conversation_done)

    if p.person_type and p.person_type != "employee":
        st.divider()
        st.markdown(f"**Mode:** {'🏢 Visitor' if p.person_type == 'visitor' else 'ℹ️ Info'}")

    st.divider()

    if p.job_role:
        st.markdown(f"**Role:** `{p.job_role}`")
    if p.email:
        st.markdown(f"**Email:** `{p.email}`")
    if p.interview_result:
        colour = "green" if p.interview_result == "PASSED" else "red"
        st.markdown(
            f"**Result:** <span style='color:{colour}'>{p.interview_result}</span>",
            unsafe_allow_html=True
        )

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Reset", use_container_width=True):
            if st.session_state.cv_path and os.path.exists(st.session_state.cv_path):
                os.unlink(st.session_state.cv_path)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("❓ Help", use_container_width=True):
            st.info(
                "**How to use HireIQ:**\n\n"
                "1. Tell me why you're here\n"
                "2. For jobs: upload CV first\n"
                "3. Answer interview questions\n"
                "4. Check your email for results"
            )

st.markdown("""
<div class="main-header">
    <h1>🤖 HireIQ</h1>
    <p style="margin:0; opacity:0.85">Intelligent HR Assistant — TechNova Solutions</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.greeted:
    context = {k: st.session_state[k] for k in DEFAULTS if k != "greeted"}
    greeting, updated = process_message("__init__", context)
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    for k, v in updated.items():
        if k in st.session_state:
            st.session_state[k] = v
    st.session_state.greeted = True
    st.session_state.current_node = ""

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

placeholder = (
    "Type your message here…"
    if not st.session_state.conversation_done
    else "Conversation complete. Click Reset to start over."
)

if prompt := st.chat_input(placeholder, disabled=st.session_state.conversation_done):
    with st.chat_message("user"):
        st.markdown(prompt)
    context = {k: st.session_state[k] for k in DEFAULTS if k != "greeted"}
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            response, updated = process_message(prompt, context)
        st.markdown(response)
    for k, v in updated.items():
        if k in st.session_state:
            st.session_state[k] = v
    st.rerun()