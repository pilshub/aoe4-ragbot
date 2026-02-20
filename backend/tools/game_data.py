"""Tools that query in-memory game data (units, buildings, technologies)."""

import json
from models import Source

# These return (result_string, list[Source])


async def query_unit_stats(name: str, civ: str | None = None) -> tuple[str, list[Source]]:
    from data.game_store import store
    if store is None:
        return "Game data not loaded yet.", []

    results = store.search_units(name, civ)
    if not results:
        return f"No unit found matching '{name}'.", []

    # Format top 3 results
    output = []
    for unit in results[:3]:
        output.append(store.format_unit(unit))

    sources = [Source(
        type="gamedata",
        title=f"Unit stats: {name}",
        url="https://data.aoe4world.com",
    )]
    return "\n\n---\n\n".join(output), sources


async def query_building_stats(name: str, civ: str | None = None) -> tuple[str, list[Source]]:
    from data.game_store import store
    if store is None:
        return "Game data not loaded yet.", []

    results = store.search_buildings(name, civ)
    if not results:
        return f"No building found matching '{name}'.", []

    output = []
    for b in results[:3]:
        output.append(store.format_building(b))

    sources = [Source(
        type="gamedata",
        title=f"Building stats: {name}",
        url="https://data.aoe4world.com",
    )]
    return "\n\n---\n\n".join(output), sources


async def query_technology(name: str, civ: str | None = None) -> tuple[str, list[Source]]:
    from data.game_store import store
    if store is None:
        return "Game data not loaded yet.", []

    results = store.search_technologies(name, civ)
    if not results:
        return f"No technology found matching '{name}'.", []

    output = []
    for t in results[:3]:
        output.append(store.format_technology(t))

    sources = [Source(
        type="gamedata",
        title=f"Technology: {name}",
        url="https://data.aoe4world.com",
    )]
    return "\n\n---\n\n".join(output), sources


async def compare_units(unit1: str, unit2: str, civ: str | None = None) -> tuple[str, list[Source]]:
    from data.game_store import store
    if store is None:
        return "Game data not loaded yet.", []

    results1 = store.search_units(unit1, civ)
    results2 = store.search_units(unit2, civ)

    if not results1:
        return f"No unit found matching '{unit1}'.", []
    if not results2:
        return f"No unit found matching '{unit2}'.", []

    u1 = results1[0]
    u2 = results2[0]

    def get_cost_total(u):
        costs = u.get("costs") or {}
        return sum(costs.get(r, 0) for r in ["food", "wood", "gold", "stone"])

    def get_primary_damage(u):
        weapons = u.get("weapons") or []
        for w in weapons:
            d = w.get("damage")
            if d:
                return d
        return 0

    lines = [
        f"## {u1.get('name', unit1)} vs {u2.get('name', unit2)}",
        "",
        f"| Stat | {u1.get('name', unit1)} | {u2.get('name', unit2)} |",
        "|------|------|------|",
        f"| HP | {u1.get('hitpoints', 'N/A')} | {u2.get('hitpoints', 'N/A')} |",
        f"| Primary Damage | {get_primary_damage(u1)} | {get_primary_damage(u2)} |",
        f"| Total Cost | {get_cost_total(u1)} | {get_cost_total(u2)} |",
        f"| Move Speed | {u1.get('moveSpeed', 'N/A')} | {u2.get('moveSpeed', 'N/A')} |",
        f"| Age | {u1.get('age', 'N/A')} | {u2.get('age', 'N/A')} |",
    ]

    # Add detailed stats for each
    lines.append("")
    lines.append("### Detailed stats:")
    lines.append("")
    lines.append(store.format_unit(u1))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(store.format_unit(u2))

    sources = [Source(
        type="gamedata",
        title=f"Unit comparison: {unit1} vs {unit2}",
        url="https://data.aoe4world.com",
    )]
    return "\n".join(lines), sources
