# Weather Vessel CLI

## Overview
The `wv` command-line interface augments the Logistics Control Tower with automated marine weather checks, weekly scheduling intelligence, and multi-channel notifications.

## Commands

### `wv check --now`
Evaluates the highest significant wave height (Hs) and wind speed across the requested point or predefined route.

```
wv check --now --lat 24.40 --lon 54.70 --hours 48
wv check --now --route MW4-AGI
```

### `wv schedule --week`
Builds a rolling seven-day voyage proposal, prints a table to STDOUT, and writes both CSV/ICS artefacts into `WV_OUTPUT_DIR`.

```
wv schedule --week --route MW4-AGI --vessel DUNE_SAND \
  --vessel-speed 12.5 --route-distance 180 --cargo-hs-limit 2.2
```

### `wv notify`
Generates a risk summary for the specified route and pushes notifications. Use `--dry-run` to preview without sending.

```
wv notify --route MW4-AGI --dry-run
wv notify --route MW4-AGI
```

## Providers & Cache
- Primary adapters: Stormglass, Open-Meteo Marine, NOAA WaveWatch III, Copernicus Marine
- Cache location: `WV_CACHE_DIR` (default `~/.wv/cache`), TTL 30 minutes with 3-hour stale fallback
- All API keys are read from environment variables (`.env` supported)

## Automation
- Cron: `0 6,17 * * * /usr/local/bin/wv notify --route MW4-AGI`
- Windows Task Scheduler: `schtasks /Create /SC DAILY /TN "WV_0600" /TR "wv notify --route MW4-AGI" /ST 06:00`

## Quality Gates
Run the following before opening a pull request:
```
pytest -q
coverage run -m pytest
black --check .
isort --check-only .
flake8 .
mypy --strict src
```
