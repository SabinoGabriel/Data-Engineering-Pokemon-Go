"""Transform rules for PvPoke rankings and Pokemon GO families."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.constants import (
    CROSS_FORM_EVOLUTIONS,
    LEAGUES,
    PVP_ID_IGNORED_TOKENS,
    PVP_SPECIES_ALIASES,
    REGION_LOCKED_SPECIES,
    REGION_TOKENS,
    DEFAULT_LANG,
    build_transfer_suffix,
)


def regional_form_from_tokens(tokens: Iterable[str]) -> str:
    for token in tokens:
        region = REGION_TOKENS.get(token)
        if region:
            return region
    return "base"


def clean_species_id(species_id: str) -> str:
    return "_".join(
        token
        for token in species_id.lower().split("_")
        if token not in PVP_ID_IGNORED_TOKENS
    )


def normalize_pvpoke_species_id(species_id: str) -> tuple[str, str]:
    tokens = species_id.lower().split("_")
    regional_form = regional_form_from_tokens(tokens)
    species_tokens = [
        token
        for token in tokens
        if token not in REGION_TOKENS and token not in PVP_ID_IGNORED_TOKENS
    ]

    raw_species = "_".join(species_tokens)
    species_slug = PVP_SPECIES_ALIASES.get(raw_species, raw_species.replace("_", "-"))

    if regional_form == "base":
        regional_form = REGION_LOCKED_SPECIES.get(species_slug, "base")

    return species_slug, regional_form


def region_from_gamemaster_entry(entry: dict) -> str:
    """Region of a gamemaster entry, from its own id/tags only.

    Family refs (parent/evolutions) are deliberately NOT used: PvPoke lists
    cross-region links there (base Cubone lists marowak_alolan, base Raticate
    lists rattata_alolan as parent), which would mislabel base forms as regional.
    Regional evolutions with a neutral speciesId are handled by
    REGION_LOCKED_SPECIES instead.
    """
    species_id = str(entry.get("speciesId", "")).lower()

    region = regional_form_from_tokens(species_id.split("_"))
    if region != "base":
        return region

    region = regional_form_from_tokens(entry.get("tags") or [])
    if region != "base":
        return region

    base_species = clean_species_id(species_id).replace("_", "-")
    return REGION_LOCKED_SPECIES.get(base_species, "base")


def build_pokemon_dimension(gamemaster: dict) -> pd.DataFrame:
    records: list[dict] = []

    for entry in gamemaster["pokemon"]:
        species_id = str(entry.get("speciesId", "")).lower()
        tags = set(entry.get("tags") or [])
        if not entry.get("released", True):
            continue
        if "shadow" in tags or any(token in species_id.split("_") for token in ("shadow", "mega", "primal")):
            continue

        regional_form = region_from_gamemaster_entry(entry)
        species_slug, _ = normalize_pvpoke_species_id(species_id)
        fallback_family = f"FAMILY_{species_slug.upper().replace('-', '_')}"
        family_id = (entry.get("family") or {}).get("id") or fallback_family

        # Critical regional isolation rule:
        # PvPoke families intentionally group Kanto and regional branches under
        # the same family id, for example FAMILY_VULPIX for both Ninetales and
        # Alolan Ninetales. The ETL therefore stores the family as
        # family_id + regional_form. This lets utility propagate from Vulpix
        # Alolan to Ninetales Alolan, but never from Alolan Ninetales to Kanto
        # Ninetales.
        family_key = f"{family_id}|{regional_form}"

        records.append(
            {
                "entity_key": f"{species_slug}|{regional_form}",
                "pokedex_id": int(entry["dex"]),
                "nome": str(entry["speciesName"]).split(" (")[0],
                "forma_regional": regional_form,
                "species_slug": species_slug,
                "chain_id": family_id,
                "family_key": family_key,
            }
        )

    return (
        pd.DataFrame(records)
        .drop_duplicates(subset=["entity_key"])
        .sort_values(["pokedex_id", "forma_regional"])
        .reset_index(drop=True)
    )


def filter_elite_rankings(rankings: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    filtered: dict[str, pd.DataFrame] = {}

    for league, df in rankings.items():
        top_n = LEAGUES[league]["top_n"]
        elite = df[df["rank_position"] <= top_n].copy()
        normalized = elite["species_id"].apply(normalize_pvpoke_species_id)
        elite["species_slug"] = normalized.apply(lambda item: item[0])
        elite["forma_regional"] = normalized.apply(lambda item: item[1])
        filtered[league] = elite

    return filtered


def add_family_ranks(
    dimension: pd.DataFrame, filtered_rankings: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    dim = dimension.copy()
    species_to_chain = (
        dim[["species_slug", "chain_id"]]
        .drop_duplicates("species_slug")
        .set_index("species_slug")["chain_id"]
        .to_dict()
    )

    family_ranks: dict[str, dict[str, int]] = {}
    for league, ranking_df in filtered_rankings.items():
        rank_column = f"rank_{league.lower()}"
        for row in ranking_df[
            ["species_slug", "forma_regional", "rank_position"]
        ].itertuples():
            chain_id = species_to_chain.get(row.species_slug, f"unknown:{row.species_slug}")

            # Critical regional isolation rule:
            # The propagated utility key is PvPoke family_id + regional_form.
            # Galarian Stunfisk writes to "FAMILY_STUNFISK|galar", while Kanto/Base
            # Stunfisk reads from "FAMILY_STUNFISK|base" and stays unranked unless
            # that exact base branch appears in an elite PvPoke list.
            family_key = f"{chain_id}|{row.forma_regional}"
            current_rank = family_ranks.setdefault(family_key, {}).get(rank_column)
            rank_position = int(row.rank_position)
            if current_rank is None or rank_position < current_rank:
                family_ranks[family_key][rank_column] = rank_position

    # Explicit exceptions where an evolution crosses regional forms in-game
    # (Ursaring base -> Ursaluna Hisui). The target branch inherits the best
    # rank of its source branch; the reverse never happens.
    for target_key, source_keys in CROSS_FORM_EVOLUTIONS.items():
        for source_key in source_keys:
            for rank_column, rank in family_ranks.get(source_key, {}).items():
                target_ranks = family_ranks.setdefault(target_key, {})
                current = target_ranks.get(rank_column)
                if current is None or rank < current:
                    target_ranks[rank_column] = rank

    for league in LEAGUES:
        rank_column = f"rank_{league.lower()}"
        dim[rank_column] = dim["family_key"].map(
            lambda family_key: family_ranks.get(family_key, {}).get(rank_column)
        )
        dim[rank_column] = dim[rank_column].astype("Int64")

    return dim


def _unique_sorted_ids(pokedex_ids: Iterable[int]) -> list[int]:
    return sorted({int(pokedex_id) for pokedex_id in pokedex_ids})


def build_transfer_string_from_ids(
    pokedex_ids: Iterable[int], lang: str = DEFAULT_LANG, prefix: str = ""
) -> str:
    """Build one search string. `prefix` is an optional extra filter (e.g. "alola")."""
    ids = ",".join(str(pokedex_id) for pokedex_id in _unique_sorted_ids(pokedex_ids))
    head = "&".join(part for part in (prefix, ids) if part)
    return f"{head}{build_transfer_suffix(lang)}" if head else build_transfer_suffix(lang)


def build_transfer_chunks(
    pokedex_ids: Iterable[int],
    lang: str = DEFAULT_LANG,
    max_length: int | None = None,
    prefix: str = "",
) -> list[str]:
    """Split ids into self-contained search strings no longer than `max_length`.

    Every chunk carries the full safety suffix, so each one is safe to use on
    its own. Returns [] when there is nothing to transfer.
    """
    ids = _unique_sorted_ids(pokedex_ids)
    if not ids:
        return []
    if not max_length:
        return [build_transfer_string_from_ids(ids, lang, prefix)]

    chunks: list[str] = []
    current: list[int] = []
    for pokedex_id in ids:
        candidate = [*current, pokedex_id]
        if current and len(build_transfer_string_from_ids(candidate, lang, prefix)) > max_length:
            chunks.append(build_transfer_string_from_ids(current, lang, prefix))
            current = [pokedex_id]
        else:
            current = candidate
    chunks.append(build_transfer_string_from_ids(current, lang, prefix))
    return chunks
