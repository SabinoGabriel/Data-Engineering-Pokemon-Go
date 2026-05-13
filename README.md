# Pokemon GO PvP Safe Trash

[Leia em portugues do Brasil](README.pt-BR.md)

Monorepo for a Pokemon GO PvP ETL and dynamic safe transfer string app.

The backend extracts PvPoke rankings, models released Pokemon GO families in SQLite, and exposes a FastAPI endpoint that calculates a safe transfer search string on demand. The frontend is a mobile-first Next.js app with rank sliders for Great League, Ultra League, and Master League.

## Tech Stack

- Backend: Python, pandas, requests, SQLite, FastAPI, Pydantic, pytest
- Frontend: Next.js, React, TypeScript
- CI: GitHub Actions

## Architecture

```text
.
|-- backend/
|   |-- requirements.txt
|   |-- pytest.ini
|   |-- cache/                    # Local SQLite output, ignored by git
|   |-- config/
|   |-- tests/
|   `-- src/
|       |-- constants.py          # URLs, league cutoffs, region rules, transfer suffix
|       |-- database.py           # SQLite schema and persistence
|       |-- etl.py                # Extract -> Transform -> Load orchestration
|       |-- transform.py          # Family rank propagation and transfer string helpers
|       |-- api/main.py           # FastAPI app
|       `-- data_sources/
|           `-- pvpoke_client.py  # PvPoke rankings and gamemaster client
|-- frontend/
|   |-- package.json
|   `-- app/
|       |-- page.tsx              # Dynamic safe trash UI
|       `-- globals.css
`-- .github/workflows/ci.yml
```

## Business Rule: Regional Isolation

Regional forms and base forms are separate PvP families. The backend propagates rank utility with this key:

```text
family_id|regional_form
```

For example, `FAMILY_VULPIX|alola` and `FAMILY_VULPIX|base` are independent. Alolan Ninetales can protect Alolan Vulpix, but it never protects Kanto Vulpix.

This rule is implemented in `backend/src/transform.py` and covered by unit tests.

## Dynamic Ranking Model

The SQLite `pokemon_dimension` table stores exact nullable ranks:

- `rank_gl`
- `rank_ul`
- `rank_ml`

Pokemon outside a league cutoff have `NULL` for that league. The API receives active cutoffs from the frontend and treats a Pokemon family as protected when any active league rank is within the selected top N.

## Backend API

Start from `backend/`:

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

Start from `frontend/`:

```powershell
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000`. Override with:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
```

Open:

```text
http://localhost:3000
```

## Running Tests

```powershell
cd backend
python -m pytest
```
