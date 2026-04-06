# UI (Streamlit)

Consola web da plataforma. O código vive em `app/`; as dependências Python da UI estão declaradas no **monorepo** como extra opcional `ui` em [`pyproject.toml`](../pyproject.toml) (grupo `[project.optional-dependencies]` → `ui`).

## Pré-requisitos

- Python **3.11+**
- Estar com o repositório clonado (este guia assume a pasta raiz `miletto_data_platform`)

## 1. Criar um virtualenv só para a UI

Na **raiz do repositório**, crie o ambiente **dentro de `UI/`** (fica isolado por pasta, mas usa o mesmo `pyproject.toml` da raiz):

```bash
cd miletto_data_platform
python -m venv UI/.venv
```

(Em Windows, se `python` não existir, use `py -3` no lugar de `python`.)

## 2. Ativar o virtualenv

**Git Bash (MINGW64):**

```bash
source UI/.venv/Scripts/activate
```

**PowerShell:**

```powershell
.\UI\.venv\Scripts\Activate.ps1
```

Se aparecer erro de política de execução, uma vez por utilizador:  
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**CMD:**

```cmd
UI\.venv\Scripts\activate.bat
```

> Não use `Activate.ps1` dentro do Git Bash: esse ficheiro é para PowerShell; no Bash use `source …/activate`.

## 3. Instalar apenas as dependências da aplicação UI

O ficheiro [`pyproject.toml`](../pyproject.toml) está na **raiz do monorepo**, não dentro de `UI/`. No `pip`, o `.` em `pip install -e ".[ui]"` significa **a pasta em que estás agora**. Por isso:

- Se estiveres em `UI/` e correres `pip install -e ".[ui]"`, o pip procura `UI/pyproject.toml` → **erro** (“neither setup.py nor pyproject.toml found”).

**Opção A — recomendada (a partir da raiz do repo):**

```bash
cd miletto_data_platform
pip install -U pip
pip install -e ".[ui]"
```

**Opção B — já estás dentro de `UI/`** (Git Bash), com o venv ativo:

```bash
pip install -U pip
pip install -e '..[ui]'
```

No **PowerShell**, a partir de `UI/`:

```powershell
pip install -e "..[ui]"
```

Isto instala o projeto em modo editável e **só** o extra `ui` (por exemplo **Streamlit**), sem `dev`, `kafka` ou `contracts`.

## 4. Executar a interface

Na **raiz do repo**, com o mesmo venv ativo:

```bash
streamlit run UI/app/app.py
```

Se a tua shell **já está em `UI/`**, podes usar:

```bash
streamlit run app/app.py
```

Abre o browser (por defeito `http://localhost:8501`). Para parar: `Ctrl+C`.

> **Git Bash / Windows:** `py -m streamlit` usa muitas vezes o Python **global**, não o do `.venv`. Com o venv **ativado**, use `python -m streamlit run …` (o `python` passa a ser o do ambiente). Sem ativar: `./.venv/Scripts/python.exe -m streamlit run app/app.py` a partir de `UI/`.

## Resumo rápido

| Passo | Onde | Comando |
|--------|------|--------|
| Criar venv | Raiz do repo | `python -m venv UI/.venv` |
| Ativar | Qualquer | `source UI/.venv/Scripts/activate` (Bash) ou equivalente |
| Dependências UI | Raiz do repo | `pip install -e ".[ui]"` |
| Dependências UI | Dentro de `UI/` | `pip install -e '..[ui]'` (Bash) ou `pip install -e "..[ui]"` (PowerShell) |
| Correr app | Raiz do repo | `streamlit run UI/app/app.py` |

## Problemas comuns

| Mensagem | Causa | O que fazer |
|----------|--------|-------------|
| `does not appear to be a Python project` em `.../UI` | Correste `pip install -e ".[ui]"` **dentro** de `UI/` | Faz `cd ..` para a raiz e `pip install -e ".[ui]"`, ou usa `pip install -e '..[ui]'` a partir de `UI/` (ver secção 3). |
| `No module named streamlit` ao usar `py -m streamlit` | O launcher `py` aponta para Python global sem Streamlit | Ativa o `.venv` e corre `python -m streamlit run app/app.py`, ou `./.venv/Scripts/python.exe -m streamlit run app/app.py`. Confirma com `pip install -e '..[ui]'` **com o mesmo** `python` / `.venv`. |

## Contexto para agentes / convenções

Regras e glossário da app: [`instructions/.cursorrules`](instructions/.cursorrules). Índice geral do monorepo: [`AGENTS.md`](../AGENTS.md).
