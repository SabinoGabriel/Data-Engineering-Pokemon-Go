import sqlite3

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.database import init_db


def seed_dimension(db_path):
    conn = sqlite3.connect(db_path)
    init_db(conn)
    conn.executemany(
        """
        INSERT INTO pokemon_dimension (
            entity_key,
            pokedex_id,
            nome,
            forma_regional,
            species_slug,
            chain_id,
            family_key,
            rank_gl,
            rank_ul,
            rank_ml,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "stunfisk|base",
                618,
                "Stunfisk",
                "base",
                "stunfisk",
                "FAMILY_STUNFISK",
                "FAMILY_STUNFISK|base",
                None,
                None,
                None,
                "2026-05-11T00:00:00+00:00",
            ),
            (
                "stunfisk|galar",
                618,
                "Stunfisk",
                "galar",
                "stunfisk",
                "FAMILY_STUNFISK",
                "FAMILY_STUNFISK|galar",
                4,
                8,
                None,
                "2026-05-11T00:00:00+00:00",
            ),
            (
                "bulbasaur|base",
                1,
                "Bulbasaur",
                "base",
                "bulbasaur",
                "FAMILY_BULBASAUR",
                "FAMILY_BULBASAUR|base",
                51,
                None,
                None,
                "2026-05-11T00:00:00+00:00",
            ),
            (
                "charmander|base",
                4,
                "Charmander",
                "base",
                "charmander",
                "FAMILY_CHARMANDER",
                "FAMILY_CHARMANDER|base",
                None,
                None,
                39,
                "2026-05-11T00:00:00+00:00",
            ),
        ],
    )
    conn.commit()
    conn.close()


def test_health_returns_ok(tmp_path):
    client = TestClient(create_app(tmp_path / "pokemon.sqlite"))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_trash_string_filters_single_league_and_preserves_regional_isolation(tmp_path):
    db_path = tmp_path / "pokemon.sqlite"
    seed_dimension(db_path)
    client = TestClient(create_app(db_path))

    response = client.post(
        "/trash-string",
        json={"gl_top": 50, "ul_top": None, "ml_top": None},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ids"] == [1, 4, 618]
    assert payload["query_string"].startswith("1,4,618&!shiny")
    assert payload["strings"]["gl"] == "618"
    assert payload["strings"]["ul"] == ""
    assert payload["strings"]["ml"] == ""
    assert payload["strings"]["all"] == "618"
    assert payload["strings"]["trash"].startswith("1,4,618&!shiny")
    assert [pokemon["entity_key"] for pokemon in payload["lists"]["gl"]] == [
        "stunfisk|galar"
    ]
    assert [pokemon["entity_key"] for pokemon in payload["lists"]["trash"]] == [
        "bulbasaur|base",
        "charmander|base",
        "stunfisk|base",
    ]


def test_trash_string_combines_active_leagues(tmp_path):
    db_path = tmp_path / "pokemon.sqlite"
    seed_dimension(db_path)
    client = TestClient(create_app(db_path))

    response = client.post(
        "/trash-string",
        json={"gl_top": 50, "ul_top": None, "ml_top": 40},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ids"] == [1, 618]
    assert payload["strings"]["gl"] == "618"
    assert payload["strings"]["ml"] == "4"
    assert payload["strings"]["all"] == "4,618"
    assert payload["strings"]["trash"].startswith("1,618&!shiny")
    assert [pokemon["entity_key"] for pokemon in payload["lists"]["all"]] == [
        "charmander|base",
        "stunfisk|galar",
    ]


def test_trash_string_with_all_leagues_disabled_returns_all_ids(tmp_path):
    db_path = tmp_path / "pokemon.sqlite"
    seed_dimension(db_path)
    client = TestClient(create_app(db_path))

    response = client.post(
        "/trash-string",
        json={"gl_top": None, "ul_top": None, "ml_top": None},
    )

    assert response.status_code == 200
    assert response.json()["ids"] == [1, 4, 618]
