"""SQLite user profile store — per-turn personalization."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/profile.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def get_profile(user_id: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT data FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
    return json.loads(row[0]) if row else {}


def update_profile(user_id: str, updates: dict) -> None:
    profile = get_profile(user_id)
    profile.update(updates)
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO profiles (user_id, data) VALUES (?, ?)",
            (user_id, json.dumps(profile)),
        )
        conn.commit()


def profile_to_context(user_id: str) -> str:
    profile = get_profile(user_id)
    if not profile:
        return ""
    lines = [f"{k}: {v}" for k, v in profile.items()]
    return "User profile:\n" + "\n".join(lines)
