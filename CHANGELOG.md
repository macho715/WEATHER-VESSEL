# Changelog

## [Unreleased]
### Added
- Introduced `wv` Typer CLI with `check`, `schedule`, and `notify` workflows backed by Stormglass, Open-Meteo Marine, and NOAA WaveWatch III providers.
- Implemented disk-backed cache (`~/.wv/cache`) with three-hour TTL and provider fallback/resilience logic.
- Added weekly voyage planner that prints ASCII tables and exports CSV + ICS schedules with risk notes.
- Delivered email, Slack, and Telegram notification adapters plus twice-daily Asia/Dubai auto-check scheduler.
- Published `.env.example`, `plan.md`, and comprehensive pytest coverage for providers, risk rules, scheduler, notifications, and CLI.

### Changed
- Replaced legacy FastAPI usage docs with CLI-centric README guidance, including cron and Task Scheduler recipes.
- Centralized configuration via `pyproject.toml` with strict tooling defaults (`black`, `isort`, `flake8`, `mypy`).
- Normalized numeric outputs to two decimal places and ensured bilingual docstrings across new modules.

### Fixed
- Resolved timezone drift by hard-coding Asia/Dubai context inside scheduling and notification flows.
- Ensured provider outages (HTTP 429/timeout) automatically cascade to fallbacks or serve cached responses.
