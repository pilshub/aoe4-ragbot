"""In-memory searchable store for game data (units, buildings, technologies)."""

from __future__ import annotations
from data.glossary import GLOSSARY

# Extra game knowledge that the data API doesn't capture well.
# These are verified in-game mechanics/roles that supplement raw stat data.
UNIT_EXTRA_INFO: dict[str, str] = {
    "springald": "ROLE: Anti-siege weapon. Springalds are THE primary counter to Mangonels and other siege units. Their high single-target ranged damage combined with siege units having 0 ranged armor makes them extremely effective. Always build Springalds to counter enemy Mangonels.",
    "mangonel": "ROLE: Anti-ranged-mass. Effective against groups of archers/crossbowmen due to AoE splash. Countered by Springalds (anti-siege) and melee cavalry charges.",
    "battering ram": "ROLE: Building destroyer. Extremely effective against buildings with +300 bonus damage. Very vulnerable to melee attacks from cavalry and infantry. Garrisoning infantry inside increases movement speed.",
    "trebuchet": "ROLE: Long-range siege. Outranges all defensive buildings. Must pack/unpack to move. Countered by cavalry charges and Springalds.",
    "bombard": "ROLE: Heavy anti-building and anti-siege. Massive single-target damage destroys buildings and siege quickly. Slow and expensive.",
}

BUILDING_EXTRA_INFO: dict[str, str] = {
    "keep": "MECHANIC: Each garrisoned unit adds an extra arrow to the Keep's attack, significantly increasing total damage output. A fully garrisoned Keep (15 units) fires 16 arrows per volley.",
    "town center": "MECHANIC: Can garrison villagers for protection. Garrisoned villagers add arrows to the TC's attack. Has the Town Bell ability to call all nearby villagers inside.",
}


class GameStore:
    def __init__(self, data: dict[str, list]):
        self.units_raw = data.get("units", [])
        self.buildings_raw = data.get("buildings", [])
        self.technologies_raw = data.get("technologies", [])

        # Build lookup indexes: lowercase name -> list of entries
        self.units = self._index(self.units_raw)
        self.buildings = self._index(self.buildings_raw)
        self.technologies = self._index(self.technologies_raw)

        # Build reverse index: building_id -> list of techs produced there
        self.techs_by_building = self._index_techs_by_building(self.technologies_raw)

        print(f"[store] Indexed {len(self.units)} units, {len(self.buildings)} buildings, {len(self.technologies)} technologies")

    @staticmethod
    def _index_techs_by_building(techs: list) -> dict[str, list]:
        """Reverse index: building_id -> list of techs produced there."""
        idx: dict[str, list] = {}
        for tech in techs:
            for building_id in (tech.get("producedBy") or []):
                key = building_id.lower().replace("-", " ")
                idx.setdefault(key, []).append(tech)
        return idx

    def get_techs_for_building(self, building_name: str, civ: str | None = None) -> list:
        """Get technologies researched at a building, optionally filtered by civ."""
        resolved = self._resolve_name(building_name)
        techs = []
        for key, items in self.techs_by_building.items():
            if self._word_match(resolved, key) or self._word_match(key, resolved):
                techs.extend(items)
        # Filter by civ
        if civ and techs:
            from config import resolve_civ
            canonical_civ = resolve_civ(civ)
            if canonical_civ:
                filtered = [t for t in techs if canonical_civ in (t.get("civs") or [])]
                if filtered:
                    techs = filtered
        # Deduplicate
        seen = set()
        unique = []
        for t in techs:
            tid = t.get("id") or t.get("pbgid") or id(t)
            if tid not in seen:
                seen.add(tid)
                unique.append(t)
        return sorted(unique, key=lambda t: (t.get("age", 9), t.get("name", "")))

    def _index(self, items: list) -> dict[str, list]:
        idx: dict[str, list] = {}
        for item in items:
            name = (item.get("name") or "").lower()
            if name:
                idx.setdefault(name, []).append(item)
            # Also index by baseId for alternate lookups
            base_id = (item.get("baseId") or "").lower().replace("_", " ")
            if base_id and base_id != name:
                idx.setdefault(base_id, []).append(item)
        return idx

    def _resolve_name(self, query: str) -> str:
        """Expand abbreviations and normalize."""
        q = query.lower().strip().replace("_", " ")
        # Check glossary for abbreviation
        if q in GLOSSARY:
            return GLOSSARY[q].lower()
        return q

    @staticmethod
    def _word_match(query: str, text: str) -> bool:
        """Check if query appears in text at a word boundary (prefix or after space)."""
        if query == text:
            return True
        if text.startswith(query):
            return True
        if f" {query}" in text:
            return True
        return False

    def _search(self, index: dict[str, list], name: str, civ: str | None = None, raw_items: list | None = None) -> list:
        resolved = self._resolve_name(name)
        results = []

        # Exact match first
        if resolved in index:
            results = index[resolved]
        else:
            # Partial match — require word-boundary alignment
            # This prevents "loom" matching "bloomery" while allowing
            # "knight" matching "royal knight" and "spear" matching "spearman"
            for key, items in index.items():
                if self._word_match(resolved, key) or self._word_match(key, resolved):
                    results.extend(items)

        # If few results found and raw_items available, also search by displayClasses
        # This catches cases like searching "ship" finding units classed as "Ship"/"Warship"
        if raw_items and len(results) < 3:
            class_matches = []
            for item in raw_items:
                classes = item.get("displayClasses") or item.get("classes") or []
                classes_lower = " ".join(str(c) for c in classes).lower()
                if resolved in classes_lower:
                    class_matches.append(item)
            if class_matches:
                results.extend(class_matches)

        # Filter by civ if specified
        if civ and results:
            from config import resolve_civ
            canonical_civ = resolve_civ(civ)
            if canonical_civ:
                filtered = [
                    item for item in results
                    if canonical_civ in [c.lower().replace(" ", "_") for c in (item.get("civs") or [])]
                    or canonical_civ.replace("_", " ") in [c.lower() for c in (item.get("civs") or [])]
                ]
                if filtered:
                    results = filtered

        # Deduplicate by id
        seen = set()
        unique = []
        for item in results:
            item_id = item.get("id") or item.get("pbgid") or id(item)
            if item_id not in seen:
                seen.add(item_id)
                unique.append(item)
        return unique

    def search_units(self, name: str, civ: str | None = None) -> list:
        return self._search(self.units, name, civ, raw_items=self.units_raw)

    def search_buildings(self, name: str, civ: str | None = None) -> list:
        return self._search(self.buildings, name, civ, raw_items=self.buildings_raw)

    def search_technologies(self, name: str, civ: str | None = None) -> list:
        return self._search(self.technologies, name, civ, raw_items=self.technologies_raw)

    def format_unit(self, unit: dict) -> str:
        """Format a unit entry into a readable string for the LLM."""
        lines = []
        name = unit.get("name", "Unknown")
        civs = ", ".join(unit.get("civs") or ["All"])
        lines.append(f"**{name}** ({civs})")

        desc = unit.get("description", "")
        if desc:
            lines.append(desc)

        classes = unit.get("displayClasses") or unit.get("classes") or []
        if classes:
            lines.append(f"Type: {', '.join(classes)}")

        age = unit.get("age")
        if age:
            lines.append(f"Age: {age}")

        # Costs
        costs = unit.get("costs") or {}
        cost_parts = []
        for res in ["food", "wood", "gold", "stone"]:
            val = costs.get(res, 0)
            if val:
                cost_parts.append(f"{val} {res}")
        pop = costs.get("popcap", 0)
        if pop:
            cost_parts.append(f"{pop} pop")
        build_time = costs.get("time")
        if build_time:
            cost_parts.append(f"{build_time}s build time")
        if cost_parts:
            lines.append(f"Cost: {', '.join(cost_parts)}")

        # HP
        hp = unit.get("hitpoints")
        if hp:
            lines.append(f"HP: {hp}")

        # Weapons
        weapons = unit.get("weapons") or []
        for w in weapons:
            w_type = w.get("type", "")
            damage = w.get("damage")
            if damage:
                speed = w.get("speed")
                rng = w.get("range") or w.get("maxRange")
                parts = [f"Damage: {damage}"]
                if speed:
                    parts.append(f"speed {speed}s")
                if rng:
                    parts.append(f"range {rng}")
                lines.append(f"Weapon ({w_type}): {', '.join(parts)}")
                # Bonus damage modifiers
                modifiers = w.get("modifiers") or []
                for mod in modifiers:
                    target = mod.get("target", {})
                    value = mod.get("value", 0)
                    effect = mod.get("effect", "")
                    target_classes = target.get("class", [])
                    if value and target_classes:
                        class_names = [" ".join(c) for c in target_classes]
                        sign = "+" if value > 0 else ""
                        lines.append(f"  Bonus vs {', '.join(class_names)}: {sign}{value}")

        # Armor
        armor = unit.get("armor") or []
        if isinstance(armor, list):
            for a in armor:
                a_type = a.get("type", "")
                a_val = a.get("value", 0)
                if a_val:
                    lines.append(f"Armor ({a_type}): {a_val}")

        # Movement speed
        speed = unit.get("moveSpeed")
        if speed:
            lines.append(f"Move speed: {speed}")

        # Sight
        sight = unit.get("sight")
        if sight and isinstance(sight, dict):
            lines.append(f"Line of sight: {sight.get('line', 'N/A')}")

        # Supplementary game knowledge not in raw data
        base_id = (unit.get("baseId") or name or "").lower().replace("-", " ")
        for key, info in UNIT_EXTRA_INFO.items():
            if key in base_id or key in name.lower():
                lines.append(info)
                break

        return "\n".join(lines)

    def format_building(self, building: dict) -> str:
        """Format a building entry."""
        lines = []
        name = building.get("name", "Unknown")
        civs = ", ".join(building.get("civs") or ["All"])
        lines.append(f"**{name}** ({civs})")

        desc = building.get("description", "")
        if desc:
            lines.append(desc)

        age = building.get("age")
        if age:
            lines.append(f"Age: {age}")

        costs = building.get("costs") or {}
        cost_parts = []
        for res in ["food", "wood", "gold", "stone"]:
            val = costs.get(res, 0)
            if val:
                cost_parts.append(f"{val} {res}")
        if cost_parts:
            lines.append(f"Cost: {', '.join(cost_parts)}")

        hp = building.get("hitpoints")
        if hp:
            lines.append(f"HP: {hp}")

        # Garrison
        garrison = building.get("garrison")
        has_garrison = False
        if garrison and isinstance(garrison, dict):
            capacity = garrison.get("capacity", 0)
            if capacity:
                lines.append(f"Garrison capacity: {capacity}")
                has_garrison = True

        # Armor
        armor = building.get("armor") or []
        if isinstance(armor, list):
            for a in armor:
                a_type = a.get("type", "")
                a_val = a.get("value", 0)
                if a_val:
                    lines.append(f"Armor ({a_type}): {a_val}")

        # Weapons
        weapons = building.get("weapons") or []
        has_weapons = False
        for w in weapons:
            w_type = w.get("type", "")
            damage = w.get("damage")
            if damage:
                has_weapons = True
                rng = w.get("range") or w.get("maxRange")
                speed = w.get("speed")
                parts = [f"Damage: {damage}"]
                if speed:
                    parts.append(f"speed {speed}s")
                if rng:
                    parts.append(f"range {rng}")
                lines.append(f"Weapon ({w_type}): {', '.join(parts)}")

        # Note about garrison bonus for defensive buildings
        if has_garrison and has_weapons:
            lines.append("Note: Garrisoned units add extra arrows, increasing total damage output.")

        # Sight
        sight = building.get("sight")
        if sight and isinstance(sight, dict):
            lines.append(f"Line of sight: {sight.get('line', 'N/A')}")

        # Supplementary game knowledge not in raw data
        base_id = (building.get("baseId") or name or "").lower().replace("-", " ")
        for key, info in BUILDING_EXTRA_INFO.items():
            if key in base_id or key in name.lower():
                lines.append(info)
                break

        return "\n".join(lines)

    def format_technology(self, tech: dict) -> str:
        """Format a technology entry."""
        lines = []
        name = tech.get("name", "Unknown")
        civs = ", ".join(tech.get("civs") or ["All"])
        lines.append(f"**{name}** ({civs})")

        desc = tech.get("description", "")
        if desc:
            lines.append(desc)

        age = tech.get("age")
        if age:
            lines.append(f"Age: {age}")

        # Researched at
        produced_by = tech.get("producedBy") or []
        if produced_by:
            buildings = [b.replace("_", " ").title() for b in produced_by]
            lines.append(f"Researched at: {', '.join(buildings)}")

        costs = tech.get("costs") or {}
        cost_parts = []
        for res in ["food", "wood", "gold", "stone"]:
            val = costs.get(res, 0)
            if val:
                cost_parts.append(f"{val} {res}")
        build_time = costs.get("time")
        if build_time:
            cost_parts.append(f"{build_time}s research time")
        if cost_parts:
            lines.append(f"Cost: {', '.join(cost_parts)}")

        return "\n".join(lines)


# Global store instance, initialized on startup
store: GameStore | None = None
