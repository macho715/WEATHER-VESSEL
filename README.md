# Weather Vessel CLI

Weather Vessel delivers marine weather intelligence, risk scoring, and voyage scheduling for logistics control towers. The CLI aggregates multiple providers (Stormglass, Open-Meteo Marine, NOAA WaveWatch III, Copernicus) with automatic fallback, disk caching, and timezone-safe scheduling in **Asia/Dubai**.

## Key Features

- 🌊 **Multi-provider marine data** with retries, quota-aware backoff, and cache fallback (≤3 h)
- 🧭 **Risk assessment** from significant wave height, wind speed/direction, and swell parameters
- 📅 **7-day voyage schedule** with CSV and ICS exports and fixed 2-decimal metrics
- 📣 **Notifications** via Email (default), Slack, and Telegram with dry-run support
- ⏱️ **Twice-daily checks** aligned to 06:00 / 17:00 Asia/Dubai for automated alerts

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[all]
cp .env.example .env
```

Set the relevant API keys and notification endpoints in `.env`. Never commit real credentials.

### Required Environment Variables

| Variable | Description |
| --- | --- |
| `STORMGLASS_API_KEY` | Stormglass connector API key (used by `marine_ops` package) |
| `WORLDTIDES_API_KEY` | WorldTides connector API key |
| `OPEN_METEO_BASE` | Optional override for Open-Meteo Marine endpoint |
| `OPEN_METEO_TIMEOUT` | Request timeout (seconds) for Open-Meteo fallback |
| `APP_LOG_LEVEL` | Log verbosity (default `INFO`) |
| `TZ` | Application timezone (set to `UTC`) |
| `WV_STORMGLASS_API_KEY` | Legacy Stormglass key for CLI provider manager |
| `WV_OPEN_METEO_ENDPOINT` | Optional custom Open-Meteo base URL |
| `WV_NOAA_WW3_ENDPOINT` | Optional NOAA WaveWatch III JSON endpoint |
| `WV_COPERNICUS_ENDPOINT` / `WV_COPERNICUS_TOKEN` | Optional Copernicus API configuration |
| `WV_SMTP_*` | SMTP host/port/credentials for email |
| `WV_EMAIL_RECIPIENTS` | Comma separated default recipients |
| `WV_SLACK_WEBHOOK` | Slack webhook URL (optional) |
| `WV_TELEGRAM_TOKEN` / `WV_TELEGRAM_CHAT_ID` | Telegram bot configuration |
| `WV_OUTPUT_DIR` | Directory for generated CSV/ICS (default `outputs/`) |

Risk thresholds can be tuned via `WV_MEDIUM_WAVE_THRESHOLD`, `WV_HIGH_WAVE_THRESHOLD`, `WV_MEDIUM_WIND_THRESHOLD`, and `WV_HIGH_WIND_THRESHOLD`.

### Marine Operations Toolkit (`marine_ops`)

The new `marine_ops` package provides a reusable toolkit for hybrid AGI/DAS workflows:

- **Connectors**: Stormglass, WorldTides, and Open-Meteo fallback clients that normalize responses into a common schema with ISO 8601 UTC timestamps and per-variable unit metadata.
- **Core utilities**: Unit conversions, quality control (physical bounds + IQR clipping), μ/σ bias correction, and weighted ensemble blending with 2-decimal precision.
- **ERI v0**: Externalized YAML rules converted into a 0–100 Environmental Readiness Index (ERI) score with quality badges highlighting data gaps and bias adjustments.
- **Settings + Fallback**: `MarineOpsSettings` bootstraps connectors from environment variables while `fetch_forecast_with_fallback` routes around Stormglass rate limits/timeouts using Open-Meteo Marine.

```python
import datetime as dt

from marine_ops.connectors import OpenMeteoFallback, StormglassConnector, fetch_forecast_with_fallback
from marine_ops.core import MarineOpsSettings
from marine_ops.eri import compute_eri_timeseries, load_rule_set

settings = MarineOpsSettings.from_env()
stormglass = settings.build_stormglass_connector()
fallback = settings.build_open_meteo_fallback()
start = dt.datetime.now(tz=dt.timezone.utc)
end = start + dt.timedelta(days=3)
series = fetch_forecast_with_fallback(25.0, 55.0, start, end, stormglass, fallback)
rules = load_rule_set("tests/marine_ops/fixtures/eri_rules.yaml")
eri_points = compute_eri_timeseries(series, rules)
```

### ADNOC × Al Bahar voyage fusion

- Harmonise **Combined(seas)**, onshore/offshore significant wave height, and wind guidance into a single decision.
- Apply calibrated shrinkage (`α=0.85`, `β=0.80`) and alert weighting (`γ=0.15` for *rough at times*, `γ=0.30` for **High seas**).
- Produce **Go / Conditional / No-Go** plus ETA and buffer minutes with a minimal speed-loss model (`f_wind`, `f_wave`).

```python
from wv.core.fusion import FusionInputs, decide_and_eta

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

decision = decide_and_eta(inputs)
print(decision.model_dump())
# {'hs_fused_m': 1.43, 'wind_fused_kt': 20.0, 'decision': 'Conditional Go (coastal window)',
#  'eta_hours': 3.32, 'buffer_minutes': 45}
```

### Sample CSVs & Health Check

- Generate RFC 4180 compliant samples: `python scripts/generate_sample_csv.py --output .`
- Smoke test running services on ports **3000–3005**: `powershell .\scripts\health_check.ps1`
- Sample outputs live at `sample_timeseries.csv` and `sample_jobs.csv`, ready for downstream ingestion tests.

## Usage

All commands honor `.env` configuration and display values rounded to two decimal places.

### Immediate risk snapshot

```bash
wv check --now --route MW4-AGI
wv check --now --lat 24.40 --lon 54.70 --hours 72
```

### Weekly schedule generation

```bash
wv schedule --week --route MW4-AGI --vessel DUNE_SAND --vessel-speed 12 --route-distance 120 --cargo-hs-limit 2.5
```

Outputs:

- Table printed to STDOUT (Asia/Dubai timestamps)
- `outputs/schedule_week.csv`
- `outputs/schedule_week.ics`

Override the export path with `WV_OUTPUT_DIR`.

### Notifications

```bash
# Dry run with Slack + Telegram
wv notify --route MW4-AGI --dry-run --slack --telegram

# Email to explicit recipients
wv notify --route MW4-AGI --email-to ops@example.com --email-to master@vessel.local
```

When no `--email-to` is provided, the CLI uses `WV_EMAIL_RECIPIENTS`.

## Automation

Schedule the twice-daily checks at **06:00** and **17:00 Asia/Dubai**.

### Linux/macOS (cron)

```
0 6,17 * * * /usr/local/bin/wv notify --route MW4-AGI >> /var/log/wv.log 2>&1
```

### Windows Task Scheduler

```
schtasks /Create /SC DAILY /MO 1 /TN "WV_0600" /TR "wv notify --route MW4-AGI" /ST 06:00
schtasks /Create /SC DAILY /MO 1 /TN "WV_1700" /TR "wv notify --route MW4-AGI" /ST 17:00
```

## Development

```bash
pip install -e .[all]
pytest -q --cov=src
black --check .
isort --check-only .
flake8 .
mypy --strict src
```

The `tests/marine_ops` suite exercises connector normalization, unit conversion, QC/bias/ensemble pipelines, and end-to-end ERI scoring from the sample CSV fixtures (coverage ≥ 70%).

### Running Smoke Tests

```bash
wv check --now --lat 24.40 --lon 54.70
wv schedule --week --route MW4-AGI --vessel DUNE_SAND
wv notify --dry-run --route MW4-AGI
```

## Caching Strategy

Forecast results are cached on disk at `~/.wv/cache/` with a 3-hour TTL. Provider outages (timeouts, HTTP 429, 5xx) cause the manager to fall back to the next provider or last known cache hit.

## License

MIT License. See `LICENSE` for details.
