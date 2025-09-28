# Changelog

## [Unreleased]
### Added
- Auto-detect headerless voyage CSV exports so MW4 schedule dumps upload without manual editing.
- Enable AI weather insight panel with screenshot uploads analysed through the OpenAI gateway.
- Support clipboard paste and drag-and-drop ingestion for ADNOC weather screenshots so control tower operators can analyse live captures without saving files manually.
- Provide in-app API gateway configuration with persistent storage to target custom OpenAI deployment ports.
- Mirror clipboard attachments in a persistent inline tray so pasted captures stay visible outside the assistant modal.
- Separate sail vs discharge weather limits with inline readiness badges and voyage mini-Gantt bars.
- Add MW4 waiting strategy toggle so vessels hold departure until both sail and discharge windows are safe.
- Cover gateway workflows with automated pytest suite to ensure OpenAI connectivity remains green.

### Fixed
- Handle missing `OPENAI_API_KEY` gracefully by loading `.env` configuration and surfacing
  configuration errors directly from the OpenAI gateway endpoints.
- Surface detailed OpenAI gateway errors in the UI when assistant or briefing calls fail instead of returning opaque 502 messages.
- Align OpenAI Responses payloads with `input_text` / `output_text` blocks to eliminate invalid value errors during assistant calls.
