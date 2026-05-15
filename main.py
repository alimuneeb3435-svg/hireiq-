"""
HireIQ - Main Orchestrator
"""

from langgraph.graph import StateGraph, END
from utils.state import HireIQState
from utils.pdf_reader import extract_text_from_pdf
from agents.router_agent import classify_person, extract_email_from_message, get_natural_clarification
from agents.interview_agent import conduct_interview, generate_interview_questions, is_valid_cv
from agents.rag_agent import answer_client_question
from agents.visitor_agent import (
    handle_visitor_request, generate_visitor_response,
    check_guide_availability, extract_day_from_message,
    extract_time_from_message, AVAILABLE_SLOTS
)
from agents.email_agent import send_interview_email, send_visitor_email
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    temperature=0.5,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# ── Node: Greet ───────────────────────────────────────────────────────────────
def greet_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "greet"
    state["response"] = (
        "👋 Welcome to **HireIQ** — TechNova Solutions' intelligent HR assistant!\n\n"
        "I can help you with:\n"
        "- 💼 **Job Applications** — Upload your CV and complete a screening interview\n"
        "- 🏢 **Office Visits** — Schedule a tour of our Lahore office\n"
        "- ℹ️ **Company Info** — Ask about our services, culture, or contact details\n\n"
        "How can I help you today?"
    )
    return state

# ── Node: Route ───────────────────────────────────────────────────────────────
def route_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "route"
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    person_type = classify_person(last_msg)
    state["person_type"] = person_type
    if person_type == "unknown":
        state["response"] = get_natural_clarification(last_msg)
        state["current_node"] = "unknown_handled"
    return state

# ── Node: Job — collect CV ────────────────────────────────────────────────────
def job_collect_cv_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "job_collect_cv"
    if state.get("cv_text"):
        state["response"] = (
            "✅ Your CV is already loaded!\n\n"
            "Which position are you applying for?\n\n"
            "**Available Roles:**\n"
            "1. AI/ML Engineer\n2. Software Engineer\n3. Data Scientist\n"
            "4. Project Manager\n5. Business Analyst\n6. DevOps Engineer"
        )
        return state
    cv_path = state.get("cv_path")
    if cv_path and os.path.exists(cv_path):
        cv_text = extract_text_from_pdf(cv_path)
        if cv_text:
            if not is_valid_cv(cv_text):
                state["response"] = (
                    "⚠️ The uploaded file does not appear to be a valid CV.\n\n"
                    "Please upload a proper resume that includes:\n"
                    "- Skills\n- Education\n- Experience or projects"
                )
                return state
            state["cv_text"] = cv_text
            state["cv_received"] = True
            state["response"] = (
                "✅ **CV received and analysed!**\n\n"
                "Which position are you applying for?\n\n"
                "**Available Roles:**\n"
                "1. AI/ML Engineer\n2. Software Engineer\n3. Data Scientist\n"
                "4. Project Manager\n5. Business Analyst\n6. DevOps Engineer"
            )
        else:
            state["response"] = (
                "⚠️ I could not extract text from your PDF. "
                "Please make sure it is not a scanned image-only PDF, then re-upload."
            )
    else:
        state["response"] = (
            "📎 To apply for a position, please **upload your CV (PDF)** "
            "using the sidebar on the left.\n\n"
            "Once uploaded, we will guide you through the screening interview."
        )
    return state

# ── Node: Job — collect role ──────────────────────────────────────────────────
def job_collect_role_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "job_collect_role"
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"].lower() if messages else ""

    ROLES = [
        "AI/ML Engineer", "Software Engineer", "Data Scientist",
        "Project Manager", "Business Analyst", "DevOps Engineer"
    ]

    if last_msg.strip() in ["1", "2", "3", "4", "5", "6"]:
        detected = ROLES[int(last_msg.strip()) - 1]
    else:
        prompt = f"""The user is selecting a job role from this numbered list:
1. AI/ML Engineer
2. Software Engineer
3. Data Scientist
4. Project Manager
5. Business Analyst
6. DevOps Engineer

User input: "{last_msg}"

The user may have typed a number, partial name, or full name.
Respond with ONLY the exact role name from the list above.
If you cannot match it, respond with ONLY: UNKNOWN"""
        role_response = llm.invoke(prompt)
        detected = role_response.content.strip()

    if detected in ROLES:
        state["job_role"] = detected
        state["response"] = (
            f"Great choice! You are applying for **{detected}**.\n\n"
            f"Please provide your **email address** so we can send you the interview result."
        )
    else:
        state["response"] = (
            "Please specify which role you are interested in:\n\n"
            "1. AI/ML Engineer\n2. Software Engineer\n3. Data Scientist\n"
            "4. Project Manager\n5. Business Analyst\n6. DevOps Engineer\n\n"
            "You can type the number or the role name."
        )
    return state

# ── Node: Job — collect email ─────────────────────────────────────────────────
def job_collect_email_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "job_collect_email"
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""

    ROLES = [
        "AI/ML Engineer", "Software Engineer", "Data Scientist",
        "Project Manager", "Business Analyst", "DevOps Engineer"
    ]

    if last_msg.strip() in ["1", "2", "3", "4", "5", "6"]:
        index = int(last_msg.strip()) - 1
        state["job_role"] = ROLES[index]
        state["response"] = (
            f"Got it! Switching your application to **{ROLES[index]}**.\n\n"
            f"Please provide your **email address** to continue."
        )
        return state

    change_role_prompt = f"""The user is in the email collection step of a job application for {state.get('job_role', 'a position')}.
User said: "{last_msg}"

Is the user trying to change their job role? This includes:
- Typing a number like "2" or "3" (referring to role list)
- Saying "change to X", "I want X instead"
- Mentioning a different role name

Answer with ONLY: YES or NO"""
    change_check = llm.invoke(change_role_prompt)
    if "YES" in change_check.content.strip().upper():
        state["job_role"] = None
        return job_collect_role_node(state)

    email = extract_email_from_message(last_msg)
    if email:
        state["email"] = email
        job_role = state.get("job_role", "the position")
        cv_text = state.get("cv_text", "")
        questions = generate_interview_questions(cv_text, job_role)
        state["interview_state"] = {
            "questions": questions,
            "questions_asked": [],
            "answers_given": [],
            "current_question_index": 0,
            "total_score": 0,
            "passed": False
        }
        state["response"] = (
            f"✅ Email registered: **{email}**\n\n"
            f"Let's begin your screening interview for **{job_role}**.\n"
            f"There are **{len(questions)} questions** — please answer each one thoughtfully.\n\n"
            f"---\n\n"
            f"**Question 1 of {len(questions)}:**\n\n{questions[0]}"
        )
        state["interview_state"]["questions_asked"].append(questions[0])
    else:
        dynamic_prompt = f"""You are a friendly HR assistant at TechNova Solutions.
The candidate is applying for {state.get('job_role', 'a position')}.
They need to provide their email address but instead said: "{last_msg}"

Respond naturally and conversationally:
- If they said they do not have an email, explain politely that email is required and suggest creating a free Gmail account
- If they said something unrelated, gently redirect them to provide their email
- Keep it under 3 sentences, warm and helpful"""
        dynamic_response = llm.invoke(dynamic_prompt)
        state["response"] = dynamic_response.content.strip()
    return state

# ── Node: Interview ───────────────────────────────────────────────────────────
def interview_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "interview"
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    job_role = state.get("job_role", "")
    iv_state = state.get("interview_state", {})
    questions = iv_state.get("questions", [])
    current_idx = iv_state.get("current_question_index", 0)
    answers = iv_state.get("answers_given", [])

    answers.append(last_msg.strip())
    iv_state["answers_given"] = answers
    next_idx = current_idx + 1

    if next_idx < len(questions):
        iv_state["current_question_index"] = next_idx
        next_q = questions[next_idx]
        iv_state["questions_asked"].append(next_q)
        state["interview_state"] = iv_state
        state["response"] = (
            f"**Question {next_idx + 1} of {len(questions)}:**\n\n{next_q}"
        )
    else:
        state["current_node"] = "evaluate"
        cv_text = state.get("cv_text", "CV not provided")
        qa_pairs = [
            {"question": q, "answer": a}
            for q, a in zip(iv_state["questions_asked"], answers)
        ]
        evaluation = conduct_interview(cv_text, job_role, qa_pairs)
        score = evaluation.get("score", 0)
        decision = evaluation.get("decision", "FAILED")
        reason = evaluation.get("reason", "")
        iv_state["total_score"] = score
        iv_state["passed"] = decision == "PASSED"
        state["interview_state"] = iv_state
        state["interview_result"] = decision

        if decision == "PASSED":
            result_msg = (
                "🎉 **Congratulations!** Based on your responses, you have been "
                "**selected** for the next stage — a technical assessment with our team."
            )
        else:
            result_msg = (
                "Thank you for your time. Unfortunately, your responses did not meet "
                "the minimum requirements for this role right now. "
                "We encourage you to upskill and apply again in the future."
            )

        send_interview_email(state)
        email = state.get("email", "")
        state["response"] = (
            f"**Interview Complete!** ✅\n\n"
            f"**Score:** {score}/100\n"
            f"**Decision:** {decision}\n\n"
            f"{result_msg}\n\n"
            f"**Feedback:** {reason}\n\n"
            f"📧 A detailed result email has been sent to **{email}**."
        )
        state["conversation_done"] = True
    return state

# ── Node: RAG ─────────────────────────────────────────────────────────────────
def rag_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "rag"
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""
    answer = answer_client_question(last_msg)
    state["response"] = f"📚 {answer}"
    return state

# ── Node: Visitor ─────────────────────────────────────────────────────────────
def get_visitor_llm_response(situation: str, context: dict = {}) -> str:
    prompt = f"""You are a friendly receptionist at TechNova Solutions in Lahore.

Situation: {situation}
Context: {context}

Available days: Monday to Friday
Available times: 10:00 AM, 12:00 PM, 2:00 PM, 4:00 PM
Guides: Ahmed Khan (Mon/Wed/Fri), Sara Malik (Tue/Thu), Usman Ali (all week)
Address: 24 Tech Avenue, Gulberg III, Lahore

Respond naturally and conversationally in 2-3 sentences maximum.
Be warm and helpful. Do not use bullet points or markdown formatting."""
    response = llm.invoke(prompt)
    return response.content.strip()

def visitor_node(state: HireIQState) -> HireIQState:
    state["current_node"] = "visitor"
    messages = state.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""

    pending_day = state.get("pending_day", "")
    pending_time = state.get("pending_time", "")

    if not state.get("preferred_time"):
        current_day = extract_day_from_message(last_msg)
        current_time = extract_time_from_message(last_msg)
        final_day = current_day or pending_day
        final_time = current_time or pending_time
        if final_day and final_time:
            last_msg = f"{final_day} at {final_time}"
            state["pending_day"] = ""
            state["pending_time"] = ""
        elif final_day and not final_time:
            state["pending_day"] = final_day
            state["pending_time"] = ""
        elif final_time and not final_day:
            state["pending_time"] = final_time
            state["pending_day"] = ""

    email = state.get("email", "")
    preferred_time = state.get("preferred_time", "")

    if preferred_time:
        change_prompt = f"""The user said: "{last_msg}"
Are they trying to change or correct their already confirmed visit slot of {preferred_time}?
Examples: "No I want Tuesday instead", "Actually make it Wednesday", "Change to 2pm"
Answer with ONLY: YES or NO"""
        change_check = llm.invoke(change_prompt)
        if "YES" in change_check.content.strip().upper():
            state["preferred_time"] = ""
            state["visit_slot"] = ""
            state["assigned_guide"] = ""
            state["guide_available"] = None
            state["pending_day"] = ""
            state["pending_time"] = ""
            preferred_time = ""

    if not preferred_time:
        day = extract_day_from_message(last_msg)
        time = extract_time_from_message(last_msg)

        if day and time:
            state["preferred_time"] = f"{day} at {time}"
            available, guide = check_guide_availability(day, time)
            state["guide_available"] = available
            state["assigned_guide"] = guide or ""
            state["visit_slot"] = f"{day} at {time}"
            if not email:
                state["response"] = get_visitor_llm_response(
                    f"{day} at {time} is available with guide {guide}. Need email to confirm.",
                    {"day": day, "time": time, "guide": guide}
                )
            else:
                send_visitor_email(state)
                state["response"] = get_visitor_llm_response(
                    f"Visit confirmed for {day} at {time} with {guide}. Email sent to {email}.",
                    {"day": day, "time": time, "guide": guide, "email": email}
                )
                state["conversation_done"] = True
        elif day and not time:
            state["pending_day"] = day
            state["response"] = get_visitor_llm_response(
                f"User selected {day} as preferred day but has not chosen a time yet",
                {"day": day}
            )
        elif time and not day:
            state["response"] = get_visitor_llm_response(
                f"User selected {time} as preferred time but has not chosen a day yet",
                {"time": time}
            )
        else:
            state["response"] = get_visitor_llm_response(
                "User wants to visit the office but has not mentioned a specific day or time yet",
                {"last_message": last_msg}
            )
    elif not email:
        email = extract_email_from_message(last_msg)
        if email:
            state["email"] = email
            send_visitor_email(state)
            state["response"] = get_visitor_llm_response(
                f"Visit confirmed for {state.get('visit_slot', preferred_time)} with {state.get('assigned_guide')}. Email sent to {email}.",
                {"slot": state.get("visit_slot"), "guide": state.get("assigned_guide"), "email": email}
            )
            state["conversation_done"] = True
        else:
            state["response"] = get_visitor_llm_response(
                f"Slot {preferred_time} is confirmed with {state.get('assigned_guide')}. Waiting for email address.",
                {"slot": preferred_time, "guide": state.get("assigned_guide")}
            )
    else:
        state["response"] = generate_visitor_response(state)

    return state

# ── process_message ───────────────────────────────────────────────────────────
def process_message(message: str, context: dict = None) -> tuple:
    if context is None:
        context = {}

    state: HireIQState = {
        "person_type":       context.get("person_type"),
        "name":              context.get("name"),
        "email":             context.get("email"),
        "cv_text":           context.get("cv_text"),
        "cv_path":           context.get("cv_path"),
        "cv_received":       context.get("cv_received", False),
        "job_role":          context.get("job_role"),
        "interview_state":   context.get("interview_state"),
        "interview_result":  context.get("interview_result"),
        "client_question":   context.get("client_question"),
        "rag_answer":        context.get("rag_answer"),
        "preferred_time":    context.get("preferred_time"),
        "guide_available":   context.get("guide_available"),
        "assigned_guide":    context.get("assigned_guide"),
        "visit_slot":        context.get("visit_slot"),
        "pending_day":       context.get("pending_day", ""),
        "pending_time":      context.get("pending_time", ""),
        "messages":          context.get("messages", []) + [{"role": "user", "content": message}],
        "current_node":      context.get("current_node", ""),
        "error_count":       context.get("error_count", 0),
        "conversation_done": context.get("conversation_done", False),
        "response":          "",
    }

    current_node = state["current_node"]
    person_type  = state.get("person_type")

    if not current_node and message == "__init__":
        result = greet_node(state)

    elif not current_node:
        routed = route_node(state)
        p_type = routed.get("person_type", "client")
        if p_type == "unknown":
            state["response"] = routed.get("response", "Hi! How can I help you?")
            state["person_type"] = None
            result = state
        elif p_type == "employee":
            result = job_collect_cv_node(routed)
        elif p_type == "visitor":
            result = visitor_node(routed)
        else:
            result = rag_node(routed)

    else:
        if person_type == "employee":
            cv_text  = state.get("cv_text")
            job_role = state.get("job_role")
            email    = state.get("email")
            iv_state = state.get("interview_state")
            done     = state.get("conversation_done", False)
            if done:
                result = state
            elif not cv_text:
                result = job_collect_cv_node(state)
            elif not job_role:
                result = job_collect_role_node(state)
            elif not email:
                result = job_collect_email_node(state)
            elif iv_state:
                result = interview_node(state)
            else:
                result = job_collect_cv_node(state)

        elif person_type == "visitor":
            result = visitor_node(state)

        else:
            routed = route_node(state)
            p_type = routed.get("person_type", "client")
            if p_type == "unknown":
                state["response"] = routed.get("response", "I can help with job applications, office visits, or company information. What would you like to do?")
                state["person_type"] = None
                result = state
            elif p_type == "employee":
                result = job_collect_cv_node(routed)
            elif p_type == "visitor":
                result = visitor_node(routed)
            else:
                result = rag_node(routed)

    response = result.get("response", "I'm sorry, something went wrong. Please try again.")

    updated_context = {
        "person_type":       result.get("person_type"),
        "name":              result.get("name"),
        "email":             result.get("email"),
        "cv_text":           result.get("cv_text"),
        "cv_path":           result.get("cv_path"),
        "cv_received":       result.get("cv_received", False),
        "job_role":          result.get("job_role"),
        "interview_state":   result.get("interview_state"),
        "interview_result":  result.get("interview_result"),
        "client_question":   result.get("client_question"),
        "rag_answer":        result.get("rag_answer"),
        "preferred_time":    result.get("preferred_time"),
        "guide_available":   result.get("guide_available"),
        "assigned_guide":    result.get("assigned_guide"),
        "visit_slot":        result.get("visit_slot"),
        "pending_day":       result.get("pending_day", ""),
        "pending_time":      result.get("pending_time", ""),
        "messages":          result.get("messages", []) + [{"role": "assistant", "content": response}],
        "current_node":      result.get("current_node", ""),
        "error_count":       result.get("error_count", 0),
        "conversation_done": result.get("conversation_done", False),
    }

    return response, updated_context