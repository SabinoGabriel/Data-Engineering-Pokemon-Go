# Pokemon GO PvP Safe Trash

[Read in English](README.md)

Monorepo para um ETL de rankings PvP de Pokemon GO e uma aplicacao de Lixeira Segura dinamica.

O backend extrai rankings do PvPoke, modela familias de Pokemon GO em SQLite e expoe uma API FastAPI que calcula a string de transferencia sob demanda. O frontend e um app Next.js mobile-first com sliders de rank para Great League, Ultra League e Master League.

## Stack

- Backend: Python, pandas, requests, SQLite, FastAPI, Pydantic, pytest
- Frontend: Next.js, React, TypeScript
- CI: GitHub Actions

## Arquitetura

```text
.
|-- backend/
|   |-- requirements.txt
|   |-- pytest.ini
|   |-- cache/                    # SQLite local, ignorado pelo git
|   |-- config/
|   |-- tests/
|   `-- src/
|       |-- constants.py          # URLs, cortes por liga, regioes, sufixo da string
|       |-- database.py           # Schema SQLite e persistencia
|       |-- etl.py                # Orquestracao Extract -> Transform -> Load
|       |-- transform.py          # Propagacao de ranks por familia e helpers
|       |-- api/main.py           # App FastAPI
|       `-- data_sources/
|           `-- pvpoke_client.py  # Cliente PvPoke
|-- frontend/
|   |-- package.json
|   `-- app/
|       |-- page.tsx              # UI dinamica da Lixeira Segura
|       `-- globals.css
`-- .github/workflows/ci.yml
```

## Regra de Negocio: Isolamento Regional

Formas regionais e formas base sao familias PvP separadas. O backend propaga utilidade de rank com esta chave:

```text
family_id|regional_form
```

Por exemplo, `FAMILY_VULPIX|alola` e `FAMILY_VULPIX|base` sao independentes. Alolan Ninetales pode proteger Alolan Vulpix, mas nunca protege Vulpix de Kanto.

Essa regra fica em `backend/src/transform.py` e e coberta por testes unitarios.

## Modelo Dinamico de Rankings

A tabela SQLite `pokemon_dimension` armazena ranks exatos e anulaveis:

- `rank_gl`
- `rank_ul`
- `rank_ml`

Pokemon fora do corte de uma liga recebem `NULL` naquela coluna. A API recebe os cortes ativos do frontend e considera uma familia protegida quando qualquer rank ativo esta dentro do Top N selecionado.

## Backend API

A partir de `backend/`:

```powershell
python -m pip install -r requirements.txt
python -m src.etl
uvicorn src.api.main:app --reload
```

Endpoints:

- `GET /health`
- `POST /trash-string`

Request:

```json
{
  "gl_top": 50,
  "ul_top": null,
  "ml_top": 40
}
```

Response:

```json
{
  "ids": [1, 3, 7],
  "query_string": "1,3,7&!shiny&!lucky&!shadow&!purified&!legendary&!mythical&!costume&!4*&!3*&!@special"
}
```

## Frontend

A partir de `frontend/`:

```powershell
npm install
npm run dev
```

O frontend espera a API em `http://localhost:8000`. Para trocar:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
```

Abra:

```text
http://localhost:3000
```

## Testes

```powershell
cd backend
python -m pytest
```
