"""Fusion decision tests."""

from __future__ import annotations

from wv.core.fusion import FusionInputs, decide_and_eta


def test_coastal_route_conditional_window() -> None:
    inputs = FusionInputs(
        combined_ft=6.0,
        wind_adnoc=20.0,
        hs_onshore_ft=1.5,
        hs_offshore_ft=3.0,
        wind_albahar=20.0,
        alert="rough at times westward",
        offshore_weight=0.35,
        distance_nm=35.0,
        planned_speed_kt=12.0,
    )
    result = decide_and_eta(inputs)

    assert result.decision == "Conditional Go (coastal window)"
    assert result.hs_fused_m == 1.43
    assert result.wind_fused_kt == 20.0
    assert result.eta_hours == 3.32
    assert result.buffer_minutes == 45


def test_high_seas_forces_no_go() -> None:
    inputs = FusionInputs(
        combined_ft=8.0,
        wind_adnoc=24.0,
        hs_onshore_ft=4.0,
        hs_offshore_ft=6.0,
        wind_albahar=26.0,
        alert="High seas westward",
        offshore_weight=0.65,
        distance_nm=80.0,
        planned_speed_kt=14.0,
    )
    result = decide_and_eta(inputs)

    assert result.decision == "No-Go"
    assert result.hs_fused_m == 2.16
    assert result.wind_fused_kt == 26.0
    assert result.eta_hours == 6.81
    assert result.buffer_minutes == 60


def test_clear_conditions_go() -> None:
    inputs = FusionInputs(
        combined_ft=2.5,
        wind_adnoc=12.0,
        hs_onshore_ft=1.0,
        hs_offshore_ft=1.2,
        wind_albahar=11.0,
        alert=None,
        offshore_weight=0.30,
        distance_nm=20.0,
        planned_speed_kt=13.0,
    )
    result = decide_and_eta(inputs)

    assert result.decision == "Go"
    assert result.hs_fused_m == 0.52
    assert result.wind_fused_kt == 12.0
    assert result.eta_hours == 1.59
    assert result.buffer_minutes == 45
