"""Tools for searching Liquipedia esports wiki (rate-limited)."""

from config import CACHE_TTL_LIQUIPEDIA
from cache import cache
from utils import fetch_json_liquipedia, truncate
from models import Source

import re


async def search_liquipedia(query: str) -> tuple[str, list[Source]]:
    """Search Liquipedia for AoE4 esports information."""
    cache_key = f"liquipedia_search:{query.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{query} Age of Empires IV",
        "srlimit": 5,
        "format": "json",
    }
    data = await fetch_json_liquipedia(params)
    if data is None:
        return "Error: Could not search Liquipedia (rate limited or unavailable).", []

    results = data.get("query", {}).get("search", [])
    if not results:
        return f"No Liquipedia pages found for '{query}'.", []

    lines = [f"## Liquipedia results for '{query}'", ""]
    for r in results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        snippet_clean = re.sub(r"<[^>]+>", "", snippet)
        url = f"https://liquipedia.net/ageofempires/{title.replace(' ', '_')}"
        lines.append(f"### [{title}]({url})")
        lines.append(f"{snippet_clean}")
        lines.append("")

    result = "\n".join(lines)
    sources = [Source(
        type="liquipedia",
        title=f"Liquipedia: {query}",
        url=f"https://liquipedia.net/ageofempires/index.php?search={query}",
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_LIQUIPEDIA)
    return result, sources
