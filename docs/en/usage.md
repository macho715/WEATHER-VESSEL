# Weather Vessel Usage Guide

- Install dependencies with `pip install -e .[all]`.
- Configure providers and notifications via `.env` (see `.env.example`).
- Run `wv check --now --route MW4-AGI` for instant risk scoring.
- Run `wv schedule --week --route MW4-AGI` to emit STDOUT table, CSV, and ICS artefacts.
- Trigger alerts with `wv notify --route MW4-AGI --dry-run --slack --telegram`.
- Automate at 06:00 / 17:00 Asia/Dubai using cron or Windows Task Scheduler examples from the README.
