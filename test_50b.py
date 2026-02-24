"""50-query test suite — Round 2 (different queries from round 1)."""

import json
import time
import urllib.request

API = "https://aoe4-ragbot-production.up.railway.app/api/chat"


def query_bot(msg: str) -> dict:
    body = json.dumps({"messages": [{"role": "user", "content": msg}]}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream",
    })
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        elapsed = time.time() - start
    except Exception as e:
        return {"error": str(e), "time": -1}

    tokens, sources, tools = [], [], []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                d = json.loads(line[6:])
                if d.get("type") == "token":
                    tokens.append(d["content"])
                elif d.get("type") == "sources":
                    sources = d.get("sources", [])
                elif d.get("type") == "tool_call":
                    tools.append(d.get("content", ""))
            except:
                pass
    text = "".join(tokens)
    return {
        "time": round(elapsed, 1),
        "chars": len(text),
        "sources": len(sources),
        "tools": tools,
        "text": text,
        "has_ages": any(x in text for x in ["### I", "### II", "### III", "### IV"]),
        "has_matchups": "### V" in text or "Matchup" in text.lower(),
        "has_rating": "Valoraci" in text or "Rating" in text,
        "bad_ages": "Segunda Edad" in text or "Tercera Edad" in text or "Cuarta Edad" in text,
    }


TESTS = [
    # === CIV GUIDES — different phrasings ===
    ("ES", "CIV", "Que estrategia sigo con los rusos?"),
    ("EN", "CIV", "Give me a guide for Ottomans"),
    ("ES", "CIV", "Como se juegan los chinos en ranked?"),
    ("EN", "CIV", "Tips for playing Malians"),
    ("ES", "CIV", "Explicame como jugar ingleses"),
    ("EN", "CIV", "Ayyubids strategy for 1v1"),
    ("ES", "CIV", "Que hago con los abasidas?"),
    ("EN", "CIV", "French gameplay guide"),
    ("ES", "CIV", "Quiero aprender bizantinos"),
    ("EN", "CIV", "Delhi Sultanate tips and tricks"),

    # === MATCHUPS CRUZADOS ===
    ("ES", "MU", "Mongoles contra franceses, como juego?"),
    ("EN", "MU", "English vs Ottomans matchup"),
    ("ES", "MU", "HRE contra chinos, que hago?"),
    ("EN", "MU", "Byzantines vs Rus who wins?"),
    ("ES", "MU", "Como gano con japoneses contra mongoles?"),

    # === COUNTERS ESPECIFICOS ===
    ("EN", "CTR", "How to counter mass horsemen?"),
    ("ES", "CTR", "Que hago contra rush de piqueros?"),
    ("EN", "CTR", "Best counter to bombards?"),
    ("ES", "CTR", "Como defiendo un tower rush?"),
    ("EN", "CTR", "How to deal with Mangudai?"),

    # === UNIT STATS ===
    ("EN", "DAT", "Crossbowman stats"),
    ("ES", "DAT", "Estadisticas del arquero de arco largo"),
    ("EN", "DAT", "Compare Horseman vs Knight"),
    ("ES", "DAT", "Cuanto cuesta un ariete?"),
    ("EN", "DAT", "What is the HP of a Keep?"),

    # === PLAYERS ===
    ("EN", "PLR", "Who is the number 1 player right now?"),
    ("ES", "PLR", "Top jugadores de Francia"),
    ("EN", "PLR", "VortiX player profile"),
    ("ES", "PLR", "Busca a DeMusliM"),
    ("EN", "PLR", "Best players from China"),

    # === STRATEGY ===
    ("ES", "STR", "Cual es la mejor civ para principiantes?"),
    ("EN", "STR", "What are the strongest civs this season?"),
    ("ES", "STR", "Como hago un rush feudal?"),
    ("EN", "STR", "Best water map civs?"),
    ("ES", "STR", "Como defiendo un fast castle?"),

    # === BUILD ORDERS ===
    ("ES", "BO", "Build order para rush de caballeros franceses"),
    ("EN", "BO", "Mongol tower rush build order"),
    ("ES", "BO", "Build order de fast imperial con chinos"),

    # === PRO OPINIONS ===
    ("EN", "PRO", "What does MarineLorD think about the meta?"),
    ("ES", "PRO", "Que dice Valdemar sobre los japoneses?"),
    ("EN", "PRO", "Beastyqt tier list"),

    # === MECHANICS & LORE ===
    ("ES", "MEC", "Como funcionan los sitios sagrados?"),
    ("EN", "MEC", "How do relics work in AoE4?"),
    ("ES", "MEC", "Cuanto tiempo tarda una maravilla?"),
    ("EN", "MEC", "What are the victory conditions?"),

    # === EDGE CASES ===
    ("ES", "EDG", "Como juego con los celtas?"),
    ("EN", "EDG", "Britons guide"),
    ("ES", "EDG", "Que es mejor, AoE2 o AoE4?"),
    ("EN", "EDG", "When was AoE4 released?"),
    ("ES", "EDG", "Hola, que puedes hacer?"),
]

print(f"Running {len(TESTS)} tests (Round 2) against {API}\n")
print(f"{'#':>2} {'L':>2} {'Cat':>3} {'Time':>5} {'Chr':>5} {'Src':>3} {'Tls':>3} {'Age':>3} {'MU':>3} {'Rat':>3} {'Bad':>3} Query")
print("-" * 120)

results = []
errors = []
for i, (lang, cat, query) in enumerate(TESTS):
    r = query_bot(query)
    results.append((lang, cat, query, r))

    if "error" in r:
        print(f"{i+1:>2} {lang:>2} {cat:>3} ERROR {query[:60]}")
        errors.append((i+1, query, r["error"]))
        continue

    ages = "Y" if r["has_ages"] else "-"
    mu = "Y" if r["has_matchups"] else "-"
    rat = "Y" if r["has_rating"] else "-"
    bad = "!" if r["bad_ages"] else "-"
    tls = len(r["tools"])
    print(f"{i+1:>2} {lang:>2} {cat:>3} {r['time']:>5}s {r['chars']:>5} {r['sources']:>3} {tls:>3} {ages:>3} {mu:>3} {rat:>3} {bad:>3} {query[:60]}")

# === SUMMARY ===
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

valid = [(l, c, q, r) for l, c, q, r in results if "error" not in r]
total = len(valid)
avg_time = sum(r["time"] for _, _, _, r in valid) / total if total else 0
total_time = sum(r["time"] for _, _, _, r in valid)

print(f"Total: {len(TESTS)} tests, {total} OK, {len(errors)} errors")
print(f"Avg time: {avg_time:.1f}s | Total time: {total_time:.0f}s")

# Civ guide stats
civ_results = [(l, c, q, r) for l, c, q, r in valid if c == "CIV"]
if civ_results:
    civ_ages = sum(1 for _, _, _, r in civ_results if r["has_ages"])
    civ_mu = sum(1 for _, _, _, r in civ_results if r["has_matchups"])
    civ_rat = sum(1 for _, _, _, r in civ_results if r["has_rating"])
    civ_bad = sum(1 for _, _, _, r in civ_results if r["bad_ages"])
    civ_avg = sum(r["time"] for _, _, _, r in civ_results) / len(civ_results)
    print(f"\nCiv Guides ({len(civ_results)}):")
    print(f"  Ages:     {civ_ages}/{len(civ_results)}")
    print(f"  Matchups: {civ_mu}/{len(civ_results)}")
    print(f"  Ratings:  {civ_rat}/{len(civ_results)}")
    print(f"  Bad ages: {civ_bad}/{len(civ_results)}")
    print(f"  Avg time: {civ_avg:.1f}s")

# Stats by category
for cat_name, cat_code in [("Matchups", "MU"), ("Counters", "CTR"), ("Game Data", "DAT"),
                            ("Players", "PLR"), ("Strategy", "STR"), ("Build Orders", "BO"),
                            ("Pro Opinions", "PRO"), ("Mechanics", "MEC"), ("Edge Cases", "EDG")]:
    cat_results = [(l, c, q, r) for l, c, q, r in valid if c == cat_code]
    if cat_results:
        cat_avg = sum(r["time"] for _, _, _, r in cat_results) / len(cat_results)
        cat_tools = sum(len(r["tools"]) for _, _, _, r in cat_results) / len(cat_results)
        print(f"\n{cat_name} ({len(cat_results)}):")
        print(f"  Avg time: {cat_avg:.1f}s | Avg tools: {cat_tools:.1f}")

# Issues
print("\n" + "=" * 80)
print("ISSUES FOUND")
print("=" * 80)
issues = []
for _, cat, query, r in results:
    if "error" in r:
        continue
    if cat == "CIV" and not r["has_ages"]:
        issues.append(f"MISSING AGES: {query}")
    if cat == "CIV" and not r["has_matchups"]:
        issues.append(f"MISSING MATCHUPS: {query}")
    if cat == "CIV" and not r["has_rating"]:
        issues.append(f"MISSING RATING: {query}")
    if r["bad_ages"]:
        issues.append(f"BAD AGE NAMES: {query}")
    if r["chars"] == 0:
        issues.append(f"EMPTY RESPONSE: {query}")
    if r["time"] > 25:
        issues.append(f"TOO SLOW ({r['time']}s): {query}")
    # Check edge cases - non-AoE4 civs should NOT have guide content
    if cat == "EDG" and ("celtas" in query.lower() or "britons" in query.lower()):
        if r["has_ages"]:
            issues.append(f"FALSE CIV GUIDE (should say not in AoE4): {query}")

if issues:
    for iss in issues:
        print(f"  - {iss}")
else:
    print("  None! All tests passed.")

# Show interesting responses
print("\n" + "=" * 80)
print("NOTABLE RESPONSES (first 200 chars)")
print("=" * 80)
notable_cats = {"EDG", "MEC", "PRO"}
for _, cat, query, r in results:
    if "error" in r:
        continue
    if cat in notable_cats:
        print(f"\nQ: {query}")
        print(f"A: {r['text'][:200].replace(chr(10), ' ')}...")
