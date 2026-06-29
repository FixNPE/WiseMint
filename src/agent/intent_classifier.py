"""Zero-shot intent routing using the LLM."""
from __future__ import annotations

from enum import Enum

from groq import Groq

_client: Groq | None = None


class Intent(str, Enum):
    QA = "qa"
    PORTFOLIO = "portfolio"
    PLANNING = "planning"
    GENERAL = "general"


_SYSTEM = """You are an intent classifier for a financial assistant.
Classify the user message into exactly one of: qa, portfolio, planning, general.
- qa: factual questions about financial concepts
- portfolio: requests to analyze holdings, allocation, or live prices
- planning: retirement, savings goals, debt payoff projections
- general: greetings, out-of-scope, unclear
Reply with only the label, nothing else."""


def classify(message: str, client: Groq | None = None) -> Intent:
    c = client or _get_client()
    resp = c.chat.completions.create(
        model=_model(),
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": message},
        ],
        max_tokens=10,
        temperature=0,
    )
    label = resp.choices[0].message.content.strip().lower()
    try:
        return Intent(label)
    except ValueError:
        return Intent.GENERAL


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq()  # reads GROQ_API_KEY from env
    return _client


def _model() -> str:
    import os
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
