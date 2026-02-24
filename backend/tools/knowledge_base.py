"""Tool for searching pro player content via SQLite + OpenAI embeddings.

Searches both Vortix's written civilization guides and YouTube transcript
excerpts from pro players (Beastyqt, Valdemar, Vortix, MarineLorD).

When the query mentions a specific civilization, loads that civ's full guide
as context (no chunking loss) and supplements with YouTube semantic search.
"""

import os
import re

from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from models import Source

EMBEDDING_MODEL = "text-embedding-3-small"
GUIDES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "guides")
_async_client: AsyncOpenAI | None = None

# Maps aliases (lowercase) to civ_id used in guide filenames (e.g., byzantines.md)
# IMPORTANT: These must match the .md filenames in data/guides/
CIV_ALIASES: dict[str, str] = {
    # English names
    "abbasid": "abbasid_dynasty", "abbasid dynasty": "abbasid_dynasty",
    "ayyubids": "ayyubids", "ayyubid": "ayyubids",
    "byzantines": "byzantines", "byzantine": "byzantines", "byz": "byzantines",
    "chinese": "chinese", "china": "chinese",
    "delhi": "delhi_sultanate", "delhi sultanate": "delhi_sultanate",
    "english": "english",
    "french": "french", "france": "french",
    "holy roman empire": "holy_roman_empire", "hre": "holy_roman_empire",
    "japanese": "japanese", "japan": "japanese",
    "jeanne d'arc": "jeannes_darc", "jeanne darc": "jeannes_darc", "joan of arc": "jeannes_darc",
    "malians": "malians", "mali": "malians",
    "mongols": "mongols", "mongol": "mongols",
    "order of the dragon": "order_of_the_dragon", "ootd": "order_of_the_dragon", "dragon": "order_of_the_dragon", "order dragon": "order_of_the_dragon",
    "ottomans": "ottomans", "ottoman": "ottomans",
    "rus": "rus",
    "zhu xi": "zhuxis_legacy", "zhu xi's legacy": "zhuxis_legacy", "zhu xis legacy": "zhuxis_legacy",
    "house of lancaster": "house_of_lancaster", "lancaster": "house_of_lancaster",
    "golden horde": "golden_horde", "horda dorada": "golden_horde",
    "knights templar": "knights_templar", "templar": "knights_templar", "templarios": "knights_templar",
    "macedonian dynasty": "macedonian_dynasty", "macedonians": "macedonian_dynasty",
    "sengoku daimyo": "sengoku_daimyo", "sengoku": "sengoku_daimyo",
    "tughlaq dynasty": "tughlaq_dynasty", "tughlaq": "tughlaq_dynasty",
    # Spanish names
    "abasidas": "abbasid_dynasty", "abasí": "abbasid_dynasty", "abasi": "abbasid_dynasty", "abasida": "abbasid_dynasty", "dinastía abasí": "abbasid_dynasty",
    "ayubidas": "ayyubids", "ayubíes": "ayyubids",
    "bizantinos": "byzantines", "bizantino": "byzantines",
    "chinos": "chinese", "chino": "chinese",
    "sultanato de delhi": "delhi_sultanate",
    "ingleses": "english", "inglés": "english", "ingles": "english",
    "franceses": "french", "francés": "french", "frances": "french",
    "sacro imperio": "holy_roman_empire", "sacro imperio romano": "holy_roman_empire",
    "japoneses": "japanese", "japonés": "japanese", "japones": "japanese",
    "juana de arco": "jeannes_darc",
    "malienses": "malians",
    "mongoles": "mongols",
    "orden del dragón": "order_of_the_dragon", "orden del dragon": "order_of_the_dragon",
    "otomanos": "ottomans", "otomano": "ottomans",
    "rusos": "rus", "ruso": "rus",
    "legado de zhu xi": "zhuxis_legacy",
    "casa de lancaster": "house_of_lancaster",
    "dinastía macedonia": "macedonian_dynasty", "macedonios": "macedonian_dynasty",
    "dinastía tughlaq": "tughlaq_dynasty",
}

# Display names for guide source citations
CIV_DISPLAY: dict[str, str] = {
    "abbasid_dynasty": "Abbasid Dynasty", "ayyubids": "Ayyubids",
    "byzantines": "Byzantines", "chinese": "Chinese",
    "delhi_sultanate": "Delhi Sultanate", "english": "English",
    "french": "French", "holy_roman_empire": "Holy Roman Empire",
    "japanese": "Japanese", "jeannes_darc": "Jeanne d'Arc",
    "malians": "Malians", "mongols": "Mongols",
    "order_of_the_dragon": "Order of the Dragon", "ottomans": "Ottomans",
    "rus": "Rus", "zhuxis_legacy": "Zhu Xi's Legacy",
    "knights_templar": "Knights Templar", "house_of_lancaster": "House of Lancaster",
    "golden_horde": "Golden Horde", "macedonian_dynasty": "Macedonian Dynasty",
    "sengoku_daimyo": "Sengoku Daimyo", "tughlaq_dynasty": "Tughlaq Dynasty",
}

# Build regex pattern: sort by length (longest first) to match multi-word names first
_sorted_aliases = sorted(CIV_ALIASES.keys(), key=len, reverse=True)
_CIV_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(a) for a in _sorted_aliases) + r')\b',
    re.IGNORECASE,
)


def _detect_civ(query: str) -> str | None:
    """Detect civilization name in query, return civ_id or None."""
    m = _CIV_PATTERN.search(query.lower())
    if m:
        return CIV_ALIASES.get(m.group(1).lower())
    return None


def _load_guide(civ_id: str) -> str | None:
    """Load a civ's full guide markdown from disk. Returns None if not found."""
    path = os.path.join(GUIDES_DIR, f"{civ_id}.md")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _get_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _async_client


async def search_pro_content(
    query: str,
    channel: str | None = None,
    language: str | None = None,
    n_results: int = 5,
) -> tuple[str, list[Source]]:
    """Search pro player content: Vortix's written guides + YouTube transcripts.

    When the query mentions a specific civilization, loads the FULL guide
    as context (no chunking) and supplements with YouTube semantic search.
    When no civ is detected, falls back to standard semantic search.
    """
    import knowledge

    if knowledge.count() == 0:
        return "Pro content knowledge base is empty. No content has been ingested yet.", []

    lines: list[str] = []
    sources: list[Source] = []

    # Detect civilization in query
    detected_civ = _detect_civ(query)

    # If civ detected, load full guide from disk (no chunking loss)
    guide_loaded = False
    if detected_civ:
        guide_text = _load_guide(detected_civ)
        if guide_text:
            civ_name = CIV_DISPLAY.get(detected_civ, detected_civ)
            lines.append(f"### Guía de Vortix — {civ_name} [Full Written Guide]")
            lines.append(f"**Source:** Vortix's exclusive written guide (complete)\n")
            lines.append(guide_text)
            lines.append("")
            sources.append(Source(
                type="guide",
                title=f"Guía de Vortix — {civ_name}",
                url="",
            ))
            guide_loaded = True

    # If we loaded a full guide, skip the expensive embedding call — the guide
    # has everything needed. Only do semantic search when no guide was loaded.
    results: list[dict] = []
    if not guide_loaded:
        client = _get_client()
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = response.data[0].embedding

        cap = min(n_results, 10)
        results = knowledge.search(
            query_embedding=query_embedding,
            n_results=cap,
            channel=channel,
            language=language,
        )

    if not results and not guide_loaded:
        return f"No relevant pro content found for '{query}'.", []

    # Format semantic search results
    seen_sources: set[str] = set()
    for r in results:
        meta = r["metadata"]
        source_type = meta.get("source", "youtube")

        # Skip guide chunks if we already loaded the full guide
        if guide_loaded and source_type == "vortix_guide":
            continue

        similarity = r["similarity"]
        doc = r["document"]
        channel_name = meta.get("channel", "Unknown")
        title = meta.get("title", "Unknown")
        date = meta.get("upload_date", "")

        date_display = ""
        if date and len(date) == 8:
            date_display = f"{date[:4]}-{date[4:6]}-{date[6:]}"

        if source_type == "vortix_guide":
            # Only reached when no civ was detected
            lines.append(f"### {title} [Written Guide]")
            lines.append(f"**Relevance:** {similarity:.0%} | **Source:** Vortix's exclusive written guide")
            lines.append(f"\n> {doc[:1000]}\n")

            if title not in seen_sources:
                seen_sources.add(title)
                sources.append(Source(type="guide", title=title, url=""))
        else:
            ts_start = meta.get("timestamp_start", 0)
            minutes = ts_start // 60
            seconds = ts_start % 60
            video_url = meta.get("url", "")
            video_id = meta.get("video_id", "")

            lines.append(f"### {title} — {channel_name}")
            lines.append(f"**Relevance:** {similarity:.0%} | **Timestamp:** {minutes}:{seconds:02d} | **Date:** {date_display}")
            lines.append(f"**Link:** {video_url}")
            lines.append(f"\n> {doc[:800]}\n")

            if video_id not in seen_sources:
                seen_sources.add(video_id)
                sources.append(Source(
                    type="youtube",
                    title=f"{channel_name}: {title} ({minutes}:{seconds:02d})",
                    url=video_url,
                ))

    return "\n".join(lines), sources
