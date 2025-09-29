"""이메일 알림 발송기. | Email notification sender."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import NotificationConfig


class EmailNotifier:
    """SMTP 이메일 발송기. | SMTP email notifier."""

    def __init__(self, config: NotificationConfig) -> None:
        self.config = config

    def send(self, subject: str, body: str) -> None:  # pragma: no cover - external SMTP
        """이메일 발송. | Send email notification."""

        if not self.config.email_from or not self.config.email_to:
            raise ValueError("Email sender/recipients not configured")
        if not self.config.smtp_host:
            raise ValueError("SMTP host not configured")

        message = EmailMessage()
        message["From"] = self.config.email_from
        message["To"] = ", ".join(self.config.email_to)
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as client:
            client.starttls()
            if self.config.smtp_username and self.config.smtp_password:
                client.login(self.config.smtp_username, self.config.smtp_password)
            client.send_message(message)
