"""SMTP delivery using the standard library (PHP equivalent: mail())."""

import os
import smtplib
from email.message import EmailMessage


def send(to, subject, body):
    # PHP: mail($to, $subject, $body, $headers) provides email delivery.
    # mail() delegates transport to configured mail software; smtplib connects
    # directly to our SMTP server.
    message = EmailMessage()
    message["From"] = os.environ.get("MAIL_FROM", "noreply@camagru.local")
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(
        os.environ.get("SMTP_HOST", "mailpit"),
        int(os.environ.get("SMTP_PORT", "1025")),
        timeout=10,
    ) as smtp:
        smtp.send_message(message)


def send_link(email, title, page, token):
    url = os.environ.get("APP_URL", "http://localhost:8000").rstrip("/")
    send(
        email,
        title,
        f"Follow this link:\n{url}/?page={page}&token={token}\n\n"
        "If you did not request this, ignore this email.",
    )
