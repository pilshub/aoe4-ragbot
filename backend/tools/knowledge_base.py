"""Tool for searching pro player YouTube content via SQLite + OpenAI embeddings."""

from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from models import Source

EMBEDDING_MODEL = "text-embedding-3-small"
_async_client: AsyncOpenAI | None = None


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
    """Search pro player YouTube content for strategy guides, tier lists, and tips."""
    import knowledge

    if knowledge.count() == 0:
        return "Pro content knowledge base is empty. No YouTube transcripts have been ingested yet.", []

    # Generate query embedding
    client = _get_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_embedding = response.data[0].embedding

    # Search knowledge base
    results = knowledge.search(
        query_embedding=query_embedding,
        n_results=min(n_results, 10),
        channel=channel,
        language=language,
    )

    if not results:
        return f"No relevant pro content found for '{query}'.", []

    # Format results
    lines = []
    sources = []

    for r in results:
        meta = r["metadata"]
        similarity = r["similarity"]
        doc = r["document"]

        ts_start = meta.get("timestamp_start", 0)
        minutes = ts_start // 60
        seconds = ts_start % 60

        video_url = meta.get("url", "")
        channel_name = meta.get("channel", "Unknown")
        title = meta.get("title", "Unknown")
        date = meta.get("upload_date", "")

        # Format date nicely
        date_display = ""
        if date and len(date) == 8:
            date_display = f"{date[:4]}-{date[4:6]}-{date[6:]}"

        lines.append(f"### {title} — {channel_name}")
        lines.append(f"**Relevance:** {similarity:.0%} | **Timestamp:** {minutes}:{seconds:02d} | **Date:** {date_display}")
        lines.append(f"**Link:** {video_url}")
        lines.append(f"\n> {doc[:800]}\n")

        sources.append(Source(
            type="youtube",
            title=f"{channel_name}: {title} ({minutes}:{seconds:02d})",
            url=video_url,
        ))

    result = "\n".join(lines)
    return result, sources
