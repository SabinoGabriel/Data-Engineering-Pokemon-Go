"""SQLite persistence for the ETL output."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pandas as pd

from src.constants import DB_PATH


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS raw_rankings (
            league TEXT NOT NULL,
            species_id TEXT NOT NULL,
            species_name TEXT NOT NULL,
            rating REAL,
            rank_position INTEGER NOT NULL,
            extracted_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pokemon_dimension (
            entity_key TEXT PRIMARY KEY,
            pokedex_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            forma_regional TEXT NOT NULL,
            species_slug TEXT NOT NULL,
            chain_id TEXT NOT NULL,
            family_key TEXT NOT NULL,
            quantidade_listas INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO metadata (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def get_metadata(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def has_dimension(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) FROM pokemon_dimension").fetchone()[0] > 0


def read_dashboard_dimension(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT pokedex_id, nome, forma_regional, quantidade_listas
        FROM pokemon_dimension
        ORDER BY pokedex_id, forma_regional
        """,
        conn,
    )


def persist_rankings(conn: sqlite3.Connection, rankings: dict[str, pd.DataFrame]) -> None:
    conn.execute("DELETE FROM raw_rankings")
    raw_df = pd.concat(rankings.values(), ignore_index=True)
    raw_df.to_sql("raw_rankings", conn, if_exists="append", index=False)
    conn.commit()


def persist_dimension(conn: sqlite3.Connection, dimension: pd.DataFrame) -> None:
    conn.execute("DELETE FROM pokemon_dimension")
    output = dimension.copy()
    output["updated_at"] = now_utc()
    output.to_sql("pokemon_dimension", conn, if_exists="append", index=False)
    conn.commit()
