"""
Incremental update: check for new videos and ingest them.

Looks at existing video_candidates.json, finds the latest date per channel,
scrapes new videos since then, and auto-ingests educational content.

Usage:
    cd backend
    python -m scripts.update_knowledge
    python -m scripts.update_knowledge --dry-run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.scrape_youtube import (
    CHANNELS, CHANNEL_LANGUAGES, matches_keywords,
    MIN_DURATION_SECS, MAX_DURATION_SECS,
)
from scripts.ingest_videos import (
    download_transcript, chunk_transcript, embed_texts,
    CATALOG_PATH, TRANSCRIPT_DELAY,
)

import time
import yt_dlp
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_latest_dates(videos: list[dict]) -> dict[str, str]:
    """Get the latest upload_date per channel from existing catalog."""
    latest = {}
    for v in videos:
        ch = v["channel"]
        date = v.get("upload_date", "")
        if date and (ch not in latest or date > latest[ch]):
            latest[ch] = date
    return latest


def find_new_videos(channel_name: str, channel_url: str, date_after: str) -> list[dict]:
    """Find new videos from a channel after a given date."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": 30,
    }

    new_videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = info.get("entries", []) if info else []

            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get("id", "")
                title = entry.get("title", "")
                duration = entry.get("duration") or 0
                upload_date = entry.get("upload_date", "")

                if not video_id or not title:
                    continue
                if upload_date and upload_date <= date_after:
                    continue
                if duration < MIN_DURATION_SECS or duration > MAX_DURATION_SECS:
                    continue
                if not matches_keywords(title):
                    continue

                new_videos.append({
                    "video_id": video_id,
                    "channel": channel_name,
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "upload_date": upload_date or "",
                    "duration_seconds": duration,
                    "language_hint": CHANNEL_LANGUAGES.get(channel_name, "en"),
                    "approved": True,  # Auto-approve for incremental updates
                })

    except Exception as e:
        print(f"  [ERROR] {channel_name}: {e}")

    return new_videos


def main():
    parser = argparse.ArgumentParser(description="Incremental knowledge base update")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added without doing it")
    args = parser.parse_args()

    # Load existing catalog
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            existing_videos = json.load(f)
    else:
        existing_videos = []

    existing_ids = {v["video_id"] for v in existing_videos}
    latest_dates = get_latest_dates(existing_videos)

    # Default: 30 days ago if no existing data for a channel
    default_after = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    print(f"Checking {len(CHANNELS)} channels for new videos...")
    if latest_dates:
        for ch, date in sorted(latest_dates.items()):
            print(f"  {ch}: latest video from {date}")

    all_new = []
    for name, url in CHANNELS.items():
        date_after = latest_dates.get(name, default_after)
        print(f"\n[{name}] Checking for videos after {date_after}...")
        new_videos = find_new_videos(name, url, date_after)

        # Filter out already known videos
        truly_new = [v for v in new_videos if v["video_id"] not in existing_ids]
        if truly_new:
            print(f"  Found {len(truly_new)} new videos")
            all_new.extend(truly_new)
        else:
            print(f"  No new videos")

    if not all_new:
        print("\nNo new videos to ingest. Everything is up to date.")
        return

    print(f"\n{'=' * 60}")
    print(f"NEW VIDEOS FOUND: {len(all_new)}")
    print(f"{'=' * 60}")
    for v in all_new:
        print(f"  [{v['channel']}] {v['title']} ({v['upload_date']})")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # Ingest new videos
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)

    openai_client = OpenAI(api_key=api_key)

    import knowledge

    ingested = 0
    for i, video in enumerate(all_new):
        print(f"\n[{i + 1}/{len(all_new)}] {video['channel']}: {video['title']}")

        transcript = download_transcript(video["video_id"], video.get("language_hint", "en"))
        if not transcript:
            continue
        time.sleep(TRANSCRIPT_DELAY)

        chunks = chunk_transcript(transcript)
        if not chunks:
            continue

        try:
            texts = [c["text"] for c in chunks]
            embeddings = embed_texts(openai_client, texts)

            ids = [f"{video['video_id']}_chunk_{j}" for j in range(len(chunks))]
            metadatas = []
            for c in chunks:
                ts_start = int(c["timestamp_start"])
                metadatas.append({
                    "source": "youtube",
                    "channel": video["channel"],
                    "title": video["title"],
                    "video_id": video["video_id"],
                    "url": f"https://www.youtube.com/watch?v={video['video_id']}&t={ts_start}",
                    "upload_date": video.get("upload_date", ""),
                    "language": video.get("language_hint", "en"),
                    "timestamp_start": ts_start,
                    "timestamp_end": int(c["timestamp_end"]),
                })

            knowledge.upsert_chunks(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
            video["ingested"] = True
            ingested += 1
            print(f"  [done] {len(chunks)} chunks stored")
        except Exception as e:
            print(f"  [ERROR] {e}")

    # Update catalog
    existing_videos.extend(all_new)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_videos, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"UPDATE COMPLETE: {ingested}/{len(all_new)} videos ingested")
    print(f"Total chunks in knowledge base: {knowledge.count()}")


if __name__ == "__main__":
    main()
