"""BGE-small-en embedding wrapper (lazy-loaded singleton)."""
from __future__ import annotations

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
MODEL_NAME = "BAAI/bge-small-en-v1.5"


def embed(texts: list[str]) -> list[list[float]]:
    return _get_model().encode(texts, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    return embed([f"Represent this sentence for searching relevant passages: {text}"])[0]


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model
