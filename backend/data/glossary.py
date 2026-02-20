"""Gaming abbreviation expansion for AoE4 queries."""

GLOSSARY = {
    # Units
    "maa": "Man-at-Arms",
    "xbow": "Crossbowman",
    "xbows": "Crossbowman",
    "spears": "Spearman",
    "spear": "Spearman",
    "knights": "Knight",
    "knight": "Knight",
    "archers": "Archer",
    "archer": "Archer",
    "horsemen": "Horseman",
    "horseman": "Horseman",
    "mango": "Mangonel",
    "mangos": "Mangonel",
    "ram": "Battering Ram",
    "rams": "Battering Ram",
    "treb": "Trebuchet",
    "trebs": "Trebuchet",
    "springs": "Springald",
    "nob": "Nest of Bees",
    "bombards": "Bombard",
    # Strategy
    "fc": "Fast Castle",
    "ff": "Fast Feudal",
    "fi": "Fast Imperial",
    "bo": "build order",
    "eco": "economy",
    "2tc": "2 Town Center",
    "3tc": "3 Town Center",
    # Buildings
    "tc": "Town Center",
    "bb": "Blacksmith",
    # Ages
    "dark age": "Age I",
    "feudal": "Age II",
    "feudal age": "Age II",
    "castle": "Age III",
    "castle age": "Age III",
    "imperial": "Age IV",
    "imperial age": "Age IV",
    "age1": "Age I",
    "age2": "Age II",
    "age3": "Age III",
    "age4": "Age IV",
    # Game modes
    "qm": "Quick Match",
    "rm": "Ranked Match",
    # Stats
    "wr": "win rate",
    "wp": "win percentage",
    "pr": "pick rate",
    # Civs (short)
    "hre": "Holy Roman Empire",
    "del": "Delhi Sultanate",
    "abb": "Abbasid Dynasty",
    "ott": "Ottomans",
    "mon": "Mongols",
    "fre": "French",
    "eng": "English",
    "chi": "Chinese",
    "mal": "Malians",
    "byz": "Byzantines",
    "jap": "Japanese",
    "jda": "Jeanne d'Arc",
    "otd": "Order of the Dragon",
    "zxl": "Zhu Xi's Legacy",
    "kt": "Knights Templar",
    "gol": "Golden Horde",
}


def expand_query(text: str) -> str:
    """Expand known gaming abbreviations in user text for better matching."""
    words = text.split()
    expanded = []
    for word in words:
        lower = word.lower().strip(".,!?()[]")
        if lower in GLOSSARY:
            expanded.append(GLOSSARY[lower])
        else:
            expanded.append(word)
    return " ".join(expanded)
