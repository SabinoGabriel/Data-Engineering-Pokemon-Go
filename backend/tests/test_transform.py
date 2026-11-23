import pandas as pd

from src.transform import (
    add_family_ranks,
    build_pokemon_dimension,
    build_transfer_chunks,
    build_transfer_string_from_ids,
    normalize_pvpoke_species_id,
    region_from_gamemaster_entry,
)


def test_normalize_pvpoke_species_id_keeps_regional_forms_independent():
    assert normalize_pvpoke_species_id("stunfisk_galarian") == ("stunfisk", "galar")
    assert normalize_pvpoke_species_id("stunfisk") == ("stunfisk", "base")
    assert normalize_pvpoke_species_id("ninetales_alolan_shadow") == ("ninetales", "alola")
    assert normalize_pvpoke_species_id("obstagoon") == ("obstagoon", "galar")


def test_region_from_gamemaster_entry_locks_regional_evolutions_with_neutral_ids():
    entry = {
        "speciesId": "obstagoon",
        "tags": ["shadoweligible"],
        "family": {"id": "FAMILY_ZIGZAGOON", "parent": "linoone_galarian"},
    }

    assert region_from_gamemaster_entry(entry) == "galar"


def test_add_family_ranks_does_not_leak_between_base_and_regional_forms():
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
        "GL": pd.DataFrame(
            [{"species_slug": "stunfisk", "forma_regional": "galar", "rank_position": 4}]
        ),
        "UL": pd.DataFrame(
            [{"species_slug": "stunfisk", "forma_regional": "galar", "rank_position": 8}]
        ),
        "ML": pd.DataFrame(columns=["species_slug", "forma_regional", "rank_position"]),
    }

    result = add_family_ranks(dimension, filtered_rankings)

    ranks = result.set_index("entity_key")[["rank_gl", "rank_ul", "rank_ml"]]
    assert pd.isna(ranks.loc["stunfisk|base", "rank_gl"])
    assert ranks.loc["stunfisk|galar", "rank_gl"] == 4
    assert ranks.loc["stunfisk|galar", "rank_ul"] == 8
    assert pd.isna(ranks.loc["stunfisk|galar", "rank_ml"])
    assert str(result["rank_gl"].dtype) == "Int64"


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


def test_build_transfer_string_from_ids_deduplicates_ids_and_appends_safety_suffix():
    transfer_string = build_transfer_string_from_ids([1, 1, 3])

    assert transfer_string.startswith("1,3&!shiny")
    assert "&!legendary&!mythical" in transfer_string


def test_base_cubone_and_raticate_are_not_mislabeled_by_misleading_family_refs():
    # PvPoke lists marowak_alolan under base Cubone and rattata_alolan as the
    # parent of base Raticate. Those refs must not turn the base forms regional.
    cubone = {
        "speciesId": "cubone",
        "tags": [],
        "family": {"id": "FAMILY_CUBONE", "evolutions": ["marowak", "marowak_alolan"]},
    }
    raticate = {
        "speciesId": "raticate",
        "tags": [],
        "family": {"id": "FAMILY_RATTATA", "parent": "rattata_alolan"},
    }

    assert region_from_gamemaster_entry(cubone) == "base"
    assert region_from_gamemaster_entry(raticate) == "base"
    assert region_from_gamemaster_entry({**cubone, "speciesId": "cubone_alolan"}) == "alola"


def _dimension_row(slug, region, family):
    return {
        "entity_key": f"{slug}|{region}",
        "pokedex_id": 0,
        "nome": slug,
        "forma_regional": region,
        "species_slug": slug,
        "chain_id": family,
        "family_key": f"{family}|{region}",
    }


def test_ursaluna_hisui_protects_base_ursaring_and_teddiursa_but_not_the_reverse():
    dimension = pd.DataFrame(
        [
            _dimension_row("teddiursa", "base", "FAMILY_TEDDIURSA"),
            _dimension_row("ursaring", "base", "FAMILY_TEDDIURSA"),
            _dimension_row("ursaluna", "hisui", "FAMILY_TEDDIURSA"),
        ]
    )
    empty = pd.DataFrame(columns=["species_slug", "forma_regional", "rank_position"])

    ursaluna_ranked = add_family_ranks(
        dimension,
        {
            "GL": empty,
            "UL": empty,
            "ML": pd.DataFrame(
                [{"species_slug": "ursaluna", "forma_regional": "hisui", "rank_position": 12}]
            ),
        },
    ).set_index("entity_key")
    assert ursaluna_ranked.loc["ursaring|base", "rank_ml"] == 12
    assert ursaluna_ranked.loc["teddiursa|base", "rank_ml"] == 12

    ursaring_ranked = add_family_ranks(
        dimension,
        {
            "GL": pd.DataFrame(
                [{"species_slug": "ursaring", "forma_regional": "base", "rank_position": 30}]
            ),
            "UL": empty,
            "ML": empty,
        },
    ).set_index("entity_key")
    assert pd.isna(ursaring_ranked.loc["ursaluna|hisui", "rank_gl"])


def test_build_transfer_chunks_are_self_contained_and_respect_the_limit():
    ids = list(range(1, 400))

    for lang in ("en", "pt"):
        chunks = build_transfer_chunks(ids, lang, max_length=300)

        assert len(chunks) > 1
        assert all(len(chunk) <= 300 for chunk in chunks)
        assert all("&!shiny" in chunk or "&!brilhante" in chunk for chunk in chunks)
        assert all("&!4*&!3*" in chunk for chunk in chunks)
        covered = [int(i) for chunk in chunks for i in chunk.split("&")[0].split(",")]
        assert covered == ids


def test_build_transfer_chunks_returns_nothing_when_there_is_nothing_to_transfer():
    assert build_transfer_chunks([], "en", max_length=300) == []
