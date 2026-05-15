from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def classify_person(message: str) -> str:
    msg_lower = message.lower().strip()
    vague_patterns = ["hi", "hello", "hey", "how are you", "good morning", "good evening", "how r u"]
    keywords = ["apply", "job", "visit", "service", "cv", "resume", "position", "office", "info"]
    has_keyword = any(k in msg_lower for k in keywords)
    if msg_lower in vague_patterns or (len(msg_lower.split()) < 3 and not has_keyword):
        return "unknown"
    prompt = f"""You are classifying a user message for an HR assistant at TechNova Solutions.

User message: "{message}"

CATEGORIES:
- JOB_SEEKER: User wants to ACTIVELY APPLY — submitting CV, starting interview, applying for a role
- VISITOR: User wants to physically visit or tour the office
- INFO_SEEKER: User is ASKING QUESTIONS about the company — salary, benefits, remote work, internships, working hours, services, office location, culture, guides, hiring process

EXAMPLES:
"I want to apply for a job" → JOB_SEEKER
"Can I submit my CV?" → JOB_SEEKER
"Do you offer internships?" → INFO_SEEKER
"What is the salary range?" → INFO_SEEKER
"Do you offer remote work?" → INFO_SEEKER
"Who is Ahmed Khan?" → INFO_SEEKER
"What services do you offer?" → INFO_SEEKER
"I want to visit your office" → VISITOR
"Can I schedule a tour?" → VISITOR
"I want to apply for AI Engineer role" → JOB_SEEKER
"I want to apply for the job" → JOB_SEEKER

Answer with ONLY: JOB_SEEKER, VISITOR, or INFO_SEEKER"""

    response = llm.invoke(prompt)
    result = response.content.strip().upper()
    if "JOB_SEEKER" in result:
        return "employee"
    elif "VISITOR" in result:
        return "visitor"
    else:
        return "client"

def extract_email_from_message(message: str) -> str:
    import re
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
    return match.group(0) if match else ""

def get_natural_clarification(user_message: str) -> str:
    prompt = f"""The user said: "{user_message}"

You are HireIQ, a friendly HR assistant for TechNova Solutions.
This message is vague or unclear. Respond naturally based on what they actually said:
- If it is completely off-topic, politely say that is outside your scope and redirect
- If it is vague, ask a clarifying question
- If it seems career-related but unclear, gently ask if they want to apply or just get info
- If they seem frustrated, acknowledge it warmly
- Never repeat the same menu robotically

Keep it under 3 sentences. Sound human and helpful."""
    response = llm.invoke(prompt)
    return response.content.strip()