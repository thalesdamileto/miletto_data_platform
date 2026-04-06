# Este arquivo contem explicações sobre o padrão das configurações do json para pipelines bronze

# root_do_projeto deste projeto é: /Workspace/Users/thalesfmorais94@gmail.com/dlt-metadata-driven-AI-pipelines/
# Configurações para evitar erros de sintaxe
true = True
false = False

# Lista de metadados de pipelines
bronze_metadata_list =\
[
    {
    "pipeline_type": "WORKSPACE", # VALOR DEFAULT, NÃO ALTERAR
    "name": "dlt_volume_to_json-bronze.dbo.iss_data", # Nome do job, deve seguir:  dlt_volume_to_{file_format}-{destination_catalog}.{destination_schema}.{destination_table}
    "configuration": {
        "source_path": "/Volumes/workspace/default/raw/iss_data/", # Diretório de origem dos dados a serem processados, pode ser um path em um bucket/storage
        "target_schema": "dbo", # Schema de destino do pipeline, deve ser fornecido pelo usuário
        "target_table": "iss_data", # Nome de destino da tabela, deve ser fornecido pelo usuário
        "description": "Dados de localização da ISS obtidos através da API pública" # descrição dos dados do pipeline, , deve ser fornecido pelo usuário
    },
    "libraries": [ # VALOR DEFAULT, NÃO ALTERAR
        {
        "glob": {
            "include": "/Workspace/Users/thalesfmorais94@gmail.com/dlt-metadata-driven-AI-pipelines/notebooks/bronze/databricks_volume/json/dlt_volume_json_pipeline.py" # Padrão do path do noteebok, deve seguir o seguinte: Root_do_projeto/notebooks/bronze/{tipo_de_origem}/{formato_de_origem}/dlt_volume_json_pipeline.py
        }
        }
    ],
    "schema": "dbo", # Schema de destino do pipeline, deve ser fornecido pelo usuário
    "continuous": false, # VALOR DEFAULT, NÃO ALTERAR
    "development": false, # VALOR DEFAULT, NÃO ALTERAR
    "photon": true, # VALOR DEFAULT, NÃO ALTERAR
    "channel": "CURRENT", # VALOR DEFAULT, NÃO ALTERAR
    "catalog": "bronze", # VALOR DEFAULT, NÃO ALTERAR, bronze sempre será o catalogo de destino dos pipelines bronze
    "serverless": true, # VALOR DEFAULT, NÃO ALTERAR
    "root_path": "/Workspace/Shared/rooth_path/bronze/dbo/iss_data" # VALOR DEFAULT, NÃO ALTERAR
    }
]
