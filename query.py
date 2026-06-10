"""
Grounded generation for The Unofficial Guide (Project 1) — Milestone 5.

Pipeline stage 5 (Generation) from planning.md:
  retrieve top-k chunks (ChromaDB) -> build a grounded prompt -> Groq LLM.

Grounding requirements (from planning.md "Grounded Generation" / Challenges):
  - The model answers ONLY from the retrieved review chunks, never outside
    knowledge.
  - If the chunks don't support an answer, it declines ("not enough info").
  - When reviews disagree, it reports the RANGE of opinions (Challenge #1).
  - Every answer is paired with its source attribution (Challenge #2).

Public API:
    ask(question) -> {"answer": str, "sources": list[str]}

Run a quick CLI check:
    python query.py "How is Derek Aguiar's grading?"
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from embed import retrieve, TOP_K

load_dotenv()

# Groq Llama model — overridable via .env (GROQ_MODEL).
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Chunks below this cosine similarity are treated as irrelevant. If nothing
# clears the bar, we decline WITHOUT calling the LLM — this is the structural
# grounding guard that makes off-domain questions ("best dining hall?") fail
# closed instead of hallucinating. Tuned to the observed score range: real
# matches sit ~0.45-0.75, off-domain noise falls well below.
MIN_SIMILARITY = 0.20

# The exact sentence the model is told to use when it can't answer (rule 2).
# Reused both in the prompt and to detect an LLM-level decline.
DECLINE_SENTENCE = (
    "I don't have enough information in the student reviews to answer that."
)
DECLINE_MESSAGE = (
    DECLINE_SENTENCE
    + " Try asking about a UConn CS professor or course that's covered in the corpus."
)

SYSTEM_PROMPT = """You are "The Unofficial Guide", a study-aid that answers \
questions about University of Connecticut computer science professors and \
courses using ONLY the student reviews provided to you as CONTEXT.

Follow these rules strictly:
1. Use ONLY facts found in the CONTEXT. Never rely on outside knowledge or \
guess. Do not invent professors, courses, grades, or details.
2. If the CONTEXT does not contain enough information to answer, reply exactly: \
"I don't have enough information in the student reviews to answer that." and \
nothing else.
3. When reviews disagree about a professor or course, report the RANGE of \
opinions (e.g., "some students say... while others say...") rather than a \
single verdict.
4. Attribute claims to the professor or course they are about, and keep the \
answer concise (a short paragraph).
5. These are subjective student opinions, not official facts — phrase \
accordingly ("students report...", "reviewers say...")."""


_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add "
                "your key from https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


def _format_context(chunks: list[dict]) -> str:
    """Number each chunk and label it with its source for attribution."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] (source: {c['source_label']})\n{c['text']}")
    return "\n\n".join(blocks)


def _unique_sources(chunks: list[dict]) -> list[str]:
    """Distinct sources, in retrieval order, as readable attribution strings."""
    seen = set()
    sources = []
    for c in chunks:
        key = c["source"]
        if key not in seen:
            seen.add(key)
            sources.append(f"{c['source_label']} ({c['source']})")
    return sources


def ask(question: str, k: int = TOP_K) -> dict:
    """Answer a question grounded in the retrieved review chunks.

    Returns {"answer": str, "sources": list[str]}.
    """
    hits = retrieve(question, k=k)
    relevant = [h for h in hits if h["score"] >= MIN_SIMILARITY]

    # Fail closed: no relevant context -> decline without invoking the LLM.
    if not relevant:
        return {"answer": DECLINE_MESSAGE, "sources": []}

    context = _format_context(relevant)
    user_message = (
        f"CONTEXT (student reviews):\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the CONTEXT above, following all the rules."
    )

    client = _get_client()
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,          # low: factual, grounded, minimal embellishment
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # If the model declined (chunks passed the similarity floor but didn't
    # actually support an answer), don't show sources — that would imply they
    # informed an answer that was never given.
    if "don't have enough information" in answer.lower():
        return {"answer": answer, "sources": []}
    return {"answer": answer, "sources": _unique_sources(relevant)}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How is Derek Aguiar's grading in algorithms?"
    result = ask(q)
    print(f"Q: {q}\n")
    print("ANSWER:\n" + result["answer"] + "\n")
    print("SOURCES:")
    for s in result["sources"]:
        print(f"  • {s}")
