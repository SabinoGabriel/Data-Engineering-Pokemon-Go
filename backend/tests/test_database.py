import sqlite3

import pandas as pd

from src.database import init_db, persist_dimension


def test_persist_dimension_stores_nullable_ranks_as_sql_integers(tmp_path):
    db_path = tmp_path / "pokemon.sqlite"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    dimension = pd.DataFrame(
        [
            {
                "entity_key": "stunfisk|base",
                "pokedex_id": 618,
                "nome": "Stunfisk",
                "forma_regional": "base",
                "species_slug": "stunfisk",
                "chain_id": "FAMILY_STUNFISK",
                "family_key": "FAMILY_STUNFISK|base",
                "rank_gl": pd.NA,
                "rank_ul": pd.NA,
                "rank_ml": pd.NA,
            },
            {
                "entity_key": "stunfisk|galar",
                "pokedex_id": 618,
                "nome": "Stunfisk",
                "forma_regional": "galar",
                "species_slug": "stunfisk",
                "chain_id": "FAMILY_STUNFISK",
                "family_key": "FAMILY_STUNFISK|galar",
                "rank_gl": 4,
                "rank_ul": 8,
                "rank_ml": pd.NA,
            },
        ]
    )

    persist_dimension(conn, dimension)

    rows = conn.execute(
        """
        SELECT entity_key, rank_gl, typeof(rank_gl), rank_ml, typeof(rank_ml)
        FROM pokemon_dimension
        ORDER BY entity_key
        """
    ).fetchall()

    assert rows == [
        ("stunfisk|base", None, "null", None, "null"),
        ("stunfisk|galar", 4, "integer", None, "null"),
    ]
