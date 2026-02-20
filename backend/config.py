import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- LLM ---
OPENAI_MODEL = "gpt-5-mini"

# --- External API URLs ---
AOE4WORLD_BASE = "https://aoe4world.com/api/v0"
AOE4DATA_BASE = "https://data.aoe4world.com"
AOE4GUIDES_BASE = "https://aoe4guides.com"
WIKI_BASE = "https://ageofempires.fandom.com/api.php"
LIQUIPEDIA_BASE = "https://liquipedia.net/ageofempires/api.php"

# --- Rate limits ---
LIQUIPEDIA_MIN_INTERVAL = 2.0  # seconds between requests

# --- Cache TTLs (seconds) ---
CACHE_TTL_STATS = 3600      # 1 hour for civ stats/winrates
CACHE_TTL_PLAYERS = 300     # 5 minutes for player data
CACHE_TTL_WIKI = 86400      # 24 hours for wiki pages
CACHE_TTL_BUILDS = 3600     # 1 hour for build orders
CACHE_TTL_LIQUIPEDIA = 3600 # 1 hour for liquipedia

# --- Limits ---
MAX_TOOL_CALLS_PER_TURN = 8

# --- Civilization mappings ---
# Canonical names used by aoe4world API
CIVILIZATIONS = [
    "abbasid_dynasty", "ayyubids", "byzantines", "chinese",
    "delhi_sultanate", "english", "french", "holy_roman_empire",
    "japanese", "jeannes_darc", "malians", "mongols",
    "order_of_the_dragon", "ottomans", "rus", "zhuxis_legacy",
    "knights_templar", "house_of_lancaster", "golden_horde",
    "macedonian_dynasty", "sengoku_daimyo", "tughlaq_dynasty",
]

# User input -> aoe4world API name
CIV_ALIASES = {
    # English names / abbreviations
    "abbasid": "abbasid_dynasty", "abb": "abbasid_dynasty", "ab": "abbasid_dynasty",
    "abbasid dynasty": "abbasid_dynasty",
    "ayyubids": "ayyubids", "ayy": "ayyubids", "ay": "ayyubids",
    "byzantines": "byzantines", "byz": "byzantines", "by": "byzantines",
    "chinese": "chinese", "chi": "chinese", "ch": "chinese",
    "delhi": "delhi_sultanate", "delhi sultanate": "delhi_sultanate", "del": "delhi_sultanate", "de": "delhi_sultanate",
    "english": "english", "eng": "english", "en": "english",
    "french": "french", "fre": "french", "fr": "french",
    "hre": "holy_roman_empire", "holy roman empire": "holy_roman_empire",
    "hr": "holy_roman_empire", "hl": "holy_roman_empire",
    "japanese": "japanese", "jap": "japanese", "ja": "japanese",
    "jeanne": "jeannes_darc", "jeanne d'arc": "jeannes_darc", "jda": "jeannes_darc", "je": "jeannes_darc",
    "malians": "malians", "mal": "malians", "ma": "malians",
    "mongols": "mongols", "mon": "mongols", "mo": "mongols",
    "order of the dragon": "order_of_the_dragon", "ootd": "order_of_the_dragon",
    "otd": "order_of_the_dragon", "od": "order_of_the_dragon", "dragon": "order_of_the_dragon",
    "ottomans": "ottomans", "ott": "ottomans", "ot": "ottomans",
    "rus": "rus", "ru": "rus",
    "zhu xi": "zhuxis_legacy", "zhu xi's legacy": "zhuxis_legacy", "zxl": "zhuxis_legacy", "zx": "zhuxis_legacy",
    "knights templar": "knights_templar", "kt": "knights_templar", "templar": "knights_templar",
    "house of lancaster": "house_of_lancaster", "lancaster": "house_of_lancaster", "hol": "house_of_lancaster",
    "golden horde": "golden_horde", "gol": "golden_horde",
    "macedonian dynasty": "macedonian_dynasty", "macedonians": "macedonian_dynasty", "mac": "macedonian_dynasty",
    "sengoku": "sengoku_daimyo", "sengoku daimyo": "sengoku_daimyo", "sen": "sengoku_daimyo",
    "tughlaq": "tughlaq_dynasty", "tughlaq dynasty": "tughlaq_dynasty", "tug": "tughlaq_dynasty",
    # Spanish names
    "ingleses": "english", "franceses": "french", "mongoles": "mongols",
    "chinos": "chinese", "japoneses": "japanese", "otomanos": "ottomans",
    "bizantinos": "byzantines", "sacro imperio": "holy_roman_empire",
    "sultanato de delhi": "delhi_sultanate", "malienses": "malians",
}

# aoe4guides.com uses different codes
GUIDES_CIV_MAP = {
    "english": "ENG", "french": "FRE", "holy_roman_empire": "HRE",
    "mongols": "MON", "chinese": "CHI", "delhi_sultanate": "DEL",
    "rus": "RUS", "abbasid_dynasty": "ABB", "ottomans": "OTT",
    "malians": "MAL", "japanese": "JAP", "byzantines": "BYZ",
    "ayyubids": "AYY", "jeannes_darc": "JDA", "order_of_the_dragon": "OTD",
    "zhuxis_legacy": "ZXL", "knights_templar": "KTE",
}

# Display names
CIV_DISPLAY_NAMES = {
    "abbasid_dynasty": "Abbasid Dynasty", "ayyubids": "Ayyubids",
    "byzantines": "Byzantines", "chinese": "Chinese",
    "delhi_sultanate": "Delhi Sultanate", "english": "English",
    "french": "French", "holy_roman_empire": "Holy Roman Empire",
    "japanese": "Japanese", "jeannes_darc": "Jeanne d'Arc",
    "malians": "Malians", "mongols": "Mongols",
    "order_of_the_dragon": "Order of the Dragon", "ottomans": "Ottomans",
    "rus": "Rus", "zhuxis_legacy": "Zhu Xi's Legacy",
    "knights_templar": "Knights Templar", "house_of_lancaster": "House of Lancaster",
    "golden_horde": "Golden Horde", "macedonian_dynasty": "Macedonian Dynasty",
    "sengoku_daimyo": "Sengoku Daimyo", "tughlaq_dynasty": "Tughlaq Dynasty",
}


def resolve_civ(name: str) -> str | None:
    """Resolve a user-provided civilization name to the canonical aoe4world API name."""
    if not name:
        return None
    key = name.lower().strip()
    if key in CIVILIZATIONS:
        return key
    return CIV_ALIASES.get(key)
