import csv
import json
import os
import re
import uuid
from pathlib import Path

from agno.agent import Agent
from agno.models.ollama import Ollama

# Configuracao de caminhos
REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "data_contract" / "samples"
CONTRACTS_FILE = REPO_ROOT / "data_contract" / "new_data_contracts.json"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Garantir que as pastas existam
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CONTRACTS_FILE), exist_ok=True)

# Definicao do Agente
contract_agent = Agent(
    name="Contract Architect",
    model=Ollama(id=OLLAMA_MODEL),
    description="Voce e um especialista em Data Contracts para plataformas Delta Lake.",
    instructions=[
        "1. Read data_contract/instructions/.cursorrules to understand the contract rules.",
        "2. Use apenas o contexto de CSV fornecido no prompt para inferencia.",
        "3. Identifique nomes de colunas, tipos de dados e possiveis dados sensiveis (PII).",
        "4. Gere um esquema de contrato em formato JSON.",
        "5. Responda apenas com um objeto JSON valido (sem markdown, sem texto extra, sem tool calls).",
    ],
    markdown=False,
)


def _extract_json_object(text):
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        try:
            obj, _ = decoder.raw_decode(cleaned[match.start() :])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("Nao foi encontrado JSON valido na resposta do agente.")


def _normalize_contract_payload(payload, bronze_requirements, data_producer):
    if isinstance(payload, dict) and payload.get("name") == "save_file":
        contents = payload.get("parameters", {}).get("contents", [])
        first = contents[0] if contents and isinstance(contents[0], dict) else {}
        bronze = {
            "parameters": first.get("parameters", bronze_requirements.get("parameters", {})),
            "data_consumers": first.get("data_consumers")
            or first.get("parameters", {}).get("data_consumers")
            or bronze_requirements.get("data_consumers", []),
        }
        return {
            "_id": uuid.uuid4().hex[:12],
            "data_producer": data_producer,
            "sub_contracts": {"bronze": bronze},
        }
    return payload


def _save_contract(contract):
    if os.path.exists(CONTRACTS_FILE):
        with open(CONTRACTS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
    else:
        existing = []

    existing.append(contract)
    with open(CONTRACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def _read_csv_context(file_path, sample_rows=5):
    rows = []
    encodings = ["utf-8", "latin-1"]
    last_error = None

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                for _, row in zip(range(sample_rows), reader):
                    rows.append(row)
                return headers, rows
        except UnicodeDecodeError as exc:
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise ValueError(f"Nao foi possivel ler CSV: {file_path}")


def generate_bronze_contract(filename, bronze_requirements, data_producer):
    csv_path = SAMPLES_DIR / filename
    headers, sample_data = _read_csv_context(csv_path, sample_rows=5)

    prompt = (
        "Considere a primeira linha do csv como headers. "
        f"Arquivo analisado: {csv_path.as_posix()}. "
        f"Headers: {json.dumps(headers, ensure_ascii=False)}. "
        f"Amostra de linhas: {json.dumps(sample_data, ensure_ascii=False)}. "
        "Crie um contrato no schema exato abaixo, com apenas sub_contracts.bronze:\n"
        "{"
        '"_id":"<12_hex>",'
        '"data_producer":"<email>",'
        '"sub_contracts":{"bronze":{"parameters":{"source_path":"<path>","target_schema":"dbo","target_table":"<table>","description":"<text>"},"data_consumers":[{"consumer":"<name>","purpose":"<purpose>","priority":"P1|P2|P3"}]}}'
        "}\n"
        f"Use data_producer='{data_producer}'. "
        f"Use estes campos obrigatorios de bronze como base: {json.dumps(bronze_requirements, ensure_ascii=False)}."
    )

    contract_agent.print_response(prompt)

    response = contract_agent.run(prompt)
    response_text = getattr(response, "content", str(response))
    payload = _extract_json_object(response_text)
    contract = _normalize_contract_payload(payload, bronze_requirements, data_producer)

    contract_id = contract.get("_id", "")
    if not isinstance(contract_id, str) or not re.fullmatch(r"[0-9a-f]{12}", contract_id):
        contract["_id"] = uuid.uuid4().hex[:12]
    contract.setdefault("data_producer", data_producer)
    contract.setdefault("sub_contracts", {})
    contract["sub_contracts"].setdefault("bronze", {})

    bronze = contract["sub_contracts"]["bronze"]
    bronze.setdefault("parameters", {})
    bronze.setdefault("data_consumers", [])

    default_params = bronze_requirements.get("parameters", {})
    bronze["parameters"] = {**default_params, **bronze.get("parameters", {})}
    if not bronze.get("data_consumers"):
        bronze["data_consumers"] = bronze_requirements.get("data_consumers", [])

    final_contract = {
        "_id": contract["_id"],
        "data_producer": contract["data_producer"],
        "sub_contracts": {
            "bronze": {
                "parameters": bronze["parameters"],
                "data_consumers": bronze["data_consumers"],
            }
        },
    }

    _save_contract(final_contract)
    print(json.dumps(final_contract, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    bronze_requirements = {
        "parameters": {
            "source_path": "data_contract/samples/vendas.csv",
            "target_schema": "dbo",
            "target_table": "vendas_bronze",
            "description": "Dados de vendas brutos para teste do agente de contrato",
        },
        "data_consumers": [
            {
                "consumer": "Thales Morais",
                "purpose": "Silver process",
                "priority": "P2",
            }
        ],
    }
    generate_bronze_contract("vendas.csv", bronze_requirements, "vendas_email@squad.com")
