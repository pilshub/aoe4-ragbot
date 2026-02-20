"""Tools for AoE4 World esports/tournament ELO leaderboard."""

import json
from config import AOE4WORLD_BASE, CACHE_TTL_STATS
from cache import cache
from utils import fetch_json, truncate
from models import Source


async def get_esports_leaderboard(
    page: int = 1,
    query: str | None = None,
) -> tuple[str, list[Source]]:
    """Get the esports tournament ELO leaderboard."""
    params = {"page": page}
    if query:
        params["query"] = query

    cache_key = f"esports_lb:{page}:{query}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{AOE4WORLD_BASE}/esports/leaderboards/1"
    data = await fetch_json(url, params)
    if data is None:
        return "Error: Could not fetch esports leaderboard from aoe4world.com.", []

    players = data.get("players", data) if isinstance(data, dict) else data

    lines = ["## Esports Tournament ELO Leaderboard", ""]
    lines.append("| Rank | Player | Tournament ELO |")
    lines.append("|------|--------|---------------|")

    if isinstance(players, list):
        for p in players[:20]:
            rank = p.get("rank", "?")
            name = p.get("name", "Unknown")
            rating = p.get("rating", p.get("elo", 0))
            flag = p.get("country", "")
            flag_str = f" [{flag.upper()}]" if flag else ""
            lines.append(f"| #{rank} | {name}{flag_str} | {rating} |")
    else:
        lines.append(truncate(json.dumps(players, indent=2, default=str), 2000))

    result = "\n".join(lines)
    sources = [Source(
        type="aoe4world",
        title="Esports leaderboard",
        url="https://aoe4world.com/esports/leaderboards/1",
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_STATS)
    return result, sources
