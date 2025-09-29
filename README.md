# Weather Vessel - Logistics Control Tower v2.5

A comprehensive maritime logistics control system delivering a browser-based control tower, marine weather intelligence, and a structured CLI for automated risk surveillance.

## Features

### 🗺️ Control Tower UI
- Interactive Leaflet map with live vessel route visualization and ETA projections
- CSV/JSON voyage schedule ingestion with weather-linked adjustments
- AI assistant for daily briefing, document analysis, and rapid risk mitigation guidance
- ADNOC weather screenshot parsing with automated hazard tagging
- Accessibility aligned with WCAG 2.2 AA (keyboard navigation, high contrast, ARIA labelling)

### 🌊 Command Line Intelligence
- Multi-provider marine forecast aggregation with disk cache and provider fallback
- Twice-daily risk assessments tuned to Asia/Dubai timezone thresholds
- Automated notifications via Email (default) with Slack/Telegram opt-ins
- Rolling 7-day voyage schedule recommendations exported to CSV and ICS
- Structured logging, configurable thresholds, and deterministic two-decimal metric formatting

## Installation

```bash
git clone https://github.com/macho715/WEATHER-VESSEL.git
cd WEATHER-VESSEL
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .[dev]
```

## Configuration

All configuration values can be supplied through environment variables or a `.env` file. Copy `.env.example` to `.env` and populate as needed:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose |
| --- | --- |
| `STORMGLASS_API_KEY` | Stormglass marine API key |
| `COPERNICUS_API_KEY` | Copernicus Marine API key |
| `WV_EMAIL_FROM`, `WV_EMAIL_TO` | Email sender and comma-separated recipients |
| `WV_SMTP_HOST`, `WV_SMTP_PORT`, `WV_SMTP_USERNAME`, `WV_SMTP_PASSWORD` | SMTP credentials (STARTTLS) |
| `WV_SLACK_WEBHOOK` | Optional Slack incoming webhook URL |
| `WV_TELEGRAM_TOKEN`, `WV_TELEGRAM_CHAT_ID` | Optional Telegram bot credentials |
| `WV_CACHE_DIR` | Disk cache directory (default `~/.wv/cache`) |
| `WV_OUTPUT_DIR` | Output artifact directory (default `outputs/`) |
| `WV_MEDIUM_HS`, `WV_HIGH_HS`, `WV_MEDIUM_WIND`, `WV_HIGH_WIND` | Override default risk thresholds |

## CLI Usage

All commands are exposed through the Typer application `wv`.

### Immediate Risk Check
```bash
wv check --now --lat 24.40 --lon 54.70 --hours 48
```
Outputs the highest Hs / wind readings (two decimals) and rule-based reasons. Use `--route MW4-AGI` to query the predefined route waypoints instead of raw coordinates.

### Weekly Schedule Suggestion
```bash
wv schedule --week --route MW4-AGI --vessel DUNE_SAND \
  --vessel-speed 12.5 --route-distance 180 --cargo-hs-limit 2.2
```
Produces a seven-day table in the terminal, and writes `schedule_week.csv` plus `schedule_week.ics` inside `WV_OUTPUT_DIR`.

### Notification Dispatch
```bash
wv notify --route MW4-AGI --dry-run
wv notify --route MW4-AGI  # sends via configured Email/Slack/Telegram
```
When all providers fail or rate-limit, the CLI transparently falls back to cached data (<=3 hours old).

## Scheduling Automation

### Linux/macOS (cron)
```
0 6,17 * * * /usr/local/bin/wv notify --route MW4-AGI >> /var/log/wv.log 2>&1
```

### Windows Task Scheduler
```
schtasks /Create /SC DAILY /MO 1 /TN "WV_0600" /TR "wv notify --route MW4-AGI" /ST 06:00
schtasks /Create /SC DAILY /MO 1 /TN "WV_1700" /TR "wv notify --route MW4-AGI" /ST 17:00
```

## Testing & Quality Gates

```bash
pytest -q
coverage run -m pytest
black --check .
isort --check-only .
flake8 .
mypy --strict src
```

Coverage is enforced at ≥70%, and numeric outputs are consistently formatted to two decimals.

## Legacy UI Gateway

To continue using the existing FastAPI gateway + HTML control tower:

```bash
python -m uvicorn openai_gateway:app --host 0.0.0.0 --port 8000 --reload
# Open logistics_control_tower_v2.html in a browser
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the testing & quality gates above
4. Submit a pull request with detailed context

## License

This project is licensed under the MIT License - see the LICENSE file for details.
