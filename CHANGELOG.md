# Changelog

## [Unreleased]
### Added
- Enable AI weather insight panel with screenshot uploads analysed through the OpenAI gateway.
- Support clipboard paste and drag-and-drop ingestion for ADNOC weather screenshots so control tower operators can analyse live captures without saving files manually.
- Provide in-app API gateway configuration with persistent storage to target custom OpenAI deployment ports.

### Fixed
- Handle missing `OPENAI_API_KEY` gracefully by loading `.env` configuration and surfacing
  configuration errors directly from the OpenAI gateway endpoints.
- Surface detailed OpenAI gateway errors in the UI when assistant or briefing calls fail instead of returning opaque 502 messages.

## [0.2.0] - 2024-10-07
### Added
- Introduced the `wv` CLI with immediate risk checks, weekly schedule suggestions, and notification dispatch flows.
- Implemented modular marine forecast adapters (Stormglass, Open-Meteo Marine, NOAA WW3, Copernicus) with disk caching and fallback handling.
- Added structured risk assessment domain models, weekly scheduler, and notification senders for email/Slack/Telegram.

### Changed
- Documented environment-driven configuration, automation examples, and quality gates in the README.
- Adopted Pydantic-based logistics models (`LogiBaseModel`) with strict typing across the new Python package.

### Fixed
- Ensured provider cache serialization uses JSON-safe payloads and added guardrails for malformed API responses.
