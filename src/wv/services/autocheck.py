"""자동 위험 점검 스케줄러. | Auto risk check scheduler."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Protocol, Sequence, Tuple
from zoneinfo import ZoneInfo

from wv.core.models import ForecastPoint
from wv.core.risk import compute_risk
from wv.core.utils import format_metric


class MarineServiceProtocol(Protocol):
    """해양 서비스 인터페이스. | Marine service interface."""

    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> Sequence[ForecastPoint]:
        """예측을 반환. | Return forecast."""


class NotificationClient(Protocol):
    """알림 클라이언트 인터페이스. | Notification client interface."""

    def send_all(self, title: str, message: str, dry_run: bool = False) -> None:
        """알림을 전송. | Send notifications."""


class AutoCheckScheduler:
    """정시 알림을 실행. | Execute scheduled notifications."""

    def __init__(
        self,
        marine_service: MarineServiceProtocol,
        notifier: NotificationClient,
        routes: Mapping[str, Tuple[float, float]],
        timezone_name: str = "Asia/Dubai",
    ) -> None:
        self.marine_service = marine_service
        self.notifier = notifier
        self.routes = dict(routes)
        self.tz = ZoneInfo(timezone_name)

    def _is_window(self, moment: datetime) -> bool:
        local = moment.astimezone(self.tz)
        return local.minute == 0 and local.hour in {6, 17}

    def run_pending(self, now: datetime | None = None) -> None:
        """예약된 작업을 실행. | Run pending jobs."""
        moment = now or datetime.now(timezone.utc)
        if not self._is_window(moment):
            return
        for route, coords in self.routes.items():
            lat, lon = coords
            points = self.marine_service.get_forecast(lat=lat, lon=lon, hours=48)
            if not points:
                continue
            assessment = compute_risk(points[0])
            subject = f"Scheduled marine risk - {route}"
            body = (
                f"Risk Level: {assessment.level.value}\n"
                f"Hs: {format_metric(points[0].hs, 'm')}\n"
                f"Wind: {format_metric(points[0].wind_speed, 'kt')}\n"
                f"Reasons: {', '.join(assessment.reasons)}"
            )
            self.notifier.send_all(subject, body, dry_run=False)
