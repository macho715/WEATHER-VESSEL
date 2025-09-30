"""ADNOC·Al Bahar 결합 의사결정. ADNOC and Al Bahar fused decision support."""

from __future__ import annotations

from typing import Final

from pydantic import Field, field_validator, model_validator

from wv.core.models import LogiBaseModel

FT_TO_M: Final[float] = 0.3048
_MIN_SPEED_KT: Final[float] = 0.1
_ALERT_GAMMA: Final[dict[str, float]] = {
    "": 0.0,
    "rough at times westward": 0.15,
}


class FusionCoefficients(LogiBaseModel):
    """결합 계수 설정. Fusion coefficient configuration."""

    alpha: float = Field(default=0.85, ge=0.0)
    beta: float = Field(default=0.80, ge=0.0)
    wind_factor: float = Field(default=0.06, ge=0.0)
    wave_factor: float = Field(default=0.60, ge=0.0)


class FusionInputs(LogiBaseModel):
    """결합 입력 파라미터. Fusion input parameters."""

    combined_ft: float = Field(..., ge=0.0)
    wind_adnoc: float = Field(..., ge=0.0)
    hs_onshore_ft: float = Field(..., ge=0.0)
    hs_offshore_ft: float = Field(..., ge=0.0)
    wind_albahar: float = Field(..., ge=0.0)
    alert: str | None = None
    offshore_weight: float = Field(..., ge=0.0, le=1.0)
    distance_nm: float = Field(..., gt=0.0)
    planned_speed_kt: float = Field(..., gt=0.0)

    @field_validator("alert")
    @classmethod
    def _normalize_alert(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class FusionResult(LogiBaseModel):
    """결합 결과. Fusion output summary."""

    hs_fused_m: float
    wind_fused_kt: float
    decision: str
    eta_hours: float
    buffer_minutes: int

    @model_validator(mode="after")
    def _round(self) -> "FusionResult":
        object.__setattr__(self, "hs_fused_m", round(self.hs_fused_m, 2))
        object.__setattr__(self, "wind_fused_kt", round(self.wind_fused_kt, 2))
        object.__setattr__(self, "eta_hours", round(self.eta_hours, 2))
        return self


def _alert_gamma(alert: str | None) -> float:
    """경보 가중치를 계산. Compute gamma weight from alert."""

    key = (alert or "").strip().casefold()
    if key.startswith("high seas"):
        return 0.30
    if "rough at times" in key:
        return 0.15
    return _ALERT_GAMMA.get(key, 0.0)


def _is_forced_no_go(alert: str | None) -> bool:
    """강제 출항 금지 여부 확인. Determine forced no-go condition."""

    key = (alert or "").strip().casefold()
    return key.startswith("high seas") or key.startswith("fog")


def decide_and_eta(
    inputs: FusionInputs, coefficients: FusionCoefficients | None = None
) -> FusionResult:
    """결합 의사결정 및 ETA 계산. Fuse signals and compute ETA."""

    coeffs = coefficients or FusionCoefficients()

    hs_on_m = inputs.hs_onshore_ft * FT_TO_M
    hs_off_m = inputs.hs_offshore_ft * FT_TO_M
    hs_from_adnoc = coeffs.alpha * (inputs.combined_ft * FT_TO_M)

    hs_ncm = (1.0 - inputs.offshore_weight) * hs_on_m + inputs.offshore_weight * hs_off_m
    gamma = _alert_gamma(inputs.alert)
    hs_fused = max(hs_ncm, coeffs.beta * hs_from_adnoc) * (1.0 + gamma)

    wind_fused = max(inputs.wind_adnoc, inputs.wind_albahar)

    if _is_forced_no_go(inputs.alert):
        decision = "No-Go"
    elif hs_fused <= 1.0 and wind_fused <= 20.0 and gamma == 0.0:
        decision = "Go"
    elif hs_fused > 1.2 or wind_fused > 22.0:
        decision = "No-Go"
    else:
        decision = "Conditional Go"

    if decision == "No-Go" and inputs.offshore_weight <= 0.40 and hs_on_m <= 1.0 and gamma <= 0.15:
        decision = "Conditional Go (coastal window)"

    wind_penalty = coeffs.wind_factor * max(wind_fused - 10.0, 0.0)
    wave_penalty = coeffs.wave_factor * hs_fused
    effective_speed = max(inputs.planned_speed_kt - wind_penalty - wave_penalty, _MIN_SPEED_KT)
    eta_hours = inputs.distance_nm / effective_speed

    buffer_minutes = 45 if inputs.offshore_weight <= 0.40 else 60

    return FusionResult(
        hs_fused_m=hs_fused,
        wind_fused_kt=wind_fused,
        decision=decision,
        eta_hours=eta_hours,
        buffer_minutes=buffer_minutes,
    )


__all__ = [
    "FusionCoefficients",
    "FusionInputs",
    "FusionResult",
    "decide_and_eta",
]
