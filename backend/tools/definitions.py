"""OpenAI tool/function JSON schemas for all 16 tools."""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_civ_stats",
            "description": "Get win rate, pick rate, and game count statistics for all civilizations in a specific game mode. Can filter by ELO/rank level, patch version, and map.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["rm_solo", "rm_2v2", "rm_3v3", "rm_4v4", "qm_1v1", "qm_2v2", "qm_3v3", "qm_4v4"],
                        "description": "Game mode. rm_solo = Ranked 1v1, rm_2v2/rm_3v3/rm_4v4 = Ranked Team, qm_1v1 = Quick Match 1v1, qm_2v2/3v3/4v4 = Quick Match Team. For 'team games' use rm_2v2 or rm_4v4.",
                    },
                    "map": {"type": "string", "description": "Filter by map name (e.g. 'four_lakes', 'dry_arabia', 'rocky_river', 'hideout', 'ancient_spires'). Use underscores."},
                    "patch": {"type": "string", "description": "Patch version number. Omit for current patch."},
                    "rank_level": {"type": "string", "description": "Filter by rank: bronze, silver, gold, platinum, diamond, conqueror."},
                    "rating_min": {"type": "integer", "description": "Minimum ELO rating to filter."},
                    "rating_max": {"type": "integer", "description": "Maximum ELO rating to filter."},
                },
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_matchup_stats",
            "description": "Get head-to-head win rate statistics between two specific civilizations. Can filter by map to see matchup on a specific map.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["rm_solo", "rm_2v2", "rm_3v3", "rm_4v4", "qm_1v1", "qm_2v2", "qm_3v3", "qm_4v4"],
                    },
                    "civ1": {"type": "string", "description": "First civilization name (e.g. 'english', 'French', 'mongols')"},
                    "civ2": {"type": "string", "description": "Second civilization name"},
                    "map": {"type": "string", "description": "Filter by map name (e.g. 'four_lakes', 'dry_arabia', 'rocky_river'). Use underscores."},
                    "patch": {"type": "string"},
                    "rank_level": {"type": "string"},
                },
                "required": ["mode", "civ1", "civ2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_map_stats",
            "description": "Get statistics for maps including games played and which civilizations perform best on each map.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["rm_solo", "rm_2v2", "rm_3v3", "rm_4v4", "qm_1v1", "qm_2v2", "qm_3v3", "qm_4v4"],
                    },
                    "map_name": {"type": "string", "description": "Optional map name to filter (e.g. 'Dry Arabia', 'Rocky River')"},
                    "patch": {"type": "string"},
                },
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_player",
            "description": "Search for a player by name. Returns matching players with their profile IDs and ratings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Player name to search for (minimum 3 characters)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_player_profile",
            "description": "Get detailed profile for a player including ratings, win rates, and stats. Use search_player first to get the profile_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_id": {"type": "string", "description": "The player's profile_id from aoe4world"},
                },
                "required": ["profile_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_player_matches",
            "description": "Get recent match history for a player showing civilizations, opponents, results, and maps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_id": {"type": "string"},
                    "count": {"type": "integer", "description": "Number of matches (default 10, max 50)"},
                    "leaderboard": {"type": "string", "description": "Filter by game mode"},
                },
                "required": ["profile_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_leaderboard",
            "description": "Get the ranked leaderboard showing top players with their rating, rank, and win rate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["rm_solo", "rm_2v2", "rm_3v3", "rm_4v4", "qm_1v1", "qm_2v2", "qm_3v3", "qm_4v4"],
                    },
                    "page": {"type": "integer", "description": "Page number (default 1)"},
                    "country": {"type": "string", "description": "Filter by country code (e.g. 'de', 'kr', 'es')"},
                },
                "required": ["mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_esports_leaderboard",
            "description": "Get the esports/tournament ELO leaderboard showing pro players ranked by tournament performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "query": {"type": "string", "description": "Search for a specific pro player"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_unit_stats",
            "description": "Get detailed stats for a unit: HP, damage, armor, cost, speed, range, production time. Supports abbreviations like 'maa' (Man-at-Arms), 'xbow' (Crossbowman).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unit name or abbreviation"},
                    "civ": {"type": "string", "description": "Optional civilization for civ-specific variant"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_building_stats",
            "description": "Get detailed stats for a building or landmark: HP, cost, garrison capacity, production options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Building or landmark name"},
                    "civ": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_technology",
            "description": "Get details about a technology: what it does, cost, research time, which building researches it, age requirement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Technology name"},
                    "civ": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_units",
            "description": "Compare two units side-by-side showing HP, damage, armor, cost, speed, and range differences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit1": {"type": "string", "description": "First unit name"},
                    "unit2": {"type": "string", "description": "Second unit name"},
                    "civ": {"type": "string", "description": "Civilization context for civ-specific variants"},
                },
                "required": ["unit1", "unit2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_build_orders",
            "description": "Search for build orders (step-by-step strategy guides) for a civilization.",
            "parameters": {
                "type": "object",
                "properties": {
                    "civ": {"type": "string", "description": "Civilization name or code (e.g. 'english', 'ENG', 'French', 'MON')"},
                    "strategy": {"type": "string", "description": "Strategy type: Rush, Fast Castle, Boom"},
                    "count": {"type": "integer", "description": "Number of build orders (default 3, max 10)"},
                },
                "required": ["civ"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_liquipedia",
            "description": "Search Liquipedia for AoE4 esports: tournaments, pro player bios, team rosters, match results. Rate limited.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g. 'Red Bull Wololo', 'Beastyqt', 'tournaments 2026')"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ageup_stats",
            "description": "Get age-up timing analytics for civilizations: average, fastest, and most common times to reach Feudal, Castle, and Imperial ages. Shows win rates per landmark path (e.g. 'French who pick School of Cavalry reach Feudal at 4:44 avg with 51% winrate'). Can filter by rank/ELO to compare timings across skill levels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "civilization": {"type": "string", "description": "Civilization name (e.g. 'french', 'english', 'mongols'). Omit for all civs comparison."},
                    "mode": {
                        "type": "string",
                        "enum": ["rm_solo", "rm_2v2", "rm_3v3", "rm_4v4", "qm_1v1", "qm_2v2", "qm_3v3", "qm_4v4"],
                        "description": "Game mode. Default: rm_solo.",
                    },
                    "rank_level": {"type": "string", "description": "Filter by rank: bronze, silver, gold, platinum, diamond, conqueror. Useful to compare timings across skill levels."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_pro_content",
            "description": "Search YouTube transcripts from pro AoE4 players (Beastyqt, Valdemar, Vortix, MarineLorD) for strategy guides, tier lists, tips, build order explanations, and meta analysis. Use this when users ask about strategies, opinions, or advice from pro players, or when other tools don't have subjective/strategic information. Returns relevant excerpts with YouTube timestamp links.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing what information to find (e.g. 'french knight rush strategy', 'best civilization for beginners', 'how to counter english longbows')",
                    },
                    "channel": {
                        "type": "string",
                        "enum": ["Beastyqt", "Valdemar", "Vortix", "MarineLorD"],
                        "description": "Filter results to a specific pro player's content. Omit to search all channels.",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["en", "es"],
                        "description": "Filter by language. 'es' for Vortix's Spanish content. Omit to search all languages.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_patch_notes",
            "description": "Get information about AoE4 patches and game seasons. Shows current patch version and season. Use when users ask about current meta changes, what patch we're on, season info, or game version.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "string",
                        "description": "Specific patch version to look up. Omit for current/latest.",
                    },
                },
                "required": [],
            },
        },
    },
]
