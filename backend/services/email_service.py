"""
ElevateIQ — Asynchronous Email Notification Service
=====================================================
Dispatches formatted HTML emails via SMTP for meeting invites,
reminders, and security notifications.
"""

import os
import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("elevateiq.services.email")

SMTP_SERVER   = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL  = os.getenv("SENDER_EMAIL", "noreply@elevateiq.internal")


def _send_smtp_task(recipient: str, subject: str, html_content: str):
    """Worker task executing SMTP connection & delivery."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        log.info("SMTP credentials not configured — skipping actual network send for '%s' to %s", subject, recipient)
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [recipient], msg.as_string())

        log.info("Email successfully dispatched to %s with subject: %s", recipient, subject)
    except Exception as exc:
        log.error("Failed to send email to %s: %s", recipient, exc)


def send_email_async(recipient: str, subject: str, html_content: str):
    """Spawns daemon thread to send email without blocking HTTP/Socket thread."""
    thread = threading.Thread(target=_send_smtp_task, args=(recipient, subject, html_content))
    thread.daemon = True
    thread.start()


def send_meeting_reminder_email(recipient_email: str, recipient_name: str, meeting_title: str, scheduled_time: str, join_url: str):
    """Send branded meeting reminder email."""
    subject = f"⏰ Meeting Reminder: {meeting_title}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #080911; color: #ffffff; padding: 30px; borderRadius: 16px;">
        <h2 style="color: #6366f1;">ElevateIQ Meeting Reminder</h2>
        <p>Hi <strong>{recipient_name}</strong>,</p>
        <p>This is a reminder that your scheduled session <strong>"{meeting_title}"</strong> is starting soon.</p>
        <div style="background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 20px 0;">
            <p><strong>Session:</strong> {meeting_title}</p>
            <p><strong>Scheduled Start:</strong> {scheduled_time}</p>
        </div>
        <a href="{join_url}" style="background: linear-gradient(to right, #4f46e5, #9333ea); color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
            Join Meeting Now
        </a>
    </div>
    """
    send_email_async(recipient_email, subject, html_content)
