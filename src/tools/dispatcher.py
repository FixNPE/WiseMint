"""Routes tool calls from the agent to the appropriate module."""
from __future__ import annotations

from typing import Any


def dispatch(name: str, args: dict[str, Any], user_id: str = "default") -> Any:
    if name == "retrieve_knowledge":
        from src.kb.retrieval import retrieve
        return retrieve(args["query"])

    if name == "get_market_data":
        from src.market.alpha_vantage import get_quote
        return get_quote(args["ticker"])

    if name == "finance_math":
        from src.tools.finance_math import calculate
        return calculate(args["operation"], args.get("params", {}))

    if name == "get_user_profile":
        from src.memory.profile_db import get_profile
        return get_profile(user_id)

    return {"error": f"Unknown tool: {name}"}
