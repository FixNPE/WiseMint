"""Unit tests for market data cache."""
import time
from src.market import cache


def test_set_and_get():
    cache.set("test_key", {"price": 150.0})
    result = cache.get("test_key")
    assert result == {"price": 150.0}


def test_missing_key_returns_none():
    assert cache.get("nonexistent_xyz") is None
