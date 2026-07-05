"""ReAct agent orchestrator — at most MAX_AGENT_STEPS tool calls per turn."""
from __future__ import annotations

import json
import os
from typing import Any

from groq import BadRequestError, Groq

from src.agent.intent_classifier import Intent, classify
from src.tools.dispatcher import dispatch

MAX_STEPS = int(os.getenv("MAX_AGENT_STEPS", "6"))
_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_SYSTEM = """You are FinAdvisor, an educational financial guidance assistant.
You have access to tools for retrieval, market data, financial math, and user memory.
Think step by step. Use tools when you need factual data. Never give directives like
"you must buy X" — always frame answers as educational information.
Add a disclaimer to any response that could be construed as financial advice."""

_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_knowledge",
            "description": "Retrieve relevant passages from the financial knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_data",
            "description": "Fetch live price and basic fundamentals for a ticker symbol.",
            "parameters": {
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finance_math",
            "description": "Run deterministic financial calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["compound_interest", "amortization", "glide_path", "portfolio_risk"],
                    },
                    "params": {"type": "object"},
                },
                "required": ["operation", "params"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Retrieve the current user's saved financial profile.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def run(user_message: str, user_id: str = "default", history: list[dict] | None = None) -> str:
    client = Groq()
    intent = classify(user_message, client)

    messages: list[dict] = [{"role": "system", "content": _system_with_intent(intent)}]
    if history:
        messages.extend(history[-6:])  # last 3 turns for context
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_STEPS):
        try:
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                tools=_TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
                temperature=0.3,
            )
        except BadRequestError:
            # Model generated a malformed tool call (Llama XML-format bug).
            # Retry once without tools so the user gets a plain answer.
            fallback = client.chat.completions.create(
                model=_MODEL, messages=messages, temperature=0.3
            )
            return fallback.choices[0].message.content or ""

        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

        for tc in msg.tool_calls:
            args: dict[str, Any] = json.loads(tc.function.arguments)
            result = dispatch(tc.function.name, args, user_id=user_id)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    # Fallback: ask LLM to summarise with what it has
    messages.append({"role": "user", "content": "Please summarise your findings so far."})
    final = client.chat.completions.create(model=_MODEL, messages=messages, temperature=0.3)
    return final.choices[0].message.content or ""


def _system_with_intent(intent: Intent) -> str:
    hints = {
        Intent.QA: "Focus on clear educational explanations with KB citations.",
        Intent.PORTFOLIO: "Analyse holdings with live prices and concentration metrics.",
        Intent.PLANNING: "Project goal timelines with deterministic math tools.",
        Intent.GENERAL: "Be helpful and redirect financial questions appropriately.",
    }
    return f"{_SYSTEM}\n\nDetected intent: {intent.value}. {hints[intent]}"
