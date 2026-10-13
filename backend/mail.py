"""SMTP delivery using the standard library (PHP equivalent: mail())."""
import os
import smtplib
from email.message import EmailMessage


def send(to, subject, body):
    message = EmailMessage()
    message['From'] = os.environ.get('MAIL_FROM', 'noreply@camagru.local')
    message['To'] = to
    message['Subject'] = subject
    message.set_content(body)
    with smtplib.SMTP(os.environ.get('SMTP_HOST', 'mailpit'),
                      int(os.environ.get('SMTP_PORT', '1025')), timeout=10) as smtp:
        smtp.send_message(message)
