"""50-query comprehensive test suite for AoE4 RAGBot."""

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
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        elapsed = time.time() - start
    except Exception as e:
        return {"error": str(e), "time": -1}

    tokens, sources = [], []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                d = json.loads(line[6:])
                if d.get("type") == "token":
                    tokens.append(d["content"])
                elif d.get("type") == "sources":
                    sources = d.get("sources", [])
            except:
                pass
    text = "".join(tokens)
    return {
        "time": round(elapsed, 1),
        "chars": len(text),
        "sources": len(sources),
        "text": text,
        "has_ages": any(x in text for x in ["### I", "### II", "### III", "### IV"]),
        "has_matchups": "### V" in text or "matchup" in text.lower(),
        "has_rating": "Valoraci" in text or "Rating" in text,
        "bad_ages": "Segunda Edad" in text or "Tercera Edad" in text or "Cuarta Edad" in text,
    }


TESTS = [
    # === CIV GUIDES (22 — all civs) ===
    ("ES", "CIV", "Como juego abasidas en 1v1?"),
    ("ES", "CIV", "Como juego ayubidas?"),
    ("EN", "CIV", "How to play Byzantines?"),
    ("ES", "CIV", "Guia de chinos"),
    ("ES", "CIV", "Como juego el sultanato de delhi?"),
    ("EN", "CIV", "English guide"),
    ("ES", "CIV", "Como juego franceses en 1v1?"),
    ("EN", "CIV", "How do I play HRE?"),
    ("ES", "CIV", "Dame la guia de japoneses"),
    ("ES", "CIV", "Como juego Juana de Arco?"),
    ("ES", "CIV", "Guia de malienses"),
    ("EN", "CIV", "How to play Mongols?"),
    ("ES", "CIV", "Como juego la Orden del Dragon?"),
    ("ES", "CIV", "Como juego con los otomanos?"),
    ("EN", "CIV", "Rus guide for 1v1"),
    ("EN", "CIV", "How to play Zhu Xi's Legacy?"),
    ("ES", "CIV", "Como se juegan los templarios?"),
    ("ES", "CIV", "Guia de la Casa de Lancaster"),
    ("ES", "CIV", "Como juego la Horda Dorada?"),
    ("ES", "CIV", "Como juego con los macedonios?"),
    ("EN", "CIV", "Sengoku Daimyo guide"),
    ("ES", "CIV", "Guia de la dinastia Tughlaq"),

    # === COUNTERS & MATCHUPS (6) ===
    ("EN", "CTR", "What counters knights?"),
    ("ES", "CTR", "Como contraresto mangoneles?"),
    ("EN", "CTR", "Best counter to mass archers?"),
    ("ES", "CTR", "Franceses vs Ingleses, quien gana?"),
    ("EN", "CTR", "Mongols vs French matchup"),
    ("ES", "CTR", "Como gano contra HRE?"),

    # === PLAYER QUERIES (5) ===
    ("EN", "PLR", "Show me the top 5 players"),
    ("ES", "PLR", "Busca al jugador Beastyqt"),
    ("EN", "PLR", "Top 3 players from Korea"),
    ("ES", "PLR", "Quien es el mejor jugador de España?"),
    ("EN", "PLR", "MarineLorD profile"),

    # === UNIT & GAME DATA (5) ===
    ("EN", "DAT", "What are the stats of the Man-at-Arms?"),
    ("ES", "DAT", "Comparame el caballero con el lancero"),
    ("EN", "DAT", "How much does a Trebuchet cost?"),
    ("ES", "DAT", "Que tecnologias tiene el herrero?"),
    ("EN", "DAT", "What is the range of a Longbowman?"),

    # === STRATEGY & META (4) ===
    ("EN", "STR", "What is the current meta?"),
    ("ES", "STR", "Cual es la mejor civ para 1v1?"),
    ("EN", "STR", "Best civ for team games?"),
    ("ES", "STR", "Que civ es mejor para hacer fast castle?"),

    # === BUILD ORDERS (2) ===
    ("ES", "BO", "Dame el build order de franceses"),
    ("EN", "BO", "English longbow rush build order"),

    # === PRO OPINIONS (2) ===
    ("ES", "PRO", "Que opina Beastyqt de los mongoles?"),
    ("EN", "PRO", "What does Vortix think about Byzantines?"),

    # === EDGE CASES (4) ===
    ("EN", "EDG", "How to play Aztecs?"),
    ("ES", "EDG", "Como juego con los vikingos?"),
    ("EN", "EDG", "What is the best wonder?"),
    ("ES", "EDG", "Que son los sitios sagrados?"),
]

print(f"Running {len(TESTS)} tests against {API}\n")
print(f"{'#':>2} {'L':>2} {'Cat':>3} {'Time':>5} {'Chr':>5} {'Src':>3} {'Age':>3} {'MU':>3} {'Rat':>3} {'Bad':>3} Query")
print("-" * 115)

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
    print(f"{i+1:>2} {lang:>2} {cat:>3} {r['time']:>5}s {r['chars']:>5} {r['sources']:>3} {ages:>3} {mu:>3} {rat:>3} {bad:>3} {query[:60]}")

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
civ_ages = sum(1 for _, _, _, r in civ_results if r["has_ages"])
civ_mu = sum(1 for _, _, _, r in civ_results if r["has_matchups"])
civ_rat = sum(1 for _, _, _, r in civ_results if r["has_rating"])
civ_bad = sum(1 for _, _, _, r in civ_results if r["bad_ages"])
civ_avg = sum(r["time"] for _, _, _, r in civ_results) / len(civ_results) if civ_results else 0
print(f"\nCiv Guides ({len(civ_results)}):")
print(f"  Ages present: {civ_ages}/{len(civ_results)}")
print(f"  Matchups:     {civ_mu}/{len(civ_results)}")
print(f"  Ratings:      {civ_rat}/{len(civ_results)}")
print(f"  Bad age names:{civ_bad}/{len(civ_results)}")
print(f"  Avg time:     {civ_avg:.1f}s")

# Non-civ stats by category
for cat_name, cat_code in [("Counters", "CTR"), ("Players", "PLR"), ("Game Data", "DAT"),
                            ("Strategy", "STR"), ("Build Orders", "BO"), ("Pro Opinions", "PRO"),
                            ("Edge Cases", "EDG")]:
    cat_results = [(l, c, q, r) for l, c, q, r in valid if c == cat_code]
    if cat_results:
        cat_avg = sum(r["time"] for _, _, _, r in cat_results) / len(cat_results)
        print(f"\n{cat_name} ({len(cat_results)}):")
        print(f"  Avg time: {cat_avg:.1f}s")

# Errors
if errors:
    print("\nERRORS:")
    for idx, q, err in errors:
        print(f"  #{idx}: {q[:50]} → {err[:80]}")

# Highlight any issues
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
    if r["time"] > 20:
        issues.append(f"TOO SLOW ({r['time']}s): {query}")

if issues:
    for iss in issues:
        print(f"  - {iss}")
else:
    print("  None! All tests passed.")
