"""커넥터 단위 테스트. Connector unit tests."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import httpx

from marine_ops.connectors.open_meteo_fallback import (
    OpenMeteoFallback,
    fetch_forecast_with_fallback,
)
from marine_ops.connectors.stormglass import STORMGLASS_PARAMS, StormglassConnector
from marine_ops.connectors.worldtides import WorldTidesConnector
from marine_ops.core.schema import MarineVariable, UnitEnum

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    path = FIXTURE_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def make_client(payload: dict) -> httpx.Client:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    return httpx.Client(transport=transport)


def test_stormglass_connector_parses_hours() -> None:
    connector = StormglassConnector(
        api_key="test",
        client=make_client(load_fixture("stormglass_response.json")),
    )
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    series = connector.fetch_forecast(25.0, 55.0, start, end)
    assert len(series.points) == 2
    first_point = series.points[0]
    assert first_point.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") == "2025-01-01T00:00:00Z"
    variables = {measurement.variable for measurement in first_point.measurements}
    assert {item[1] for item in STORMGLASS_PARAMS}.issubset(variables)
    assert first_point.measurements[0].unit in {
        UnitEnum.METERS,
        UnitEnum.METERS_PER_SECOND,
        UnitEnum.DEGREES,
    }


def test_worldtides_connector_heights() -> None:
    connector = WorldTidesConnector(
        api_key="dummy",
        client=make_client(load_fixture("worldtides_response.json")),
    )
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    series = connector.fetch_heights(25.0, 55.0, start)
    assert len(series.points) == 2
    assert series.points[0].measurements[0].variable == MarineVariable.TIDE_HEIGHT
    assert series.points[0].measurements[0].value == 0.6


def test_open_meteo_fallback_transforms_response() -> None:
    connector = OpenMeteoFallback(
        client=make_client(load_fixture("open_meteo_response.json")),
    )
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    series = connector.fetch_forecast(25.0, 55.0, start, end)
    assert len(series.points) == 2
    assert any(
        m.variable == MarineVariable.SIGNIFICANT_WAVE_HEIGHT for m in series.points[0].measurements
    )
    assert series.points[0].measurements[0].value == 1.1


def test_fetch_forecast_with_fallback_on_rate_limit() -> None:
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)

    def stormglass_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"errors": ["rate limit"]}, request=request)

    def open_meteo_handler(request: httpx.Request) -> httpx.Response:
        payload = load_fixture("open_meteo_response.json")
        return httpx.Response(200, json=payload, request=request)

    stormglass_client = httpx.Client(transport=httpx.MockTransport(stormglass_handler))
    open_meteo_client = httpx.Client(transport=httpx.MockTransport(open_meteo_handler))

    stormglass = StormglassConnector(api_key="test", client=stormglass_client)
    fallback = OpenMeteoFallback(client=open_meteo_client)
    series = fetch_forecast_with_fallback(25.0, 55.0, start, end, stormglass, fallback)
    assert series.points
    assert series.points[0].metadata.source == "open-meteo"


def test_stormglass_handles_missing_values() -> None:
    payload = load_fixture("stormglass_response.json")
    payload["hours"][0]["waveHeight"] = {}
    connector = StormglassConnector(api_key="test", client=make_client(payload))
    start = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    series = connector.fetch_forecast(25.0, 55.0, start, end)
    assert any(
        m.variable == MarineVariable.SIGNIFICANT_WAVE_HEIGHT for m in series.points[1].measurements
    )
