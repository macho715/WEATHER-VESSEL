# Plan

## RED
- Write failing tests for risk assessment thresholds and provider fallback caching behavior. ✅
- Write CLI snapshot tests covering `wv check --now`, `wv schedule --week`, and dry-run notify output. ✅

## GREEN
- Implement domain models, risk computation, provider adapters with cache/fallback, and CLI logic to satisfy tests. ✅

## REFACTOR
- Clean up shared utilities, ensure structured logging, and optimize notification output formatting without altering behavior. ✅
