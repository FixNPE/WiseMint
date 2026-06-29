"""Alpha Vantage API client with 30-min TTL cache."""
from __future__ import annotations

import os

import httpx

from src.market import cache

BASE_URL = "https://www.alphavantage.co/query"


def get_quote(ticker: str) -> dict:
    key = f"quote:{ticker.upper()}"
    cached = cache.get(key)
    if cached is not None:
        return {**cached, "_cached": True}

    api_key = os.getenv("ALPHA_VANTAGE_KEY", "demo")
    params = {"function": "GLOBAL_QUOTE", "symbol": ticker.upper(), "apikey": api_key}

    try:
        resp = httpx.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quote = data.get("Global Quote", {})
        result = {
            "ticker": ticker.upper(),
            "price": float(quote.get("05. price", 0)),
            "change_pct": quote.get("10. change percent", "0%"),
            "volume": quote.get("06. volume", "N/A"),
            "latest_trading_day": quote.get("07. latest trading day", ""),
        }
        cache.set(key, result)
        return result
    except (httpx.HTTPError, ValueError, KeyError) as e:
        return {"ticker": ticker.upper(), "error": str(e)}


def get_sector_performance() -> dict:
    key = "sectors"
    cached = cache.get(key)
    if cached is not None:
        return cached

    api_key = os.getenv("ALPHA_VANTAGE_KEY", "demo")
    params = {"function": "SECTOR", "apikey": api_key}
    try:
        resp = httpx.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("Rank A: Real-Time Performance", {})
        cache.set(key, result)
        return result
    except (httpx.HTTPError, ValueError) as e:
        return {"error": str(e)}
