"""
retrieve.py — Milestone 4: semantic retrieval over the ChromaDB store.

Embeds a query with the same all-MiniLM-L6-v2 model and returns the top-k most
similar chunks, each with its source metadata and cosine distance. Lower distance
= more similar (0.0 is identical; ~1.0 is unrelated).

Run directly to test retrieval against the evaluation questions:
    python retrieve.py
"""

from __future__ import annotations

from embed import COLLECTION_NAME, get_collection, get_model

TOP_K = 4  # see planning.md — enough to surface conflicting opinions, not so many it dilutes


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the top-k chunks for a query.

    Each result: {"text", "source", "url", "filename", "chunk_index", "distance"}.
    """
    model = get_model()
    collection = get_collection(reset=False)

    query_embedding = model.encode([query], normalize_embeddings=True).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    hits: list[dict] = []
    for text, meta, dist in zip(documents, metadatas, distances):
        hits.append(
            {
                "text": text,
                "source": meta.get("source", "Unknown"),
                "url": meta.get("url", ""),
                "filename": meta.get("filename", ""),
                "chunk_index": meta.get("chunk_index"),
                "distance": round(float(dist), 4),
            }
        )
    return hits


# The evaluation questions from planning.md, for quick retrieval testing.
EVAL_QUERIES = [
    "What unique food items can you get at Crossroads that aren't at other dining halls?",
    "How many flex dollars does the Gold meal plan include?",
    "Why do students say Clark Kerr is inconvenient despite the food?",
    "Do students agree on whether Cafe 3 is a good dining hall?",
    "What's the best dining hall at UC Berkeley according to students?",
]


if __name__ == "__main__":
    for q in EVAL_QUERIES:
        print("\n" + "=" * 74)
        print(f"QUERY: {q}")
        print("=" * 74)
        for i, hit in enumerate(retrieve(q), 1):
            flag = "  <-- weak match" if hit["distance"] > 0.5 else ""
            print(f"\n[{i}] distance={hit['distance']}{flag}")
            print(f"    source: {hit['source'][:62]}")
            print(f"    {hit['text'][:240]}{'...' if len(hit['text']) > 240 else ''}")
