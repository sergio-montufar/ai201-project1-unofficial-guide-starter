# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Student reviews of **computer science professors and courses at the University of Connecticut (UConn)**. The official course catalog and School of Computing pages list each CSE course's topics, credits, and prerequisites, but say nothing about what actually shapes a student's experience: which professor teaches a section best, how hard the exams are, whether the grade is curved, how heavy the weekly problem-set load is, and how approachable the instructor is. That knowledge lives only in student-written reviews scattered across RateMyProfessors, Coursicle, and r/UConn — so a student has to piece it together across several sites. The university has no incentive to publish candid assessments of teaching quality or difficulty, which is exactly why this unofficial knowledge is valuable and hard to find through official channels.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors — Derek Aguiar | Professor review site | https://www.ratemyprofessors.com/professor/2460362 → `documents/rmp_derek_aguiar.txt` |
| 2 | RateMyProfessors — Justin Furuness | Professor review site | https://www.ratemyprofessors.com/professor/3127655 → `documents/rmp_justin_furuness.txt` |
| 3 | RateMyProfessors — Jonathan Clark | Professor review site | https://www.ratemyprofessors.com/professor/2898389 → `documents/rmp_jonathan_clark.txt` |
| 4 | RateMyProfessors — Wei Zhang | Professor review site | https://www.ratemyprofessors.com/professor/2999154 → `documents/rmp_wei_zhang.txt` |
| 5 | RateMyProfessors — Lina Kloub | Professor review site | https://www.ratemyprofessors.com/professor/2754387 → `documents/rmp_lina_kloub.txt` |
| 6 | RateMyProfessors — Laurent Michel | Professor review site | https://www.ratemyprofessors.com/professor/1135923 → `documents/rmp_laurent_michel.txt` |
| 7 | Coursicle — CSE 2050 (Lina Kloub) | Course review site | https://www.coursicle.com/uconn/courses/CSE/2050/ → `documents/coursicle_cse2050_kloub.txt` |
| 8 | Coursicle — CSE 3500 (Justin Furuness) | Course review site | https://www.coursicle.com/uconn/courses/CSE/3500/ → `documents/coursicle_cse3500_furuness.txt` |
| 9 | Coursicle — CSE 3100 (Swamy Pattipati) | Course review site | https://www.coursicle.com/uconn/courses/CSE/3100/ → `documents/coursicle_cse3100_swamy.txt` |
| 10 | Reddit — r/UConn thread "Any Feelings on CSE 4300" (Prof. Khan) | Forum / discussion thread | https://www.reddit.com/r/UConn/ → `documents/reddit_cse4300_khan.txt` |

> **Note:** 10 sources across three source types (professor review site, course-review site, forum). RateMyProfessors (6 pages) was scraped programmatically; Coursicle (rate-limited) and Reddit (crawler-blocked) were collected manually. Lina Kloub appears on two platforms (RateMyProfessors + Coursicle), which deepens CSE 2050 coverage. An earlier RateMyProfessors source (Cooper Frank) was dropped because he is a teaching assistant rather than a professor, which is off-domain.

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** Target ~450 characters (~115 tokens) for the fixed-size path, but the **primary strategy is one review per chunk**. Reviews are split on a `---` delimiter (or blank lines); each review becomes its own chunk regardless of length, and only a review longer than 600 characters is fixed-split into ~450-char pieces. Fragments shorter than 25 characters are dropped.

**Overlap:** ~50 characters on the fixed-size path; **0 overlap** on the per-review path, since each review is already a self-contained opinion.

**Why these choices fit your documents:** This is a review-heavy corpus, not long prose. A RateMyProfessors/Coursicle review is typically 1–4 sentences expressing one self-contained opinion about a specific professor or course. One-review-per-chunk keeps each opinion as its own retrievable unit; larger chunks would merge unrelated reviews — even reviews of *different professors* — into a single vector and blur retrieval. **Preprocessing before chunking** (`clean_text` in `ingest.py`): decode HTML entities (`&amp;`, `&nbsp;`, `&#39;`), strip HTML tags, and drop boilerplate — nav menus, cookie banners, ads, footers, "Read more"/share links, vote/rating counts, and bare URL/`Source:` lines — using a two-tier filter (unambiguous chrome dropped at any length; metadata labels dropped only on short lines so prose like "...office hours are super helpful. Would take again." survives). Each chunk is then prefixed with a `[Professor/Course]` label so it stays self-attributing even when the review text only says "he"/"the professor."

**Final chunk count:** **37 chunks across 10 documents** (avg ~3.7/doc; sizes 69–416 chars). This is below the 50-chunk rule of thumb — not because chunks are too large, but because several sources (especially the manually-collected Coursicle/Reddit pages) contribute only 1–3 reviews each; the count rises directly with more collected reviews.

**Sample chunks** (5 chunks, each shown with its source document — every chunk is prefixed with a `[Professor/Course]` label for self-attribution):

1. **`coursicle_cse2050_kloub.txt`** — `[CSE 2050 Kloub]` Professor Kloub was a great professor and made the class really easy. Her lectures are easy to follow. When we learn a new data structure or algorithm she will draw them on the board and go step by step explaining everything that happens. She's also willing to answer questions and seems like she really cares.
2. **`coursicle_cse3100_swamy.txt`** — `[CSE 3100 Swamy]` The course along with the exams and homework are pretty tough, however Swamy knows this and takes it into account while grading. Show up to lecture, pay attention, and you'll be rewarded. Dude is hilarious too, always looked forward to lecture because it was like going to a comedy club. Don't use AI, code on your own, ask for help.
3. **`coursicle_cse3500_furuness.txt`** — `[CSE 3500 Furuness]` Absolutely goated professor! Not only does he know the material, but he is willing to teach you more about Python and give opportunities to become an even better programmer. If you are struggling in this course, come in during office hours, do the practice tests, and look for resources and videos online.
4. **`reddit_cse4300_khan.txt`** — `[CSE 4300 Khan]` That final was rough compared to the last two exams. While many of the questions seemed fair content-wise, the sheer number of them was overwhelming. The average on the first exam wasn't great (55%) and the second (~66%) was only a little better. These exams add up to about 61% of our grade, so the grading leans heavily on exams.
5. **`rmp_derek_aguiar.txt`** — `[Derek Aguiar]` If you have the opportunity to, definitely take it with Derek! He's an awesome guy and you learn so much. Would recommend!

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dimensional embeddings, ~256-token max input), with embeddings normalized and stored in **ChromaDB** using cosine distance. Chosen because it runs locally with no API key or rate limits, is fast, and its short context window is a natural fit for short reviews. Retrieval uses **top-k = 5**.

**Production tradeoff reflection:** If cost weren't a constraint and this served real students, I'd weigh: **(1) Accuracy on domain text** — a larger model (`all-mpnet-base-v2`, or an API model like OpenAI `text-embedding-3-large` / Voyage) better captures nuance like sarcasm and hedged opinions ("not the worst, but…") that are common in reviews. **(2) Context length** — MiniLM truncates at ~256 tokens, so unusually long reviews lose their tail; a longer-context model would preserve them. **(3) Latency & local vs. API** — MiniLM is local and instant; API models add network latency and per-call cost but offload compute. **(4) Multilingual** — not needed here (reviews are English), so I wouldn't pay for multilingual capability. Net: I'd move to `all-mpnet-base-v2` for an accuracy bump while staying local before reaching for a paid API model.

**Retrieval test examples** (top chunks per query, with cosine distance — lower = closer):

**Example 1 — "How is Derek Aguiar's grading in his algorithms class?"**
| dist | source | chunk (excerpt) |
|---|---|---|
| 0.389 | `rmp_derek_aguiar.txt` | "Awesome algorithms professor, you will genuinely learn so much…" |
| 0.446 | `rmp_derek_aguiar.txt` | "He's a good professor. But exam and homework was hard." |
| 0.467 | `rmp_derek_aguiar.txt` | "People say Aguiar's section is harder, but his grading is very forgiving. Homework is mostly completion…" |

*Why these are relevant:* all three are from Aguiar's own reviews, and rank 3 directly answers the grading question. The embedding correctly clustered the query with Aguiar's algorithms reviews rather than other professors' — name + topic ("algorithms," "grading") both contributed.

**Example 2 — "Who teaches CSE 2050 Data Structures and what is she like?"**
| dist | source | chunk (excerpt) |
|---|---|---|
| 0.325 | `coursicle_cse2050_kloub.txt` | "Professor Kloub was a great professor and made the class really easy…" |
| 0.409 | `coursicle_cse3100_swamy.txt` | (header chunk — off-topic) |
| 0.421 | `rmp_lina_kloub.txt` | "Lina Kloub is an amazing professor, and honestly one of the best instructors…" |

*Why these are relevant:* the top hit names Kloub and describes her teaching (the exact answer), and rank 3 pulls her reviews from a **different source** (RateMyProfessors) — the system converges on Kloub across both platforms. The rank-2 Swamy header is a thin-corpus artifact and is off-topic.

**Example 3 — "Is there a curve in CSE 4300 with Khan?"**
| dist | source | chunk (excerpt) |
|---|---|---|
| 0.465 | `reddit_cse4300_khan.txt` | "I also thought the exam was really rough… a curve of a whole letter grade…" |
| 0.552 | `reddit_cse4300_khan.txt` | (header chunk) |
| 0.602 | `reddit_cse4300_khan.txt` | "…my C got curved to a B. The final was ridiculously long." |

All three hits come from the Khan/CSE 4300 thread, and ranks 1 and 3 carry the answer about the curve.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The model (Groq `llama-3.3-70b-versatile`, temperature 0.2) is given the retrieved chunks as `CONTEXT` and a system prompt with explicit rules (in `query.py`): (1) *"Use ONLY facts found in the CONTEXT. Never rely on outside knowledge or guess. Do not invent professors, courses, grades, or details."* (2) *"If the CONTEXT does not contain enough information to answer, reply exactly: 'I don't have enough information in the student reviews to answer that.'"* (3) *"When reviews disagree... report the RANGE of opinions rather than a single verdict."* (4) attribute claims and phrase them as subjective ("students report..."). This was verified with an adversarial test: asking *what topics CSE 3100 covers* — which the model could easily answer from training knowledge — correctly returned the decline, because the reviews don't describe course topics.

**Structural grounding choices:** Beyond the prompt, two structural guards: (a) a **similarity floor** (`MIN_SIMILARITY = 0.20`) — if no retrieved chunk clears the bar, the system declines *without calling the LLM*, so clearly off-domain questions ("best dining hall?") fail closed; (b) the context is formatted as numbered, source-labeled blocks so claims can be traced.

**How source attribution is surfaced in the response:** `ask()` returns `{"answer", "sources"}`; the Gradio UI shows the answer plus a **"Retrieved from"** list of the distinct sources (e.g. `Derek Aguiar (rmp_derek_aguiar.txt)`). When the model declines, the source list is cleared, so a "not enough information" response is never paired with misleading citations. (Caveat: the list reflects what was *retrieved*, not strictly what was *cited* — see Failure Case Analysis.)

**Example responses with source attribution** (actual system output):

> **Q:** How is Derek Aguiar's grading in his algorithms class?
> **A:** Students report that Derek Aguiar's grading in his algorithms class is very forgiving. Reviewers say that homework is mostly completion-based if you follow the guidelines, and on exams, as long as you follow the general formula, you'll get most points even if your solution is wrong.
> **Retrieved from:** Derek Aguiar (`rmp_derek_aguiar.txt`); Justin Furuness (`rmp_justin_furuness.txt`); CSE 2050 Kloub (`coursicle_cse2050_kloub.txt`)

> **Q:** Is there a curve in CSE 4300 (Operating Systems) with Khan?
> **A:** Students report that there is a curve in CSE 4300 with Professor Khan. One reviewer mentions a curve of a whole letter grade, although they are unsure of the specifics. Another reviewer shares their personal experience, stating that their grade was curved from a C to a B.
> **Retrieved from:** CSE 4300 Khan (`reddit_cse4300_khan.txt`); Jonathan Clark (`rmp_jonathan_clark.txt`); Wei Zhang (`rmp_wei_zhang.txt`)

**Out-of-scope query (refusal):**

> **Q:** What's the best dining hall on campus?
> **A:** I don't have enough information in the student reviews to answer that.
> **Retrieved from:** *(none — no sources shown)*

This question is on-topic for "campus life" but outside the corpus (which only covers CS professors/courses), so the system declines rather than answering from the model's general knowledge.

---

## Query Interface

The system ships with a **Gradio** web app (`app.py`) wrapping the end-to-end `query.ask()` function. Launch it with `python app.py`, which serves a local URL (default `http://127.0.0.1:7860`).

**Input field**
- **Your question** — a free-text box for a natural-language question about a UConn CS professor or course.

**Output fields**
- **Answer** — the grounded answer generated from the retrieved reviews (or the refusal message if nothing relevant is found).
- **Retrieved from** — a bulleted list of the distinct source documents the answer drew on; empty when the system declines.

**Sample interaction transcript:**

```
[Your question]
What do students think of Justin Furuness for CSE 3500?

[Answer]
Students report that Justin Furuness is a great professor, but CSE 3500 with him
can be stressful. Some students say he grades strictly, with exams worth 80 percent
of the grade, and that the course is all programming with no proofs, which can be
challenging. However, others say he is lenient with grading and available after
class. Reviewers agree that his class will help improve programming skills, with
some recommending him for those who want a challenge, while others suggest
considering a different professor for an easier experience.

[Retrieved from]
• Justin Furuness (rmp_justin_furuness.txt)
• Laurent Michel (rmp_laurent_michel.txt)
```

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | How is Derek Aguiar's grading in his algorithms class? | Forgiving: homework mostly completion-based, partial credit on exams if you follow the formula, and the final lets you recover earlier exam points. | "Grading is very forgiving — homework mostly completion-based, exams give most points if you follow the general formula even if the solution is wrong." Correctly grounded, **but** added "another student notes Aguiar is lenient" — that "lenient" line is actually from a **Furuness** review that was also retrieved, and it **omitted** the final-recovery detail. | Relevant (Aguiar on top; Furuness/Kloub in tail) | **Partially accurate** — core claims right, but one claim cross-attributed from Furuness and one expected detail missing. |
| 2 | What do students think of Justin Furuness for CSE 3500? | Knowledgeable; makes a hard, programming-heavy class approachable; **opinions on grading differ** (strict, exams ~80% vs. lenient); ranked among the best. | "Knowledgeable; opinions vary — some say great and approachable, others say stressful with strict grading; adds programming (harder but improves skills); one found him lenient and available, another warns exams are 80% of the grade." | Relevant | **Accurate** — captures the range of opinions, including the 80%-exams and lenient-vs-strict split. |
| 3 | Who teaches CSE 2050 (Data Structures) and what is she like? | **Lina Kloub** — easy to follow, draws structures/algorithms step-by-step on the board, answers questions, clearly cares. | "Professor Kloub teaches it; lectures easy to follow, explains data structures/algorithms step by step, willing to answer questions, seems to really care." | Relevant (Kloub on top; off-course chunks in tail) | **Accurate** — matches the single CSE 2050 review faithfully. |
| 4 | For CSE 3100, what do students say about Wei Zhang vs. Swamy Pattipati? | **Zhang**: hard to understand, lectures misaligned with exams → students recommend **Swamy**. **Swamy**: tough but grades accommodatingly, entertaining lectures. | "Zhang's exams may not reflect lectures (~60% overlap); some recommend Swamy instead. Then states 'the reviews do not provide direct comparisons' — **failed to use the Swamy review** (tough-but-accommodating, hilarious lectures) that was retrieved and in the source list." | Partially relevant (Zhang strong; Swamy chunk only at rank ~5; Kloub off-topic in middle) | **Partially accurate** — Zhang/recommend-Swamy correct, but the Swamy characterization was omitted despite being in context. |
| 5 | Is there a curve in CSE 4300 (Operating Systems) with Khan, and how are the exams? | Exam-heavy (~61% of grade), low averages; a **curve of ~a full letter grade** (C→B); very long final. | "Possible curve of a whole letter grade; one student's C curved to a B; exams rough with high question volume and low averages, a significant portion of the grade; final long; some found content outdated." | Relevant (all top hits from the Khan file) | **Accurate** — includes the curve, the C→B example, exam weighting, and the long final. |

**Retrieval quality:** Relevant for Q1–Q3 and Q5; Partially relevant for Q4 (the Swamy review ranks just below the top-k boundary, so the comparison is one-sided).
**Response accuracy:** Accurate (Q2, Q3, Q5) / Partially accurate (Q1, Q4) / Inaccurate (none).

**Summary:** 3 of 5 fully accurate, 2 partially accurate, 0 inaccurate, 0 hallucinated. Both partials trace to the same root cause — a **thin corpus**: with few chunks per topic, an off-entity chunk (Furuness's "lenient" in Q1) or an under-ranked relevant chunk (Swamy in Q4) slips into or out of the top-k and skews the synthesis. The grounding itself held: every claim came from a retrieved chunk, and no answer invented facts.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "For CSE 3100, what do students say about Wei Zhang versus Swamy Pattipati?" (Eval Q4)

**What the system returned:** It described Wei Zhang correctly (lectures don't match the exam, ~60% overlap) and noted that some students recommend Swamy instead — but then stated *"the reviews do not provide direct comparisons of the two professors' teaching styles or the content of their classes."* The substance of the Swamy review (tough course, but he grades accommodatingly, and his lectures are entertaining) was missing entirely.

**Root cause (tied to a specific pipeline stage):** A **chunking** flaw surfacing at the **retrieval** top-k boundary. Inspecting the ranked results for this query (cosine distance):

| rank | chunk | distance | in top-5? |
|---|---|---|---|
| 1–3 | Wei Zhang reviews | 0.347–0.417 | ✅ |
| 4 | **CSE 2050 Kloub** (off-topic) | 0.531 | ✅ |
| 5 | **Swamy — bare header line** ("Swamy Pattipati — CSE 3100 (Systems Programming)") | 0.547 | ✅ |
| 6 | **Swamy — the actual review** (grades accommodatingly, funny lectures) | 0.548 | ❌ |

The Coursicle source file was written as a header line, a `---` separator, then the review, so chunking produced **two** chunks for Swamy: a contentless header and the real review. The header chunk has dense keyword overlap with the query ("Swamy Pattipati", "CSE 3100") so it ranks *above* the opinion-bearing review. At k=5 the model therefore received the **header (no information)** and was cut off from the **review (rank 6) by a 0.001 distance margin** — while an unrelated CSE 2050 chunk consumed the rank-4 slot. The generation step behaved correctly given its inputs; the failure was that the only Swamy *content* never entered the context.

**What you would change to fix it:** Two changes, in order of impact:
1. **Don't emit header-only chunks (chunking fix).** Since every chunk is already prefixed with its `[label]`, the in-file "Professor — Course — University" header is redundant; dropping it (or merging it into the review instead of separating with `---`) eliminates the contentless chunk and lets the real Swamy review rise from rank 6 into the top-5.
2. **Course-aware retrieval filtering (retrieval fix).** When the query names a course (e.g., "CSE 3100"), filter the ChromaDB query with a `where` clause on a `course` metadata field so off-topic chunks like the CSE 2050 (Kloub) review can't occupy a top-k slot. This directly targets the cross-course leakage flagged in planning.md Challenge #2.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the Chunking Strategy and Retrieval Approach with concrete numbers *before* coding meant the implementation was mostly translation rather than guesswork — the chunk size, ~50-char overlap, `all-MiniLM-L6-v2`, and top-k=5 became constants in `ingest.py`/`embed.py` directly. The Anticipated Challenges section paid off most: Challenge #2 (cross-entity retrieval, "include the professor/course label in each chunk's text") directly motivated the `[label]` prefix I added after inspecting chunks and finding pronoun-only reviews ("he"/"the professor") weren't self-attributing — a fix I would not have prioritized without having named the risk in advance.

**One way your implementation diverged from the spec, and why:** The spec framed chunking around a 400–500-char fixed size; in practice I made **one-review-per-chunk the primary path** and used fixed-size splitting only as a fallback for reviews over 600 chars, because real reviews are short and self-contained, so forcing a uniform size would have merged or split opinions unnaturally. The **evaluation questions also changed**: the original five assumed professor↔course pairings (e.g. Don Sheehy for CSE 2050) that turned out to be wrong or uncollected, so after gathering the real corpus I rewrote them to match what the documents actually say (Lina Kloub for CSE 2050; added Prof. Khan / CSE 4300 from Reddit). The retrieval `k` stayed at 5 — and the Q4 failure analysis showed why dropping below 5 would be worse.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Ingestion & chunking**

- *What I gave the AI:* My Chunking Strategy section from planning.md plus sample RateMyProfessors review files, and asked it to implement document loading, boilerplate cleaning, and chunking.
- *What it produced:* `ingest.py` with `load_documents()`, `clean_text()`, and a per-review/fixed-size `chunk_text()`.
- *What I changed or overrode:* After inspecting the output I found two problems and directed fixes: (1) most chunks relied on pronouns ("he"/"the professor") and weren't self-attributing, so I had it prepend a `[Professor/Course]` label to every chunk; (2) the boilerplate filter was dropping real review sentences that merely contained words like "would take again," so I had it switch to a length-guarded, two-tier filter. I also bumped the minimum chunk size from 20 to 25 chars to drop a content-free "Derek is the GOAT!!!" fragment.

**Instance 2 — Grounded generation**

- *What I gave the AI:* My grounding requirements (answer only from retrieved context, decline when unsupported, cite sources) and a Gradio interface skeleton, and asked it to wire generation together with Groq.
- *What it produced:* `query.py` (`ask()` → grounded Groq call) and `app.py` (the Gradio UI).
- *What I changed or overrode:* Testing surfaced a bug — when the model declined an off-domain question, the UI still listed retrieved sources, implying citations for an answer that was never given. I had it detect the decline and return an empty source list. I also kept the structural similarity floor (`MIN_SIMILARITY = 0.20`) as a guard so clearly off-domain queries fail closed without an LLM call, and verified grounding held with an adversarial "what does CSE 3100 cover?" test.
