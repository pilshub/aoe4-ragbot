"""Tool registry mapping tool names to their implementation functions."""

from tools.aoe4world_stats import get_civ_stats, get_matchup_stats, get_map_stats
from tools.aoe4world_players import search_player, get_player_profile, get_player_matches
from tools.aoe4world_leaderboards import get_leaderboard
from tools.aoe4world_esports import get_esports_leaderboard
from tools.game_data import query_unit_stats, query_building_stats, query_technology, compare_units
from tools.build_orders import search_build_orders
from tools.liquipedia import search_liquipedia
from tools.ageups import get_ageup_stats
from tools.knowledge_base import search_pro_content
from tools.aoe4world_patches import get_patch_notes

TOOL_REGISTRY = {
    "get_civ_stats": get_civ_stats,
    "get_matchup_stats": get_matchup_stats,
    "get_map_stats": get_map_stats,
    "search_player": search_player,
    "get_player_profile": get_player_profile,
    "get_player_matches": get_player_matches,
    "get_leaderboard": get_leaderboard,
    "get_esports_leaderboard": get_esports_leaderboard,
    "query_unit_stats": query_unit_stats,
    "query_building_stats": query_building_stats,
    "query_technology": query_technology,
    "compare_units": compare_units,
    "search_build_orders": search_build_orders,
    "search_liquipedia": search_liquipedia,
    "get_ageup_stats": get_ageup_stats,
    "search_pro_content": search_pro_content,
    "get_patch_notes": get_patch_notes,
}
