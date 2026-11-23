"""REST API for dynamic Pokemon GO safe transfer strings."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.constants import DB_PATH, REGION_SEARCH_TERMS
from src.transform import build_transfer_chunks


class TrashFilters(BaseModel):
    gl_top: int | None = Field(default=None, ge=1)
    ul_top: int | None = Field(default=None, ge=1)
    ml_top: int | None = Field(default=None, ge=1)
    lang: Literal["en", "pt"] = "en"
    # Max characters per search string. None = a single string.
    max_length: int | None = Field(default=None, ge=60, le=2000)


class PokemonSummary(BaseModel):
    entity_key: str
    pokedex_id: int
    nome: str
    forma_regional: str
    rank_gl: int | None
    rank_ul: int | None
    rank_ml: int | None


class MixedPokemon(BaseModel):
    """A Pokedex number where some forms are useful and others are not.

    The in-game search by number selects every form, so these numbers are kept
    out of the main trash string.
    """

    pokedex_id: int
    nome: str
    protected_forms: list[str]
    trash_forms: list[str]


class MixedString(BaseModel):
    """Experimental region-scoped string, e.g. "alola&26,52&!shiny..."."""

    label: str
    pokedex_ids: list[int]
    chunks: list[str]


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
    chunks: list[str]
    mixed: list[MixedPokemon]
    mixed_strings: list[MixedString]
    lists: TrashLists
    strings: SearchStrings


def allowed_origins() -> list[str]:
    configured = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def create_app(db_path: Path = DB_PATH) -> FastAPI:
    app = FastAPI(title="Pokemon GO PvP Safe Trash API")
    app.state.db_path = db_path

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins(),
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
        safe_ids, mixed = split_safe_and_mixed(lists)
        chunks = build_transfer_chunks(safe_ids, filters.lang, filters.max_length)
        strings = SearchStrings(
            gl=build_search_string(lists.gl),
            ul=build_search_string(lists.ul),
            ml=build_search_string(lists.ml),
            all=build_search_string(lists.all),
            trash=chunks[0] if chunks else "",
        )
        return TrashStringResponse(
            ids=safe_ids,
            query_string=chunks[0] if chunks else "",
            chunks=chunks,
            mixed=mixed,
            mixed_strings=build_mixed_strings(lists, mixed, filters),
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


def split_safe_and_mixed(lists: TrashLists) -> tuple[list[int], list[MixedPokemon]]:
    """Separate Pokedex numbers where every form is trash from mixed ones.

    The game's number search matches all forms of that number, so a number is
    only safe to transfer when none of its forms is protected.
    """
    protected_by_id: dict[int, list[PokemonSummary]] = {}
    trash_by_id: dict[int, list[PokemonSummary]] = {}
    for item in lists.all:
        protected_by_id.setdefault(item.pokedex_id, []).append(item)
    for item in lists.trash:
        trash_by_id.setdefault(item.pokedex_id, []).append(item)

    safe_ids = sorted(set(trash_by_id) - set(protected_by_id))
    mixed = [
        MixedPokemon(
            pokedex_id=pokedex_id,
            nome=trash_by_id[pokedex_id][0].nome,
            protected_forms=sorted({i.forma_regional for i in protected_by_id[pokedex_id]}),
            trash_forms=sorted({i.forma_regional for i in trash_by_id[pokedex_id]}),
        )
        for pokedex_id in sorted(set(trash_by_id) & set(protected_by_id))
    ]
    return safe_ids, mixed


def build_mixed_strings(
    lists: TrashLists, mixed: list[MixedPokemon], filters: TrashFilters
) -> list[MixedString]:
    """Experimental: scope the search to one region so only trash forms match.

    Relies on the game's region terms ("alola", "galar", ...) also matching
    regional forms, which is unverified. The base-form string excludes every
    region instead.
    """
    by_form: dict[str, list[int]] = {}
    for entry in mixed:
        for form in entry.trash_forms:
            if form in entry.protected_forms:
                # Same region on both sides (e.g. Castform weather forms):
                # a region search cannot tell them apart, so keep it out.
                continue
            by_form.setdefault(form, []).append(entry.pokedex_id)

    result: list[MixedString] = []
    for form, ids in by_form.items():
        if form == "base":
            prefix = "&".join(f"!{region}" for region in REGION_SEARCH_TERMS)
            label = "Base/Kanto"
        else:
            prefix = form
            label = form.capitalize()
        chunks = build_transfer_chunks(ids, filters.lang, filters.max_length, prefix)
        result.append(
            MixedString(
                label=label,
                pokedex_ids=sorted(ids),
                chunks=chunks,
            )
        )
    return sorted(result, key=lambda item: item.label)


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
