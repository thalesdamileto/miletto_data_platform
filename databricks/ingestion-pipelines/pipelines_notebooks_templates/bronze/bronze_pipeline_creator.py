import json
import requests
import os

DATABRICKS_HOST = "https://<seu-workspace>.azuredatabricks.net"
TOKEN = "<seu-token>"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

CONFIG_PATH = "config/1-bronze/databricks_volume/"


# ---------------------------------
# Unity Catalog
# ---------------------------------

def schema_exists(catalog, schema):

    url = f"{DATABRICKS_HOST}/api/2.1/unity-catalog/schemas/{catalog}.{schema}"

    r = requests.get(url, headers=HEADERS)

    return r.status_code == 200


def create_schema(catalog, schema):

    url = f"{DATABRICKS_HOST}/api/2.1/unity-catalog/schemas"

    payload = {
        "name": schema,
        "catalog_name": catalog
    }

    r = requests.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()

    print(f"Schema criado: {catalog}.{schema}")


def ensure_schema_exists(catalog, schema):

    if not schema_exists(catalog, schema):
        print(f"Schema {catalog}.{schema} não existe. Criando...")
        create_schema(catalog, schema)
    else:
        print(f"Schema {catalog}.{schema} já existe")


# ---------------------------------
# Pipelines
# ---------------------------------

def get_existing_pipelines():

    url = f"{DATABRICKS_HOST}/api/2.0/pipelines"

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    pipelines = response.json().get("statuses", [])

    return {p["name"]: p["pipeline_id"] for p in pipelines}


def create_pipeline(config):

    url = f"{DATABRICKS_HOST}/api/2.0/pipelines"

    r = requests.post(url, headers=HEADERS, json=config)
    r.raise_for_status()

    print(f"Pipeline criado: {config['name']}")


def update_pipeline(pipeline_id, config):

    url = f"{DATABRICKS_HOST}/api/2.0/pipelines/{pipeline_id}"

    r = requests.put(url, headers=HEADERS, json=config)
    r.raise_for_status()

    print(f"Pipeline atualizado: {config['name']}")


# ---------------------------------
# encontrar arquivos JSON
# ---------------------------------

def find_json_files(base_path):

    json_files = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    return json_files


# ---------------------------------
# execução principal
# ---------------------------------

existing = get_existing_pipelines()

json_files = find_json_files(CONFIG_PATH)

print(f"{len(json_files)} arquivos de configuração encontrados")

for file_path in json_files:

    print(f"\nProcessando: {file_path}")

    with open(file_path) as f:
        pipeline_configs = json.load(f)

    # suporta array ou objeto único
    if not isinstance(pipeline_configs, list):
        pipeline_configs = [pipeline_configs]

    for config in pipeline_configs:

        name = config["name"]
        catalog = config["catalog"]
        schema = config["schema"]

        ensure_schema_exists(catalog, schema)

        if name in existing:
            update_pipeline(existing[name], config)
        else:
            create_pipeline(config)