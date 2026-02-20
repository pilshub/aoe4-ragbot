"""Tool for AoE4 World age-up timing analytics."""

import asyncio
import aiohttp
from config import AOE4WORLD_BASE, CACHE_TTL_STATS, resolve_civ, CIV_DISPLAY_NAMES
from cache import cache
from models import Source


async def _fetch_ageups(params: dict) -> dict | None:
    """Fetch from the analytics endpoint with a browser-like User-Agent.
    The ageups endpoint is internal and rate-limits bot User-Agents aggressively."""
    url = f"{AOE4WORLD_BASE}/stats/analytics/ageups"
    try:
        async with aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None


def _fmt_time(seconds: float | None) -> str:
    """Convert seconds to M:SS format."""
    if seconds is None:
        return "N/A"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


async def get_ageup_stats(
    civilization: str | None = None,
    mode: str = "rm_solo",
    rank_level: str | None = None,
) -> tuple[str, list[Source]]:
    """Get age-up timing analytics: average/fastest/typical times to reach each age, by landmark path, with win rates."""
    params = {}
    if civilization:
        canonical = resolve_civ(civilization)
        if canonical:
            params["civilization"] = canonical
    if mode:
        params["leaderboard"] = mode
    if rank_level:
        params["rank_level"] = rank_level

    cache_key = f"ageups:{params}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = await _fetch_ageups(params)
    if data is None:
        return "Error: Could not fetch age-up analytics from aoe4world.com. The endpoint may be rate-limited — try again in a minute.", []

    # The key data is in the "age1-4" section (full landmark paths) or "age1-2", "age1-3"
    # Use the deepest available section for the most complete data
    entries = data.get("data", {})
    metadata = {m.get("pbgid"): m for m in data.get("ageups_metadata", [])}

    civ_filter = params.get("civilization", "")
    civ_display = CIV_DISPLAY_NAMES.get(civ_filter, civilization or "All Civilizations")
    rank_label = f" ({rank_level})" if rank_level else ""

    lines = [f"## Age-Up Timing Analytics: {civ_display}{rank_label}", ""]

    # If a specific civ is requested, show detailed landmark path analysis
    if civ_filter:
        # Use age1-2 for Feudal landmark choices, age1-3 for Castle paths, age1-4 for full paths
        for section_key, section_label in [("age1-2", "Feudal Age (Age II) Landmarks"), ("age1-3", "Castle Age (Age III) Paths"), ("age1-4", "Full Game Landmark Paths")]:
            section = entries.get(section_key, [])
            if not section:
                continue

            # Filter to our civ
            civ_entries = [e for e in section if e.get("civilization") == civ_filter]
            if not civ_entries:
                continue

            lines.append(f"### {section_label}")
            lines.append("")

            for entry in sorted(civ_entries, key=lambda x: x.get("player_games_count", 0), reverse=True):
                games = entry.get("player_games_count", 0)
                if games < 50:  # Skip tiny sample sizes
                    continue

                wr = entry.get("win_rate")
                wr_str = f"{wr:.1f}%" if wr is not None else "N/A"

                # Build landmark path description
                path_parts = []
                for age_num in [2, 3, 4]:
                    name = entry.get(f"age{age_num}_name")
                    avg = entry.get(f"age{age_num}_finished_at_average")
                    mode_time = entry.get(f"age{age_num}_finished_at_mode")
                    fastest = entry.get(f"age{age_num}_finished_at_minimum")
                    if name:
                        time_str = f"avg {_fmt_time(avg)}, typical {_fmt_time(mode_time)}, fastest {_fmt_time(fastest)}"
                        path_parts.append(f"**Age {age_num} → {name}**: {time_str}")

                if path_parts:
                    lines.append(f"**Path:** {' → '.join([entry.get(f'age{n}_name', '?') for n in [2,3,4] if entry.get(f'age{n}_name')])}")
                    lines.append(f"- **Games:** {games:,} | **Win Rate:** {wr_str}")
                    for part in path_parts:
                        lines.append(f"- {part}")
                    lines.append("")

    else:
        # No specific civ — show per-civ summary from "age1" (has one entry per civ)
        # "total" only has 1 aggregate entry with empty civilization, so prefer "age1"
        total = entries.get("age1", entries.get("total", []))
        if isinstance(total, list) and total:
            lines.append("| Civilization | Games | Win Rate | Avg Feudal | Avg Castle | Avg Imperial |")
            lines.append("|-------------|-------|----------|------------|------------|--------------|")

            for entry in sorted(total, key=lambda x: x.get("player_games_count", 0), reverse=True):
                civ_name = entry.get("civilization", "")
                if not civ_name:
                    continue
                display = CIV_DISPLAY_NAMES.get(civ_name, civ_name)
                games = entry.get("player_games_count", 0)
                wr = entry.get("win_rate")
                wr_str = f"{wr:.1f}%" if wr is not None else "N/A"
                feudal = _fmt_time(entry.get("age2_finished_at_average"))
                castle = _fmt_time(entry.get("age3_finished_at_average"))
                imperial = _fmt_time(entry.get("age4_finished_at_average"))
                lines.append(f"| {display} | {games:,} | {wr_str} | {feudal} | {castle} | {imperial} |")

    result = "\n".join(lines)
    source_url = "https://aoe4world.com/stats/analytics/ageups"
    sources = [Source(type="aoe4world", title=f"Age-up analytics: {civ_display}", url=source_url)]

    cache.set(cache_key, (result, sources), CACHE_TTL_STATS)
    return result, sources
