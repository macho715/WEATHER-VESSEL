"""알림 채널 관리. | Manage notification channels."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Sequence

LOGGER = logging.getLogger("wv.notify")


@dataclass(slots=True)
class NotificationChannel:
    """알림 채널 인터페이스. | Notification channel interface."""

    def send(self, title: str, message: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class NotificationManager:
    """다중 채널 알림 관리자. | Multi-channel notification manager."""

    def __init__(self, channels: Sequence[NotificationChannel]) -> None:
        self.channels: List[NotificationChannel] = list(channels)

    def send_all(self, title: str, message: str, dry_run: bool = False) -> None:
        """모든 채널에 전송. | Send to all channels."""
        if dry_run:
            LOGGER.info("Dry run: %s - %s", title, message)
            return
        for channel in self.channels:
            try:
                channel.send(title, message)
            except Exception as exc:  # pragma: no cover - logging path
                LOGGER.error("Notification via %s failed: %s", channel.__class__.__name__, exc)
