"""
Static data for Pokemon GO that doesn't change frequently.

This module contains hardcoded lists of Pokemon categories:
- Pseudo-legendaries
- Starter Pokemon (final evolutions)
- Regional forms
- Mega evolution priorities
- Baby Pokemon mappings
"""

from typing import Dict, List, Set


class StaticData:
    """
    Static Pokemon data that doesn't require API calls.
    
    This includes special categories, form variations, and
    other Pokemon classifications that are relatively stable.
    """
    
    # === VALUABLE POKEMON (Always Keep) ===
    
    PSEUDO_LEGENDARIES: List[str] = [
        # Gen 1
        'dragonite',
        
        # Gen 2
        'tyranitar',
        
        # Gen 3
        'salamence',
        'metagross',
        
        # Gen 4
        'garchomp',
        
        # Gen 5
        'hydreigon',
        
        # Gen 6
        'goodra',
        
        # Gen 7
        'kommo-o',
        
        # Gen 8
        'dragapult',
        
        # Gen 9
        'baxcalibur'
    ]
    
    STARTER_FINALS: List[str] = [
        # Gen 1 - Kanto
        'venusaur', 'charizard', 'blastoise',
        
        # Gen 2 - Johto
        'meganium', 'typhlosion', 'feraligatr',
        
        # Gen 3 - Hoenn
        'sceptile', 'blaziken', 'swampert',
        
        # Gen 4 - Sinnoh
        'torterra', 'infernape', 'empoleon',
        
        # Gen 5 - Unova
        'serperior', 'emboar', 'samurott',
        
        # Gen 6 - Kalos
        'chesnaught', 'delphox', 'greninja',
        
        # Gen 7 - Alola
        'decidueye', 'incineroar', 'primarina',
        
        # Gen 8 - Galar
        'rillaboom', 'cinderace', 'inteleon',
        
        # Gen 9 - Paldea
        'meowscarada', 'skeledirge', 'quaquaval'
    ]
    
    # Pokemon with Mega Evolutions that are meta-relevant
    MEGA_PRIORITY: List[str] = [
        'rayquaza',
        'lucario',
        'garchomp',
        'salamence',
        'metagross',
        'blaziken',
        'gengar',
        'gardevoir',
        'charizard',
        'mewtwo',
        'tyranitar',
        'gyarados',
        'alakazam',
        'swampert',
        'sceptile',
        'latios',
        'latias'
    ]
    
    # === FORM VARIATIONS ===
    
    REGIONAL_FORMS: List[str] = [
        'alolan',
        'galarian',
        'hisuian',
        'paldean'
    ]
    
    # Pokemon with multiple forms that affect stats
    FORM_VARIATIONS: Dict[str, List[str]] = {
        'deoxys': ['normal', 'attack', 'defense', 'speed'],
        'giratina': ['altered', 'origin'],
        'shaymin': ['land', 'sky'],
        'tornadus': ['incarnate', 'therian'],
        'thundurus': ['incarnate', 'therian'],
        'landorus': ['incarnate', 'therian'],
        'enamorus': ['incarnate', 'therian'],
        'kyurem': ['normal', 'black', 'white'],
        'necrozma': ['normal', 'dusk-mane', 'dawn-wings', 'ultra'],
        'zygarde': ['10%', '50%', 'complete'],
        'hoopa': ['confined', 'unbound'],
        'oricorio': ['baile', 'pom-pom', 'pau', 'sensu'],
        'lycanroc': ['midday', 'midnight', 'dusk'],
        'wishiwashi': ['solo', 'school'],
        'minior': ['meteor', 'core'],
    }
    
    # Cosmetic forms (same stats, different appearance)
    COSMETIC_FORMS: List[str] = [
        'spinda',      # 4 billion+ patterns
        'unown',       # 28 letters
        'vivillon',    # Regional wing patterns
        'furfrou',     # Trims
        'flabebe',     # Flower colors (if same color)
        'shellos',     # East/West (same stats)
        'gastrodon',   # East/West (same stats)
        'deerling',    # Seasonal (same stats)
        'sawsbuck',    # Seasonal (same stats)
    ]
    
    # === BABY POKEMON (Need special handling for evolution chains) ===
    
    BABY_POKEMON_MAP: Dict[str, str] = {
        # Baby -> Evolution
        'pichu': 'pikachu',
        'cleffa': 'clefairy',
        'igglybuff': 'jigglypuff',
        'togepi': 'togetic',
        'tyrogue': 'hitmonlee',  # Or hitmonchan, hitmontop
        'smoochum': 'jynx',
        'elekid': 'electabuzz',
        'magby': 'magmar',
        'azurill': 'marill',
        'wynaut': 'wobbuffet',
        'budew': 'roselia',
        'chingling': 'chimecho',
        'bonsly': 'sudowoodo',
        'mime-jr': 'mr-mime',
        'happiny': 'chansey',
        'munchlax': 'snorlax',
        'riolu': 'lucario',
        'mantyke': 'mantine',
        'toxel': 'toxtricity',
    }
    
    # Reverse mapping: Evolution -> Baby
    EVOLUTION_TO_BABY_MAP: Dict[str, str] = {
        v: k for k, v in BABY_POKEMON_MAP.items()
    }
    
    # === LEGENDARY POKEMON ===
    
    LEGENDARY_POKEMON: List[str] = [
        # Gen 1
        'articuno', 'zapdos', 'moltres', 'mewtwo',
        
        # Gen 2
        'raikou', 'entei', 'suicune', 'lugia', 'ho-oh',
        
        # Gen 3
        'regirock', 'regice', 'registeel', 'latias', 'latios',
        'kyogre', 'groudon', 'rayquaza',
        
        # Gen 4
        'uxie', 'mesprit', 'azelf', 'dialga', 'palkia',
        'heatran', 'regigigas', 'giratina', 'cresselia',
        
        # Gen 5
        'cobalion', 'terrakion', 'virizion', 'tornadus',
        'thundurus', 'reshiram', 'zekrom', 'landorus',
        'kyurem',
        
        # Gen 6
        'xerneas', 'yveltal', 'zygarde',
        
        # Gen 7
        'tapu-koko', 'tapu-lele', 'tapu-bulu', 'tapu-fini',
        'cosmog', 'cosmoem', 'solgaleo', 'lunala', 'necrozma',
        
        # Gen 8
        'zacian', 'zamazenta', 'eternatus', 'regieleki', 'regidrago',
        'glastrier', 'spectrier', 'calyrex',
        
        # Gen 9
        'wo-chien', 'chien-pao', 'ting-lu', 'chi-yu',
        'koraidon', 'miraidon'
    ]
    
    MYTHICAL_POKEMON: List[str] = [
        'mew', 'celebi', 'jirachi', 'deoxys',
        'phione', 'manaphy', 'darkrai', 'shaymin', 'arceus',
        'victini', 'keldeo', 'meloetta', 'genesect',
        'diancie', 'hoopa', 'volcanion',
        'magearna', 'marshadow', 'zeraora', 'meltan', 'melmetal',
        'zarude', 'pecharunt'
    ]
    
    # === USELESS POKEMON (Common Blacklist Candidates) ===
    
    ROUTE_COMMONS: List[str] = [
        'bidoof', 'patrat', 'lillipup', 'bunnelby',
        'yungoos', 'skwovet', 'lechonk'
    ]
    
    EARLY_BUGS: List[str] = [
        'caterpie', 'weedle', 'wurmple', 'kricketot',
        'sewaddle', 'scatterbug', 'grubbin', 'blipbug',
        'tarountula'
    ]
    
    WATER_TRASH: List[str] = [
        'luvdisc', 'finneon', 'basculin', 'wishiwashi',
        'arrokuda'
    ]
    
    # === HELPER METHODS ===
    
    @classmethod
    def get_all_valuable_pokemon(cls) -> Set[str]:
        """
        Get combined set of all valuable Pokemon.
        
        Returns:
            Set of Pokemon species IDs that should always be kept.
        """
        valuable = set()
        valuable.update(cls.PSEUDO_LEGENDARIES)
        valuable.update(cls.STARTER_FINALS)
        valuable.update(cls.MEGA_PRIORITY)
        valuable.update(cls.LEGENDARY_POKEMON)
        valuable.update(cls.MYTHICAL_POKEMON)
        return valuable
    
    @classmethod
    def get_common_trash(cls) -> Set[str]:
        """
        Get combined set of commonly transferred Pokemon.
        
        Returns:
            Set of Pokemon species IDs that are safe to transfer.
        """
        trash = set()
        trash.update(cls.ROUTE_COMMONS)
        trash.update(cls.EARLY_BUGS)
        trash.update(cls.WATER_TRASH)
        return trash
    
    @classmethod
    def is_regional_form(cls, form_name: str) -> bool:
        """
        Check if a form name is a regional variant.
        
        Args:
            form_name: Form name to check (e.g., 'alolan', 'galarian').
        
        Returns:
            True if it's a regional form.
        """
        return form_name.lower() in [f.lower() for f in cls.REGIONAL_FORMS]
    
    @classmethod
    def has_form_variations(cls, species_id: str) -> bool:
        """
        Check if a Pokemon has form variations that affect stats.
        
        Args:
            species_id: Pokemon species ID.
        
        Returns:
            True if Pokemon has meaningful form variations.
        """
        return species_id in cls.FORM_VARIATIONS
    
    @classmethod
    def get_baby_for_evolution(cls, species_id: str) -> str | None:
        """
        Get baby form for a Pokemon if it exists.
        
        Args:
            species_id: Evolved Pokemon species ID.
        
        Returns:
            Baby Pokemon species ID if exists, None otherwise.
        """
        return cls.EVOLUTION_TO_BABY_MAP.get(species_id)


# Example usage
if __name__ == "__main__":
    print("=== Static Data Examples ===\n")
    
    print(f"Pseudo-Legendaries: {len(StaticData.PSEUDO_LEGENDARIES)}")
    print(f"  Examples: {', '.join(StaticData.PSEUDO_LEGENDARIES[:5])}")
    
    print(f"\nStarter Finals: {len(StaticData.STARTER_FINALS)}")
    print(f"  Gen 1: {', '.join(StaticData.STARTER_FINALS[:3])}")
    
    print(f"\nTotal Valuable Pokemon: {len(StaticData.get_all_valuable_pokemon())}")
    
    print(f"\nCommon Trash: {len(StaticData.get_common_trash())}")
    print(f"  Examples: {', '.join(list(StaticData.get_common_trash())[:5])}")
    
    print(f"\nGiratina has forms? {StaticData.has_form_variations('giratina')}")
    if StaticData.has_form_variations('giratina'):
        print(f"  Forms: {StaticData.FORM_VARIATIONS['giratina']}")
    
    print(f"\nBaby for Lucario: {StaticData.get_baby_for_evolution('lucario')}")
