"""Telegram 알림 모듈. | Telegram notification module."""

from __future__ import annotations

import httpx

from wv.notify.manager import NotificationChannel


class TelegramNotifier(NotificationChannel):
    """텔레그램 봇 발송기. | Telegram bot sender."""

    def __init__(self, bot_token: str, chat_id: str, client: httpx.Client | None = None) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.client = client or httpx.Client()
        self._owns_client = client is None

    def __del__(self) -> None:
        if getattr(self, "_owns_client", False):
            self.client.close()

    def send(self, title: str, message: str) -> None:
        """텔레그램으로 메시지를 발송. | Send message to Telegram."""
        base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"{title}\n{message}",
            "parse_mode": "Markdown",
        }
        response = self.client.post(base_url, data=payload, timeout=10)
        if response.status_code >= 400:
            raise RuntimeError(f"Telegram notification failed: {response.status_code}")
