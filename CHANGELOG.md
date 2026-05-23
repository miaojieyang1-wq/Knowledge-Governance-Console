# Changelog

## 2026-05-19

- Replaced JSON persistence with local SQLite storage in `data/knowledge_base.db`.
- Added YAML synchronization exports under `sync/` for Agent-side indexing.
- Added dashboard alerts, reference trace display, and inline Badcase correction flow.
- Removed obsolete in-app helper code left from the earlier JSON implementation.

## 2026-05-22

- Added repeatable `selfcheck.py` and `run_selfcheck.bat` smoke checks.
- Hardened SQLite schema initialization for older local database files.
- Improved query filtering and Badcase status list compatibility.
- Split dense Streamlit page handlers into smaller rendering helpers for safer UI iteration.
- Added `docs/decisions.md` to document the console, SQLite, YAML sync, and Windows launcher boundaries.
- Made the Windows launcher startup wait timeout configurable through `config.yaml`.
- Cleaned same-ID legacy Markdown sync files when exporting or removing YAML sync files.
- Preserved the quick trust-rating correction behavior so it logs the change without bumping the knowledge version.
- Added safe integer config parsing so invalid dashboard thresholds fall back gracefully.
- Moved Streamlit styling into `static/knowledge_console.css` to keep the app entrypoint easier to maintain.
- Added Git line-ending rules for CSS assets.
- Added a Git line-ending rule for `.gitattributes` itself.
- Aligned `start_knowledge_console.bat` with the Python launcher so bat and exe startup share config and port fallback behavior.
- Normalized batch scripts to LF in Git attributes to match the project encoding rules.
- Added environment-variable overrides for runtime configuration while preserving `config.yaml` defaults.
- Added a Git line-ending rule for `.env.example`.
