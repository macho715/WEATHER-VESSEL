"""이메일 알림. Email notifications."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Sequence

from wv.core.models import NotificationMessage

LOGGER = logging.getLogger(__name__)


def send_email(
    message: NotificationMessage, recipients: Sequence[str], *, dry_run: bool = False
) -> None:
    """SMTP 이메일 발송. Send email via SMTP."""

    host = os.getenv("WV_SMTP_HOST")
    port = int(os.getenv("WV_SMTP_PORT", "587"))
    username = os.getenv("WV_SMTP_USERNAME")
    password = os.getenv("WV_SMTP_PASSWORD")
    sender = os.getenv("WV_EMAIL_SENDER", username or "noreply@weather-vessel.local")

    if dry_run or not host or not recipients:
        LOGGER.info("Dry-run email: %s -> %s", message.subject, ", ".join(recipients))
        LOGGER.debug("Body:\n%s", message.body)
        return

    email_message = EmailMessage()
    email_message["Subject"] = message.subject
    email_message["From"] = sender
    email_message["To"] = ", ".join(recipients)
    email_message.set_content(message.body)

    try:
        with smtplib.SMTP(host, port, timeout=10) as client:
            client.starttls()
            if username and password:
                client.login(username, password)
            client.send_message(email_message)
            LOGGER.info("Sent email notification to %s", ", ".join(recipients))
    except smtplib.SMTPException as exc:
        LOGGER.error("SMTP error: %s", exc)
        raise


__all__ = ["send_email"]
