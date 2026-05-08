# Data Engineering Pokemon GO PvP ETL Dashboard

[Leia em portugues do Brasil](README.pt-BR.md)

Python data engineering project that builds an ETL pipeline and an interactive Streamlit dashboard for Pokemon GO PvP rankings.

The pipeline extracts PvPoke ranking data, transforms it with pandas, stores the curated output in SQLite, and generates a safe in-game transfer search string for Pokemon with no detected PvP family utility.

## Tech Stack

- Python
- pandas
- requests
- SQLite
- Streamlit
- pytest
- GitHub Actions

## What This Project Demonstrates

- ETL pipeline design with clear Extract, Transform and Load layers
- API and raw JSON integration from GitHub-hosted data sources
- Data modeling for domain-specific business rules
- pandas transformations and DataFrame-based analytics
- SQLite persistence for reproducible local results
- Streamlit dashboard development
- Automated tests for critical transformation logic
- Portfolio-friendly repository structure for data engineering roles

## Data Sources

- Great League rankings: PvPoke top 150
- Ultra League rankings: PvPoke top 100
- Master League rankings: PvPoke top 40
- Pokemon dimension: PvPoke `gamemaster.json`

The project uses PvPoke's `gamemaster.json` as the main Pokemon dimension because it reflects Pokemon GO-specific forms, released Pokemon, PvP IDs, shadows and family metadata more accurately than a generic Pokedex source.

## Architecture

```text
.
|-- app.py                         # Streamlit entrypoint
|-- requirements.txt               # Python dependencies
|-- README.pt-BR.md                # Brazilian Portuguese documentation
|-- LICENSE                        # MIT license
|-- cache/                         # Local SQLite output, ignored by git
|-- tests/                         # Unit tests for transformation rules
|-- .github/workflows/ci.yml       # GitHub Actions CI
|-- src/
|   |-- constants.py               # URLs, league cutoffs, regions and transfer suffix
|   |-- dashboard.py               # Streamlit UI and filters
|   |-- database.py                # SQLite schema and persistence
|   |-- etl.py                     # Extract -> Transform -> Load orchestration
|   |-- transform.py               # Business rules, regional forms and family propagation
|   |-- data_sources/
|   |   |-- pvpoke_client.py       # PvPoke rankings and gamemaster client
|   |   `-- static_data.py         # Legacy auxiliary data
|   `-- utils/
|       `-- logger.py              # Project logger
```

## Business Rule: Regional Forms

Pokemon with the same base species but different regional forms must be treated as independent entities. For example, Alolan Ninetales must never protect Kanto Ninetales, and Galarian Stunfisk must never protect base Stunfisk.

The ETL propagates PvP usefulness through the key:

```text
family_id|regional_form
```

This means `FAMILY_VULPIX|alola` and `FAMILY_VULPIX|base` are separate families for scoring purposes.

The rule is implemented in `src/transform.py` and covered by unit tests.

## Dashboard Output

The dashboard displays:

- `Pokedex ID`
- `Name`
- `Regional Form`
- `League Count`

The **Safe Trash String** section lists unique Pokedex IDs with `quantidade_listas == 0` and appends this Pokemon GO safety suffix:

```text
&!shiny&!lucky&!shadow&!purified&!legendary&!mythical&!costume&!4*&!3*&!@special
```

## Getting Started

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the dashboard:

```powershell
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Running Tests

```powershell
pytest
```

## Local Database

The ETL writes local data to:

```text
cache/pokemon_go_pvp.sqlite
```

Main tables:

- `raw_rankings`: raw PvPoke ranking snapshots
- `pokemon_dimension`: final curated dimension with `quantidade_listas`
- `metadata`: refresh metadata

## Repository Keywords

This project is intentionally structured around common data engineering and analytics keywords:

`python`, `pandas`, `streamlit`, `sqlite`, `etl`, `data-engineering`, `dashboard`, `api-integration`, `pokemon-go`, `pvpoke`, `pytest`, `github-actions`

## License

MIT.
