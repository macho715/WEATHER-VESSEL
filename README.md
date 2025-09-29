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
| `WV_STORMGLASS_API_KEY` | Stormglass API key |
| `WV_OPEN_METEO_ENDPOINT` | Optional custom Open-Meteo base URL |
| `WV_NOAA_WW3_ENDPOINT` | Optional NOAA WaveWatch III JSON endpoint |
| `WV_COPERNICUS_ENDPOINT` / `WV_COPERNICUS_TOKEN` | Optional Copernicus API configuration |
| `WV_SMTP_*` | SMTP host/port/credentials for email |
| `WV_EMAIL_RECIPIENTS` | Comma separated default recipients |
| `WV_SLACK_WEBHOOK` | Slack webhook URL (optional) |
| `WV_TELEGRAM_TOKEN` / `WV_TELEGRAM_CHAT_ID` | Telegram bot configuration |
| `WV_OUTPUT_DIR` | Directory for generated CSV/ICS (default `outputs/`) |

Risk thresholds can be tuned via `WV_MEDIUM_WAVE_THRESHOLD`, `WV_HIGH_WAVE_THRESHOLD`, `WV_MEDIUM_WIND_THRESHOLD`, and `WV_HIGH_WIND_THRESHOLD`.

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
