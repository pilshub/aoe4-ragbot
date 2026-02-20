import asyncio
import re
import aiohttp

_session: aiohttp.ClientSession | None = None
_liquipedia_lock = asyncio.Lock()
_liquipedia_last_call = 0.0

USER_AGENT = "AoE4RAGBot/1.0 (contact: github.com/aoe4ragbot)"


async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            headers={"User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=15),
        )
    return _session


async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


async def fetch_json(url: str, params: dict | None = None) -> dict | list | None:
    """Fetch JSON from a URL. Returns None on error."""
    session = await get_session()
    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            return None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None


async def fetch_json_liquipedia(params: dict) -> dict | None:
    """Fetch from Liquipedia with rate limiting (1 req / 2 sec)."""
    global _liquipedia_last_call
    from config import LIQUIPEDIA_BASE, LIQUIPEDIA_MIN_INTERVAL

    async with _liquipedia_lock:
        now = asyncio.get_event_loop().time()
        wait = LIQUIPEDIA_MIN_INTERVAL - (now - _liquipedia_last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        _liquipedia_last_call = asyncio.get_event_loop().time()

    session = await get_session()
    try:
        async with session.get(LIQUIPEDIA_BASE, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            return None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None


def clean_wikitext(text: str) -> str:
    """Strip MediaWiki markup to plain text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove wiki links [[target|display]] -> display
    text = re.sub(r"\[\[[^\]]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Remove templates {{ }}
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    # Remove category links
    text = re.sub(r"\[\[Category:[^\]]+\]\]", "", text)
    # Remove bold/italic markers
    text = re.sub(r"'{2,}", "", text)
    # Remove section headers (== title ==) but keep title
    text = re.sub(r"={2,}\s*(.+?)\s*={2,}", r"\n\1\n", text)
    # Clean excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_chars: int = 3000) -> str:
    """Truncate text to max_chars, adding ellipsis if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
