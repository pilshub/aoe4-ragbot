"""Tools for searching build orders from aoe4guides.com."""

import re
from config import AOE4GUIDES_BASE, CACHE_TTL_BUILDS, resolve_civ, GUIDES_CIV_MAP
from cache import cache
from utils import fetch_json, truncate
from models import Source

# Minimum scoreAllTime to consider a build worth showing
MIN_SCORE = 7.0

# Current game season (update when new season drops)
CURRENT_SEASON = 12


def _extract_season_number(season_str: str) -> int | None:
    """Extract season number from strings like 'Season 9'."""
    m = re.search(r'(\d+)', season_str or "")
    return int(m.group(1)) if m else None


def _recency_adjusted_score(build: dict) -> float:
    """Compute a score that balances quality (scoreAllTime) with recency (season).

    A build from the current season keeps its full score.
    Each season older applies a 10% penalty, down to a floor of 0.4x.
    This means a Season 5 classic (score 10.8) adjusts to ~4.3,
    while a Season 11 build (score 9.0) adjusts to ~8.1.
    """
    base = build.get("scoreAllTime", 0)
    season_num = _extract_season_number(build.get("season", ""))
    if season_num is None:
        return base * 0.5  # Unknown season — treat as old

    age = max(0, CURRENT_SEASON - season_num)
    factor = max(0.4, 1.0 - (age * 0.10))
    return base * factor


def _clean_step_html(text: str) -> str:
    """Strip HTML from step descriptions, converting img alt text to readable names."""
    # Replace img tags with their alt text (these contain unit/resource names)
    text = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*/?\s*>', r' \1 ', text)
    # Remove any remaining img or HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Clean HTML entities
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('-&gt;', '→')
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


async def search_build_orders(
    civ: str = "ANY",
    strategy: str | None = None,
    count: int = 3,
) -> tuple[str, list[Source]]:
    """Search for build orders by civilization and strategy type."""
    # Resolve civ to aoe4guides code
    canonical = resolve_civ(civ)
    guides_code = GUIDES_CIV_MAP.get(canonical, civ.upper()) if canonical else civ.upper()

    cache_key = f"builds:{guides_code}:{strategy}:{count}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Fetch top-rated builds (orderBy=scoreAllTime is critical for quality)
    url = f"{AOE4GUIDES_BASE}/api/builds"
    params = {"civ": guides_code, "orderBy": "scoreAllTime"}

    data = await fetch_json(url, params)
    if data is None:
        return "Error: Could not fetch build orders from aoe4guides.com.", []

    builds = data if isinstance(data, list) else data.get("builds", data.get("data", []))
    if not builds:
        return f"No build orders found for {civ}.", []

    # Filter out low-quality builds
    builds = [b for b in builds if b.get("scoreAllTime", 0) >= MIN_SCORE]

    # Re-sort by recency-adjusted score (newer quality builds float up)
    builds.sort(key=_recency_adjusted_score, reverse=True)

    # Filter by strategy if specified (client-side, API doesn't support it)
    if strategy and builds:
        strategy_lower = strategy.lower()
        # Match against strategy tag, title, and description
        filtered = [
            b for b in builds
            if strategy_lower in (b.get("strategy", "") or "").lower()
            or strategy_lower in (b.get("title", "") + " " + b.get("description", "")).lower()
        ]
        if filtered:
            builds = filtered

    if not builds:
        return f"No quality build orders found for {civ} (strategy: {strategy or 'any'}).", []

    lines = [f"## Top Build Orders ({civ})", ""]

    for b in builds[:count]:
        title = b.get("title", "Untitled")
        author = b.get("author", "Unknown")
        description = b.get("description", "")
        build_id = b.get("id", b.get("_id", ""))
        civ_name = b.get("civ", guides_code)
        score = b.get("scoreAllTime", 0)
        views = b.get("views", 0)
        likes = b.get("likes", 0)
        upvotes = b.get("upvotes", 0)
        strat_tag = b.get("strategy", "")
        map_tag = b.get("map", "")
        season = b.get("season", "")
        video = b.get("video", "")

        # Creator badge
        creator = b.get("creatorName", "")
        author_display = f"{author} ({creator} - Featured Creator)" if creator else author

        lines.append(f"### {title}")
        # Freshness label
        season_num = _extract_season_number(season)
        if season_num is not None:
            age = CURRENT_SEASON - season_num
            if age <= 1:
                freshness = "CURRENT PATCH"
            elif age <= 3:
                freshness = "Recent"
            else:
                freshness = f"Old (Season {season_num}, may be outdated)"
        else:
            freshness = "Unknown patch"

        meta_parts = [f"**Author:** {author_display}", f"**Civ:** {civ_name}"]
        if strat_tag:
            meta_parts.append(f"**Strategy:** {strat_tag}")
        if map_tag:
            meta_parts.append(f"**Map:** {map_tag}")
        meta_parts.append(f"**Patch:** {freshness}")
        meta_parts.append(f"**Views:** {views:,}")
        meta_parts.append(f"**Likes:** {likes}")
        lines.append(" | ".join(meta_parts))

        if description:
            lines.append(f"\n{truncate(description, 400)}")

        # Parse steps by age
        steps_sections = b.get("steps", [])
        if isinstance(steps_sections, list) and steps_sections:
            age_names = {0: "", 1: "Dark Age", 2: "Feudal Age", 3: "Castle Age", 4: "Imperial Age"}
            for section in steps_sections:
                if not isinstance(section, dict):
                    continue
                age = section.get("age", 0)
                section_type = section.get("type", "age")
                age_label = age_names.get(age, f"Age {age}")

                if section_type == "ageUp":
                    lines.append(f"\n**Aging up to {age_label}:**")
                elif age_label:
                    lines.append(f"\n**{age_label}:**")

                gameplan = section.get("gameplan", "")
                if gameplan:
                    lines.append(f"*Plan: {_clean_step_html(gameplan)}*")

                inner_steps = section.get("steps", [])
                if isinstance(inner_steps, list):
                    for step in inner_steps[:10]:
                        if not isinstance(step, dict):
                            continue
                        time = re.sub(r'<[^>]+>', '', step.get("time", "")).strip()
                        desc = _clean_step_html(step.get("description", ""))
                        food = step.get("food", "")
                        wood = step.get("wood", "")
                        gold = step.get("gold", "")
                        stone = step.get("stone", "")

                        res_parts = []
                        if food:
                            res_parts.append(f"{food}F")
                        if wood:
                            res_parts.append(f"{wood}W")
                        if gold:
                            res_parts.append(f"{gold}G")
                        if stone:
                            res_parts.append(f"{stone}S")
                        res_str = f" [{'/'.join(res_parts)}]" if res_parts else ""

                        time_str = f"({time}) " if time else ""
                        if desc:
                            lines.append(f"- {time_str}{desc}{res_str}")

        build_url = f"{AOE4GUIDES_BASE}/builds/{build_id}" if build_id else ""
        links = []
        if build_url:
            links.append(f"[Full build order]({build_url})")
        if video:
            # Clean embed URL to normal URL
            yt_url = video.replace("/embed/", "/watch?v=") if "/embed/" in video else video
            links.append(f"[Video guide]({yt_url})")
        if links:
            lines.append(f"\n{' | '.join(links)}")
        lines.append("")

    result = "\n".join(lines)
    sources = [
        Source(
            type="aoe4guides",
            title=f"Build orders: {civ}",
            url=f"{AOE4GUIDES_BASE}/builds/{builds[0].get('id', '')}" if builds and builds[0].get("id") else AOE4GUIDES_BASE,
        )
    ]
    cache.set(cache_key, (result, sources), CACHE_TTL_BUILDS)
    return result, sources
