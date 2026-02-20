"""Tool for fetching AoE4 patch notes and season information."""

from config import AOE4WORLD_BASE, CACHE_TTL_WIKI
from cache import cache
from utils import fetch_json, truncate
from models import Source


async def get_patch_notes(
    patch: str | None = None,
) -> tuple[str, list[Source]]:
    """Get current season info and recent patch changes."""
    cache_key = f"patches:{patch or 'current'}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    sources = [Source(type="aoe4world", title="Patch information", url="https://aoe4world.com")]

    # Try the stats endpoint which includes patch metadata
    url = f"{AOE4WORLD_BASE}/stats/rm_solo/civilizations"
    data = await fetch_json(url)

    if data and isinstance(data, dict):
        patch_info = data.get("patch", data.get("patch_number", ""))
        season_info = data.get("season", data.get("season_number", ""))
        total_games = data.get("total_games", data.get("games_count", ""))

        if patch_info or season_info:
            lines = ["## Current AoE4 Game Version", ""]
            if patch_info:
                lines.append(f"- **Patch:** {patch_info}")
            if season_info:
                lines.append(f"- **Season:** {season_info}")
            if total_games:
                lines.append(f"- **Total ranked games tracked:** {total_games:,}" if isinstance(total_games, int) else f"- **Total ranked games tracked:** {total_games}")
            lines.append("")
            lines.append("For detailed patch notes, check the official Age of Empires website or the in-game news section.")

            result = "\n".join(lines)
            cache.set(cache_key, (result, sources), CACHE_TTL_WIKI)
            return result, sources

    # Fallback: try to get patch info from recent games
    url_games = f"{AOE4WORLD_BASE}/games"
    games_data = await fetch_json(url_games, {"limit": 1})

    if games_data and isinstance(games_data, dict):
        games = games_data.get("games", [])
        if games:
            game = games[0]
            current_patch = game.get("patch", "Unknown")
            current_season = game.get("season", "Unknown")
            started_at = game.get("started_at", "")

            lines = ["## Current AoE4 Game Version", ""]
            lines.append(f"- **Patch:** {current_patch}")
            if current_season and current_season != "Unknown":
                lines.append(f"- **Season:** {current_season}")
            if started_at:
                lines.append(f"- **Latest game tracked:** {started_at}")
            lines.append("")
            lines.append("For detailed patch notes with balance changes, check the official Age of Empires website.")

            result = "\n".join(lines)
            cache.set(cache_key, (result, sources), CACHE_TTL_WIKI)
            return result, sources

    return "Could not retrieve patch information at this time.", sources
