"""
ingest.py — Milestone 3: document ingestion and chunking.

Loads every .txt file in documents/, separates the SOURCE:/URL: header from the
body (the header becomes metadata so attribution stays attached to every chunk),
then splits the body into paragraph-sized chunks.

Chunking strategy (see planning.md):
  - Split on blank lines so each chunk is one self-contained dining-hall / topic
    paragraph. Our documents are short guides where each paragraph reviews exactly
    one hall, so a paragraph is the natural unit of meaning.
  - No overlap: the key fact for each hall lives entirely within its own paragraph.
  - Hard cap (MAX_CHARS): an unusually long paragraph is split on sentence
    boundaries so no single chunk dominates an embedding.

Run directly to inspect the output:
    python ingest.py
"""

from __future__ import annotations

import glob
import os
import re

DOCUMENTS_DIR = "documents"
MAX_CHARS = 1000  # safety cap for an unusually long paragraph
INTRO_MAX_CHARS = 120  # a short first paragraph is a doc-level summary, not content


def load_documents(documents_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """Load every .txt file, splitting the SOURCE:/URL: header into metadata.

    Returns a list of dicts: {"source", "url", "filename", "body"}.
    The body excludes the header lines and the NOTE: line.
    """
    docs: list[dict] = []
    paths = sorted(glob.glob(os.path.join(documents_dir, "*.txt")))

    for path in paths:
        with open(path, encoding="utf-8") as f:
            raw = f.read()

        source = "Unknown source"
        url = ""
        body_lines: list[str] = []

        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("SOURCE:"):
                source = stripped[len("SOURCE:"):].strip()
            elif stripped.startswith("URL:"):
                url = stripped[len("URL:"):].strip()
            elif stripped.startswith("NOTE:"):
                # Provenance note for humans; not part of the searchable body.
                continue
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()
        docs.append(
            {
                "source": source,
                "url": url,
                "filename": os.path.basename(path),
                "body": body,
            }
        )

    return docs


def _split_long_paragraph(paragraph: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Split an over-long paragraph on sentence boundaries, packing sentences
    into pieces no longer than max_chars. Used only when a paragraph exceeds the cap.
    """
    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current += " " + sentence
        else:
            pieces.append(current)
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def chunk_document(doc: dict, max_chars: int = MAX_CHARS) -> list[dict]:
    """Split one document's body into paragraph chunks with attached metadata.

    Returns a list of dicts: {"text", "source", "url", "filename", "chunk_index"}.
    """
    # Paragraphs are separated by one or more blank lines.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", doc["body"]) if p.strip()]

    # Drop a short leading paragraph: in our corpus the first paragraph of a
    # document is a meta-summary ("A guide to eating on campus...") that describes
    # the document rather than any dining hall. These add noise to the vector store
    # without carrying a retrievable fact. Real facts are never this short *and* first,
    # so this removes the 6 intro lines while preserving every substantive paragraph.
    if paragraphs and len(paragraphs[0]) < INTRO_MAX_CHARS:
        paragraphs = paragraphs[1:]

    chunks: list[dict] = []
    for paragraph in paragraphs:
        for piece in _split_long_paragraph(paragraph, max_chars):
            if not piece.strip():
                continue
            chunks.append(
                {
                    "text": piece.strip(),
                    "source": doc["source"],
                    "url": doc["url"],
                    "filename": doc["filename"],
                    "chunk_index": len(chunks),
                }
            )
    return chunks


def build_chunks(documents_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """Load all documents and return the full flat list of chunks across the corpus.

    Each chunk gets a globally-unique 'id' of the form '<filename>::<n>'.
    """
    all_chunks: list[dict] = []
    for doc in load_documents(documents_dir):
        for chunk in chunk_document(doc):
            chunk["id"] = f"{chunk['filename']}::{chunk['chunk_index']}"
            all_chunks.append(chunk)
    return all_chunks


if __name__ == "__main__":
    docs = load_documents()
    chunks = build_chunks()

    print(f"Loaded {len(docs)} documents from '{DOCUMENTS_DIR}/'.")
    print(f"Produced {len(chunks)} chunks total.\n")

    lengths = [len(c["text"]) for c in chunks]
    if lengths:
        print(
            f"Chunk length (chars): min={min(lengths)}  "
            f"max={max(lengths)}  avg={sum(lengths) // len(lengths)}\n"
        )

    # Print 5 representative chunks for inspection (first chunk of the first 5 docs).
    print("=" * 70)
    print("SAMPLE CHUNKS (one from each of the first 5 documents)")
    print("=" * 70)
    seen_files: set[str] = set()
    shown = 0
    for c in chunks:
        if c["filename"] in seen_files:
            continue
        seen_files.add(c["filename"])
        shown += 1
        print(f"\n[{shown}] id={c['id']}")
        print(f"    source: {c['source']}")
        print(f"    chars : {len(c['text'])}")
        print(f"    text  : {c['text'][:400]}{'...' if len(c['text']) > 400 else ''}")
        if shown == 5:
            break
