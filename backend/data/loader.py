"""Downloads and caches static game data from data.aoe4world.com."""

import json
import os
import time
import asyncio
import aiohttp

from config import AOE4DATA_BASE

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_MAX_AGE = 7 * 24 * 3600  # 7 days

DATA_FILES = {
    "units": "/units/all.json",
    "buildings": "/buildings/all.json",
    "technologies": "/technologies/all.json",
}


def _cache_path(name: str) -> str:
    return os.path.join(CACHE_DIR, f"{name}.json")


def _cache_is_fresh(name: str) -> bool:
    path = _cache_path(name)
    if not os.path.exists(path):
        return False
    age = time.time() - os.path.getmtime(path)
    return age < CACHE_MAX_AGE


def _read_cache(name: str) -> list | None:
    path = _cache_path(name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_cache(name: str, data: list):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


async def _download(session: aiohttp.ClientSession, name: str, path: str) -> list | None:
    url = f"{AOE4DATA_BASE}{path}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                raw = await resp.json()
                # API wraps data in {"__note__": ..., "__version__": ..., "data": [...]}
                if isinstance(raw, dict) and "data" in raw:
                    data = raw["data"]
                else:
                    data = raw
                _write_cache(name, data)
                return data
    except Exception as e:
        print(f"[loader] Failed to download {name}: {e}")
    return None


async def load_all() -> dict[str, list]:
    """Load all game data. Uses cache if fresh, downloads otherwise."""
    result = {}

    # Check which files need downloading
    to_download = {}
    for name, path in DATA_FILES.items():
        if _cache_is_fresh(name):
            cached = _read_cache(name)
            if cached is not None:
                result[name] = cached
                print(f"[loader] {name}: loaded from cache ({len(cached)} items)")
                continue
        to_download[name] = path

    if to_download:
        async with aiohttp.ClientSession(
            headers={"User-Agent": "AoE4RAGBot/1.0"}
        ) as session:
            tasks = [
                _download(session, name, path)
                for name, path in to_download.items()
            ]
            results = await asyncio.gather(*tasks)
            for (name, _), data in zip(to_download.items(), results):
                if data is not None:
                    result[name] = data
                    print(f"[loader] {name}: downloaded ({len(data)} items)")
                else:
                    # Fallback to stale cache
                    cached = _read_cache(name)
                    if cached:
                        result[name] = cached
                        print(f"[loader] {name}: using stale cache ({len(cached)} items)")
                    else:
                        result[name] = []
                        print(f"[loader] {name}: NO DATA AVAILABLE")

    return result
