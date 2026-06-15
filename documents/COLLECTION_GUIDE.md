# Document Collection Guide — UC Berkeley Campus Dining

**Domain:** UC Berkeley dining hall & campus food experiences (student-generated, unofficial).

**Goal:** Paste *real* student-generated text into the 10 files below. Each file = one source
(a Reddit thread, a Yelp page's reviews, a blog post, etc.). Aim for variety so that together
they answer different kinds of questions.

## How to paste

1. Open the source in your browser.
2. Select the substantive text (the actual reviews/opinions — NOT the nav bar, ads, "upvote",
   sidebar, or "related threads").
3. Paste it into the matching `.txt` file below, **replacing** the `[PASTE ...]` placeholder.
4. Keep the first `SOURCE:` and `URL:` lines at the top — the pipeline reads those for attribution.
5. Don't worry about being perfect — the cleaning step in ingest.py strips a lot of junk. But
   the less garbage you paste, the better your chunks.

## What to collect (named UCB dining halls help your test questions be verifiable)

The big named UC Berkeley dining locations students talk about:
- **Crossroads** (the biggest residential dining hall)
- **Cafe 3** (Unit 3)
- **Clark Kerr / CKC** (Clark Kerr Campus dining)
- **Foothill** (Foothill dining hall)
- Plus meal-plan / meal-point / late-night / "best dining hall" debate threads

## Suggested sources (find 10+ — these are starting points, not exhaustive)

| File | What to put in it | Where to look |
|------|-------------------|---------------|
| 01_reddit_best_dining_hall.txt | A r/berkeley thread debating which dining hall is best | search r/berkeley "best dining hall" |
| 02_reddit_crossroads.txt       | Thread(s) specifically about Crossroads | r/berkeley "crossroads" |
| 03_reddit_cafe3.txt            | Thread(s) about Cafe 3 / Unit 3 dining | r/berkeley "cafe 3" |
| 04_reddit_clark_kerr.txt       | Thread(s) about Clark Kerr / CKC dining | r/berkeley "clark kerr dining" |
| 05_reddit_foothill.txt         | Thread(s) about Foothill dining | r/berkeley "foothill dining" |
| 06_reddit_meal_plan.txt        | Thread about meal plans / meal points / whether worth it | r/berkeley "meal plan worth it" |
| 07_yelp_crossroads.txt         | Yelp reviews for Crossroads / a dining hall | yelp.com search "Crossroads Berkeley" |
| 08_yelp_cafe3.txt              | Yelp reviews for Cafe 3 or another hall | yelp.com |
| 09_blog_dining_guide.txt       | A student blog / Daily Cal / Medium "guide to Berkeley dining" | google "berkeley dining hall guide student blog" |
| 10_reddit_late_night_hours.txt | Thread about late-night dining / hours / wait times | r/berkeley "late night dining hours" |

You can rename/repurpose files freely — just keep the `SOURCE:` / `URL:` header lines.

**Minimum: 10 documents.** More variety = better retrieval and a more interesting eval.
When done, tell me "documents are in" and I'll build the ingestion pipeline.
