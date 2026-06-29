"""30-minute TTL disk cache for market data (~85% hit rate target)."""
from __future__ import annotations

import os
from pathlib import Path

import diskcache

_cache: diskcache.Cache | None = None
TTL = int(os.getenv("CACHE_TTL_SECONDS", "1800"))


def get(key: str):
    return _get_cache().get(key)


def set(key: str, value) -> None:
    _get_cache().set(key, value, expire=TTL)


def _get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None:
        cache_dir = Path("data/market_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        _cache = diskcache.Cache(str(cache_dir))
    return _cache
