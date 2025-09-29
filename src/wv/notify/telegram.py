"""Telegram 알림 발송기. | Telegram notification sender."""

from __future__ import annotations

from typing import Optional

import httpx


class TelegramNotifier:
    """Telegram Bot 발송기. | Telegram bot notifier."""

    def __init__(self, token: Optional[str], chat_id: Optional[str]) -> None:
        self.token = token
        self.chat_id = chat_id

    def send(self, message: str) -> None:  # pragma: no cover - network call
        """Telegram 메시지 발송. | Send Telegram message."""

        if not self.token or not self.chat_id:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        with httpx.Client(timeout=5.0) as client:
            response = client.post(url, data={"chat_id": self.chat_id, "text": message})
            response.raise_for_status()
