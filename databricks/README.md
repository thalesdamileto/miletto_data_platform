# Databricks Ingestion - RAW

Este fluxo automatiza a criacao de jobs RAW no Databricks a partir do contrato de dados.

## Fonte de verdade

- Contrato: `data_contract/data_contracts.json`
- Metadado de jobs RAW: `databricks/ingestion-pipelines/pipelines_metadata/raw/raw_data_pipes.json`
- Criador/sincronizador: `databricks/ingestion-pipelines/pipelines_notebooks_templates/raw/raw_pipeline_creator.py`

## Campos obrigatorios no contrato para RAW

Para cada contrato com `sub_contracts.raw`, os campos abaixo sao obrigatorios:

- `_id`
- `data_producer` (email para notificacao)
- `sub_contracts.raw.parameters.file_name` (nome do notebook RAW, ex.: `iss_raw_data.py`)
- `sub_contracts.raw.parameters.schedule.databricks_quartz_cron`
- `sub_contracts.raw.parameters.target_path`

## O que o `raw_pipeline_creator.py` faz

1. Le o `data_contracts.json`.
2. Valida os campos obrigatorios do sub-contrato RAW.
3. Gera/atualiza o arquivo `raw_data_pipes.json` no formato esperado de Job Databricks.
4. Consulta jobs existentes no workspace.
5. Atualiza jobs existentes (mesmo nome) e cria jobs que ainda nao existem.

## Regras aplicadas no metadado RAW

- Nome do job: `raw_job_<notebook_sem_extensao>_<_id>`
- Task key: `<notebook_sem_extensao>_<_id>`
- Notebook path: `<notebook_base_path>/<notebook_sem_extensao>`
- `base_parameters.target_path`: vem do contrato RAW
- `schedule.quartz_cron_expression`: vem do contrato RAW
- `email_notifications.on_failure`: recebe o `data_producer`
- `schedule.timezone_id`: configuravel (padrao `America/Sao_Paulo`)

## Widgets esperados no notebook `raw_pipeline_creator.py`

- `databricks_host`: URL do workspace (obrigatorio para sincronizar jobs)
- `databricks_token`: token PAT (obrigatorio para sincronizar jobs)
- `contracts_path`: padrao `data_contract/data_contracts.json`
- `metadata_path`: padrao `databricks/ingestion-pipelines/pipelines_metadata/raw/raw_data_pipes.json`
- `notebook_base_path`: base de notebooks RAW no Repos
- `timezone_id`: padrao `America/Sao_Paulo`

Sem `databricks_host` e `databricks_token`, o notebook falha na etapa de sincronizacao de jobs.
