"""Tools for AoE4 World civilization statistics, matchups, and map data."""

import json
from config import AOE4WORLD_BASE, CACHE_TTL_STATS, resolve_civ, CIV_DISPLAY_NAMES
from cache import cache
from utils import fetch_json, truncate
from models import Source


async def get_civ_stats(
    mode: str = "rm_solo",
    map: str | None = None,
    patch: str | None = None,
    rank_level: str | None = None,
    rating_min: int | None = None,
    rating_max: int | None = None,
) -> tuple[str, list[Source]]:
    """Get win/pick rates for all civilizations."""
    params = {}
    if map:
        params["map"] = map
    if patch:
        params["patch"] = patch
    if rank_level:
        params["rank_level"] = rank_level
    if rating_min and rating_max:
        params["rating"] = f"{rating_min}-{rating_max}"
    elif rating_min:
        params["rating"] = f">{rating_min}"
    elif rating_max:
        params["rating"] = f"<{rating_max}"

    cache_key = f"civ_stats:{mode}:{json.dumps(params, sort_keys=True)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{AOE4WORLD_BASE}/stats/{mode}/civilizations"
    data = await fetch_json(url, params)
    if data is None:
        return "Error: Could not fetch civilization stats from aoe4world.com.", []

    # Format results
    civs = data if isinstance(data, list) else data.get("data", data.get("civilizations", []))
    if not civs:
        return "No civilization data available for this mode/filter.", []

    map_label = f" on {map.replace('_', ' ').title()}" if map else ""
    lines = [f"## Civilization Stats ({mode}{map_label})", ""]
    lines.append("| Civilization | Win Rate | Pick Rate | Games |")
    lines.append("|-------------|----------|-----------|-------|")

    if isinstance(civs, dict):
        # API may return dict keyed by civ name
        for civ_key, stats in sorted(civs.items(), key=lambda x: x[1].get("win_rate", 0) if isinstance(x[1], dict) else 0, reverse=True):
            if isinstance(stats, dict):
                display = CIV_DISPLAY_NAMES.get(civ_key, civ_key)
                wr = stats.get("win_rate", 0)
                pr = stats.get("pick_rate", 0)
                games = stats.get("games_count", 0)
                wr_pct = f"{wr * 100:.1f}%" if wr < 1 else f"{wr:.1f}%"
                pr_pct = f"{pr * 100:.1f}%" if pr < 1 else f"{pr:.1f}%"
                lines.append(f"| {display} | {wr_pct} | {pr_pct} | {games:,} |")
    elif isinstance(civs, list):
        for civ in sorted(civs, key=lambda x: x.get("win_rate", 0), reverse=True):
            display = civ.get("name", civ.get("civilization", "Unknown"))
            wr = civ.get("win_rate", 0)
            pr = civ.get("pick_rate", 0)
            games = civ.get("games_count", 0)
            wr_pct = f"{wr * 100:.1f}%" if wr < 1 else f"{wr:.1f}%"
            pr_pct = f"{pr * 100:.1f}%" if pr < 1 else f"{pr:.1f}%"
            lines.append(f"| {display} | {wr_pct} | {pr_pct} | {games:,} |")

    result = "\n".join(lines)
    source_url = f"https://aoe4world.com/stats/{mode}/civilizations"
    sources = [Source(type="aoe4world", title=f"Civ stats ({mode})", url=source_url)]

    cache.set(cache_key, (result, sources), CACHE_TTL_STATS)
    return result, sources


async def get_matchup_stats(
    mode: str = "rm_solo",
    civ1: str = "",
    civ2: str = "",
    map: str | None = None,
    patch: str | None = None,
    rank_level: str | None = None,
) -> tuple[str, list[Source]]:
    """Get head-to-head win rate between two civilizations."""
    params = {}
    if map:
        params["map"] = map
    if patch:
        params["patch"] = patch
    if rank_level:
        params["rank_level"] = rank_level

    url = f"{AOE4WORLD_BASE}/stats/{mode}/matchups"
    data = await fetch_json(url, params)
    if data is None:
        return "Error: Could not fetch matchup data from aoe4world.com.", []

    # Resolve civ names
    c1 = resolve_civ(civ1)
    c2 = resolve_civ(civ2)
    c1_display = CIV_DISPLAY_NAMES.get(c1, civ1) if c1 else civ1
    c2_display = CIV_DISPLAY_NAMES.get(c2, civ2) if c2 else civ2

    # API returns {"data": [{"civilization": "x", "other_civilization": "y", "win_rate": 0.5, ...}]}
    # It's a flat list of all matchup combinations (484 entries for 22 civs)
    entries = data.get("data", []) if isinstance(data, dict) else data if isinstance(data, list) else []

    # Find the specific matchup
    matchup = None
    for entry in entries:
        entry_civ = entry.get("civilization", "")
        entry_opp = entry.get("other_civilization", "")
        if c1 and c2 and entry_civ == c1 and entry_opp == c2:
            matchup = entry
            break

    # Try reversed order if not found
    matchup_reversed = False
    if not matchup:
        for entry in entries:
            entry_civ = entry.get("civilization", "")
            entry_opp = entry.get("other_civilization", "")
            if c1 and c2 and entry_civ == c2 and entry_opp == c1:
                matchup = entry
                matchup_reversed = True
                break

    if matchup:
        wr = matchup.get("win_rate", 0)
        games = matchup.get("games_count", 0)
        wins = matchup.get("win_count", 0)
        # win_rate is from the perspective of "civilization" (the first civ in the entry)
        if matchup_reversed:
            # Entry is c2 vs c1, so win_rate is c2's perspective
            c2_wr = wr
            c1_wr = 100 - wr if wr > 1 else 1 - wr
        else:
            c1_wr = wr
            c2_wr = 100 - wr if wr > 1 else 1 - wr

        c1_pct = f"{c1_wr * 100:.1f}%" if c1_wr <= 1 else f"{c1_wr:.1f}%"
        c2_pct = f"{c2_wr * 100:.1f}%" if c2_wr <= 1 else f"{c2_wr:.1f}%"

        map_label = f" on {map.replace('_', ' ').title()}" if map else ""
        c1_val = c1_wr if c1_wr > 1 else c1_wr * 100
        c2_val = c2_wr if c2_wr > 1 else c2_wr * 100
        if c1_val > c2_val:
            verdict = f"**{c1_display}** has the advantage."
        elif c2_val > c1_val:
            verdict = f"**{c2_display}** has the advantage."
        else:
            verdict = "The matchup is perfectly even."
        result = (
            f"## {c1_display} vs {c2_display} ({mode}{map_label})\n\n"
            f"- **{c1_display} win rate:** {c1_pct}\n"
            f"- **{c2_display} win rate:** {c2_pct}\n"
            f"- **Games played:** {games:,}\n"
            f"- **Verdict:** {verdict}\n"
        )
    else:
        # Couldn't find specific matchup — list all matchups for civ1
        civ1_matchups = [e for e in entries if e.get("civilization") == c1]
        if civ1_matchups:
            map_label = f" on {map.replace('_', ' ').title()}" if map else ""
            lines = [f"## {c1_display} Matchups ({mode}{map_label})\n"]
            lines.append("| Opponent | Win Rate | Games |")
            lines.append("|----------|----------|-------|")
            for m in sorted(civ1_matchups, key=lambda x: x.get("win_rate", 0), reverse=True):
                opp = CIV_DISPLAY_NAMES.get(m.get("other_civilization", ""), m.get("other_civilization", ""))
                mwr = m.get("win_rate", 0)
                mg = m.get("games_count", 0)
                mwr_pct = f"{mwr * 100:.1f}%" if mwr <= 1 else f"{mwr:.1f}%"
                lines.append(f"| {opp} | {mwr_pct} | {mg:,} |")
            result = "\n".join(lines)
        else:
            result = f"No matchup data found for {c1_display} vs {c2_display} in {mode}."

    sources = [Source(
        type="aoe4world",
        title=f"Matchup: {c1_display} vs {c2_display}",
        url=f"https://aoe4world.com/stats/{mode}/matchups",
    )]
    return result, sources


async def get_map_stats(
    mode: str = "rm_solo",
    map_name: str | None = None,
    patch: str | None = None,
) -> tuple[str, list[Source]]:
    """Get map statistics and which civs perform best on each map."""
    params = {}
    if patch:
        params["patch"] = patch
    if map_name:
        params["include_civs"] = "true"

    url = f"{AOE4WORLD_BASE}/stats/{mode}/maps"
    data = await fetch_json(url, params)
    if data is None:
        return "Error: Could not fetch map data from aoe4world.com.", []

    maps = data if isinstance(data, list) else data.get("data", data.get("maps", []))

    if map_name and isinstance(maps, (list, dict)):
        # Filter to specific map — API uses "map" key, not "name"
        target = map_name.lower()
        if isinstance(maps, list):
            maps = [m for m in maps if target in (m.get("map", "") or m.get("name", "") or "").lower()]
        elif isinstance(maps, dict):
            maps = {k: v for k, v in maps.items() if target in k.lower()}

    # Format as readable markdown instead of raw JSON
    lines = []

    if map_name:
        # Specific map: show details + per-civ breakdown if available
        map_entry = maps[0] if isinstance(maps, list) and maps else maps if isinstance(maps, dict) else None
        if map_entry and isinstance(map_entry, dict):
            name = map_entry.get("map", map_entry.get("name", map_name))
            games = map_entry.get("games_count", 0)
            duration_avg = map_entry.get("duration_average", 0)
            duration_med = map_entry.get("duration_median", 0)
            best_civ = map_entry.get("highest_win_rate_civilization", "")
            lines.append(f"## {name} ({mode})")
            lines.append(f"**Total games:** {games:,}")
            if duration_med:
                lines.append(f"**Median game duration:** {int(duration_med) // 60}m {int(duration_med) % 60}s")
            if best_civ:
                best_display = CIV_DISPLAY_NAMES.get(best_civ, best_civ.replace("_", " ").title())
                lines.append(f"**Highest win rate civ:** {best_display}")
            lines.append("")

            # Per-civ stats on this map — API returns dict keyed by civ slug
            civs = map_entry.get("civilizations", map_entry.get("civs", {}))
            if isinstance(civs, dict) and civs:
                lines.append("| Civilization | Win Rate | Games |")
                lines.append("|-------------|----------|-------|")
                for civ_key, stats in sorted(civs.items(), key=lambda x: x[1].get("win_rate", 0) if isinstance(x[1], dict) else 0, reverse=True):
                    if isinstance(stats, dict):
                        civ_name = CIV_DISPLAY_NAMES.get(civ_key, civ_key.replace("_", " ").title())
                        wr = stats.get("win_rate", 0)
                        cg = stats.get("games_count", 0)
                        # API returns win_rate as percentage (e.g., 53.8), not fraction
                        wr_pct = f"{wr:.1f}%" if wr > 1 else f"{wr * 100:.1f}%"
                        lines.append(f"| {civ_name} | {wr_pct} | {cg:,} |")
            elif isinstance(civs, list) and civs:
                lines.append("| Civilization | Win Rate | Games |")
                lines.append("|-------------|----------|-------|")
                for c in sorted(civs, key=lambda x: x.get("win_rate", 0), reverse=True):
                    civ_name = CIV_DISPLAY_NAMES.get(
                        c.get("civilization", ""), c.get("name", c.get("civilization", "Unknown"))
                    )
                    wr = c.get("win_rate", 0)
                    cg = c.get("games_count", 0)
                    wr_pct = f"{wr:.1f}%" if wr > 1 else f"{wr * 100:.1f}%"
                    lines.append(f"| {civ_name} | {wr_pct} | {cg:,} |")
            else:
                lines.append("No per-civilization breakdown available for this map.")
        elif not maps:
            lines.append(f"No data found for map '{map_name}'. Try the exact map name (e.g., 'Dry Arabia', 'Rocky River').")
        else:
            lines.append(truncate(json.dumps(maps, indent=2, default=str), 2000))
    else:
        # All maps overview — API uses "map" key for map name
        lines.append(f"## Map Statistics ({mode})\n")
        lines.append("| Map | Games Played | Avg Duration | Best Civ |")
        lines.append("|-----|-------------|-------------|----------|")
        if isinstance(maps, list):
            for m in sorted(maps, key=lambda x: x.get("games_count", 0), reverse=True)[:20]:
                name = m.get("map", m.get("name", "Unknown"))
                games = m.get("games_count", 0)
                dur = m.get("duration_median", 0)
                dur_str = f"{int(dur) // 60}m" if dur else "N/A"
                best = m.get("highest_win_rate_civilization", "")
                best_display = CIV_DISPLAY_NAMES.get(best, best.replace("_", " ").title()) if best else "N/A"
                lines.append(f"| {name} | {games:,} | {dur_str} | {best_display} |")
        elif isinstance(maps, dict):
            for map_key, stats in sorted(maps.items(), key=lambda x: x[1].get("games_count", 0) if isinstance(x[1], dict) else 0, reverse=True)[:20]:
                games = stats.get("games_count", 0) if isinstance(stats, dict) else 0
                lines.append(f"| {map_key} | {games:,} | N/A | N/A |")
        else:
            lines.append(truncate(json.dumps(maps, indent=2, default=str), 2000))

    result = "\n".join(lines)
    sources = [Source(
        type="aoe4world",
        title=f"Map stats ({mode})",
        url=f"https://aoe4world.com/stats/{mode}/maps",
    )]
    return result, sources
