"""해양 단위 변환 유틸. Marine unit conversion utilities."""

from __future__ import annotations

KNOT_TO_METER_PER_SECOND = 0.514444
METER_PER_SECOND_TO_KNOT = 1.943844
FOOT_TO_METER = 0.3048
METER_TO_FOOT = 3.28084


def knots_to_meters_per_second(knots: float) -> float:
    """노트→미터매초 변환. Convert knots to meters per second."""

    return round(knots * KNOT_TO_METER_PER_SECOND, 2)


def meters_per_second_to_knots(speed: float) -> float:
    """미터매초→노트 변환. Convert meters per second to knots."""

    return round(speed * METER_PER_SECOND_TO_KNOT, 2)


def feet_to_meters(feet: float) -> float:
    """피트→미터 변환. Convert feet to meters."""

    return round(feet * FOOT_TO_METER, 2)


def meters_to_feet(meters: float) -> float:
    """미터→피트 변환. Convert meters to feet."""

    return round(meters * METER_TO_FOOT, 2)
