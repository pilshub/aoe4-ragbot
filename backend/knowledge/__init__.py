"""SQLite-based vector knowledge base for AoE4 pro content.

Stores text chunks with OpenAI embeddings in SQLite. Computes cosine
similarity with numpy for semantic search. No external vector DB needed.
"""

import json
import os
import sqlite3
from typing import Any

import numpy as np

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "knowledge.db")

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(DB_DIR, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_schema(_conn)
    return _conn


def _init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            document TEXT NOT NULL,
            embedding BLOB NOT NULL,
            source TEXT NOT NULL,
            channel TEXT,
            title TEXT,
            video_id TEXT,
            url TEXT,
            upload_date TEXT,
            language TEXT,
            timestamp_start INTEGER,
            timestamp_end INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_video_id ON chunks(video_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_channel ON chunks(channel);
    """)
    conn.commit()


def count() -> int:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
    return row[0] if row else 0


def has_video(video_id: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM chunks WHERE video_id = ? LIMIT 1", (video_id,)).fetchone()
    return row is not None


def upsert_chunks(
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
):
    """Insert or replace chunks with their embeddings and metadata."""
    conn = get_conn()
    for chunk_id, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
        emb_blob = np.array(emb, dtype=np.float32).tobytes()
        conn.execute(
            """INSERT OR REPLACE INTO chunks
               (id, document, embedding, source, channel, title, video_id, url, upload_date, language, timestamp_start, timestamp_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk_id,
                doc,
                emb_blob,
                meta.get("source", ""),
                meta.get("channel", ""),
                meta.get("title", ""),
                meta.get("video_id", ""),
                meta.get("url", ""),
                meta.get("upload_date", ""),
                meta.get("language", ""),
                meta.get("timestamp_start", 0),
                meta.get("timestamp_end", 0),
            ),
        )
    conn.commit()


def search(
    query_embedding: list[float],
    n_results: int = 5,
    channel: str | None = None,
    language: str | None = None,
) -> list[dict]:
    """Search for the most similar chunks using cosine similarity."""
    conn = get_conn()

    # Build query with optional filters
    sql = "SELECT id, document, embedding, source, channel, title, video_id, url, upload_date, language, timestamp_start, timestamp_end FROM chunks"
    conditions = []
    params: list[Any] = []
    if channel:
        conditions.append("channel = ?")
        params.append(channel)
    if language:
        conditions.append("language = ?")
        params.append(language)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    rows = conn.execute(sql, params).fetchall()
    if not rows:
        return []

    # Compute cosine similarities
    query_vec = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return []

    results = []
    for row in rows:
        emb = np.frombuffer(row["embedding"], dtype=np.float32)
        emb_norm = np.linalg.norm(emb)
        if emb_norm == 0:
            continue
        similarity = float(np.dot(query_vec, emb) / (query_norm * emb_norm))
        results.append({
            "id": row["id"],
            "document": row["document"],
            "similarity": similarity,
            "metadata": {
                "source": row["source"],
                "channel": row["channel"],
                "title": row["title"],
                "video_id": row["video_id"],
                "url": row["url"],
                "upload_date": row["upload_date"],
                "language": row["language"],
                "timestamp_start": row["timestamp_start"],
                "timestamp_end": row["timestamp_end"],
            },
        })

    # Sort by similarity (highest first) and return top N
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:n_results]


def reset():
    """Delete all chunks. Used during full re-ingestion."""
    conn = get_conn()
    conn.execute("DELETE FROM chunks")
    conn.commit()


def close():
    global _conn
    if _conn:
        _conn.close()
        _conn = None
