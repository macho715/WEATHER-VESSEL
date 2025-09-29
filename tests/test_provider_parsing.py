import pytest

from wv.providers.copernicus import CopernicusMarineProvider
from wv.providers.noaa_ww3 import NoaaWaveWatchProvider
from wv.providers.open_meteo import OpenMeteoMarineProvider
from wv.providers.sample import SampleProvider
from wv.providers.stormglass import StormglassProvider


@pytest.fixture(autouse=True)
def _no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WV_STORMGLASS_API_KEY", raising=False)
    monkeypatch.delenv("WV_STORMGLASS_ENDPOINT", raising=False)
    monkeypatch.delenv("WV_NOAA_WW3_ENDPOINT", raising=False)
    monkeypatch.delenv("WV_COPERNICUS_ENDPOINT", raising=False)
    monkeypatch.delenv("WV_COPERNICUS_TOKEN", raising=False)


def test_sample_provider_generates_points() -> None:
    provider = SampleProvider()
    points = list(provider.fetch_forecast(24.4, 54.7, 12))
    assert len(points) >= 1


def test_stormglass_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WV_STORMGLASS_API_KEY", "dummy")
    monkeypatch.setenv("WV_STORMGLASS_ENDPOINT", "https://example.com")
    provider = StormglassProvider()

    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        return {
            "hours": [
                {
                    "time": "2024-01-01T00:00:00+00:00",
                    "waveHeight": {"sg": 1.2},
                    "wavePeriod": {"sg": 7.5},
                    "waveDirection": {"sg": 120},
                    "windSpeed": {"sg": 15},
                    "windDirection": {"sg": 90},
                    "swellHeight": {"sg": 1.0},
                    "swellPeriod": {"sg": 8.0},
                    "swellDirection": {"sg": 100},
                }
            ]
        }

    monkeypatch.setattr("wv.providers.stormglass.request_json", fake_request)
    points = list(provider.fetch_forecast(24.4, 54.7, 6))
    assert points[0].hs == 1.2


def test_open_meteo_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OpenMeteoMarineProvider()

    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        return {
            "hourly": {
                "time": ["2024-01-01T00:00:00+00:00"],
                "wave_height": [1.5],
                "wave_direction": [100],
                "wave_period": [7.5],
                "wind_speed_10m": [18.0],
                "wind_direction_10m": [80],
                "swell_wave_height": [1.2],
                "swell_wave_direction": [110],
                "swell_wave_period": [8.5],
            }
        }

    monkeypatch.setattr("wv.providers.open_meteo.request_json", fake_request)
    points = list(provider.fetch_forecast(24.4, 54.7, 6))
    assert points[0].wind_speed == 18.0


def test_noaa_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WV_NOAA_WW3_ENDPOINT", "https://example.com")
    provider = NoaaWaveWatchProvider()

    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        return {
            "data": [
                {
                    "time": "2024-01-01T00:00:00+00:00",
                    "hs": 1.3,
                    "tp": 7.0,
                    "dp": 120,
                    "wind_speed": 16,
                    "wind_dir": 85,
                }
            ]
        }

    monkeypatch.setattr("wv.providers.noaa_ww3.request_json", fake_request)
    points = list(provider.fetch_forecast(24.4, 54.7, 6))
    assert points[0].hs == 1.3


def test_copernicus_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WV_COPERNICUS_ENDPOINT", "https://example.com")
    monkeypatch.setenv("WV_COPERNICUS_TOKEN", "token")
    provider = CopernicusMarineProvider()

    def fake_request(method, url, **kwargs):  # type: ignore[unused-argument]
        return {
            "samples": [
                {
                    "time": "2024-01-01T00:00:00+00:00",
                    "hs": 1.4,
                    "tp": 6.8,
                    "dp": 110,
                    "wind_speed": 14,
                    "wind_dir": 70,
                }
            ]
        }

    monkeypatch.setattr("wv.providers.copernicus.request_json", fake_request)
    points = list(provider.fetch_forecast(24.4, 54.7, 6))
    assert points[0].dp == 110
