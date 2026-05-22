# Decisions

## Standalone Governance Boundary

The console is the producer and manager of structured knowledge. Downstream Agent systems are consumers only.

The console must not import Agent modules, call Agent runtime code, or write into Agent-owned storage. Integration happens through stable local artifacts exported from the console.

## Local SQLite Storage

Knowledge units, Badcase records, changelog entries, and reference logs are stored in `data/knowledge_base.db` by default. The data directory and database name are configurable through `config.yaml`.

SQLite keeps the tool simple to run on a local Windows workstation while avoiding fragile JSON rewrites as records grow.

## YAML Synchronization

Active, non-expired knowledge units are exported as one YAML file per knowledge unit under `sync/`. The YAML format is intentionally configuration-like so Agent-side indexing scripts can scan the folder and ingest the files without the console knowing how vector indexing is implemented.

Deprecated knowledge removes its corresponding sync file. Knowledge registration and correction refresh the sync file automatically.

## Windows Launcher

`KnowledgeGovernanceConsole.exe` and `start_knowledge_console.bat` are convenience launchers for local use. They start Streamlit from the project runtime, pick an available port based on `config.yaml`, and keep launcher diagnostics in `launcher.log`.
