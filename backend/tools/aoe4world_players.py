"""Tools for AoE4 World player search, profiles, and match history."""

import json
from config import AOE4WORLD_BASE, CACHE_TTL_PLAYERS
from cache import cache
from utils import fetch_json, truncate
from models import Source


async def search_player(query: str) -> tuple[str, list[Source]]:
    """Search for a player by name."""
    if len(query) < 3:
        return "Search query must be at least 3 characters.", []

    cache_key = f"player_search:{query.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{AOE4WORLD_BASE}/players/search"
    data = await fetch_json(url, {"query": query})
    if data is None:
        return "Error: Could not search players on aoe4world.com.", []

    players = data.get("players", data) if isinstance(data, dict) else data
    if not players:
        return f"No players found matching '{query}'.", []

    # Show top 5 results
    lines = [f"## Players matching '{query}'", ""]
    if isinstance(players, list):
        for p in players[:5]:
            name = p.get("name", "Unknown")
            pid = p.get("profile_id", "")
            country = p.get("country", "")
            # Get rating from modes
            modes = p.get("modes", {}) or p.get("leaderboards", {})
            rating_info = ""
            if isinstance(modes, dict):
                for mode_key in ["rm_solo", "qm_1v1", "rm_1v1"]:
                    mode_data = modes.get(mode_key, {})
                    if isinstance(mode_data, dict) and mode_data.get("rating"):
                        rating_info = f" | ELO: {mode_data['rating']}"
                        break
            flag = f" [{country.upper()}]" if country else ""
            lines.append(f"- **{name}**{flag}{rating_info} (profile_id: {pid})")
    else:
        lines.append(truncate(json.dumps(players, indent=2, default=str), 2000))

    result = "\n".join(lines)
    sources = [Source(
        type="aoe4world",
        title=f"Player search: {query}",
        url=f"https://aoe4world.com/players/search?query={query}",
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_PLAYERS)
    return result, sources


async def get_player_profile(profile_id: str) -> tuple[str, list[Source]]:
    """Get detailed profile for a player."""
    cache_key = f"player_profile:{profile_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{AOE4WORLD_BASE}/players/{profile_id}"
    data = await fetch_json(url)
    if data is None:
        return f"Error: Could not fetch profile for player {profile_id}.", []

    name = data.get("name", "Unknown")
    country = data.get("country", "")
    flag = f" [{country.upper()}]" if country else ""

    lines = [f"## {name}{flag}", ""]

    # Modes/leaderboards
    modes = data.get("modes", {}) or data.get("leaderboards", {})
    if isinstance(modes, dict):
        for mode_name, mode_data in modes.items():
            if not isinstance(mode_data, dict):
                continue
            rating = mode_data.get("rating")
            if not rating:
                continue
            rank = mode_data.get("rank", "N/A")
            wr = mode_data.get("win_rate", 0)
            wins = mode_data.get("wins_count", 0)
            losses = mode_data.get("losses_count", 0)
            games = mode_data.get("games_count", wins + losses)
            streak = mode_data.get("streak", 0)
            wr_pct = f"{wr * 100:.1f}%" if wr and wr < 1 else f"{wr:.1f}%" if wr else "N/A"
            lines.append(f"### {mode_name}")
            lines.append(f"- Rating: **{rating}** (Rank #{rank})")
            lines.append(f"- Win rate: {wr_pct} ({wins}W / {losses}L)")
            lines.append(f"- Games: {games}")
            if streak:
                lines.append(f"- Streak: {'+' if streak > 0 else ''}{streak}")
            lines.append("")

    result = "\n".join(lines)
    sources = [Source(
        type="aoe4world",
        title=f"Player profile: {name}",
        url=f"https://aoe4world.com/players/{profile_id}",
    )]
    cache.set(cache_key, (result, sources), CACHE_TTL_PLAYERS)
    return result, sources


async def get_player_matches(
    profile_id: str,
    count: int = 10,
    leaderboard: str | None = None,
) -> tuple[str, list[Source]]:
    """Get recent match history for a player."""
    params = {"limit": min(count, 50)}
    if leaderboard:
        params["leaderboard"] = leaderboard

    url = f"{AOE4WORLD_BASE}/players/{profile_id}/games"
    data = await fetch_json(url, params)
    if data is None:
        return f"Error: Could not fetch matches for player {profile_id}.", []

    games = data.get("games", data) if isinstance(data, dict) else data
    if not games:
        return "No recent matches found.", []

    lines = ["## Recent Matches", ""]
    lines.append("| Map | Civ | vs Civ | Result | Duration |")
    lines.append("|-----|-----|--------|--------|----------|")

    if isinstance(games, list):
        for g in games[:count]:
            map_name = g.get("map", "Unknown")
            duration = g.get("duration")
            dur_str = f"{duration // 60}m" if duration else "N/A"

            # Parse teams — API wraps each player in {"player": {...}}
            teams = g.get("teams", [])
            player_civ = "?"
            opp_civ = "?"
            result_str = "?"
            for team in teams:
                if isinstance(team, list):
                    for entry in team:
                        p = entry.get("player", entry) if isinstance(entry, dict) else entry
                        if str(p.get("profile_id")) == str(profile_id):
                            player_civ = p.get("civilization", "?")
                            result_str = "Win" if p.get("result") == "win" else "Loss"
                        else:
                            opp_civ = p.get("civilization", "?")

            lines.append(f"| {map_name} | {player_civ} | {opp_civ} | {result_str} | {dur_str} |")
    else:
        lines.append(truncate(json.dumps(games, indent=2, default=str), 2000))

    result = "\n".join(lines)
    sources = [Source(
        type="aoe4world",
        title="Match history",
        url=f"https://aoe4world.com/players/{profile_id}/games",
    )]
    return result, sources
