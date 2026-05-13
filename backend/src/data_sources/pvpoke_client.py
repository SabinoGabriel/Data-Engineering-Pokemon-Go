"""PvPoke GitHub client used by the ETL."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests

from src.constants import GAMEMASTER_URL, HTTP_TIMEOUT, LEAGUES


class PvPokeClient:
    """Small client for PvPoke raw JSON files."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "pokemon-go-pvp-etl/1.0"})

    def fetch_json(self, url: str) -> dict | list:
        response = self.session.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def fetch_rankings(self) -> dict[str, pd.DataFrame]:
        extracted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        rankings: dict[str, pd.DataFrame] = {}

        for league, config in LEAGUES.items():
            raw_rows = self.fetch_json(config["url"])
            rows = [
                {
                    "league": league,
                    "species_id": str(row.get("speciesId", "")).strip().lower(),
                    "species_name": str(row.get("speciesName", "")).strip(),
                    "rating": row.get("rating"),
                    "rank_position": index,
                    "extracted_at": extracted_at,
                }
                for index, row in enumerate(raw_rows, start=1)
            ]
            rankings[league] = pd.DataFrame(rows)

        return rankings

    def fetch_gamemaster(self) -> dict:
        gamemaster = self.fetch_json(GAMEMASTER_URL)
        if not isinstance(gamemaster, dict):
            raise TypeError("PvPoke gamemaster response must be a JSON object.")
        return gamemaster
