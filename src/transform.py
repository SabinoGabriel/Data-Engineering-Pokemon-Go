"""Transform rules for PvPoke rankings and Pokemon GO families."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.constants import (
    LEAGUES,
    PVP_ID_IGNORED_TOKENS,
    PVP_SPECIES_ALIASES,
    REGION_LOCKED_SPECIES,
    REGION_TOKENS,
    TRANSFER_SUFFIX,
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
    species_id = str(entry.get("speciesId", "")).lower()
    tags = entry.get("tags") or []
    family = entry.get("family") or {}
    family_refs = [family.get("parent"), *(family.get("evolutions") or [])]

    region = regional_form_from_tokens(species_id.split("_"))
    if region != "base":
        return region

    region = regional_form_from_tokens(tags)
    if region != "base":
        return region

    for family_ref in family_refs:
        if not family_ref:
            continue
        region = regional_form_from_tokens(str(family_ref).split("_"))
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


def compute_quantidade_listas(
    dimension: pd.DataFrame, filtered_rankings: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    dim = dimension.copy()
    species_to_chain = (
        dim[["species_slug", "chain_id"]]
        .drop_duplicates("species_slug")
        .set_index("species_slug")["chain_id"]
        .to_dict()
    )

    family_leagues: dict[str, set[str]] = {}
    for league, ranking_df in filtered_rankings.items():
        for row in ranking_df[["species_slug", "forma_regional"]].drop_duplicates().itertuples():
            chain_id = species_to_chain.get(row.species_slug, f"unknown:{row.species_slug}")

            # Critical regional isolation rule:
            # The propagated utility key is PvPoke family_id + regional_form.
            # Galarian Stunfisk writes to "FAMILY_STUNFISK|galar", while
            # Kanto/Base Stunfisk reads from "FAMILY_STUNFISK|base" and stays
            # at 0 unless that exact base branch appears in an elite PvPoke list.
            family_key = f"{chain_id}|{row.forma_regional}"
            family_leagues.setdefault(family_key, set()).add(league)

    dim["quantidade_listas"] = dim["family_key"].map(
        lambda family_key: len(family_leagues.get(family_key, set()))
    )
    return dim


def build_transfer_string(df: pd.DataFrame) -> str:
    zero_ids = sorted(
        int(pokedex_id)
        for pokedex_id in df.loc[df["quantidade_listas"] == 0, "pokedex_id"].dropna().unique()
    )
    ids = ",".join(str(pokedex_id) for pokedex_id in zero_ids)
    return f"{ids}{TRANSFER_SUFFIX}" if ids else TRANSFER_SUFFIX
