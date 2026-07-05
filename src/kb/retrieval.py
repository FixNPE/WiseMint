"""Hybrid BM25 + ChromaDB retrieval with RRF fusion."""
from __future__ import annotations

import pickle
from pathlib import Path

import chromadb

from src.kb.embeddings import embed_query
from src.kb.ingest import BM25_PATH, COLLECTION, _build_client

TOP_K = 5
RRF_K = 60  # constant in RRF formula


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    dense = _dense_search(query, top_k)
    sparse = _sparse_search(query, top_k)
    return _rrf_fuse(dense, sparse, top_k)


def _dense_search(query: str, top_k: int) -> list[dict]:
    col = _get_collection()
    results = col.query(
        query_embeddings=[embed_query(query)],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"text": doc, "source": meta.get("source", ""), "score": 1 - dist})
    return hits


def _sparse_search(query: str, top_k: int) -> list[dict]:
    if not BM25_PATH.exists():
        return []
    with open(BM25_PATH, "rb") as f:
        data = pickle.load(f)
    index = data["index"]
    chunks = data["chunks"]
    tokens = query.lower().split()
    scores = index.get_scores(tokens)
    ranked = sorted(zip(scores, chunks), reverse=True)[:top_k]
    return [{"text": c["text"], "source": c["metadata"]["source"], "score": s} for s, c in ranked]


def _rrf_fuse(dense: list[dict], sparse: list[dict], top_k: int) -> list[dict]:
    scores: dict[str, float] = {}
    texts: dict[str, str] = {}
    sources: dict[str, str] = {}

    for rank, hit in enumerate(dense, 1):
        key = hit["text"][:80]
        scores[key] = scores.get(key, 0) + 1 / (RRF_K + rank)
        texts[key] = hit["text"]
        sources[key] = hit["source"]

    for rank, hit in enumerate(sparse, 1):
        key = hit["text"][:80]
        scores[key] = scores.get(key, 0) + 1 / (RRF_K + rank)
        texts[key] = hit["text"]
        sources[key] = hit["source"]

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{"text": texts[k], "source": sources[k], "rrf_score": s} for k, s in ranked]


def _get_collection() -> chromadb.Collection:
    return _build_client().get_or_create_collection(COLLECTION)
