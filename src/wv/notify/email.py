"""이메일 알림 모듈. | Email notification module."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional, Protocol, Sequence

from wv.notify.manager import NotificationChannel


class SupportsSendMessage(Protocol):
    """SMTP 호환 객체 프로토콜. | Protocol for SMTP-like clients."""

    def send_message(self, message: EmailMessage) -> None:
        """메시지를 전송. | Send message."""


class EmailNotifier(NotificationChannel):
    """이메일 발송 도우미. | Helper for sending email."""

    def __init__(
        self,
        smtp_client: Optional[SupportsSendMessage] | None = None,
        sender: Optional[str] | None = None,
        recipients: Optional[Sequence[str]] | None = None,
    ) -> None:
        self.sender = sender or os.getenv("WV_EMAIL_SENDER", "noreply@weather-vessel.local")
        env_recipients = os.getenv("WV_EMAIL_RECIPIENTS", "")
        if recipients is not None:
            self.recipients = list(recipients)
        elif env_recipients:
            self.recipients = [item.strip() for item in env_recipients.split(",") if item.strip()]
        else:
            self.recipients = []
        self.smtp_client = smtp_client

    def _make_connection(self) -> smtplib.SMTP:
        host = os.getenv("WV_SMTP_HOST", "localhost")
        port = int(os.getenv("WV_SMTP_PORT", "25"))
        username = os.getenv("WV_SMTP_USERNAME")
        password = os.getenv("WV_SMTP_PASSWORD")
        use_tls = os.getenv("WV_SMTP_TLS", "false").lower() in {"true", "1", "yes"}
        client = smtplib.SMTP(host=host, port=port, timeout=10)
        if use_tls:
            client.starttls()
        if username and password:
            client.login(username, password)
        return client

    def send(self, subject: str, body: str) -> None:
        """이메일을 발송. | Send an email."""
        if not self.recipients:
            return
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = ", ".join(self.recipients)
        message.set_content(body)

        if self.smtp_client is not None:
            self.smtp_client.send_message(message)
            return

        with self._make_connection() as client:
            client.send_message(message)
