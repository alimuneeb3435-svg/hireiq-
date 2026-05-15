from agents.mail_sender import send_email

def send_interview_email(state: dict) -> bool:
    email = state.get("email", "")
    job_role = state.get("job_role", "the position")
    iv_state = state.get("interview_state", {})
    score = iv_state.get("total_score", 0)
    decision = state.get("interview_result", "FAILED")
    name = state.get("name", "Candidate")

    if not email:
        return False

    if decision == "PASSED":
        subject = f"HireIQ — Congratulations! You Passed — {job_role}"
        body = f"""
        <h2>Congratulations {name}!</h2>
        <p>We are pleased to inform you that you have <strong>PASSED</strong> the initial screening for <strong>{job_role}</strong> at TechNova Solutions.</p>
        <p><strong>Score:</strong> {score}/100</p>
        <p>Our team will contact you shortly for the next stage — a technical assessment.</p>
        <br>
        <p>Best regards,<br>HireIQ — TechNova Solutions HR Team</p>
        """
    else:
        subject = f"HireIQ — Application Update — {job_role}"
        body = f"""
        <h2>Dear {name},</h2>
        <p>Thank you for applying for <strong>{job_role}</strong> at TechNova Solutions.</p>
        <p>After reviewing your responses, we regret to inform you that you did not meet the minimum requirements for this role at this time.</p>
        <p><strong>Score:</strong> {score}/100</p>
        <p>We encourage you to upskill and apply again in the future.</p>
        <br>
        <p>Best regards,<br>HireIQ — TechNova Solutions HR Team</p>
        """
    return send_email(email, subject, body)

def send_visitor_email(state: dict) -> bool:
    email = state.get("email", "")
    visit_slot = state.get("visit_slot", "")
    guide = state.get("assigned_guide", "Our team")
    name = state.get("name", "Visitor")

    if not email:
        return False

    subject = "HireIQ — Visit Confirmation — TechNova Solutions"
    body = f"""
    <h2>Visit Confirmed!</h2>
    <p>Dear {name},</p>
    <p>Your visit to TechNova Solutions has been confirmed.</p>
    <p><strong>Date & Time:</strong> {visit_slot}</p>
    <p><strong>Guide:</strong> {guide}</p>
    <p><strong>Address:</strong> 24 Tech Avenue, Gulberg III, Lahore, Pakistan</p>
    <p>Please bring a valid ID. We look forward to seeing you!</p>
    <br>
    <p>Best regards,<br>HireIQ — TechNova Solutions</p>
    """
    return send_email(email, subject, body)