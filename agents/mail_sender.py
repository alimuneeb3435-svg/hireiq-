import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        # Try secrets first, then fall back to env
        try:
            sender_email = st.secrets["EMAIL_SENDER"]
            sender_password = st.secrets["EMAIL_PASSWORD"]
        except:
            sender_email = os.getenv("EMAIL_SENDER")
            sender_password = os.getenv("EMAIL_PASSWORD")
        
        print("EMAIL:", sender_email)
        if not sender_email or not sender_password:
            print("Email credentials not configured")
            return False
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email
        
        part = MIMEText(body, "html")
        msg.attach(part)
        
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(
                sender_email,
                to_email,
                msg.as_string()
            )
        
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
