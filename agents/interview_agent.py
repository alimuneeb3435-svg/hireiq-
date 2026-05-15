from crewai import Agent, Task, Crew, Process, LLM
import os
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY")
)

def is_valid_cv(cv_text: str) -> bool:
    text_lower = cv_text.lower()
    personal_keywords = [
        "curriculum vitae", "resume", "objective", "career objective",
        "professional summary", "work experience", "employment history",
        "date of birth", "nationality", "cgpa", "gpa",
        "bachelor of", "master of", "b.sc", "b.e", "m.sc", "bs ",
        "graduated", "currently pursuing", "seeking", "looking for",
        "internship", "university", "college", "degree"
    ]
    technical_doc_keywords = [
        "abstract", "introduction", "conclusion", "references cited",
        "ieee", "published in", "doi:", "copyright", "all rights reserved",
        "chapter ", "section ", "figure ", "table ", "equation "
    ]
    personal_matches = sum(1 for kw in personal_keywords if kw in text_lower)
    tech_matches = sum(1 for kw in technical_doc_keywords if kw in text_lower)
    if tech_matches >= 3:
        return False
    return personal_matches >= 2

def generate_interview_questions(cv_text: str, job_role: str) -> list:
    generator = Agent(
        role="Interview Question Generator",
        goal=f"Generate interview questions for {job_role}",
        backstory="You are an expert technical interviewer.",
        llm=llm,
        verbose=False
    )
    task = Task(
        description=f"""Generate exactly 5 interview questions for the role: {job_role}

Candidate CV:
{cv_text[:1000]}

Rules:
- Make questions relevant to the candidate's actual CV background
- Mix easy to medium difficulty
- Relate questions to how their background applies to {job_role}

Format:
Q1: ...
Q2: ...
Q3: ...
Q4: ...
Q5: ...
""",
        agent=generator,
        expected_output="A list of 5 structured interview questions in Q1-Q5 format"
    )
    crew = Crew(
        agents=[generator],
        tasks=[task],
        process=Process.sequential,
        verbose=False
    )
    result = crew.kickoff()
    text = str(result)
    questions = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("Q") and ":" in line:
            questions.append(line.split(":", 1)[1].strip())
    return questions[:5]

def conduct_interview(cv_text: str, job_role: str, questions_and_answers: list) -> dict:
    scorer = Agent(
        role="HR Scoring Agent",
        goal="Evaluate interview performance and make hiring decision",
        backstory="You are a senior HR professional who scores candidates objectively.",
        llm=llm,
        verbose=False
    )
    qa_history = ""
    for i, qa in enumerate(questions_and_answers, 1):
        qa_history += f"\nQ{i}: {qa['question']}\nA{i}: {qa['answer']}\n"

    scoring_task = Task(
        description=f"""Evaluate this candidate for {job_role} position.

CV SUMMARY:
{cv_text[:1000] if cv_text else "CV not provided"}

INTERVIEW TRANSCRIPT:
{qa_history}

Provide a score from 0-100 and a PASS/FAIL decision.
Passing score is 70 or above.

Consider:
- Relevant skills match (MOST IMPORTANT)
- Field relevance — unrelated background should score max 50
- Communication clarity
- Experience relevance
- Problem-solving ability

Respond in this exact format:
SCORE: [number]
DECISION: [PASSED/FAILED]
REASON: [brief explanation 2-3 sentences]
""",
        agent=scorer,
        expected_output="SCORE, DECISION, and REASON in specified format"
    )
    scoring_crew = Crew(
        agents=[scorer],
        tasks=[scoring_task],
        process=Process.sequential,
        verbose=False
    )
    result = scoring_crew.kickoff()
    result_text = str(result)
    score = 0
    decision = "FAILED"
    reason = ""
    for line in result_text.split('\n'):
        if line.startswith('SCORE:'):
            try:
                score = int(line.replace('SCORE:', '').strip())
            except:
                score = 0
        elif line.startswith('DECISION:'):
            decision = line.replace('DECISION:', '').strip().upper()
        elif line.startswith('REASON:'):
            reason = line.replace('REASON:', '').strip()
    return {
        "score": score,
        "decision": decision,
        "reason": reason
    }
