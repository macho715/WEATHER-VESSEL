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
