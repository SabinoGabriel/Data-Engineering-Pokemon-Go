"""Orchestration for the Pokemon GO PvP ETL."""

from __future__ import annotations

import pandas as pd

from src.data_sources.pvpoke_client import PvPokeClient
from src.database import (
    connect_db,
    has_dimension,
    init_db,
    now_utc,
    persist_dimension,
    persist_rankings,
    read_pokemon_dimension,
    set_metadata,
)
from src.transform import add_family_ranks, build_pokemon_dimension, filter_elite_rankings


def run_etl(force_refresh: bool = False, client: PvPokeClient | None = None) -> pd.DataFrame:
    conn = connect_db()
    init_db(conn)

    if has_dimension(conn) and not force_refresh:
        return read_pokemon_dimension(conn)

    pvpoke = client or PvPokeClient()
    rankings = pvpoke.fetch_rankings()
    filtered = filter_elite_rankings(rankings)
    dimension = build_pokemon_dimension(pvpoke.fetch_gamemaster())
    final_dimension = add_family_ranks(dimension, filtered)

    persist_rankings(conn, rankings)
    persist_dimension(conn, final_dimension)
    set_metadata(conn, "last_refresh_utc", now_utc())
    conn.commit()

    return final_dimension.sort_values(["pokedex_id", "forma_regional"])


if __name__ == "__main__":
    run_etl(force_refresh=True)
