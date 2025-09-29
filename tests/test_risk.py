import datetime as dt

from wv.core.models import ForecastPoint
from wv.core.risk import RiskLevel, assess_risk, default_risk_config


def _point(**kwargs):
    base = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
    defaults = dict(
        time=base,
        lat=24.4,
        lon=54.7,
        hs=1.5,
        tp=8.0,
        dp=100.0,
        wind_speed=12.0,
        wind_dir=90.0,
        swell_height=1.0,
        swell_period=9.0,
        swell_direction=105.0,
    )
    defaults.update(kwargs)
    return ForecastPoint(**defaults)


def test_risk_medium_on_wave_height() -> None:
    assessment = assess_risk([_point(hs=2.2)])
    assert assessment.level is RiskLevel.MEDIUM
    assert any("wave" in reason.reason_en.lower() for reason in assessment.reasons)


def test_risk_high_on_wind() -> None:
    assessment = assess_risk([_point(wind_speed=29.0)])
    assert assessment.level is RiskLevel.HIGH


def test_risk_low_below_thresholds() -> None:
    cfg = default_risk_config()
    assessment = assess_risk(
        [_point(hs=cfg.medium_wave_threshold - 0.1, wind_speed=cfg.medium_wind_threshold - 0.1)]
    )
    assert assessment.level is RiskLevel.LOW
