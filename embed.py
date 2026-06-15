"""
embed.py — Milestone 4: embed chunks and load them into ChromaDB.

Embeds every chunk from ingest.py with all-MiniLM-L6-v2 and stores it in a
persistent local ChromaDB collection, with source/url/chunk_index metadata so
retrieval can cite where each answer came from.

The collection uses cosine distance (hnsw:space="cosine"), which is the metric
all-MiniLM-L6-v2 is trained for; ChromaDB's default is squared-L2, which would
put distances on a different, less interpretable scale.

Run directly to (re)build the store:
    python embed.py
"""

from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import build_chunks

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "unofficial_guide"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# Cache the model so embed.py and retrieve.py reuse one instance per process.
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load (once) and return the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def get_collection(reset: bool = False):
    """Return the persistent ChromaDB collection (creating it if needed).

    If reset=True, delete any existing collection first so we rebuild from scratch.
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_store() -> int:
    """Embed all chunks and (re)load them into ChromaDB. Returns the chunk count."""
    chunks = build_chunks()
    model = get_model()
    collection = get_collection(reset=True)

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [
        {
            "source": c["source"],
            "url": c["url"],
            "filename": c["filename"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    # normalize_embeddings=True pairs with cosine space for stable distances.
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


if __name__ == "__main__":
    n = build_store()
    print(f"Embedded and stored {n} chunks in ChromaDB collection "
          f"'{COLLECTION_NAME}' (cosine space) at './{CHROMA_DIR}/'.")
