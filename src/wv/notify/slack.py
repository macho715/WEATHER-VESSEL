"""Slack 알림 모듈. | Slack notification module."""

from __future__ import annotations

import httpx

from wv.notify.manager import NotificationChannel


class SlackNotifier(NotificationChannel):
    """Slack 웹훅 발송기. | Slack webhook sender."""

    def __init__(self, webhook_url: str, client: httpx.Client | None = None) -> None:
        self.webhook_url = webhook_url
        self.client = client or httpx.Client()
        self._owns_client = client is None

    def __del__(self) -> None:
        if getattr(self, "_owns_client", False):
            self.client.close()

    def send(self, title: str, message: str) -> None:
        """Slack으로 메시지를 발송. | Send message to Slack."""
        payload = {"text": f"*{title}*\n{message}"}
        response = self.client.post(self.webhook_url, json=payload, timeout=10)
        if response.status_code >= 400:
            raise RuntimeError(f"Slack notification failed: {response.status_code}")
