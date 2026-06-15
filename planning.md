# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

My Unofficial Guide covers **UC Berkeley dining hall and campus food experiences** — what
students actually think of the four dining commons (Crossroads, Cafe 3, Clark Kerr, Foothill)
and other on-campus food spots, plus how the meal-plan system really works in practice.

This knowledge is valuable and hard to find through official channels because the official
Berkeley Dining site describes every hall in the same glossy language ("flagship," "international
cuisine," "great-tasting meals"). It won't tell you that Cafe 3 is widely considered "one of the
worst" halls, that Clark Kerr's food is great but the line is so long you leave half-full, or that
the same hall (Clark Kerr) gets ranked both #1 and #4 by different students. That lived,
contradictory, opinion-heavy knowledge only exists in student blogs, review sites, and threads.

---

## Documents

I collected 10 documents from 10 distinct public sources. Reddit and Yelp blocked automated
collection (403 / JavaScript-rendered), so I used student blogs, campus review sites, and the
Daily Californian instead. Text was condensed by an automated web fetch step; each file records
its real source URL for attribution. I deliberately included **conflicting opinions** across
sources and **one official source** (Berkeley Dining) to contrast with the unofficial voices.

| #  | Source | Description | URL or location |
|----|--------|-------------|-----------------|
| 1  | Her Campus @ UCB | All 4 halls ranked; Crossroads #1, Clark Kerr #4 | documents/01_hercampus_halls_ranked.txt |
| 2  | visit.berkeley.edu | All 4 halls ranked; Clark Kerr #1, Cafe 3 #4 (conflicts with #1) | documents/02_visitberkeley_halls_ranked.txt |
| 3  | SayTastes | Student reviews; calls Cafe 3 "one of the worst" | documents/03_saytastes_student_reviews.txt |
| 4  | Daily Californian food blog | On-campus dining + meal-plan guide | documents/04_dailycal_dining_guide.txt |
| 5  | UC Berkeley UHS | "Places to Eat" campus guide, incl. late-night | documents/05_uhs_places_to_eat.txt |
| 6  | Study Abroad Foundation | Meal plan mechanics: swipes, flex dollars, plan tiers | documents/06_saf_meal_plans.txt |
| 7  | RateMyDorm / Roomsurf | Clark Kerr & Foothill atmosphere + the uphill walk | documents/07_ratemydorm_clarkkerr_foothill.txt |
| 8  | CampusReel | Meal plan structure (Blue/Gold) + Crossroads first-year view | documents/08_campusreel_meal_plans.txt |
| 9  | Berkeley Dining (OFFICIAL) | Official Crossroads description — included for contrast | documents/09_dining_crossroads_official.txt |
| 10 | Daily Californian "good/bad/ugly" | Student soundbites on all 4 halls | documents/10_dailycal_good_bad_ugly.txt |

---

## Chunking Strategy

**Chunk size:** One paragraph per chunk (split on blank lines), with a maximum cap of ~1,000
characters so an unusually long paragraph gets split rather than dominating. In practice each
chunk is ~250–700 characters.

**Overlap:** None between paragraphs (paragraphs are already self-contained), but the document's
`SOURCE`/`URL` header is attached to every chunk as metadata so attribution never gets separated
from the text.

**Reasoning:** My documents are short guides where each paragraph reviews exactly one dining hall
or one topic (look at doc 03 — "Cafe 3. Rated poorly..." is a complete, standalone thought). A
fixed 500-character split would cut mid-paragraph and merge two different halls into one chunk,
which the assignment explicitly warns against. Paragraph chunks are individually answerable: a
query like "what do students say about Cafe 3?" should match the Cafe-3 paragraph cleanly without
dragging in Foothill. I skip overlap because the key fact for each hall lives entirely within its
own paragraph — there is no fact that spans a paragraph boundary that overlap would rescue.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`. Runs locally, no API key, no
rate limits, 384-dim embeddings, fast on CPU — a good fit for a small corpus and free-tier project.

**Top-k:** 4. My corpus contains conflicting opinions about the same hall across different sources.
With k=4 the retriever can surface *both* sides of a debate (e.g. the "Clark Kerr is best" review
and the "Clark Kerr is overrated" review) instead of committing to one. k=2 risks returning only
one side; k=6 starts pulling loosely-related paragraphs for narrow questions like a specific
flex-dollar amount.

**Production tradeoff reflection:** If I were deploying this for real users and cost weren't a
constraint, I'd weigh: (1) **accuracy on domain text** — a larger model like `bge-large` or an API
model (OpenAI `text-embedding-3-large`, Voyage) embeds nuanced opinion text better, which matters
when "mid," "slander," and "half-full" carry sentiment MiniLM may flatten; (2) **context length** —
MiniLM truncates at 256 tokens, fine for paragraphs but limiting if I later ingest long-form
guides; (3) **multilingual support** — Berkeley has many international students who might query in
other languages, so a multilingual model (`bge-m3`, `multilingual-e5`) would widen access;
(4) **local vs. API** — local keeps data private and free but caps quality; an API improves quality
at per-query cost and adds latency + a dependency. For this project, local MiniLM is the right
tradeoff; for production I'd likely move to a hosted model with a multilingual option.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What unique food items can you get at Crossroads that aren't at other dining halls? | Korean Fried Chicken and waffles from the waffle maker (Her Campus); special events: ribeye steak, crab legs/seafood boil, Korean chicken tenders, boba. |
| 2 | How many flex dollars does the Gold meal plan include? | Sources conflict: SAF says $500/semester with 10 weekly swipes; CampusReel says 750 flex dollars with unlimited swipes. A good answer notes the disagreement. |
| 3 | Why do students say Clark Kerr is inconvenient despite the food? | It's the farthest hall — a long 15–20 minute uphill walk — and the line is often so long you leave with your stomach half-full. |
| 4 | Do students agree on whether Cafe 3 is a good dining hall? | No — opinions conflict. SayTastes calls it "one of the worst" (salty/bland); visit.berkeley.edu calls it a "safe, convenient choice." Upside: rarely a line. |
| 5 | What's the best dining hall at UC Berkeley according to students? | Contested. visit.berkeley.edu ranks Clark Kerr #1; Her Campus ranks Crossroads #1 and Clark Kerr #4. A grounded answer should present the disagreement, not pick one. |

---

## Anticipated Challenges

1. **Conflicting sources may produce a confidently one-sided answer.** Because different documents
   rank the same hall #1 and #4, retrieval might surface only one view (especially at low k) and the
   LLM could state it as settled fact. Risk: the system sounds authoritative while hiding the
   disagreement. Mitigation: k=4 to pull multiple sources, and a grounding prompt that tells the
   model to report disagreement when the context disagrees.

2. **Numeric facts that conflict across sources (the Gold plan question).** SAF and CampusReel give
   different flex-dollar amounts. This is a deliberate trap in my eval — the system may pick one
   number and present it as correct, or hallucinate a blended number. It tests whether grounding
   actually keeps the model honest about what the documents say.

3. **(secondary) Official vs. unofficial blending.** The official Crossroads doc uses glossy
   language that may get retrieved for opinion questions and make the answer sound like marketing
   rather than student experience.

---

## Architecture

```
   ┌─────────────────────┐
   │  10 .txt documents  │   documents/*.txt  (real student sources, w/ SOURCE+URL headers)
   └──────────┬──────────┘
              │  load + clean (strip headers→metadata, drop blanks)
              ▼
   ┌─────────────────────┐
   │  Chunking           │   ingest.py — split on blank lines (paragraph), ~1000-char cap
   └──────────┬──────────┘
              │  list of chunks + {source, url, chunk_index}
              ▼
   ┌─────────────────────┐
   │  Embedding          │   sentence-transformers  all-MiniLM-L6-v2  (384-dim, local)
   └──────────┬──────────┘
              │  vectors + metadata
              ▼
   ┌─────────────────────┐
   │  Vector Store       │   ChromaDB  (local, persistent ./chroma_db)
   └──────────┬──────────┘
              │  query → top-k=4 by cosine similarity
              ▼
   ┌─────────────────────┐
   │  Retrieval          │   retrieve.py — returns top 4 chunks + sources + distances
   └──────────┬──────────┘
              │  retrieved context (chunks only)
              ▼
   ┌─────────────────────┐
   │  Generation         │   Groq  llama-3.3-70b-versatile  — grounded prompt, cites sources
   └──────────┬──────────┘
              ▼
        Gradio UI  (app.py)  — question in → answer + "Retrieved from" sources out
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I'll give Claude my Documents section (file format: each .txt has a `SOURCE:`/`URL:` header then
blank-line-separated paragraphs) and my Chunking Strategy section, and ask it to implement
`ingest.py` with a `load_documents()` that parses the header into metadata and a `chunk_document()`
that splits on blank lines with a ~1000-char cap. I'll verify by printing 5 chunks and confirming
each is one self-contained hall/topic with correct source metadata, and by checking the total chunk
count lands in the 40–60 range I expect.

**Milestone 4 — Embedding and retrieval:**
I'll give Claude my Retrieval Approach section and the architecture diagram and ask it to implement
`embed.py` (embed chunks with all-MiniLM-L6-v2, store in a persistent ChromaDB collection with
source/url/chunk_index metadata) and a `retrieve(query, k=4)` function returning chunks + sources +
distances. I'll verify by running 3 of my 5 eval questions and checking the returned chunks are
on-topic and top distances are below ~0.5.

**Milestone 5 — Generation and interface:**
I'll give Claude my grounding requirement (answer from retrieved context only; say "I don't have
enough information" otherwise; report disagreement when sources conflict) and ask it to implement
`query.py` (build the grounded prompt, call Groq, return answer + source list) and a minimal Gradio
`app.py`. I'll verify by asking an out-of-scope question (e.g. "what are the dorm prices?") and
confirming it refuses instead of inventing an answer, and by checking sources are attached
programmatically, not left to the model.
```
