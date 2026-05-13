"""REST API for dynamic Pokemon GO safe transfer strings."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.constants import DB_PATH
from src.transform import build_transfer_string_from_ids


class TrashFilters(BaseModel):
    gl_top: int | None = Field(default=None, ge=1)
    ul_top: int | None = Field(default=None, ge=1)
    ml_top: int | None = Field(default=None, ge=1)


class PokemonSummary(BaseModel):
    entity_key: str
    pokedex_id: int
    nome: str
    forma_regional: str
    rank_gl: int | None
    rank_ul: int | None
    rank_ml: int | None


class TrashLists(BaseModel):
    gl: list[PokemonSummary]
    ul: list[PokemonSummary]
    ml: list[PokemonSummary]
    all: list[PokemonSummary]
    trash: list[PokemonSummary]


class SearchStrings(BaseModel):
    gl: str
    ul: str
    ml: str
    all: str
    trash: str


class TrashStringResponse(BaseModel):
    ids: list[int]
    query_string: str
    lists: TrashLists
    strings: SearchStrings


def create_app(db_path: Path = DB_PATH) -> FastAPI:
    app = FastAPI(title="Pokemon GO PvP Safe Trash API")
    app.state.db_path = db_path

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/trash-string", response_model=TrashStringResponse)
    def trash_string(filters: TrashFilters) -> TrashStringResponse:
        lists = query_filtered_lists(app.state.db_path, filters)
        ids = sorted({pokemon.pokedex_id for pokemon in lists.trash})
        strings = SearchStrings(
            gl=build_search_string(lists.gl),
            ul=build_search_string(lists.ul),
            ml=build_search_string(lists.ml),
            all=build_search_string(lists.all),
            trash=build_transfer_string_from_ids(ids),
        )
        return TrashStringResponse(
            ids=ids,
            query_string=strings.trash,
            lists=lists,
            strings=strings,
        )

    return app


def query_filtered_lists(db_path: Path, filters: TrashFilters) -> TrashLists:
    if not db_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Pokemon database not found. Run the ETL before calling this endpoint.",
        )

    query = """
        SELECT
            entity_key,
            pokedex_id,
            nome,
            forma_regional,
            rank_gl,
            rank_ul,
            rank_ml
        FROM pokemon_dimension
        ORDER BY pokedex_id, forma_regional, nome
    """

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except sqlite3.OperationalError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.OperationalError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    pokemon = [
        PokemonSummary(
            entity_key=str(row["entity_key"]),
            pokedex_id=int(row["pokedex_id"]),
            nome=str(row["nome"]),
            forma_regional=str(row["forma_regional"]),
            rank_gl=row["rank_gl"],
            rank_ul=row["rank_ul"],
            rank_ml=row["rank_ml"],
        )
        for row in rows
    ]

    gl = _filter_ranked(pokemon, "rank_gl", filters.gl_top)
    ul = _filter_ranked(pokemon, "rank_ul", filters.ul_top)
    ml = _filter_ranked(pokemon, "rank_ml", filters.ml_top)
    protected_keys = {item.entity_key for item in [*gl, *ul, *ml]}

    return TrashLists(
        gl=gl,
        ul=ul,
        ml=ml,
        all=[item for item in pokemon if item.entity_key in protected_keys],
        trash=[item for item in pokemon if item.entity_key not in protected_keys],
    )


def query_trash_ids(db_path: Path, filters: TrashFilters) -> list[int]:
    lists = query_filtered_lists(db_path, filters)
    return sorted({pokemon.pokedex_id for pokemon in lists.trash})


def build_search_string(pokemon: list[PokemonSummary]) -> str:
    ids = sorted({item.pokedex_id for item in pokemon})
    return ",".join(str(pokedex_id) for pokedex_id in ids)


def _filter_ranked(
    pokemon: list[PokemonSummary], rank_field: str, top_n: int | None
) -> list[PokemonSummary]:
    if top_n is None:
        return []
    return [
        item
        for item in pokemon
        if getattr(item, rank_field) is not None and getattr(item, rank_field) <= top_n
    ]


app = create_app()
