"""Slack 알림 발송기. | Slack notification sender."""

from __future__ import annotations

from typing import Optional

import httpx


class SlackNotifier:
    """Slack Webhook 발송기. | Slack webhook notifier."""

    def __init__(self, webhook_url: Optional[str]) -> None:
        self.webhook_url = webhook_url

    def send(self, message: str) -> None:  # pragma: no cover - network call
        """Slack 메시지 발송. | Send Slack message."""

        if not self.webhook_url:
            return
        with httpx.Client(timeout=5.0) as client:
            response = client.post(self.webhook_url, json={"text": message})
            response.raise_for_status()
