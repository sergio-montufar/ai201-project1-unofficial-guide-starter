"""
Embedding + vector store + retrieval for The Unofficial Guide (Project 1).

Implements the Retrieval Approach from planning.md:
  - Embedding model: all-MiniLM-L6-v2 via sentence-transformers (local, 384-dim).
  - Vector store: ChromaDB (persistent, on disk at ./chroma_db).
  - Retrieval: similarity search, top-k = 5.

Chunks come from ingest.build_chunks() (clean + review-sized chunks).

Run:
    python embed.py index                 # (re)build the vector store from documents/
    python embed.py query "your question" # retrieve top-k chunks for a query
"""

from __future__ import annotations

import argparse
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import build_chunks, DOCUMENTS_DIR

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"   # from planning.md "Retrieval Approach"
COLLECTION_NAME = "uconn_cs_reviews"
PERSIST_DIR = Path("chroma_db")
TOP_K = 5                               # from planning.md "Top-k"

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def get_collection(reset: bool = False) -> chromadb.api.models.Collection.Collection:
    """Return the persistent ChromaDB collection (optionally recreated)."""
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection may not exist yet
    # cosine distance matches normalized sentence-transformers embeddings well
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(documents_dir: Path = DOCUMENTS_DIR) -> int:
    """Embed every chunk from documents/ and store it in ChromaDB."""
    chunks = build_chunks(documents_dir)
    if not chunks:
        print(f"No chunks found in {documents_dir}/ — nothing to index.")
        return 0

    model = get_model()
    embeddings = model.encode(
        [c.text for c in chunks],
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()

    collection = get_collection(reset=True)
    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "source": c.source,
                "source_label": c.source_label,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ],
    )
    print(f"Indexed {len(chunks)} chunks from "
          f"{len({c.source for c in chunks})} sources "
          f"into ChromaDB collection '{COLLECTION_NAME}'.")
    return len(chunks)


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the top-k most similar chunks for a query.

    Each result: {"text", "source", "source_label", "score"} where score is
    cosine similarity in [0, 1] (1 = most similar).
    """
    model = get_model()
    query_emb = model.encode([query], normalize_embeddings=True).tolist()
    collection = get_collection()
    res = collection.query(
        query_embeddings=query_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({
            "text": doc,
            "source": meta.get("source", "?"),
            "source_label": meta.get("source_label", "?"),
            "score": round(1 - dist, 3),   # cosine distance -> similarity
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed + retrieve UConn CS reviews.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="(re)build the vector store from documents/")

    q = sub.add_parser("query", help="retrieve top-k chunks for a question")
    q.add_argument("text", help="the question / search query")
    q.add_argument("-k", type=int, default=TOP_K, help="number of chunks (default 5)")

    args = parser.parse_args()

    if args.command == "index":
        build_index()
    elif args.command == "query":
        hits = retrieve(args.text, k=args.k)
        if not hits:
            print("No results — did you run `python embed.py index` first?")
            return
        print(f"Top {len(hits)} chunks for: {args.text!r}\n")
        for i, h in enumerate(hits, 1):
            preview = h["text"] if len(h["text"]) <= 220 else h["text"][:217] + "..."
            print(f"{i}. [{h['source_label']}] (sim {h['score']})")
            print(f"   {preview}\n")


if __name__ == "__main__":
    main()
