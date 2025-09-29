# TDD Plan (RED → GREEN → REFACTOR)

## Loop 1: Core Domain & Risk Rules
- **Red**: Write tests for `ForecastPoint` validation, caching utilities, and `compute_risk_level` boundaries (Hs, wind, missing swell).
- **Green**: Implement `LogiBaseModel`, domain models, risk computation with env overrides, numeric formatting helper.
- **Refactor**: Extract configuration module and ensure structured logging setup.

## Loop 2: Provider Adapters & Cache Fallback
- **Red**: Add adapter tests covering success, HTTP 429 retry/fallback, timeout with cache usage.
- **Green**: Implement Stormglass, Open-Meteo Marine, NOAA WW3 adapters with retry/backoff, disk cache, environment-driven config.
- **Refactor**: Generalize provider registry and response normalization utilities.

## Loop 3: Scheduler & Weekly Suggestions
- **Red**: Create tests for `generate_weekly_schedule` output, CSV/ICS creation, timezone correctness.
- **Green**: Implement scheduler module generating STDOUT table, CSV, ICS; integrate with risk notes.
- **Refactor**: Optimize schedule formatting and share table rendering utilities.

## Loop 4: Notifications & CLI Commands
- **Red**: Write tests for notification dispatch (email/slack/telegram dry-run) and CLI commands (`check --now`, `schedule --week`, `notify --dry-run`).
- **Green**: Implement notification channel classes, CLI using Typer, configuration loading, fallback sequencing.
- **Refactor**: Improve logging context, ensure CLI shares service layer, polish message templates.

## Loop 5: Integration & Cron Scheduler
- **Red**: Add integration test verifying twice-daily trigger scheduling logic referencing Asia/Dubai timezone and fallback provider order.
- **Green**: Implement scheduler service for auto checks, ensure timezone aware scheduling, update README/CHANGELOG/.env.example.
- **Refactor**: Final tidy pass, ensure metrics hooks and configuration defaults extracted.
