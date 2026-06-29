"""Ingest raw text/PDF documents into ChromaDB + BM25 index."""
from __future__ import annotations

import os
import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

from src.kb.embeddings import embed

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
COLLECTION = "finadvisor_kb"
BM25_PATH = Path("data/bm25_index.pkl")

_chroma: chromadb.HttpClient | None = None


def ingest_directory(directory: str | Path) -> int:
    """Chunk and index all .txt files in a directory. Returns doc count."""
    docs = _load_texts(Path(directory))
    chunks = _chunk_docs(docs)
    _store_chroma(chunks)
    _store_bm25(chunks)
    return len(chunks)


def _load_texts(directory: Path) -> list[tuple[str, str]]:
    results = []
    for path in directory.glob("*.txt"):
        results.append((path.stem, path.read_text(encoding="utf-8")))
    return results


def _chunk_docs(docs: list[tuple[str, str]]) -> list[dict]:
    chunks = []
    for doc_id, text in docs:
        start = 0
        idx = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end]
            chunks.append({
                "id": f"{doc_id}_{idx}",
                "text": chunk_text,
                "metadata": {"source": doc_id, "chunk": idx},
            })
            idx += 1
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _store_chroma(chunks: list[dict]) -> None:
    col = _get_collection()
    texts = [c["text"] for c in chunks]
    embeddings = embed(texts)
    col.upsert(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in chunks],
    )


def _store_bm25(chunks: list[dict]) -> None:
    tokenised = [c["text"].lower().split() for c in chunks]
    index = BM25Okapi(tokenised)
    BM25_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BM25_PATH, "wb") as f:
        pickle.dump({"index": index, "chunks": chunks}, f)


def _get_collection() -> chromadb.Collection:
    global _chroma
    if _chroma is None:
        host = os.getenv("CHROMA_HOST", "localhost")
        port = int(os.getenv("CHROMA_PORT", "8000"))
        _chroma = chromadb.HttpClient(host=host, port=port)
    return _chroma.get_or_create_collection(COLLECTION)
