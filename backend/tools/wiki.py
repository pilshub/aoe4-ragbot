"""Tools for searching the AoE Fandom wiki."""

import json
from config import WIKI_BASE, CACHE_TTL_WIKI
from cache import cache
from utils import fetch_json, clean_wikitext, truncate
from models import Source


async def search_wiki(query: str) -> tuple[str, list[Source]]:
    """Search the Age of Empires Fandom wiki."""
    cache_key = f"wiki_search:{query.lower()}"
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
    data = await fetch_json(WIKI_BASE, params)
    if data is None:
        return "Error: Could not search the AoE wiki.", []

    results = data.get("query", {}).get("search", [])
    if not results:
        return f"No wiki pages found for '{query}'.", []

    lines = [f"## Wiki results for '{query}'", ""]
    for r in results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        # Clean HTML from snippet
        import re
        snippet_clean = re.sub(r"<[^>]+>", "", snippet)
        url = f"https://ageofempires.fandom.com/wiki/{title.replace(' ', '_')}"
        lines.append(f"### [{title}]({url})")
        lines.append(f"{snippet_clean}")
        lines.append("")

    result = "\n".join(lines)
    sources = [Source(
        type="wiki",
        title=f"Wiki search: {query}",
        url=f"https://ageofempires.fandom.com/wiki/Special:Search?query={query}",
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_WIKI)
    return result, sources


async def get_wiki_page(title: str) -> tuple[str, list[Source]]:
    """Get the content of a specific wiki page."""
    cache_key = f"wiki_page:{title.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext",
        "format": "json",
    }
    data = await fetch_json(WIKI_BASE, params)
    if data is None:
        return f"Error: Could not fetch wiki page '{title}'.", []

    parse = data.get("parse", {})
    if not parse:
        error = data.get("error", {}).get("info", "Page not found")
        return f"Wiki page '{title}' not found: {error}", []

    wikitext = parse.get("wikitext", {})
    if isinstance(wikitext, dict):
        text = wikitext.get("*", "")
    else:
        text = str(wikitext)

    clean = clean_wikitext(text)
    clean = truncate(clean, 3000)

    url = f"https://ageofempires.fandom.com/wiki/{title.replace(' ', '_')}"
    result = f"## {title}\n\n{clean}"
    sources = [Source(
        type="wiki",
        title=title,
        url=url,
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_WIKI)
    return result, sources
