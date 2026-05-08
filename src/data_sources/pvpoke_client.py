"""
PvPoke API client for fetching Pokemon GO PvP rankings.

This module provides a client to fetch rankings from PvPoke's GitHub repository.
Data is cached to minimize network requests and respect rate limits.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import requests
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PvPokeClient:
    """
    Client for fetching Pokemon rankings from PvPoke.
    
    Data source: GitHub raw files (JSON format)
    Supports: Great League (1500), Ultra League (2500), Master League (10000)
    """
    
    BASE_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings"
    
    # League configurations
    LEAGUES = {
        'great': {'cp': 1500, 'name': 'Great League'},
        'ultra': {'cp': 2500, 'name': 'Ultra League'},
        'master': {'cp': 10000, 'name': 'Master League'}
    }
    
    def __init__(self, cache_enabled: bool = True, cache_expire_hours: int = 24):
        """
        Initialize PvPoke client.
        
        Args:
            cache_enabled: Whether to use HTTP caching.
            cache_expire_hours: Hours before cache expires.
        """
        self.cache_enabled = cache_enabled
        self.cache_expire_hours = cache_expire_hours
        
        # Setup cache directory
        self.cache_dir = Path("cache/pvpoke")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup session with caching
        if cache_enabled:
            cache_path = self.cache_dir / 'http_cache'
            self.session = requests_cache.CachedSession(
                str(cache_path),
                expire_after=timedelta(hours=cache_expire_hours),
                backend='sqlite'
            )
            logger.info(f"HTTP cache enabled: {cache_path}")
        else:
            self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        logger.info("PvPokeClient initialized")
    
    def fetch_league_rankings(
        self, 
        league: str, 
        limit: Optional[int] = None,
        cup: str = "all"
    ) -> List[Dict]:
        """
        Fetch rankings for a specific league.
        
        Args:
            league: League name ('great', 'ultra', 'master').
            limit: Maximum number of Pokemon to return (None = all).
            cup: Cup/meta format ('all' for overall rankings).
        
        Returns:
            List of Pokemon with rankings:
            [
                {
                    "speciesId": "azumarill",
                    "speciesName": "Azumarill",
                    "rating": 182.5,
                    "rank": 1
                },
                ...
            ]
        
        Raises:
            ValueError: If league name is invalid.
            requests.RequestException: If API request fails.
        """
        if league not in self.LEAGUES:
            raise ValueError(
                f"Invalid league '{league}'. Must be one of: {list(self.LEAGUES.keys())}"
            )
        
        cp_limit = self.LEAGUES[league]['cp']
        league_name = self.LEAGUES[league]['name']
        
        # Construct URL
        url = f"{self.BASE_URL}/{cup}/overall/rankings-{cp_limit}.json"
        
        logger.info(f"Fetching {league_name} rankings from PvPoke...")
        logger.debug(f"URL: {url}")
        
        try:
            # Make request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if from cache
            is_cached = getattr(response, 'from_cache', False)
            cache_status = "💾 [CACHED]" if is_cached else "🌐 [FRESH]"
            logger.info(f"{cache_status} Retrieved {league_name} rankings")
            
            # Parse JSON
            data = response.json()
            
            # Add rank field (1-indexed)
            for idx, pokemon in enumerate(data, start=1):
                pokemon['rank'] = idx
            
            # Apply limit if specified
            if limit:
                data = data[:limit]
                logger.info(f"Limited to top {limit} Pokemon")
            
            logger.info(f"✅ Fetched {len(data)} Pokemon for {league_name}")
            return data
        
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {league_name} rankings: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def fetch_all_rankings(
        self, 
        limits: Optional[Dict[str, int]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Fetch rankings for all leagues at once.
        
        Args:
            limits: Dictionary mapping league names to top N limits.
                   Example: {'great': 200, 'ultra': 250, 'master': 300}
                   If None, fetches all rankings.
        
        Returns:
            Dictionary mapping league names to ranking lists:
            {
                'great': [{...}, {...}],
                'ultra': [{...}, {...}],
                'master': [{...}, {...}]
            }
        """
        if limits is None:
            limits = {league: None for league in self.LEAGUES.keys()}
        
        logger.info("🚀 Fetching rankings for all leagues...")
        
        results = {}
        for league in self.LEAGUES.keys():
            limit = limits.get(league, None)
            
            try:
                rankings = self.fetch_league_rankings(league, limit=limit)
                results[league] = rankings
                
                # Rate limiting: be nice to GitHub
                time.sleep(0.5)
            
            except Exception as e:
                logger.error(f"Failed to fetch {league} league: {e}")
                results[league] = []
        
        total_pokemon = sum(len(r) for r in results.values())
        logger.info(f"✨ Fetched {total_pokemon} total Pokemon across all leagues")
        
        return results
    
    def get_pokemon_details(self, species_id: str, league: str = 'great') -> Optional[Dict]:
        """
        Get detailed information for a specific Pokemon in a league.
        
        Args:
            species_id: Pokemon identifier (e.g., 'azumarill', 'registeel').
            league: League to get ranking for.
        
        Returns:
            Pokemon details dict if found, None otherwise.
        """
        rankings = self.fetch_league_rankings(league, limit=None)
        
        for pokemon in rankings:
            if pokemon['speciesId'] == species_id:
                logger.debug(f"Found {species_id} in {league} league at rank {pokemon['rank']}")
                return pokemon
        
        logger.warning(f"{species_id} not found in {league} league rankings")
        return None
    
    def clear_cache(self):
        """Clear HTTP cache."""
        if self.cache_enabled:
            self.session.cache.clear()
            logger.info("🗑️ Cache cleared")
        else:
            logger.warning("Cache not enabled, nothing to clear")
    
    def get_cache_info(self) -> Dict:
        """
        Get information about cache status.
        
        Returns:
            Dictionary with cache statistics.
        """
        if not self.cache_enabled:
            return {'enabled': False}
        
        cache_path = self.cache_dir / 'http_cache.sqlite'
        
        info = {
            'enabled': True,
            'path': str(cache_path),
            'exists': cache_path.exists(),
            'size_mb': cache_path.stat().st_size / 1024 / 1024 if cache_path.exists() else 0,
            'expire_hours': self.cache_expire_hours
        }
        
        return info


# Example usage and testing
if __name__ == "__main__":
    from src.utils.logger import setup_logger
    
    # Setup logger for testing
    logger = setup_logger(__name__, level="DEBUG")
    
    # Create client
    client = PvPokeClient(cache_enabled=True, cache_expire_hours=24)
    
    # Test 1: Fetch Great League top 10
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Fetch Great League top 10")
    logger.info("="*50)
    
    great_top_10 = client.fetch_league_rankings('great', limit=10)
    
    for pokemon in great_top_10[:5]:
        print(f"{pokemon['rank']:3d}. {pokemon['speciesName']:20s} (Rating: {pokemon.get('rating', 'N/A')})")
    
    # Test 2: Fetch all leagues with limits
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Fetch all leagues")
    logger.info("="*50)
    
    all_rankings = client.fetch_all_rankings({
        'great': 50,
        'ultra': 50,
        'master': 30
    })
    
    for league, rankings in all_rankings.items():
        print(f"\n{league.upper()} League: {len(rankings)} Pokemon")
        if rankings:
            print(f"  #1: {rankings[0]['speciesName']}")
    
    # Test 3: Get specific Pokemon details
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Get Azumarill details")
    logger.info("="*50)
    
    azumarill = client.get_pokemon_details('azumarill', 'great')
    if azumarill:
        print(f"\nAzumarill in Great League:")
        print(f"  Rank: {azumarill['rank']}")
        print(f"  Rating: {azumarill.get('rating', 'N/A')}")
    
    # Test 4: Cache info
    logger.info("\n" + "="*50)
    logger.info("TEST 4: Cache information")
    logger.info("="*50)
    
    cache_info = client.get_cache_info()
    print(f"\nCache Info:")
    for key, value in cache_info.items():
        print(f"  {key}: {value}")
