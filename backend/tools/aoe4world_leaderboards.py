"""Tools for AoE4 World leaderboard rankings."""

import json
from config import AOE4WORLD_BASE, CACHE_TTL_STATS
from cache import cache
from utils import fetch_json, truncate
from models import Source


async def get_leaderboard(
    mode: str = "rm_solo",
    page: int = 1,
    country: str | None = None,
) -> tuple[str, list[Source]]:
    """Get the ranked leaderboard for a game mode."""
    params = {"page": page}
    if country:
        params["country"] = country.lower()

    cache_key = f"leaderboard:{mode}:{page}:{country}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{AOE4WORLD_BASE}/leaderboards/{mode}"
    data = await fetch_json(url, params)
    if data is None:
        return "Error: Could not fetch leaderboard from aoe4world.com.", []

    players = data.get("players", data) if isinstance(data, dict) else data

    country_note = f" ({country.upper()})" if country else ""
    lines = [f"## Leaderboard: {mode}{country_note} (Page {page})", ""]
    lines.append("| Rank | Player | Rating | Win Rate | Games |")
    lines.append("|------|--------|--------|----------|-------|")

    if isinstance(players, list):
        for p in players[:20]:
            rank = p.get("rank", "?")
            name = p.get("name", "Unknown")
            rating = p.get("rating", 0)
            wr = p.get("win_rate", 0)
            games = p.get("games_count", 0)
            flag = p.get("country", "")
            flag_str = f" [{flag.upper()}]" if flag else ""
            wr_pct = f"{wr * 100:.1f}%" if wr and wr < 1 else f"{wr:.1f}%" if wr else "N/A"
            lines.append(f"| #{rank} | {name}{flag_str} | {rating} | {wr_pct} | {games} |")
    else:
        lines.append(truncate(json.dumps(players, indent=2, default=str), 2000))

    result = "\n".join(lines)
    sources = [Source(
        type="aoe4world",
        title=f"Leaderboard ({mode})",
        url=f"https://aoe4world.com/leaderboards/{mode}",
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_STATS)
    return result, sources
