# Backend Architecture

The backend is responsible for turning PvPoke source data into a local SQLite model and serving dynamic Pokemon GO search strings through FastAPI.

## Responsibilities

- Extract PvPoke rankings and `gamemaster.json`.
- Normalize Pokemon GO species, forms, families, and regional branches.
- Persist exact nullable league ranks in SQLite.
- Expose API responses that separate meta strings from the safe trash string.
- Protect the regional isolation invariant: `family_id|regional_form`.

## Current Structure

```text
backend/
|-- src/
|   |-- api/main.py              # FastAPI app, request/response models, query logic
|   |-- constants.py             # PvPoke URLs, league defaults, region rules, suffix
|   |-- database.py              # SQLite schema, connection, persistence
|   |-- etl.py                   # Extract -> transform -> load orchestration
|   |-- transform.py             # Ranking normalization and family-rank propagation
|   |-- data_sources/            # External PvPoke clients and static legacy data
|   `-- utils/
`-- tests/
```

## Data Flow

1. `PvPokeClient` downloads ranking JSON for GL, UL, and ML, plus `gamemaster.json`.
2. `transform.py` builds the Pokemon dimension and normalizes PvPoke species ids.
3. Family utility is propagated by `family_key`, never by raw species id alone.
4. `database.py` stores `rank_gl`, `rank_ul`, and `rank_ml` as nullable integers.
5. `api/main.py` reads SQLite and returns:
   - per-league meta lists and strings;
   - combined meta list and string;
   - safe trash list and transfer string.

## Architecture Cleanup Plan

The current API is functional, but too much behavior lives inline in `api/main.py`. The next refactor should split it into small modules:

```text
src/api/
|-- main.py              # FastAPI app factory and route registration only
|-- schemas.py           # Pydantic request/response models
|-- routes.py            # HTTP route functions
|-- services/
|   `-- trash_service.py # Filtering, grouping, and string composition
`-- repositories/
    `-- pokemon_repo.py  # SQLite reads mapped to domain objects
```

Recommended reusable structures:

- `LeagueKey` enum or literal type for `gl`, `ul`, `ml`.
- `LEAGUE_RANK_COLUMNS` mapping, for example `{ "gl": "rank_gl" }`.
- `PokemonSummary` as a shared API schema.
- A pure service function like `build_trash_response(filters, pokemon_rows)`.
- A repository function like `load_pokemon_dimension(db_path)`.

This keeps FastAPI thin, makes the ranking rules testable without HTTP, and prevents frontend/backend contract changes from being scattered across route code.

## Testing Strategy

- Keep regional isolation tests in transformation tests.
- Add service-level tests for GL-only, combined leagues, all-disabled filters, and string generation.
- Keep route tests focused on FastAPI validation and response shape.
