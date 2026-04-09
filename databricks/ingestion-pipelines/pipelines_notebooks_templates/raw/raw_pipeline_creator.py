# Databricks notebook source
# DBTITLE 1,Imports
import json
import re
from pathlib import Path
from typing import Any

import requests


def _monorepo_root_from_notebook() -> str:
    """Raiz do repo no workspace (/Workspace/Repos/.../miletto_data_platform).

    Diferente de silver_pipeline.py: lá o 'repo_root' aponta para
    .../databricks/ingestion-pipelines (onde fica pipelines_notebooks_templates).
    Aqui precisamos da raiz do monorepo para achar data_contract/ na raiz.
    """
    nb_path = (
        dbutils.notebook.entry_point.getDbutils()
        .notebook()
        .getContext()
        .notebookPath()
        .get()
    )
    marker = "/databricks/ingestion-pipelines/pipelines_notebooks_templates"
    if marker not in nb_path:
        raise RuntimeError(
            "Não foi possível inferir a raiz do monorepo a partir do notebookPath. "
            f"Esperado trecho {marker!r} em {nb_path!r}. "
            "Preencha os widgets contracts_path e metadata_path com caminhos absolutos "
            "/Workspace/..."
        )
    prefix = nb_path.split(marker, maxsplit=1)[0]
    return f"/Workspace{prefix}"


def _resolve_workspace_path(user_path: str, monorepo_root: str) -> str:
    """Caminhos relativos são resolvidos a partir da raiz do monorepo no Repos."""
    path = user_path.strip()
    if not path:
        return path
    if path.startswith("/Workspace") or path.startswith("/Volumes"):
        return path
    if path.startswith("/Repos"):
        return path
    return str(Path(monorepo_root) / path)


def _default_notebook_base_path(monorepo_root: str) -> str:
    """Path usado em notebook_task (sem prefixo /Workspace), ex.: /Repos/.../raw."""
    root = monorepo_root.removeprefix("/Workspace")
    return (
        f"{root}/databricks/ingestion-pipelines/pipelines_notebooks_templates/raw"
    )


MONOREPO_ROOT = _monorepo_root_from_notebook()

dbutils.widgets.text("contracts_path", "data_contract/data_contracts.json")
dbutils.widgets.text(
    "metadata_path",
    "databricks/ingestion-pipelines/pipelines_metadata/raw/raw_data_pipes.json",
)
dbutils.widgets.text(
    "notebook_base_path",
    "",
)
dbutils.widgets.text("timezone_id", "America/Sao_Paulo")


DATABRICKS_HOST = dbutils.secrets.get("data-platform", "DATABRICKS_HOST").strip().rstrip("/")
DATABRICKS_TOKEN = dbutils.secrets.get("data-platform", "DATABRICKS_TOKEN").strip()

CONTRACTS_PATH = _resolve_workspace_path(
    dbutils.widgets.get("contracts_path"), MONOREPO_ROOT
)
METADATA_PATH = _resolve_workspace_path(
    dbutils.widgets.get("metadata_path"), MONOREPO_ROOT
)
_notebook_base_widget = dbutils.widgets.get("notebook_base_path").strip().rstrip("/")
NOTEBOOK_BASE_PATH = (
    _notebook_base_widget
    if _notebook_base_widget
    else _default_notebook_base_path(MONOREPO_ROOT)
)
TIMEZONE_ID = dbutils.widgets.get("timezone_id").strip() or "America/Sao_Paulo"

print(f"MONOREPO_ROOT (workspace): {MONOREPO_ROOT}")
print(f"contracts: {CONTRACTS_PATH}")
print(f"metadata: {METADATA_PATH}")
print(f"notebook_base_path (jobs): {NOTEBOOK_BASE_PATH}")

HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json",
}


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _dump_json(path: str, payload: Any) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False)


def _as_contract_list(raw_payload: Any) -> list[dict[str, Any]]:
    if isinstance(raw_payload, list):
        return [item for item in raw_payload if isinstance(item, dict)]
    if isinstance(raw_payload, dict):
        return [raw_payload]
    raise ValueError("Contrato inválido: esperado objeto JSON ou lista de objetos.")


def _notebook_stem(file_name: str) -> str:
    clean = file_name.strip()
    return clean[:-3] if clean.endswith(".py") else clean


def _validate_required_raw_fields(contract: dict[str, Any]) -> None:
    contract_id = contract.get("_id")
    producer = contract.get("data_producer")
    raw_sub = contract.get("sub_contracts", {}).get("raw", {})
    params = raw_sub.get("parameters", {})
    schedule = params.get("schedule", {}).get("databricks_quartz_cron")
    file_name = params.get("file_name")
    target_path = params.get("target_path")

    missing: list[str] = []
    if not contract_id:
        missing.append("_id")
    if not producer:
        missing.append("data_producer")
    if not schedule:
        missing.append("sub_contracts.raw.parameters.schedule.databricks_quartz_cron")
    if not file_name:
        missing.append("sub_contracts.raw.parameters.file_name")
    if not target_path:
        missing.append("sub_contracts.raw.parameters.target_path")

    if missing:
        raise ValueError(
            f"Contrato {_safe_str(contract_id)} sem campos obrigatórios RAW: {missing}"
        )


def _safe_str(value: Any) -> str:
    return str(value) if value is not None else "UNKNOWN"


def _normalize_target_path(path_value: str) -> str:
    return path_value if path_value.endswith("/") else f"{path_value}/"


def _build_raw_job_from_contract(contract: dict[str, Any]) -> dict[str, Any]:
    _validate_required_raw_fields(contract)

    contract_id = str(contract["_id"]).strip()
    producer_email = str(contract["data_producer"]).strip()
    raw_params = contract["sub_contracts"]["raw"]["parameters"]
    cron_expr = str(raw_params["schedule"]["databricks_quartz_cron"]).strip()
    file_name = str(raw_params["file_name"]).strip()
    target_path = _normalize_target_path(str(raw_params["target_path"]).strip())
    notebook_name = _notebook_stem(file_name)

    task_key = f"{notebook_name}_{contract_id}"
    return {
        "name": f"raw_job_{notebook_name}_{contract_id}",
        "email_notifications": {
            "on_failure": [producer_email],
            "no_alert_for_skipped_runs": False,
        },
        "webhook_notifications": {},
        "timeout_seconds": 0,
        "schedule": {
            "quartz_cron_expression": cron_expr,
            "timezone_id": TIMEZONE_ID,
            "pause_status": "UNPAUSED",
        },
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": task_key,
                "run_if": "ALL_SUCCESS",
                "notebook_task": {
                    "notebook_path": f"{NOTEBOOK_BASE_PATH}/{notebook_name}",
                    "base_parameters": {"target_path": target_path},
                    "source": "WORKSPACE",
                },
                "timeout_seconds": 0,
                "email_notifications": {},
                "webhook_notifications": {},
                "environment_key": "Default",
            }
        ],
        "queue": {"enabled": True},
        "environments": [
            {"environment_key": "Default", "spec": {"environment_version": "5"}}
        ],
        "performance_target": "PERFORMANCE_OPTIMIZED",
    }


def generate_raw_metadata_from_contracts(
    contracts_path: str, metadata_path: str
) -> list[dict[str, Any]]:
    raw_payload = _load_json(contracts_path)
    contracts = _as_contract_list(raw_payload)

    generated: list[dict[str, Any]] = []
    for contract in contracts:
        sub_contracts = contract.get("sub_contracts", {})
        if "raw" not in sub_contracts:
            continue
        generated.append(_build_raw_job_from_contract(contract))

    _dump_json(metadata_path, generated)
    print(f"{len(generated)} metadados RAW gravados em: {metadata_path}")
    return generated


def _list_existing_jobs() -> dict[str, int]:
    url = f"{DATABRICKS_HOST}/api/2.1/jobs/list"
    params: dict[str, Any] = {}
    mapping: dict[str, int] = {}

    while True:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        for job in payload.get("jobs", []):
            settings = job.get("settings", {})
            name = settings.get("name")
            job_id = job.get("job_id")
            if name and job_id is not None:
                mapping[str(name)] = int(job_id)

        next_token = payload.get("next_page_token")
        if not next_token:
            break
        params = {"page_token": next_token}

    return mapping


def _create_job(job_settings: dict[str, Any]) -> None:
    url = f"{DATABRICKS_HOST}/api/2.1/jobs/create"
    response = requests.post(url, headers=HEADERS, json=job_settings, timeout=30)
    response.raise_for_status()
    print(f"Job criado: {job_settings['name']}")


def _reset_job(job_id: int, job_settings: dict[str, Any]) -> None:
    url = f"{DATABRICKS_HOST}/api/2.1/jobs/reset"
    payload = {"job_id": job_id, "new_settings": job_settings}
    response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    print(f"Job atualizado: {job_settings['name']} ({job_id})")


def sync_jobs_from_metadata(metadata_path: str) -> None:
    if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
        raise ValueError(
            "Configure secrets DATABRICKS_HOST e DATABRICKS_TOKEN no scope (ex.: data-platform)."
        )

    raw_jobs = _load_json(metadata_path)
    if not isinstance(raw_jobs, list):
        raise ValueError("Metadado RAW inválido: esperado lista de jobs.")

    existing_jobs = _list_existing_jobs()
    for job_settings in raw_jobs:
        name = job_settings.get("name")
        if not name:
            raise ValueError("Cada job no metadado RAW precisa de 'name'.")

        current_id = existing_jobs.get(name)
        if current_id is None:
            _create_job(job_settings)
        else:
            _reset_job(current_id, job_settings)


def _validate_notebook_filename_pattern() -> None:
    contracts = _as_contract_list(_load_json(CONTRACTS_PATH))
    pattern = re.compile(r"^[a-zA-Z0-9_]+\.py$")

    for contract in contracts:
        raw_sub = contract.get("sub_contracts", {}).get("raw", {})
        params = raw_sub.get("parameters", {})
        file_name = params.get("file_name")
        if not file_name:
            continue
        if not pattern.match(str(file_name)):
            raise ValueError(
                "sub_contracts.raw.parameters.file_name inválido em "
                f"{_safe_str(contract.get('_id'))}: {file_name}"
            )


_validate_notebook_filename_pattern()
generate_raw_metadata_from_contracts(CONTRACTS_PATH, METADATA_PATH)
sync_jobs_from_metadata(METADATA_PATH)