import pandas as pd

from src.transform import (
    build_pokemon_dimension,
    build_transfer_string,
    compute_quantidade_listas,
    normalize_pvpoke_species_id,
    region_from_gamemaster_entry,
)


def test_normalize_pvpoke_species_id_keeps_regional_forms_independent():
    assert normalize_pvpoke_species_id("stunfisk_galarian") == ("stunfisk", "galar")
    assert normalize_pvpoke_species_id("stunfisk") == ("stunfisk", "base")
    assert normalize_pvpoke_species_id("ninetales_alolan_shadow") == ("ninetales", "alola")
    assert normalize_pvpoke_species_id("obstagoon") == ("obstagoon", "galar")


def test_region_from_gamemaster_entry_uses_family_refs_for_regional_evolutions():
    entry = {
        "speciesId": "obstagoon",
        "tags": ["shadoweligible"],
        "family": {"id": "FAMILY_ZIGZAGOON", "parent": "linoone_galarian"},
    }

    assert region_from_gamemaster_entry(entry) == "galar"


def test_compute_quantidade_listas_does_not_leak_between_base_and_regional_forms():
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
            },
            {
                "entity_key": "stunfisk|galar",
                "pokedex_id": 618,
                "nome": "Stunfisk",
                "forma_regional": "galar",
                "species_slug": "stunfisk",
                "chain_id": "FAMILY_STUNFISK",
                "family_key": "FAMILY_STUNFISK|galar",
            },
        ]
    )
    filtered_rankings = {
        "GL": pd.DataFrame([{"species_slug": "stunfisk", "forma_regional": "galar"}]),
        "UL": pd.DataFrame([{"species_slug": "stunfisk", "forma_regional": "galar"}]),
        "ML": pd.DataFrame(columns=["species_slug", "forma_regional"]),
    }

    result = compute_quantidade_listas(dimension, filtered_rankings)

    counts = result.set_index("entity_key")["quantidade_listas"].to_dict()
    assert counts["stunfisk|base"] == 0
    assert counts["stunfisk|galar"] == 2


def test_build_pokemon_dimension_uses_base_species_for_regional_family_fallback():
    gamemaster = {
        "pokemon": [
            {
                "dex": 618,
                "speciesName": "Stunfisk",
                "speciesId": "stunfisk",
                "released": True,
            },
            {
                "dex": 618,
                "speciesName": "Stunfisk (Galarian)",
                "speciesId": "stunfisk_galarian",
                "tags": ["galarian"],
                "released": True,
            },
        ]
    }

    dimension = build_pokemon_dimension(gamemaster)

    families = dimension.set_index("entity_key")["family_key"].to_dict()
    assert families["stunfisk|base"] == "FAMILY_STUNFISK|base"
    assert families["stunfisk|galar"] == "FAMILY_STUNFISK|galar"


def test_build_transfer_string_deduplicates_ids_and_appends_safety_suffix():
    df = pd.DataFrame(
        [
            {"pokedex_id": 1, "quantidade_listas": 0},
            {"pokedex_id": 1, "quantidade_listas": 0},
            {"pokedex_id": 2, "quantidade_listas": 1},
            {"pokedex_id": 3, "quantidade_listas": 0},
        ]
    )

    transfer_string = build_transfer_string(df)

    assert transfer_string.startswith("1,3&!shiny")
    assert "&!legendary&!mythical" in transfer_string
