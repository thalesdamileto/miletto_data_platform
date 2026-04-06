# Agent context index (Miletto Data Platform)

This monorepo uses **one independent application per top-level directory**. Each app keeps agent context in **`{app}/instructions/.cursorrules`** (purpose, patterns, golden examples, domain glossary).

## Important: Cursor and nested `.cursorrules`

Cursor loads workspace rules from **`.cursor/rules/`** automatically. **Paths like `databricks/instructions/.cursorrules` are not auto-injected.** Before editing an app, **read that app’s `instructions/.cursorrules`** (attach in chat with `@`, or open it explicitly).

## Read order (before making changes)

1. This file (`AGENTS.md`) and [`.cursor/rules/`](.cursor/rules/).
2. **Contracts-first workflow:** [contracts/instructions/.cursorrules](contracts/instructions/.cursorrules) → then [kafka/instructions/.cursorrules](kafka/instructions/.cursorrules) and/or [databricks/instructions/.cursorrules](databricks/instructions/.cursorrules) as the change requires.
3. **Databricks-only:** [databricks/instructions/.cursorrules](databricks/instructions/.cursorrules) (must follow [databricks/instructions/AGENT_INSTRUCTIONS.md](databricks/instructions/AGENT_INSTRUCTIONS.md)).
4. **Kafka-only:** [kafka/instructions/.cursorrules](kafka/instructions/.cursorrules).
5. **UI-only:** [UI/instructions/.cursorrules](UI/instructions/.cursorrules) (Streamlit shell under `UI/app/`).

## Application map

| Directory    | Role |
|-------------|------|
| `contracts/` | Data contracts as the trigger for cross-cutting changes (Kafka topics, Databricks metadata). |
| `kafka/`     | Declarative Kafka topic provisioning (`topics.yaml`). |
| `databricks/`| Databricks ingestion pipelines driven by JSON metadata and notebooks. |
| `UI/`        | Streamlit UI for platform navigation (`UI/app/app.py`). Run: `streamlit run UI/app/app.py` (requires `pip install -e ".[ui]"`). |

## Automation pattern

1. Load `AGENTS.md`.
2. Resolve scope (`contracts` / `kafka` / `databricks` / `UI`) and read the matching `instructions/.cursorrules`.
3. Apply edits only to paths allowed by that app’s rules.
4. Run checks from [pyproject.toml](pyproject.toml) (`ruff`, `pytest`; `mypy` when typed packages exist).
