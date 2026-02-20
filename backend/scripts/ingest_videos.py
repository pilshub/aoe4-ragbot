"""
Ingest approved YouTube videos into the knowledge base.

Reads video_candidates.json, downloads transcripts via Apify,
chunks them, generates embeddings via OpenAI, and stores in SQLite.

Usage:
    cd backend
    python -m scripts.ingest_videos
    python -m scripts.ingest_videos --reset  # Re-ingest everything from scratch
"""

import argparse
import json
import os
import sys
import time

import httpx
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import knowledge

# --- Configuration ---

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
EMBEDDING_BATCH_SIZE = 50
TRANSCRIPT_DELAY = 3  # seconds between YouTube requests (fallback only)

# Apify actor for YouTube transcripts
APIFY_ACTOR = "karamelo~youtube-transcripts"
APIFY_BATCH_SIZE = 25  # videos per Apify run

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CATALOG_PATH = os.path.join(DATA_DIR, "video_candidates.json")
TRANSCRIPT_CACHE_PATH = os.path.join(DATA_DIR, "transcript_cache.json")


def download_transcripts_apify(video_ids: list[str]) -> dict[str, list[str]]:
    """Download transcripts for multiple videos via Apify in batches.

    Returns dict mapping video_id -> list of caption strings.
    """
    apify_token = os.getenv("APIFY_API_TOKEN", "")
    if not apify_token:
        print("ERROR: APIFY_API_TOKEN not set in .env")
        sys.exit(1)

    # Load existing cache
    cache = {}
    if os.path.exists(TRANSCRIPT_CACHE_PATH):
        with open(TRANSCRIPT_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)

    # Filter out already-cached videos
    needed = [vid for vid in video_ids if vid not in cache]
    if not needed:
        print(f"All {len(video_ids)} transcripts already cached")
        return {vid: cache[vid] for vid in video_ids if vid in cache}

    print(f"Downloading {len(needed)} transcripts via Apify ({len(cache)} already cached)...")

    for batch_start in range(0, len(needed), APIFY_BATCH_SIZE):
        batch = needed[batch_start:batch_start + APIFY_BATCH_SIZE]
        batch_num = batch_start // APIFY_BATCH_SIZE + 1
        total_batches = (len(needed) + APIFY_BATCH_SIZE - 1) // APIFY_BATCH_SIZE
        print(f"\n  [Apify batch {batch_num}/{total_batches}] {len(batch)} videos...")

        urls = [f"https://www.youtube.com/watch?v={vid}" for vid in batch]

        try:
            response = httpx.post(
                f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items?token={apify_token}",
                json={
                    "urls": urls,
                    "maxRetries": 4,
                    "proxyOptions": {"useApifyProxy": True},
                },
                timeout=300,  # 5 min per batch
            )

            if response.status_code not in (200, 201):
                print(f"  [ERROR] Apify returned {response.status_code}: {response.text[:200]}")
                continue

            results = response.json()
            batch_ok = 0
            batch_empty = 0

            for item in results:
                vid = item.get("videoId", "")
                captions = item.get("captions", [])
                if vid and captions:
                    cache[vid] = captions
                    batch_ok += 1
                elif vid:
                    cache[vid] = []  # Cache empty result too to avoid re-fetching
                    batch_empty += 1

            print(f"  [OK] {batch_ok} transcripts, {batch_empty} empty/disabled")

        except httpx.TimeoutException:
            print(f"  [ERROR] Apify timeout for batch {batch_num}. Retrying with smaller batch...")
            # Retry individually for remaining videos in this batch
            for vid in batch:
                if vid in cache:
                    continue
                try:
                    resp = httpx.post(
                        f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items?token={apify_token}",
                        json={
                            "urls": [f"https://www.youtube.com/watch?v={vid}"],
                            "maxRetries": 2,
                            "proxyOptions": {"useApifyProxy": True},
                        },
                        timeout=120,
                    )
                    if resp.status_code in (200, 201):
                        items = resp.json()
                        if items and items[0].get("captions"):
                            cache[vid] = items[0]["captions"]
                        else:
                            cache[vid] = []
                except Exception as e:
                    print(f"    [ERROR] {vid}: {str(e)[:100]}")

        except Exception as e:
            print(f"  [ERROR] Apify batch failed: {str(e)[:200]}")

        # Save cache after each batch
        with open(TRANSCRIPT_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    # Return results for requested videos
    return {vid: cache.get(vid, []) for vid in video_ids}


def download_transcript_fallback(video_id: str, language_hint: str = "en") -> list[dict] | None:
    """Fallback: download transcript via youtube-transcript-api (direct, no proxy)."""
    from youtube_transcript_api import YouTubeTranscriptApi

    langs = []
    if language_hint and language_hint != "en":
        langs.append(language_hint)
    langs.extend(["en", "es", "fr"])
    seen = set()
    langs = [l for l in langs if not (l in seen or seen.add(l))]

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(langs)
        except Exception:
            pass
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(langs)
            except Exception:
                pass

        if transcript is None:
            return None

        if transcript.language_code not in ("en", "es"):
            try:
                transcript = transcript.translate("en")
            except Exception:
                pass

        fetched = transcript.fetch()
        segments = []
        for snippet in fetched:
            segments.append({
                "text": snippet.text if hasattr(snippet, "text") else str(snippet),
                "start": snippet.start if hasattr(snippet, "start") else 0.0,
                "duration": snippet.duration if hasattr(snippet, "duration") else 0.0,
            })
        return segments if segments else None

    except Exception:
        return None


def captions_to_segments(captions: list[str], video_duration_secs: int = 0) -> list[dict]:
    """Convert Apify captions (list of strings) to segments with estimated timestamps."""
    if not captions:
        return []

    # Estimate timestamps based on even distribution across video duration
    # If we don't know duration, estimate ~3 seconds per caption segment
    if video_duration_secs > 0:
        time_per_segment = video_duration_secs / len(captions)
    else:
        time_per_segment = 3.0

    segments = []
    for i, text in enumerate(captions):
        if not text:
            continue
        text = text.strip()
        if text:
            segments.append({
                "text": text,
                "start": i * time_per_segment,
                "duration": time_per_segment,
            })
    return segments


def chunk_transcript(segments: list[dict]) -> list[dict]:
    """Chunk transcript segments into ~500-token pieces with overlap."""
    enc = tiktoken.encoding_for_model("gpt-4o-mini")

    chunks = []
    current_text = ""
    current_tokens = 0
    chunk_start_time = segments[0]["start"] if segments else 0

    for seg in segments:
        seg_text = seg["text"].strip()
        if not seg_text:
            continue
        seg_tokens = len(enc.encode(seg_text))

        if current_tokens + seg_tokens > CHUNK_SIZE_TOKENS and current_text:
            # Finalize current chunk
            chunks.append({
                "text": current_text.strip(),
                "timestamp_start": chunk_start_time,
                "timestamp_end": seg["start"],
                "token_count": current_tokens,
            })

            # Overlap: keep last N tokens worth of words
            words = current_text.strip().split()
            overlap_text = ""
            overlap_tokens = 0
            for word in reversed(words):
                wt = len(enc.encode(word))
                if overlap_tokens + wt > CHUNK_OVERLAP_TOKENS:
                    break
                overlap_text = word + " " + overlap_text
                overlap_tokens += wt

            current_text = overlap_text.strip() + " " + seg_text
            current_tokens = len(enc.encode(current_text))
            chunk_start_time = seg["start"]
        else:
            if current_text:
                current_text += " " + seg_text
            else:
                current_text = seg_text
            current_tokens += seg_tokens

    # Final chunk
    if current_text.strip():
        last_seg = segments[-1]
        chunks.append({
            "text": current_text.strip(),
            "timestamp_start": chunk_start_time,
            "timestamp_end": last_seg["start"] + last_seg.get("duration", 0),
            "token_count": current_tokens,
        })

    return chunks


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    all_embeddings = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([d.embedding for d in response.data])
    return all_embeddings


def store_chunks(chunks: list[dict], video_meta: dict, embeddings: list[list[float]]):
    """Store embedded chunks in SQLite knowledge base."""
    ids = [f"{video_meta['video_id']}_chunk_{i}" for i in range(len(chunks))]

    metadatas = []
    documents = []
    for c in chunks:
        ts_start = int(c["timestamp_start"])
        documents.append(c["text"])
        metadatas.append({
            "source": "youtube",
            "channel": video_meta["channel"],
            "title": video_meta["title"],
            "video_id": video_meta["video_id"],
            "url": f"https://www.youtube.com/watch?v={video_meta['video_id']}&t={ts_start}",
            "upload_date": video_meta.get("upload_date", ""),
            "language": video_meta.get("language_hint", "en"),
            "timestamp_start": ts_start,
            "timestamp_end": int(c["timestamp_end"]),
        })

    knowledge.upsert_chunks(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def main():
    parser = argparse.ArgumentParser(description="Ingest approved YouTube videos into knowledge base")
    parser.add_argument("--reset", action="store_true", help="Reset knowledge base and re-ingest everything")
    parser.add_argument("--no-apify", action="store_true", help="Use youtube-transcript-api directly (slower, may hit rate limits)")
    args = parser.parse_args()

    # Load catalog
    if not os.path.exists(CATALOG_PATH):
        print(f"No catalog found at {CATALOG_PATH}")
        print("Run `python -m scripts.scrape_youtube` first.")
        sys.exit(1)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        videos = json.load(f)

    approved = [v for v in videos if v.get("approved")]
    if not approved:
        print("No approved videos found. Edit video_candidates.json and set 'approved': true.")
        sys.exit(1)

    print(f"Found {len(approved)} approved videos")

    # Initialize OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in .env")
        sys.exit(1)

    openai_client = OpenAI(api_key=api_key)

    if args.reset:
        print("Resetting knowledge base...")
        knowledge.reset()

    print(f"Current knowledge base size: {knowledge.count()} chunks")

    # Filter videos that need ingesting
    to_ingest = []
    already_done = 0
    for video in approved:
        if not args.reset and knowledge.has_video(video["video_id"]):
            already_done += 1
        else:
            to_ingest.append(video)

    if already_done:
        print(f"Skipping {already_done} already-ingested videos")

    if not to_ingest:
        print("All approved videos are already ingested!")
        return

    print(f"Need to ingest: {len(to_ingest)} videos")

    # Step 1: Download ALL transcripts via Apify (batch)
    if not args.no_apify:
        video_ids = [v["video_id"] for v in to_ingest]
        transcripts_map = download_transcripts_apify(video_ids)
    else:
        transcripts_map = {}

    # Step 2: Process each video
    total_chunks = 0
    total_errors = 0

    for i, video in enumerate(to_ingest):
        video_id = video["video_id"]
        channel = video["channel"]
        title = video["title"]
        safe_title = title.encode("ascii", "replace").decode("ascii")
        print(f"\n[{i + 1}/{len(to_ingest)}] {channel}: {safe_title}")

        # Get transcript from Apify cache or fallback
        captions = transcripts_map.get(video_id, [])
        if captions:
            duration = video.get("duration_seconds", 0)
            segments = captions_to_segments(captions, duration)
            print(f"  [apify] {len(segments)} segments")
        else:
            # Fallback to direct youtube-transcript-api
            print(f"  [fallback] Trying youtube-transcript-api...")
            segments = download_transcript_fallback(video_id, video.get("language_hint", "en"))
            if segments:
                print(f"  [fallback] {len(segments)} segments")
            else:
                print(f"  [skip] No transcript available")
                total_errors += 1
                continue
            time.sleep(TRANSCRIPT_DELAY)

        # Chunk
        chunks = chunk_transcript(segments)
        if not chunks:
            print(f"  [skip] No usable chunks")
            total_errors += 1
            continue

        print(f"  [chunks] {len(chunks)} chunks ({sum(c['token_count'] for c in chunks)} tokens)")

        # Embed
        try:
            texts = [c["text"] for c in chunks]
            embeddings = embed_texts(openai_client, texts)
            print(f"  [embed] {len(embeddings)} embeddings generated")
        except Exception as e:
            print(f"  [ERROR] Embedding failed: {e}")
            total_errors += 1
            continue

        # Store
        try:
            store_chunks(chunks, video, embeddings)
            total_chunks += len(chunks)
            print(f"  [stored] {len(chunks)} chunks")
        except Exception as e:
            print(f"  [ERROR] Storage failed: {e}")
            total_errors += 1
            continue

        # Mark as ingested in catalog
        video["ingested"] = True

    # Save updated catalog
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"INGESTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  New chunks stored: {total_chunks}")
    print(f"  Already ingested: {already_done}")
    print(f"  Errors: {total_errors}")
    print(f"  Total chunks in knowledge base: {knowledge.count()}")


if __name__ == "__main__":
    main()
