from datetime import datetime, timezone

import pytest

from wv.core.models import ForecastPoint
from wv.core.risk import RiskAssessment, RiskLevel, RiskRules, assess_risk


@pytest.mark.parametrize(
    "hs,wind,expected",
    [
        (1.50, 18.0, RiskLevel.LOW),
        (2.10, 18.0, RiskLevel.MEDIUM),
        (1.80, 23.0, RiskLevel.MEDIUM),
        (3.20, 20.0, RiskLevel.HIGH),
        (2.50, 29.0, RiskLevel.HIGH),
    ],
)
def test_assess_risk_levels(hs: float, wind: float, expected: RiskLevel) -> None:
    point = ForecastPoint(
        time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=hs,
        tp=8.0,
        dp=120.0,
        wind_speed=wind,
        wind_dir=200.0,
        swell_height=hs,
        swell_period=9.5,
        swell_dir=180.0,
    )

    result: RiskAssessment = assess_risk([point], rules=RiskRules())
    assert result.level == expected
    assert result.metrics["hs"] == pytest.approx(hs, abs=1e-6)
    assert result.metrics["wind_speed"] == pytest.approx(wind, abs=1e-6)


def test_assess_risk_handles_missing_swell_period() -> None:
    point = ForecastPoint(
        time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=2.8,
        tp=None,
        dp=None,
        wind_speed=21.0,
        wind_dir=180.0,
        swell_height=None,
        swell_period=None,
        swell_dir=None,
    )

    result = assess_risk([point], rules=RiskRules())
    assert result.level == RiskLevel.MEDIUM
    assert "missing swell" in " ".join(result.reasons).lower()
