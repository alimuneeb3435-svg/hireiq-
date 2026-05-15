from langchain_groq import ChatGroq
from config.prompts import CLIENT_AGENT_PROMPT
from utils.rag_setup import get_rag_answer
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    temperature=0.3,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def answer_client_question(question: str) -> str:
    context = get_rag_answer(question)
    prompt = CLIENT_AGENT_PROMPT.format(
        context=context,
        question=question
    )
    response = llm.invoke(prompt)
    return response.content.strip()
