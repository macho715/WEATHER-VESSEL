# Changelog

## [Unreleased]
### Added
- Enable AI weather insight panel with screenshot uploads analysed through the OpenAI gateway.

### Fixed
- Handle missing `OPENAI_API_KEY` gracefully by loading `.env` configuration and surfacing
  configuration errors directly from the OpenAI gateway endpoints.
