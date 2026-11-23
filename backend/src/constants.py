"""Shared configuration for the Pokemon GO PvP ETL."""

from pathlib import Path


GL_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-1500.json"
UL_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-2500.json"
ML_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-10000.json"
GAMEMASTER_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/gamemaster.json"

LEAGUES = {
    "GL": {"name": "Great League", "url": GL_URL, "top_n": 150},
    "UL": {"name": "Ultra League", "url": UL_URL, "top_n": 100},
    "ML": {"name": "Master League", "url": ML_URL, "top_n": 40},
}

HTTP_TIMEOUT = 30
DB_PATH = Path("cache") / "pokemon_go_pvp.sqlite"

# In-game search terms only work in the language the game is set to.
# "en" comes from Niantic's help page. "pt" was NOT verified in-game: it was
# compiled from third-party lists, so the UI flags it as untested.
SEARCH_TERMS = {
    "en": {
        "shiny": "shiny",
        "lucky": "lucky",
        "shadow": "shadow",
        "purified": "purified",
        "legendary": "legendary",
        "mythical": "mythical",
        "costume": "costume",
        "special": "@special",
    },
    "pt": {
        "shiny": "brilhante",
        "lucky": "sortudo",
        "shadow": "sombroso",
        "purified": "purificado",
        "legendary": "lendário",
        "mythical": "mítico",
        "costume": "traje",
        "special": "@especial",
    },
}
DEFAULT_LANG = "en"
PROTECTED_TERM_KEYS = (
    "shiny",
    "lucky",
    "shadow",
    "purified",
    "legendary",
    "mythical",
    "costume",
)


def build_transfer_suffix(lang: str = DEFAULT_LANG) -> str:
    terms = SEARCH_TERMS[lang]
    protected = "".join(f"&!{terms[key]}" for key in PROTECTED_TERM_KEYS)
    return f"{protected}&!4*&!3*&!{terms['special']}"


TRANSFER_SUFFIX = build_transfer_suffix("en")
REGION_SEARCH_TERMS = ("alola", "galar", "hisui", "paldea")

REGION_TOKENS = {
    "alola": "alola",
    "alolan": "alola",
    "galar": "galar",
    "galarian": "galar",
    "hisui": "hisui",
    "hisuian": "hisui",
    "paldea": "paldea",
    "paldean": "paldea",
}

REGION_LABELS = {
    "base": "Base/Kanto",
    "alola": "Alola",
    "galar": "Galar",
    "hisui": "Hisui",
    "paldea": "Paldea",
}

PVP_ID_IGNORED_TOKENS = {
    "altered",
    "apex",
    "armored",
    "ash",
    "average",
    "black",
    "complete",
    "dawn",
    "defense",
    "dusk",
    "east",
    "fifty",
    "flying",
    "hero",
    "incarnate",
    "large",
    "legacy",
    "mega",
    "midday",
    "midnight",
    "origin",
    "overcast",
    "plant",
    "primal",
    "purified",
    "rainy",
    "shadow",
    "small",
    "standard",
    "sunny",
    "sunshine",
    "therian",
    "west",
    "white",
    "xl",
}

PVP_SPECIES_ALIASES = {
    "ho_oh": "ho-oh",
    "jangmo_o": "jangmo-o",
    "hakamo_o": "hakamo-o",
    "kommo_o": "kommo-o",
    "mime_jr": "mime-jr",
    "mr_mime": "mr-mime",
    "mr_rime": "mr-rime",
    "nidoran_female": "nidoran-f",
    "nidoran_male": "nidoran-m",
    "porygon_z": "porygon-z",
    "tapu_bulu": "tapu-bulu",
    "tapu_fini": "tapu-fini",
    "tapu_koko": "tapu-koko",
    "tapu_lele": "tapu-lele",
    "type_null": "type-null",
}

# Some regional evolutions have a neutral speciesId in PvPoke rankings
# (obstagoon, sirfetchd, perrserker), even though they belong to a regional
# branch. These overrides keep family propagation scoped to the regional branch.
REGION_LOCKED_SPECIES = {
    "cursola": "galar",
    "mr-rime": "galar",
    "obstagoon": "galar",
    "perrserker": "galar",
    "runerigus": "galar",
    "sirfetchd": "galar",
    "basculegion": "hisui",
    "kleavor": "hisui",
    "overqwil": "hisui",
    "sneasler": "hisui",
    "ursaluna": "hisui",
}

# The only evolution in the game that crosses regional forms: base Ursaring
# evolves into Hisuian Ursaluna. Keys are family_key values; the key branch is
# protected when any listed source branch is ranked.
CROSS_FORM_EVOLUTIONS = {
    "FAMILY_TEDDIURSA|base": ("FAMILY_TEDDIURSA|hisui",),
}
