"""
Scrape YouTube channels for AoE4 educational video candidates.

Uses yt-dlp (metadata only, no video download) to list recent videos,
filters by title keywords and duration, outputs video_candidates.json
for human review.

Usage:
    cd backend
    python -m scripts.scrape_youtube
    python -m scripts.scrape_youtube --channels Beastyqt,Vortix --days 90
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta

import yt_dlp

# --- Configuration ---

CHANNELS = {
    "Beastyqt": "https://www.youtube.com/@BeastyqtSC2/videos",
    "Valdemar": "https://www.youtube.com/@Valdemar1902/videos",
    "Vortix": "https://www.youtube.com/@VortiX93/videos",
    "MarineLorD": "https://www.youtube.com/channel/UCHheEmSTX_NaAHSq2uwmlMg/videos",
}

# Language hints per channel
CHANNEL_LANGUAGES = {
    "Beastyqt": "en",
    "Valdemar": "en",
    "Vortix": "es",
    "MarineLorD": "en",
}

# Title must contain at least one of these (case-insensitive)
TITLE_KEYWORDS_EN = [
    "guide", "tier list", "tier-list", "build order", "how to", "tips",
    "strategy", "tutorial", "beginner", "advanced", "meta", "op ",
    "broken", "patch", "season", "best", "worst", "counter",
    "civilization", "civ ", "civs", "aoe4", "age of empires",
    "ranked", "matchup", "unit", "overview", "analysis", "explained",
]

TITLE_KEYWORDS_ES = [
    "guia", "guía", "tier", "orden de construccion", "consejos",
    "estrategia", "tutorial", "civilizacion", "civilización",
    "parche", "temporada", "mejor", "peor", "contra", "meta",
    "unidad", "análisis", "analisis", "como jugar", "cómo jugar",
]

ALL_KEYWORDS = TITLE_KEYWORDS_EN + TITLE_KEYWORDS_ES

MIN_DURATION_SECS = 180   # 3 minutes
MAX_DURATION_SECS = 3600  # 60 minutes
DEFAULT_MAX_AGE_DAYS = 180  # 6 months

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "video_candidates.json")


def matches_keywords(title: str) -> bool:
    """Check if title contains at least one relevant keyword."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in ALL_KEYWORDS)


def scrape_channel(channel_name: str, channel_url: str, date_after: str) -> list[dict]:
    """List videos from a YouTube channel using yt-dlp metadata extraction."""
    print(f"\n[{channel_name}] Scanning {channel_url}...")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": 100,  # Max 100 most recent videos
    }

    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = info.get("entries", []) if info else []

            print(f"  Found {len(entries)} total videos, filtering...")

            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get("id", "")
                title = entry.get("title", "")
                duration = entry.get("duration") or 0
                upload_date = entry.get("upload_date", "")

                # Skip if no essential data
                if not video_id or not title:
                    continue

                # Duration filter
                if duration < MIN_DURATION_SECS or duration > MAX_DURATION_SECS:
                    continue

                # Date filter (skip only if date IS present and too old)
                if upload_date and upload_date < date_after:
                    continue

                # Keyword filter
                if not matches_keywords(title):
                    continue

                videos.append({
                    "video_id": video_id,
                    "channel": channel_name,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "upload_date": upload_date or "",
                    "duration_seconds": duration,
                    "language_hint": CHANNEL_LANGUAGES.get(channel_name, "en"),
                    "approved": False,
                })

    except Exception as e:
        print(f"  [ERROR] Failed to scrape {channel_name}: {e}")

    print(f"  [{channel_name}] {len(videos)} candidate videos after filtering")
    return videos


def main():
    parser = argparse.ArgumentParser(description="Scrape AoE4 YouTube channels for educational content")
    parser.add_argument("--channels", type=str, default=None,
                        help="Comma-separated list of channels to scrape (default: all)")
    parser.add_argument("--days", type=int, default=DEFAULT_MAX_AGE_DAYS,
                        help=f"Max age in days (default: {DEFAULT_MAX_AGE_DAYS})")
    args = parser.parse_args()

    # Date cutoff
    cutoff = datetime.now() - timedelta(days=args.days)
    date_after = cutoff.strftime("%Y%m%d")
    print(f"Filtering videos from {cutoff.strftime('%Y-%m-%d')} onwards ({args.days} days)")

    # Select channels
    if args.channels:
        selected = [c.strip() for c in args.channels.split(",")]
        channels = {k: v for k, v in CHANNELS.items() if k in selected}
        if not channels:
            print(f"No matching channels. Available: {', '.join(CHANNELS.keys())}")
            sys.exit(1)
    else:
        channels = CHANNELS

    # Scrape each channel
    all_videos = []
    for name, url in channels.items():
        videos = scrape_channel(name, url, date_after)
        all_videos.extend(videos)

    # Sort by date (newest first)
    all_videos.sort(key=lambda v: v["upload_date"], reverse=True)

    # Load existing catalog to preserve approvals
    existing = {}
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            for v in json.load(f):
                existing[v["video_id"]] = v

    # Merge: keep approval status from existing entries
    for v in all_videos:
        if v["video_id"] in existing:
            v["approved"] = existing[v["video_id"]].get("approved", False)
            v["ingested"] = existing[v["video_id"]].get("ingested", False)

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {len(all_videos)} candidate videos")
    print(f"{'=' * 60}")
    by_channel = {}
    for v in all_videos:
        by_channel.setdefault(v["channel"], []).append(v)
    for ch, vids in sorted(by_channel.items()):
        approved = sum(1 for v in vids if v.get("approved"))
        print(f"  {ch}: {len(vids)} videos ({approved} already approved)")

    print(f"\nOutput saved to: {OUTPUT_PATH}")
    print(f"\nNext step: Review the file and set 'approved': true for videos you want to ingest.")
    print(f"Then run: python -m scripts.ingest_videos")


if __name__ == "__main__":
    main()
