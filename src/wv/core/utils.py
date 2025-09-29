"""공용 유틸리티를 제공. | Provide shared utilities."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def format_metric(value: float | None, unit: str | None = None) -> str:
    """수치를 소수 둘째 자리까지 형식화. | Format value to two decimals."""
    if value is None:
        return "N/A"
    quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    formatted = f"{quantized:.2f}"
    if unit:
        return f"{formatted} {unit}"
    return formatted
