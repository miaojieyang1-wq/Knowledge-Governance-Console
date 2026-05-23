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
