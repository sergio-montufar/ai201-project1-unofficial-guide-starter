"""
Ingestion + chunking for The Unofficial Guide (Project 1).

Implements the Chunking Strategy from planning.md:
  - Load every .txt file in documents/ (one file per professor or course).
  - Clean site boilerplate (nav, "would take again %", vote counts, ads).
  - Prefer ONE REVIEW PER CHUNK when a file is cleanly separable
    (reviews split on a "---" delimiter line or blank lines).
  - Otherwise fall back to fixed-size chunks of ~400-500 chars with ~50
    char overlap, split on word boundaries so reviews aren't cut mid-word.
  - Attach source metadata to every chunk.

Expected document format (documents/<name>.txt):

    rmp_derek_aguiar.txt
    ---------------------
    Great professor, problem sets are hard but fair. Exams are curved.
    ---
    Posts all lecture notes online. Best CS prof I've had at UConn.
    ---
    Boring lectures but the material is interesting.

Run:
    python ingest.py                 # print stats for documents/
    python ingest.py --out chunks.jsonl   # also write chunks to JSONL
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

# --- Chunking parameters (from planning.md "Chunking Strategy") -------------
CHUNK_SIZE = 450        # target chars per fixed-size chunk (~115 tokens)
CHUNK_OVERLAP = 50      # char overlap on the fixed-size path
MAX_CHUNK_SIZE = 600    # a single review longer than this gets fixed-split too
MIN_CHUNK_CHARS = 25    # drop fragments shorter than this (review text, pre-label)

DOCUMENTS_DIR = Path("documents")

# Reviews within a file may be separated by a line of dashes or by blank lines.
REVIEW_DELIMITER = re.compile(r"^\s*-{3,}\s*$", re.MULTILINE)

# --- Boilerplate cleaning ---------------------------------------------------
# Two tiers. ALWAYS_DROP targets unambiguous non-review chrome that can appear
# on a line of any length (HTML, URLs, cookie/consent banners, footers, ads,
# "read more" links, share buttons). DROP_IF_SHORT targets metadata labels that
# could also appear inside real review prose, so they are only dropped when the
# line is short (a long sentence containing the word is kept).

# Raw HTML tags are stripped before line filtering runs.
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# Leftover entities after html.unescape (e.g. malformed/double-encoded ones).
_LEFTOVER_ENTITY_RE = re.compile(r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);")

_ALWAYS_DROP_PATTERNS = [
    r"^\s*https?://\S+\s*$",                     # a bare URL on its own line
    r"^\s*www\.\S+\s*$",
    r"^\s*source\s*:",                           # "Source: RateMyProfessors (url)"
    r"\bwe use cookies\b",                       # cookie/consent banners (any length)
    r"\bcookie (policy|preferences|settings|consent)\b",
    r"\baccept (all )?cookies\b",
    r"©|\(c\)\s*\d{4}|\ball rights reserved\b",  # footer / copyright
    r"\bprivacy policy\b|\bterms of (use|service)\b",
    r"\badvertisement\b|\bsponsored\b",          # ads
    r"\bskip to (main )?content\b",              # nav
    r"found this (review )?helpful",             # "12 people found this helpful"
]
_ALWAYS_DROP_RE = re.compile("|".join(f"(?:{p})" for p in _ALWAYS_DROP_PATTERNS),
                             re.IGNORECASE)

_DROP_IF_SHORT_PATTERNS = [
    r"would take again",                        # "82% Would Take Again"
    r"level of difficulty",
    r"^\s*quality\s*$",
    r"^\s*overall quality",
    r"add a rating",
    r"rate (this )?professor",
    r"rate my professors",
    r"^\s*coursicle\b",
    r"compare professors?",
    r"i'?m professor",
    r"^\s*\d+\s+ratings?\s*$",                   # "147 ratings"
    r"^\s*\d+\s+reviews?\s*$",                   # "78 reviews"
    r"^\s*\d+\s+comments?\s*$",                  # "12 comments"
    r"^\s*helpful\s*$",
    r"was this (review )?helpful",
    r"^\s*\d+\s*$",                              # lone vote-count numbers
    r"^\s*\d+\.\d+\s*$",                         # lone rating numbers, e.g. "3.5"
    r"^\s*(share|tweet|reply|save|award|report)\s*$",  # action buttons
    r"\b(read|show|see) more\b",                # "Read more" links
    r"report (this )?(rating|review)",
    r"^\s*tags?\s*:?\s*$",
    r"\bcookie\b",
    r"^\s*top tags",
    r"^\s*menu\s*$",
]
_DROP_IF_SHORT_RE = re.compile("|".join(f"(?:{p})" for p in _DROP_IF_SHORT_PATTERNS),
                               re.IGNORECASE)

# Metadata labels (e.g. "59% Would Take Again", "Helpful") are short standalone
# lines; a real review sentence that happens to contain those words
# ("...office hours are super helpful. Would take again.") is longer and kept.
_BOILERPLATE_MAX_LINE = 45

# Nav-menu / action-button words. A SHORT line whose tokens are *all* drawn from
# this set is chrome (e.g. "Home | Professors", "Share Tweet", "Login | Sign Up")
# and is dropped. Because every token must match, real prose like
# "Great professor" or "Sign me up" (which contain non-chrome words) is kept.
_CHROME_WORDS = {
    "home", "menu", "search", "about", "contact", "help", "faq", "blog",
    "professors", "schools", "courses", "departments", "login", "log", "in",
    "logout", "signin", "sign", "up", "register", "next", "previous", "prev",
    "back", "more", "share", "tweet", "post", "reply", "save", "award", "like",
    "follow", "upvote", "downvote", "comment", "comments", "report", "edit",
    "delete", "copy", "link", "facebook", "twitter", "linkedin", "instagram",
    "email", "print",
}
_CHROME_TOKEN_RE = re.compile(r"[a-z]+")


def _is_chrome_line(line: str) -> bool:
    """True if a short line is composed only of nav/button words + separators."""
    tokens = _CHROME_TOKEN_RE.findall(line.lower())
    return bool(tokens) and all(t in _CHROME_WORDS for t in tokens)


@dataclass
class Chunk:
    text: str
    source: str                 # file name, e.g. "rmp_derek_aguiar.txt"
    source_label: str           # human label, e.g. "Rmp Derek Aguiar"
    chunk_index: int            # position within the source document
    chunk_id: str               # "<source>::<index>"
    n_chars: int = field(default=0)

    def __post_init__(self):
        self.n_chars = len(self.text)


def clean_text(raw: str) -> str:
    """Strip HTML, decode entities, drop site boilerplate, normalize whitespace.

    Keeps review prose, opinions, ratings, and in-text context (professor name,
    course number). Removes HTML tags, HTML entities, nav menus, cookie banners,
    ads, footers, "read more"/share/report links, and comment/vote counts.
    """
    # 1. Decode HTML entities (&amp; -> &, &nbsp; -> non-breaking space, &#39; -> ')
    text = html.unescape(raw)
    # 2. Strip HTML tags
    text = _HTML_TAG_RE.sub(" ", text)
    # 3. Remove any leftover/malformed entities and normalize NBSP to a space
    text = _LEFTOVER_ENTITY_RE.sub(" ", text).replace("\xa0", " ")

    kept_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept_lines.append("")          # keep blank lines as review separators
            continue
        # unambiguous chrome: drop regardless of line length
        if _ALWAYS_DROP_RE.search(stripped):
            continue
        # short lines only: drop metadata labels and nav/button chrome
        if len(stripped) <= _BOILERPLATE_MAX_LINE and (
            _DROP_IF_SHORT_RE.search(stripped) or _is_chrome_line(stripped)
        ):
            continue
        # collapse runs of internal whitespace
        kept_lines.append(re.sub(r"[ \t]+", " ", stripped))
    text = "\n".join(kept_lines)
    # collapse 3+ newlines to a double newline (paragraph/review break)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def split_into_reviews(text: str) -> list[str]:
    """Split a cleaned document into individual reviews.

    Uses an explicit '---' delimiter if present; otherwise falls back to
    blank-line separation. Returns the whole text as one item if neither
    separator yields a clean split.
    """
    if REVIEW_DELIMITER.search(text):
        parts = REVIEW_DELIMITER.split(text)
    else:
        parts = re.split(r"\n\s*\n", text)
    reviews = [p.strip() for p in parts if p.strip()]
    return reviews or ([text.strip()] if text.strip() else [])


def chunk_text(text: str, size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Fixed-size chunking on word boundaries with character overlap.

    Used for the fallback path and for any single review that exceeds
    MAX_CHUNK_SIZE. Never cuts a word in half.
    """
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # back off to the last whitespace so we don't split mid-word
            window = text.rfind(" ", start, end)
            if window > start:
                end = window
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


# Leading filename tokens that name the *site*, not the professor/course.
_SOURCE_PREFIXES = {"rmp", "ratemyprofessors", "coursicle", "reddit", "ruconn"}


def _format_token(tok: str) -> str:
    """Title-case a token, but expand course codes: 'cse2050' -> 'CSE 2050'."""
    m = re.match(r"^([a-zA-Z]{2,4})(\d{3,4})$", tok)
    if m:
        return f"{m.group(1).upper()} {m.group(2)}"
    return tok.title()


def _label_from_filename(name: str) -> str:
    """Derive a clean professor/course label from a filename.

    e.g. 'rmp_derek_aguiar.txt' -> 'Derek Aguiar',
         'coursicle_cse2050.txt' -> 'CSE 2050'.
    """
    tokens = [t for t in re.split(r"[_\-]+", Path(name).stem) if t]
    if tokens and tokens[0].lower() in _SOURCE_PREFIXES:
        tokens = tokens[1:]
    return " ".join(_format_token(t) for t in tokens) or Path(name).stem


def chunk_document(source: str, raw: str) -> list[Chunk]:
    """Clean one document and turn it into review-sized chunks."""
    cleaned = clean_text(raw)
    if not cleaned:
        return []

    label = _label_from_filename(source)
    pieces: list[str] = []
    for review in split_into_reviews(cleaned):
        if len(review) > MAX_CHUNK_SIZE:
            # per-review path, but this review is too long -> fixed-split it
            pieces.extend(chunk_text(review))
        else:
            pieces.append(review)

    chunks = []
    idx = 0
    for piece in pieces:
        # measure the review content itself, before adding the label prefix
        if len(piece) < MIN_CHUNK_CHARS:
            continue
        # prepend the source label so every chunk is self-attributing. The
        # embedder only sees chunk text (not metadata), so this strengthens
        # name/course retrieval and fixes pronoun-only chunks ("him", "the
        # professor"). Skip if the label already appears at the start.
        text = piece if piece.startswith(f"[{label}]") else f"[{label}] {piece}"
        chunks.append(Chunk(
            text=text,
            source=source,
            source_label=label,
            chunk_index=idx,
            chunk_id=f"{source}::{idx}",
        ))
        idx += 1
    return chunks


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[tuple[str, str]]:
    """Return (filename, raw_text) for every .txt file in the directory."""
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")
    docs = []
    for path in sorted(documents_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            docs.append((path.name, text))
    return docs


def build_chunks(documents_dir: Path = DOCUMENTS_DIR) -> list[Chunk]:
    """Full pipeline: load -> clean -> chunk every document."""
    all_chunks: list[Chunk] = []
    for source, raw in load_documents(documents_dir):
        all_chunks.extend(chunk_document(source, raw))
    return all_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and chunk documents/.")
    parser.add_argument("--dir", default=str(DOCUMENTS_DIR),
                        help="directory of .txt documents (default: documents/)")
    parser.add_argument("--out", default=None,
                        help="optional path to write chunks as JSONL")
    parser.add_argument("--preview", type=int, default=3,
                        help="how many sample chunks to print (default: 3)")
    args = parser.parse_args()

    chunks = build_chunks(Path(args.dir))

    if not chunks:
        print(f"No chunks produced. Add .txt files to {args.dir}/ and retry.")
        return

    sizes = [c.n_chars for c in chunks]
    n_sources = len({c.source for c in chunks})
    print(f"Sources ingested : {n_sources}")
    print(f"Total chunks     : {len(chunks)}")
    print(f"Chunk size (chars): min {min(sizes)} | "
          f"avg {sum(sizes) // len(sizes)} | max {max(sizes)}")

    print(f"\nFirst {min(args.preview, len(chunks))} chunks:")
    for c in chunks[:args.preview]:
        preview = c.text if len(c.text) <= 160 else c.text[:157] + "..."
        print(f"  [{c.chunk_id}] ({c.n_chars} chars) {preview}")

    if args.out:
        out_path = Path(args.out)
        with out_path.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
        print(f"\nWrote {len(chunks)} chunks -> {out_path}")


if __name__ == "__main__":
    main()
