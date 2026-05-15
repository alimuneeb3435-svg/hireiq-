from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    temperature=0.3,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

GUIDES = {
    "Ahmed Khan": ["Monday", "Wednesday", "Friday"],
    "Sara Malik": ["Tuesday", "Thursday"],
    "Usman Ali": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}

AVAILABLE_SLOTS = ["10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM"]

def check_guide_availability(day: str, time: str) -> tuple:
    for guide, available_days in GUIDES.items():
        if day in available_days:
            return (True, guide)
    return (False, None)

def extract_day_from_message(message: str) -> str:
    prompt = f"""Extract the day of the week from this message: "{message}"

The user may have typos or abbreviations like:
- "Moday" or "moday" = Monday
- "Tues" = Tuesday
- "Wed" = Wednesday
- "Thurs" = Thursday
- "Fri" = Friday

If a valid weekday is mentioned, respond with ONLY the correct full day name.
If no day is mentioned, respond with ONLY: NONE"""
    response = llm.invoke(prompt)
    result = response.content.strip()
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in valid_days:
        if day.lower() in result.lower():
            return day
    return ""

def extract_time_from_message(message: str) -> str:
    prompt = f"""Extract the time from this message: "{message}"

Map what the user says to one of these exact slots:
- "10 am", "10am", "10:00", "10 in the morning" = 10:00 AM
- "12 pm", "noon", "12:00" = 12:00 PM
- "2 pm", "2:00", "2 in the afternoon" = 2:00 PM
- "4 pm", "4:00", "evening" = 4:00 PM

If a time is mentioned, respond with ONLY the exact slot: 10:00 AM or 12:00 PM or 2:00 PM or 4:00 PM
If no time is mentioned, respond with ONLY: NONE"""
    response = llm.invoke(prompt)
    result = response.content.strip()
    for slot in AVAILABLE_SLOTS:
        if slot.lower() in result.lower():
            return slot
    return ""

def handle_visitor_request(state: dict) -> dict:
    return state

def generate_visitor_response(state: dict) -> str:
    return "Your visit has been confirmed. We look forward to seeing you!"
