import os
import smtplib
from email.message import EmailMessage


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """Send email using SMTP details from environment variables. Returns False if not configured."""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([smtp_host, smtp_user, smtp_password, to_email]):
        return False

    msg = EmailMessage()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    return True
