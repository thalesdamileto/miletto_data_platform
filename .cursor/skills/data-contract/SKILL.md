---
name: data-contract
description: Author and extend data_contract/data_contracts.json (raw, bronze, silver sub_contracts) and keep it aligned with Databricks pipelines_metadata. Use when defining new domains, schedules, paths, or column mappings at contract level.
---

# Data Contract Skill

## When to Activate

Use this skill when:

- Adding or editing **[data_contract/data_contracts.json](data_contract/data_contracts.json)**
- Explaining what each **sub_contract** (raw, bronze, silver) must contain
- Ensuring the contract stays consistent with **RAW / bronze / silver** metadata under `databricks/ingestion-pipelines/pipelines_metadata/`

For JSON under `pipelines_metadata/` only, use the **databricks-pipelines** skill.

## Read First

- [data_contract/instructions/.cursorrules](data_contract/instructions/.cursorrules) — canonical structure, checklist, glossary
- [databricks/instructions/AGENT_INSTRUCTIONS.md](databricks/instructions/AGENT_INSTRUCTIONS.md) — RAW mandatory fields and `raw_data_pipes.json` behavior

## Purpose

`data_contract/data_contracts.json` is the **domain source of truth** for one or more data products: who produces the data, how each layer (raw, bronze, silver) is configured, and who consumes it at each layer. Changes here should be reflected in pipeline metadata (and vice versa) so deployments match the agreed contract.

## File shape and loading behavior

- **Instructions** describe a top-level **`contract_list`** array for multiple contracts. The **current repo** may use a **single contract object** at the root instead.
- [raw_pipeline_creator.py](databricks/ingestion-pipelines/pipelines_notebooks_templates/raw/raw_pipeline_creator.py) loads contracts with `_as_contract_list()`: it accepts a **JSON array of objects** or a **single JSON object**. For **multiple** domains, prefer a **JSON array** of contract objects at the root (consistent with how the creator iterates contracts).
- Whichever shape you use, **preserve existing key names and nesting** exactly; append new contracts without deleting unrelated entries.

## Per-layer structure (must preserve nesting)

Each contract object should include:

- `_id` — stable identifier (used in RAW job naming)
- `data_producer` — email; used for failure notifications in RAW job generation
- `sub_contracts` — object with optional `raw`, `bronze`, `silver` sections

### `sub_contracts.raw`

| Area | Keys |
|------|------|
| parameters | `schedule.databricks_quartz_cron`, `file_name`, `target_path` |
| data_consumers | array of `{ consumer, purpose, priority }` |

**Mandatory for RAW orchestration** (validated in code):

- `_id`
- `data_producer`
- `sub_contracts.raw.parameters.schedule.databricks_quartz_cron`
- `sub_contracts.raw.parameters.file_name`
- `sub_contracts.raw.parameters.target_path`

**`file_name`:** must match `^[a-zA-Z0-9_]+\.py$`; file must exist under `databricks/ingestion-pipelines/pipelines_notebooks_templates/raw/`.

### `sub_contracts.bronze`

| Area | Keys |
|------|------|
| parameters | `source_path`, `target_schema`, `target_table`, `description` |
| data_consumers | array of `{ consumer, purpose, priority }` |

Align `source_path` with RAW `target_path` (typically the same Volume folder), and `target_schema` / `target_table` with bronze pipeline metadata.

### `sub_contracts.silver`

| Area | Keys |
|------|------|
| parameters | `source` (`catalog`, `schema`, `table`), `destination` (`catalog`, `schema`, `table`), `pk_columns`, `watermark_column`, `ordering_column`, `column_mapping`, `schedule.databricks_quartz_cron`, `quality_procedures` |
| data_consumers | array of `{ consumer, purpose, priority }` |

**`column_mapping` entries** (align with team conventions and silver runtime):

- Required: `source_column`, `destination_column`, `nullable`, `type`
- Optional: documented in `.cursorrules` as `force_cast`; **silver notebook** [silver_pipeline.py](databricks/ingestion-pipelines/pipelines_notebooks_templates/silver/silver_pipeline.py) reads **`cast`** (default `true`). When defining behavior that must skip casting, use **`cast`: false** in [pipelines_metadata/silver/contracts.json](databricks/ingestion-pipelines/pipelines_metadata/silver/contracts.json) `contract_list` entries; keep domain JSON consistent with whatever the silver metadata actually uses.

Types for `column_mapping` must match `TYPE_MAPPING` in [general_helpers.py](databricks/ingestion-pipelines/pipelines_notebooks_templates/helpers/general_helpers.py).

## Relationship to `pipelines_metadata`

| Contract section | Typically aligns with |
|------------------|----------------------|
| `raw` | `pipelines_metadata/raw/raw_data_pipes.json` (via `raw_pipeline_creator`) |
| `bronze` | `pipelines_metadata/bronze/databricks_volume/json/dlt_volume_to_json_*.json` |
| `silver` | `pipelines_metadata/silver/contracts.json` (`contract_list`) and `job_bronze_to_silver.json` |

Silver **runtime** reads **`contracts.json`**, not `data_contracts.json`. After editing the data contract, ensure **`contract_list`** and jobs match `sub_contracts.silver.parameters` (source, destination, keys, watermark, mapping, quality).

## Checklist when changing a contract

| Step | Action |
|------|--------|
| 1 | Update `data_contract/data_contracts.json`; preserve schema and naming; append or surgically edit one contract. |
| 2 | Verify `raw.file_name` exists under `databricks/ingestion-pipelines/pipelines_notebooks_templates/raw/`. |
| 3 | Verify bronze `source_path`, `target_schema`, `target_table` match bronze metadata. |
| 4 | Verify silver `source` / `destination`, `pk_columns`, `watermark_column`, `ordering_column`, `column_mapping`, `quality_procedures`, and schedule match `contracts.json` and any silver job. |
| 5 | Regenerate or update RAW job metadata if RAW parameters changed. |

## Design rules

1. **Append** new contracts; avoid replacing unrelated entries.
2. Keep **`data_consumers`** under each sub_contract (`raw`, `bronze`, `silver`), not only at root.
3. Use **`databricks_quartz_cron`** for schedule fields.
4. Keep value types consistent (string, boolean, array, object) with existing examples.

## Glossary

| Term | Meaning |
|------|---------|
| **Data contract** | Agreed structure and processing for one data domain across layers. |
| **data_producer** | Owner/contact for upstream data and RAW failure alerts. |
| **data_consumers** | Downstream parties per layer with `purpose` and `priority`. |
| **sub_contracts** | Layer-specific parameters and consumers. |
