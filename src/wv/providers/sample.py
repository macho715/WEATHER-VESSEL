"""샘플 데이터 공급자. Sample data provider."""

from __future__ import annotations

import datetime as dt
import math
from typing import Iterable

from wv.core.models import ForecastPoint
from wv.providers.base import BaseProvider


class SampleProvider(BaseProvider):
    """기본 샘플 예보. Deterministic sample forecast."""

    @property
    def name(self) -> str:
        """공급자 이름. Provider name."""

        return "sample"

    def fetch_forecast(self, lat: float, lon: float, hours: int) -> Iterable[ForecastPoint]:
        """모의 데이터를 생성. Generate simulated data."""

        base = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
        step_hours = 3
        total_steps = max(1, hours // step_hours)
        points: list[ForecastPoint] = []
        for idx in range(total_steps):
            time = base + dt.timedelta(hours=idx * step_hours)
            wave = 1.2 + 0.5 * math.sin(idx / 3)
            wind = 15.0 + 4.0 * math.cos(idx / 4)
            swell_period = 8.0 + 0.3 * math.sin(idx / 2)
            points.append(
                ForecastPoint(
                    time=time,
                    lat=lat,
                    lon=lon,
                    hs=round(max(wave, 0.5), 2),
                    tp=round(swell_period, 2),
                    dp=120.0,
                    wind_speed=round(max(wind, 5.0), 2),
                    wind_dir=90.0,
                    swell_height=round(max(wave - 0.3, 0.3), 2),
                    swell_period=round(swell_period, 2),
                    swell_direction=110.0,
                )
            )
        return points


__all__ = ["SampleProvider"]
