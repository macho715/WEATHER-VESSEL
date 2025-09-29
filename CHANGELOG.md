# Changelog

## [Unreleased]

### Added
- feat(cli): introduce `wv check`, `wv schedule --week`, and `wv notify` commands with Asia/Dubai alignment
- feat(providers): integrate Stormglass, Open-Meteo Marine, NOAA WaveWatch III, Copernicus, and deterministic sample fallback with disk cache
- feat(scheduler): generate 7-day ETD/ETA slots, CSV/ICS exports, and risk annotations with cargo limit escalation
- feat(notify): deliver templated alerts via Email, Slack, and Telegram with dry-run mode and environment-based recipients
- feat(docs): document cron/Task Scheduler automation, `.env` configuration, and developer workflow

### Changed
- refactor(core): centralize domain models with Pydantic `LogiBaseModel` and bilingual docstrings
- refactor(cli): adopt Typer-based modular layout with dependency injection hooks for testing
- refactor(config): move packaging to `pyproject.toml` with `[project.optional-dependencies].all`

### Fixed
- fix(cache): ensure last-known forecast (≤3 h) is returned when providers fail or rate-limit
- fix(risk): enforce 2-decimal rounding and environment-driven thresholds across CLI outputs
