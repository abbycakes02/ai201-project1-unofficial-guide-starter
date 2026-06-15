# The Unofficial Guide — Project 1

A RAG system that answers plain-language questions about **UC Berkeley dining** using
real student-generated reviews and guides — with grounded answers and source citations.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your Groq API key into .env
python embed.py               # build the ChromaDB vector store (one time)
python app.py                 # launch the Gradio UI at http://localhost:7860
# or, command line:
python query.py               # answer the 5 evaluation questions in the terminal
```

Pipeline files: `ingest.py` (load + chunk) → `embed.py` (embed + store) →
`retrieve.py` (semantic search) → `query.py` (grounded generation) → `app.py` (UI).

---

## Domain

This guide covers **UC Berkeley dining hall and campus food experiences** — what students
actually think of the four dining commons (Crossroads, Cafe 3, Clark Kerr, Foothill), other
on-campus spots, and how the meal-plan system works in practice.

This knowledge is valuable and hard to find through official channels because the official
Berkeley Dining site describes every hall in the same glossy language ("flagship,"
"international cuisine," "great-tasting meals"). It won't tell you that Cafe 3 is widely
considered "one of the worst" halls, that Clark Kerr's food is great but the line is so long
you leave half-full, or that the *same* hall (Clark Kerr) gets ranked both #1 and #4 by
different students. That lived, contradictory, opinion-heavy knowledge only exists in student
blogs, review sites, and threads.

---

## Document Sources

13 documents from 13 distinct public sources. **Reddit and Yelp blocked automated collection**
(HTTP 403 / JavaScript-rendered — exactly the obstacle the assignment warns about). Sources 1–10
came from student blogs, campus review sites, and the Daily Californian, with their text condensed
by an automated web-fetch step (a small model extracted the substantive review text from each
page). Sources 11–13 are **raw, verbatim Reddit threads and Yelp reviews** that I copied by hand
from the blocked sites and cleaned (stripping usernames, vote counts, ads, and sidebars) — these
are primary-source student text, not paraphrase. Each file stores its real source URL. I
deliberately included **conflicting opinions** across sources and **one official source** for
contrast. See the AI Usage section for full disclosure of how the text was obtained.

| #  | Source | Type | URL or file path |
|----|--------|------|-----------------|
| 1  | Her Campus @ UC Berkeley | Student ranking | documents/01_hercampus_halls_ranked.txt · https://www.hercampus.com/school/uc-berkeley/uc-berkeley-dining-halls-ranked/ |
| 2  | visit.berkeley.edu (Emily Conway) | Student ranking | documents/02_visitberkeley_halls_ranked.txt · https://visit.berkeley.edu/news/crossroads-cal's-dining-halls-ranked |
| 3  | SayTastes (Seoyun Kim) | Student reviews | documents/03_saytastes_student_reviews.txt · https://saytastes.com/schoolreviews |
| 4  | The Daily Californian food blog (Jenny Tran) | Guide | documents/04_dailycal_dining_guide.txt · https://www.dailycal.org/blogs/food-blog/swipe-into-these-on-campus-dining-locations/ |
| 5  | UC Berkeley UHS | Campus guide | documents/05_uhs_places_to_eat.txt · https://uhs.berkeley.edu/news/places-eat-uc-berkeley |
| 6  | Study Abroad Foundation (Seyoung Lee) | Meal-plan guide | documents/06_saf_meal_plans.txt · https://www.studyabroadfoundation.org/blogs/using-meal-plans-berkeley |
| 7  | RateMyDorm / Roomsurf | Student reviews | documents/07_ratemydorm_clarkkerr_foothill.txt · https://www.ratemydorm.com/reviews/university-of-california-berkeley/ |
| 8  | CampusReel | Dining guide | documents/08_campusreel_meal_plans.txt · https://www.campusreel.org/colleges/university-of-california-berkeley/dining_food |
| 9  | Berkeley Dining (**official**) | Official page | documents/09_dining_crossroads_official.txt · https://dining.berkeley.edu/crossroads |
| 10 | The Daily Californian "good/bad/ugly" | Student soundbites | documents/10_dailycal_good_bad_ugly.txt · https://www.dailycal.org/multimedia/dining-halls-the-good-the-bad-the-ugly/ |
| 11 | r/berkeley "be brutally honest" thread | **Raw Reddit (verbatim)** | documents/11_reddit_best_hall_brutal.txt · https://www.reddit.com/r/berkeley/ |
| 12 | Yelp — Cafe 3 reviews | **Raw Yelp (verbatim)** | documents/12_yelp_cafe3_reviews.txt · https://www.yelp.com/biz/cafe-3-berkeley |
| 13 | r/berkeley "best dining hall?" thread | **Raw Reddit (verbatim)** | documents/13_reddit_best_hall_thread2.txt · https://www.reddit.com/r/berkeley/ |

---

## Chunking Strategy

**Chunk size:** One paragraph per chunk (split on blank lines), capped at ~1,000 characters so
an unusually long paragraph is split on sentence boundaries rather than dominating an embedding.
In practice chunks run ~60–820 chars (avg 269).

**Overlap:** None. Each paragraph already reviews one self-contained hall/topic, so no key fact
spans a paragraph boundary that overlap would need to rescue. The `SOURCE`/`URL` header is
attached to every chunk as metadata so attribution is never separated from the text.

**Why these choices fit my documents:** My documents are short guides where each paragraph
reviews exactly one dining hall or one topic. A fixed 500-character split (which the assignment
explicitly warns against) would cut mid-paragraph and merge two different halls into one chunk.
Paragraph chunks are individually answerable: "what do students say about Cafe 3?" matches the
Cafe-3 paragraph cleanly without dragging in Foothill.

**Preprocessing:** The `SOURCE:`/`URL:` header lines are parsed into metadata; the `NOTE:`
provenance line is dropped from the searchable body. After first inspection found 6 short
"intro" paragraphs that merely *describe the document* ("A guide to eating on campus at UC
Berkeley..."), I drop a document's leading paragraph when it is under 120 characters — this
removes those noise fragments while preserving every real short fact (e.g. "Foothill... famous
for its gigantic steaks").

**Final chunk count:** **75 chunks** across 13 documents.

---

## Sample Chunks

1. **`01_hercampus_halls_ranked.txt`** — *"Clark Kerr (ranked #4). The writer offers a hot take
   against the common opinion that Clark Kerr has the best food. They note it is the farthest
   hall (a convenience point off) and serves fried foods daily... They also criticize inaccurate
   menus — sometimes being served a different dish than advertised. Still, they concede the
   dishes are not bad at all."*

2. **`03_saytastes_student_reviews.txt`** — *"Crossroads. The reviewer enjoys this hall, noting
   the meals are mostly nutritious and tasty. An Asian bar was added in fall 2023 serving pho,
   dumplings, and Thai curry. It is the closest hall to Units 1 and 2, but its popularity causes
   lines... Special events featured ribeye steak, crab legs (a seafood boil), Korean chicken
   tenders, and boba."*

3. **`04_dailycal_dining_guide.txt`** — *"Golden Bear Cafe. Located in Sproul Plaza, good for a
   quick lunch or coffee, with grab-and-go options purchasable via flex dollars. Ordering is easy
   with short waits. Favorites: Philly Cheesesteak, Chicken Tenders, and Bulgogi Fries. Has a
   Peet's Coffee, the author's go-to for iced lattes."*

4. **`05_uhs_places_to_eat.txt`** — *"Pat Brown's. On the north side of campus. Good breakfast
   selection plus Peet's Coffee — recommended for early morning classes."*

5. **`10_dailycal_good_bad_ugly.txt`** — *"Each dining hall has its own distinct character and
   layout. Clark Kerr has a Hogwarts-esque vibe with a similarly magical menu. Crossroads is more
   modern with many stations offering a variety of cuisines, while Cafe 3 and Foothill emit a
   more homey and casual feel. A perk for variety-seekers: the dining halls change up their menus
   for every meal..."*

Each is self-contained: you could answer a question from any one of them alone.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, runs locally, no API key,
no rate limits). Embeddings are normalized and stored in a ChromaDB collection configured with
**cosine** distance (`hnsw:space="cosine"`) — ChromaDB defaults to squared-L2, which would put
distances on a different, less interpretable scale.

**Production tradeoff reflection:** If I were deploying this for real users and cost weren't a
constraint, I'd weigh: **(1) accuracy on domain text** — a larger model (`bge-large`) or an API
model (OpenAI `text-embedding-3-large`, Voyage) captures opinion nuance better, which matters when
words like "mid," "slander," and "half-full" carry sentiment MiniLM may flatten; **(2) context
length** — MiniLM truncates at 256 tokens (fine for paragraphs, limiting for long-form guides);
**(3) multilingual support** — Berkeley has many international students who might query in other
languages, so `bge-m3` or `multilingual-e5` would widen access; **(4) local vs. API** — local keeps
data private and free but caps quality, while an API improves quality at per-query cost plus latency
and an external dependency. For this free-tier project, local MiniLM is the right tradeoff; for
production I'd likely move to a hosted multilingual model.

---

## Retrieval Test Results

Top-k = **4**, cosine distance (lower = more similar). All top results fall below 0.5.

**Query 1 — "What unique food items can you get at Crossroads that aren't at other dining halls?"**
- [0.32] Daily Cal: "Each hall has its own vibe — Clark Kerr Hogwarts-esque... Crossroads modern..."
- [0.33] Her Campus: "Popular menu items mentioned across the halls include orange chicken, mac and cheese..."
- [0.33] Daily Cal good/bad/ugly: "Each dining hall has its own distinct character..."
- [0.37] visit.berkeley.edu: "Crossroads (ranked #2)... BearFit build-your-own-bowl bar... truffle and garlic fries."

*Why relevant (and its limit):* all four are about Crossroads / hall comparisons, but the chunk
naming the *canonical* unique items (Korean Fried Chicken, waffles) ranked 11th and was not
retrieved — see Failure Case Analysis.

**Query 3 — "Why do students say Clark Kerr is inconvenient despite the food?"**
- [0.37] visit.berkeley.edu: "Clark Kerr (ranked #1)... the long 15 to 20 minute walk..."
- [0.37] Her Campus: "Clark Kerr (ranked #4)... it is the farthest hall (a convenience point off)..."
- [0.39] Daily Cal: "...the line is often very long, so it is hard to get seconds... leave half-full."
- [0.44] UHS: "Clark Kerr... very delicious food if you are willing to walk the distance for it."

*Why relevant:* every chunk directly pairs Clark Kerr's good food with its location/wait downside
— and the retrieval even pulled the #1-ranked and #4-ranked sources together, surfacing the
disagreement.

**Query 4 — "Do students agree on whether Cafe 3 is a good dining hall?"**
- [0.31] Daily Cal: "On Cafe 3, the recurring criticism is that it doesn't have as many options..."
- [0.33] SayTastes: "Cafe 3. Rated poorly: known to be one of the worst dining halls... very salty or very bland."
- [0.33] Daily Cal good/bad/ugly: "...Cafe 3 and Foothill emit a more homey and casual feel."
- [0.35] Daily Cal: "Dining halls (Cafe 3, Clark Kerr, Crossroads, Foothill). Each hall has its own vibe..."

*Why relevant:* the retrieval pulled both the harsh review ("one of the worst") and the gentler
"homey and casual" framing — exactly the two sides needed to answer a "do students agree?" question.

---

## Grounded Generation

**System prompt grounding instruction (verbatim, from `query.py`):**

> "You answer student questions using ONLY the numbered context passages provided... 1. Use ONLY
> information found in the provided context. Do not use outside knowledge. 2. If the context does
> not contain enough information, reply exactly: 'I don't have enough information on that.' Do not
> guess or fill gaps from memory. 3. The context may contain CONFLICTING opinions or facts from
> different sources. When sources disagree, say so explicitly and present both sides rather than
> picking one as the truth. 4. Cite the passage numbers you used inline like [1], [2]. 5. Do not
> invent dining halls, menu items, prices, or hours that are not in the context."

**Structural choices that enforce grounding:**
- Retrieved chunks are formatted as a **numbered context block**; the user message ends with
  "Answer using only the context above."
- **Generation temperature is 0.2**, keeping the model close to the source text.
- If retrieval returns nothing, `ask()` refuses **before** ever calling the LLM.

**How source attribution is surfaced:** The "Retrieved from" list is built **programmatically**
from the retrieved chunks' metadata (`unique_sources()` in `query.py`), not from anything the LLM
writes. Even if the model forgets to cite, the user still gets accurate provenance with real URLs.

**Proof grounding holds:** asking *"Who is the chancellor of UC Berkeley?"* — a fact the 70B model
certainly knows from training — still returns *"I don't have enough information on that,"* because
it isn't in the retrieved dining context.

---

## Example Responses

**In-scope, conflict reported (source attribution visible):**

> **Q:** How many flex dollars does the Gold meal plan include?
> **A:** "Sources disagree: one says the Gold Plan includes $500 flex dollars per semester [1],
> while another says the Gold meal plan provides 750 flex dollars [2]."
> **Retrieved from:** • SAF blog (studyabroadfoundation.org) • CampusReel • Daily Cal food blog

**In-scope, single grounded answer:**

> **Q:** Why do students say Clark Kerr is inconvenient despite the food?
> **A:** "Students say Clark Kerr is inconvenient due to its far location [1, 2, 3] and long wait
> times, with often very long lines [3]... despite the consensus that the food is very good."
> **Retrieved from:** • visit.berkeley.edu • Her Campus • Daily Cal • UC Berkeley UHS

**Out-of-scope refusal:**

> **Q:** How much does a dorm cost at UC Berkeley?
> **A:** "I don't have enough information on that."

---

## Query Interface

A **Gradio** web UI (`app.py`, served at `http://localhost:7860`).
- **Input:** a single textbox, "Your question" (plus 5 example buttons that seed common queries).
- **Outputs:** an "Answer" box (the grounded response) and a "Retrieved from" box (the source
  documents + URLs the answer drew from).

**Sample interaction transcript:**

```
Your question:  How many flex dollars does the Gold meal plan include?
Answer:         Sources disagree: one says the Gold Plan includes $500 flex dollars per
                semester [1], while another says the Gold meal plan provides 750 flex dollars [2].
Retrieved from: • Study Abroad Foundation (SAF) blog — https://www.studyabroadfoundation.org/...
                • CampusReel UC Berkeley dining guide — https://www.campusreel.org/...
                • The Daily Californian, food blog — https://www.dailycal.org/...
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval | Accuracy |
|---|----------|-----------------|------------------------------|-----------|----------|
| 1 | Unique food at Crossroads vs other halls | Korean Fried Chicken, waffles; special events (ribeye, crab legs, boba) | Cited BearFit bowl bar + truffle/garlic fries; **missed** KFC/waffles | Partially relevant | **Partially accurate** |
| 2 | Gold plan flex dollars | Conflict: $500 (SAF) vs 750 (CampusReel) | "Sources disagree: $500 [1] vs 750 [2]" | Relevant | **Accurate** |
| 3 | Why Clark Kerr is inconvenient | Farthest hall, 15–20 min uphill walk, long lines / leave half-full | Far location + long lines + 15–20 min walk, food still praised | Relevant | **Accurate** |
| 4 | Do students agree on Cafe 3? | No — "one of the worst" vs "safe/convenient/homey" | "Sources disagree: 'one of the worst' vs 'homey and casual'" | Relevant | **Accurate** |
| 5 | Best dining hall per students | Contested: Clark Kerr #1 (one source), Crossroads #1 (another), Foothill "objectively best" (another) | "I don't have enough information on that." (refuses) | Off-target | **Inaccurate (refuses)** |

Honest tally: **3 accurate, 1 partially accurate, 1 inaccurate.** Q5 is judged inaccurate because
the system fails to answer a question the corpus *does* contain material for — though it fails
*safely* by refusing rather than fabricating (see below).

---

## Failure Case Analysis

**Question that failed:** *"What's the best dining hall at UC Berkeley according to students?"* (Q5)

**What the system returned:** *"I don't have enough information on that."* — a refusal.

**Root cause (tied to the retrieval stage):** This is a **retrieval failure**, not a generation
failure. "Best dining hall" is an *abstract* query with no single matching chunk — my sources crown
**at least three different halls** as #1 (visit.berkeley.edu → Clark Kerr; Her Campus → Crossroads;
RateMyDorm → Foothill; plus raw Reddit threads that say "clark kerr is the best" and "foothill is
the best hands down"). Cosine similarity pulls a **generic** chunk to the top — SAF's "Berkeley's
dining system simplifies meals for students" at distance 0.30 — ahead of the actual ranking chunks,
because that filler text is lexically close to the query while carrying no ranking. The rest of the
top-4 fills with *Cafe-3-is-bad* chunks, so no retrieved passage actually states which hall is
best, and the grounding prompt correctly refuses.

**A revealing experiment:** before I added the raw Reddit "best hall" threads (sources 11 & 13),
this same question returned a *confidently wrong* answer — "Foothill is the best" — because the one
ranking chunk that reached the top-4 happened to say "objectively the best." After adding two more
sources that explicitly debate the question, the answer changed to an honest refusal. **More data
did not fix the failure** — it moved the system from a confident wrong answer to a safe non-answer,
because the underlying problem is the embedding model's inability to localize the abstract concept
"best" across chunks that each name a *different* hall. This is the strongest argument for the
hybrid-search stretch feature: a keyword signal on "best" would surface the ranking chunks that
semantic search buries.

**Secondary example (same root cause):** Q1 missed Korean Fried Chicken / waffles because the chunk
naming them leads with "The writer admits hearing Croads slander..." — its dominant embedded theme
is *opinion/ranking*, so it sat at rank 11 (distance 0.46), below thematically-similar but
answer-empty "each hall has its own vibe" chunks. The answer-bearing chunk embedded *further* from a
"food items" query than chunks that merely repeat "Crossroads / dining halls."

**What I would change to fix it:** (1) add **hybrid search** (BM25 + semantic) so a literal term
like "best" or "waffles" can rescue an answer-bearing chunk that semantic search ranks low;
(2) try **larger or query-aware chunks** so a ranking verdict and its reasoning embed together;
(3) for inherently-contested questions, **retrieve more broadly and instruct the model to enumerate
every hall some source calls best**, rather than reporting a single winner.

---

## Spec Reflection

**One way the spec helped me during implementation:** Writing the Chunking Strategy section in
`planning.md` *before* coding meant I had already decided on paragraph chunking and could justify
it — so when ingestion produced the first 54 chunks and inspection turned up 6 short "intro" fragments, I had
a clear principle ("one self-contained hall/topic per chunk") to measure against, and the fix
(dropping short leading paragraphs) followed directly from the spec instead of being an ad-hoc
patch. The eval plan also pre-committed me to two conflicting-source "trap" questions, which is why
the failure cases were anticipated rather than surprises.

**One way my implementation diverged from the spec, and why:** My spec assumed I would collect
documents from Reddit and Yelp threads via code. In practice both **blocked automated collection**
(403 / JavaScript), so sources 1–10 came from student blogs and the Daily Californian with their
text condensed by an automated fetch step. I then went back and **hand-copied three raw, verbatim
Reddit/Yelp sources** (11–13) to firm up the "real collected documents" requirement, growing the
corpus to 13 docs / 75 chunks. The retrieval approach (all-MiniLM-L6-v2, k=4) stayed exactly as
specced — I tested raising k to rescue Q1's missing fact, found it still ranked 11th, and **kept
k=4** rather than flooding every query with noise, consistent with the spec's reasoning that
too-high k dilutes context.

---

## AI Usage

I used **Claude (Claude Code, Opus 4.8)** throughout, directing it from my `planning.md` decisions.
The assignment's guardrail says the *spec* must be mine; I made all the design decisions (domain,
campus, paragraph chunking, top-k, the 5 eval questions, accuracy verdicts) and Claude drafted code
and prose from them, which I reviewed and corrected.

**Instance 1 — Document collection (and an honest caveat)**
- *What I gave the AI:* my domain (UC Berkeley dining) and a request to collect 10 real documents,
  with the instruction to try fetching real text itself rather than fabricating any.
- *What it produced:* it tried the Reddit JSON API and Yelp (both **blocked** — 403 / JS-rendered),
  then fetched 10 real public pages (Her Campus, visit.berkeley.edu, SayTastes, Daily Cal, UHS,
  SAF, RateMyDorm, CampusReel, official Berkeley Dining). The fetch step **condensed/paraphrased**
  each page rather than returning raw text. It also caught one wrong source (a "Crossroads" page
  that was a restaurant in Shillong, India) and discarded it.
- *What I changed or directed:* I required that no content be fabricated, that each file record its
  real source URL, and that this condensation be disclosed here (it is). Sources 1–10 are real and
  attributed, but **lightly paraphrased by the automated fetch**, not verbatim. To firm up the
  primary-source requirement, I then **hand-copied raw text from two r/berkeley threads and a Yelp
  Cafe 3 page** (sources 11–13) and had Claude clean them — stripping usernames, vote counts, the
  injected "Promoted" ad, and the subreddit sidebar — while keeping every student comment verbatim.
  I directed it to drop one off-domain Yelp review (a disgruntled *employee* complaining about
  hairnets, not a diner's opinion of the food).

**Instance 2 — Chunking fix after inspection**
- *What I gave the AI:* my Chunking Strategy section and the instruction to inspect the output
  before trusting it.
- *What it produced:* paragraph chunking that yielded 60 chunks, including 14 short ones. Inspection
  showed ~6 were useless doc-intro lines ("A guide to eating on campus...") and ~8 were real short
  facts ("Foothill famous for gigantic steaks").
- *What I decided:* rather than a blunt length filter (which would delete real facts), I chose to
  **drop only the short leading doc-intro paragraph**, preserving every substantive chunk — bringing
  the corpus to 54 clean chunks with no information lost.

**Instance 3 — Dependency conflict resolution**
- *What I gave the AI:* a request to add a Gradio interface.
- *What it produced:* installing Gradio 6.x broke `sentence-transformers` (a `huggingface-hub`
  version clash).
- *What I directed:* pin **Gradio 5.x** so a grader's fresh `pip install -r requirements.txt`
  resolves cleanly (`pip check` confirms no broken requirements), rather than relying on an
  install that errors but happens to run.

> **Note on `planning.md`:** Claude drafted the spec prose from the decisions I made (listed above).
> I reviewed it and own every choice in it.
