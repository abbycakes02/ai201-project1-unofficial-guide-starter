"""
query.py — Milestone 5: grounded answer generation.

Pipeline: retrieve top-k chunks -> build a context block with numbered sources ->
ask Groq's llama-3.3-70b-versatile to answer ONLY from that context -> return the
answer plus the list of source documents it drew from.

Grounding is enforced two ways:
  1. The system prompt instructs the model to use only the provided context, to say
     "I don't have enough information on that." when the context doesn't cover the
     question, and to REPORT DISAGREEMENT when sources conflict (our corpus contains
     conflicting student opinions on purpose).
  2. Source attribution is programmatic: the "sources" list is built from the
     retrieved chunks' metadata, not from anything the LLM writes. Even if the model
     forgets to cite, the caller still gets accurate provenance.

Run directly to answer the evaluation questions from the command line:
    python query.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve, TOP_K

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are The Unofficial Guide to UC Berkeley dining. You answer \
student questions using ONLY the numbered context passages provided in the user \
message. These passages come from student reviews, blogs, and guides.

Rules you must follow:
1. Use ONLY information found in the provided context. Do not use outside knowledge \
about UC Berkeley or dining in general.
2. If the context does not contain enough information to answer, reply exactly: \
"I don't have enough information on that." Do not guess or fill gaps from memory.
3. The context may contain CONFLICTING opinions or facts from different sources. \
When sources disagree, say so explicitly and present both sides rather than picking \
one as the truth (e.g. "Sources disagree: one says X, another says Y.").
4. Keep answers concise and grounded — quote or paraphrase the passages. Cite the \
passage numbers you used inline like [1], [2].
5. Do not invent dining halls, menu items, prices, or hours that are not in the context.
"""

# A separate Groq client per process; created lazily so importing this module
# (e.g. for tests) doesn't require an API key to be present.
_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = Groq(api_key=api_key)
    return _client


def build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    blocks = []
    for i, hit in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {hit['source']})\n{hit['text']}")
    return "\n\n".join(blocks)


def unique_sources(hits: list[dict]) -> list[str]:
    """Distinct source labels from the retrieved chunks, preserving rank order.

    This is the programmatic attribution — built from metadata, not the LLM output.
    """
    seen: set[str] = set()
    sources: list[str] = []
    for hit in hits:
        label = hit["source"]
        if hit.get("url"):
            label = f"{label} — {hit['url']}"
        if label not in seen:
            seen.add(label)
            sources.append(label)
    return sources


def ask(question: str, k: int = TOP_K) -> dict:
    """Answer a question with grounded generation.

    Returns {"answer": str, "sources": list[str], "hits": list[dict]}.
    """
    hits = retrieve(question, k=k)

    # Defensive grounding: if retrieval found nothing usable, refuse before calling the LLM.
    if not hits:
        return {
            "answer": "I don't have enough information on that.",
            "sources": [],
            "hits": [],
        }

    context = build_context(hits)
    user_message = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer using only the context above."
    )

    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low temp: stay close to the source text, less embellishment
    )
    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": unique_sources(hits),
        "hits": hits,
    }


if __name__ == "__main__":
    from retrieve import EVAL_QUERIES

    for q in EVAL_QUERIES:
        print("\n" + "=" * 74)
        print(f"Q: {q}")
        print("=" * 74)
        result = ask(q)
        print(f"\nANSWER:\n{result['answer']}\n")
        print("RETRIEVED FROM:")
        for s in result["sources"]:
            print(f"  • {s}")
