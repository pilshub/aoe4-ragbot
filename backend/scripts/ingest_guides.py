"""Ingest polished Vortix .md guides into the knowledge base.

Reads .md files from data/guides/, chunks them by section, generates embeddings,
and stores in knowledge.db alongside YouTube transcript chunks.

Usage:
    cd backend
    python -m scripts.ingest_guides
    python -m scripts.ingest_guides --dry-run     # Show chunks without ingesting
    python -m scripts.ingest_guides --reset        # Delete existing guide chunks first
"""

import argparse
import os
import re
import sys
import time

import numpy as np
import tiktoken

# Add parent to path so we can import knowledge
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

GUIDES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "guides")
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE_TOKENS = 400  # Slightly smaller than YouTube chunks — guides are denser
CHUNK_OVERLAP_TOKENS = 50

# Map filename to display info
CIV_DISPLAY = {
    "abbasid_dynasty": ("Abbasid Dynasty", "Dinastía Abasí"),
    "ayyubids": ("Ayyubids", "Ayubíes"),
    "byzantines": ("Byzantines", "Bizantinos"),
    "chinese": ("Chinese", "Chinos"),
    "delhi_sultanate": ("Delhi Sultanate", "Sultanato de Delhi"),
    "english": ("English", "Ingleses"),
    "french": ("French", "Franceses"),
    "golden_horde": ("Golden Horde", "Horda de Oro"),
    "holy_roman_empire": ("Holy Roman Empire", "Sacro Imperio Romano"),
    "house_of_lancaster": ("House of Lancaster", "Casa de Lancaster"),
    "japanese": ("Japanese", "Japoneses"),
    "jeannes_darc": ("Jeanne d'Arc", "Juana de Arco"),
    "knights_templar": ("Knights Templar", "Caballeros Templarios"),
    "macedonian_dynasty": ("Macedonian Dynasty", "Dinastía Macedonia"),
    "malians": ("Malians", "Malienses"),
    "mongols": ("Mongols", "Mongoles"),
    "order_of_the_dragon": ("Order of the Dragon", "Orden del Dragón"),
    "ottomans": ("Ottomans", "Otomanos"),
    "rus": ("Rus", "Rus"),
    "sengoku_daimyo": ("Sengoku Daimyo", "Sengoku Daimyo"),
    "tughlaq_dynasty": ("Tughlaq Dynasty", "Dinastía Tughlaq"),
    "zhuxis_legacy": ("Zhu Xi's Legacy", "Legado de Zhu Xi"),
}


def chunk_by_sections(text: str, civ_id: str) -> list[dict]:
    """Split markdown guide into chunks by sections, respecting token limits.

    Each chunk gets a context prefix with the civ name so it's self-contained
    even when retrieved in isolation.
    """
    enc = tiktoken.encoding_for_model("gpt-4o")
    civ_en, civ_es = CIV_DISPLAY.get(civ_id, (civ_id, civ_id))

    # Split by ## headers (keep headers with their content)
    sections = re.split(r'(?=^## )', text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    chunks = []
    for section in sections:
        # Extract section header for context
        header_match = re.match(r'^(#{2,4})\s+(.+)', section)
        section_header = header_match.group(2) if header_match else ""

        # Build context prefix
        prefix = f"[Guía de Vortix — {civ_es} ({civ_en})"
        if section_header and "Guía de Vortix" not in section_header:
            prefix += f" — {section_header}"
        prefix += "]\n\n"

        full_text = prefix + section
        tokens = enc.encode(full_text)

        if len(tokens) <= CHUNK_SIZE_TOKENS:
            chunks.append({"text": full_text, "section": section_header})
        else:
            # Split large sections into sub-chunks
            # Try splitting by ### subsections first
            subsections = re.split(r'(?=^### )', section, flags=re.MULTILINE)
            subsections = [s.strip() for s in subsections if s.strip()]

            if len(subsections) > 1:
                # Recurse on subsections
                for sub in subsections:
                    sub_header = re.match(r'^(#{2,4})\s+(.+)', sub)
                    sub_name = sub_header.group(2) if sub_header else section_header
                    sub_prefix = f"[Guía de Vortix — {civ_es} ({civ_en}) — {sub_name}]\n\n"
                    sub_full = sub_prefix + sub
                    sub_tokens = enc.encode(sub_full)

                    if len(sub_tokens) <= CHUNK_SIZE_TOKENS:
                        chunks.append({"text": sub_full, "section": sub_name})
                    else:
                        # Last resort: split by paragraphs
                        chunks.extend(_split_by_paragraphs(sub_full, sub_name, enc))
            else:
                # No subsections, split by paragraphs
                chunks.extend(_split_by_paragraphs(full_text, section_header, enc))

    return chunks


def _split_by_paragraphs(text: str, section_name: str, enc) -> list[dict]:
    """Split a long text into chunks by paragraphs, respecting token limit."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    current_tokens = 0

    for para in paragraphs:
        para_tokens = len(enc.encode(para))
        if current_tokens + para_tokens > CHUNK_SIZE_TOKENS and current:
            chunks.append({"text": current.strip(), "section": section_name})
            # Overlap: keep last paragraph
            overlap_text = paragraphs[paragraphs.index(para) - 1] if paragraphs.index(para) > 0 else ""
            current = overlap_text + "\n\n" + para
            current_tokens = len(enc.encode(current))
        else:
            current += "\n\n" + para if current else para
            current_tokens += para_tokens

    if current.strip():
        chunks.append({"text": current.strip(), "section": section_name})

    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    all_embeddings = []
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([d.embedding for d in response.data])

    return all_embeddings


def main():
    parser = argparse.ArgumentParser(description="Ingest Vortix guides into knowledge base")
    parser.add_argument("--dry-run", action="store_true", help="Show chunks without ingesting")
    parser.add_argument("--reset", action="store_true", help="Delete existing guide chunks first")
    args = parser.parse_args()

    # Load .env
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)

    import knowledge

    if not os.path.exists(GUIDES_DIR):
        print(f"Guides directory not found: {GUIDES_DIR}")
        print("Run 'python -m scripts.polish_guides' first.")
        sys.exit(1)

    md_files = sorted([f for f in os.listdir(GUIDES_DIR) if f.endswith(".md")])
    if not md_files:
        print(f"No .md files found in {GUIDES_DIR}")
        sys.exit(1)

    print(f"Found {len(md_files)} polished guides\n")

    if args.reset and not args.dry_run:
        # Delete only guide chunks (source = "vortix_guide")
        conn = knowledge.get_conn()
        deleted = conn.execute("DELETE FROM chunks WHERE source = 'vortix_guide'").rowcount
        conn.commit()
        print(f"Deleted {deleted} existing guide chunks\n")

    all_chunks = []
    all_ids = []
    all_metadatas = []

    for filename in md_files:
        civ_id = filename.replace(".md", "")
        civ_en, civ_es = CIV_DISPLAY.get(civ_id, (civ_id, civ_id))
        filepath = os.path.join(GUIDES_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_by_sections(content, civ_id)
        print(f"  {civ_en} ({civ_es}): {len(chunks)} chunks")

        if args.dry_run:
            for i, chunk in enumerate(chunks):
                print(f"    Chunk {i}: [{chunk['section'][:50]}] ({len(chunk['text'])} chars)")
                print(f"      {chunk['text'][:120]}...")
            print()
            continue

        for i, chunk in enumerate(chunks):
            chunk_id = f"vortix_guide_{civ_id}_chunk_{i}"
            all_chunks.append(chunk["text"])
            all_ids.append(chunk_id)
            all_metadatas.append({
                "source": "vortix_guide",
                "channel": "Vortix",
                "title": f"Guía de Vortix — {civ_en}",
                "video_id": f"guide_{civ_id}",
                "url": "",  # No URL for written guides
                "upload_date": "20260224",  # Today
                "language": "es",
                "timestamp_start": 0,
                "timestamp_end": 0,
            })

    if args.dry_run:
        print(f"\nTotal: {len(all_chunks)} chunks across {len(md_files)} guides")
        print("Use without --dry-run to ingest.")
        return

    if not all_chunks:
        print("No chunks to ingest.")
        return

    # Generate embeddings
    print(f"\nGenerating embeddings for {len(all_chunks)} chunks...", end=" ", flush=True)
    start = time.time()
    embeddings = embed_texts(all_chunks)
    elapsed = time.time() - start
    print(f"done ({elapsed:.1f}s)")

    # Store in knowledge base
    print("Storing in knowledge.db...", end=" ", flush=True)
    knowledge.upsert_chunks(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )
    print("done")

    total = knowledge.count()
    print(f"\nIngestion complete!")
    print(f"  Guide chunks added: {len(all_chunks)}")
    print(f"  Total chunks in DB: {total}")


if __name__ == "__main__":
    main()
