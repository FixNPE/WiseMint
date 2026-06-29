"""Deterministic financial math tools — no LLM, no network."""
from __future__ import annotations

import math
from typing import Any


def calculate(operation: str, params: dict[str, Any]) -> dict[str, Any]:
    ops = {
        "compound_interest": _compound_interest,
        "amortization": _amortization,
        "glide_path": _glide_path,
        "portfolio_risk": _portfolio_risk,
    }
    fn = ops.get(operation)
    if fn is None:
        return {"error": f"Unknown operation: {operation}"}
    try:
        return fn(params)
    except (KeyError, ZeroDivisionError, ValueError) as e:
        return {"error": str(e)}


def _compound_interest(p: dict) -> dict:
    """A = P(1 + r/n)^(nt)"""
    principal = float(p["principal"])
    rate = float(p["annual_rate"])       # e.g. 0.07 for 7%
    n = int(p.get("compounds_per_year", 12))
    t = float(p["years"])
    amount = principal * (1 + rate / n) ** (n * t)
    return {
        "future_value": round(amount, 2),
        "interest_earned": round(amount - principal, 2),
        "inputs": p,
    }


def _amortization(p: dict) -> dict:
    """Monthly payment for a fixed-rate loan."""
    principal = float(p["principal"])
    annual_rate = float(p["annual_rate"])
    months = int(p["term_months"])
    r = annual_rate / 12
    if r == 0:
        payment = principal / months
    else:
        payment = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total_paid = payment * months
    return {
        "monthly_payment": round(payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_paid - principal, 2),
    }


def _glide_path(p: dict) -> dict:
    """Target-date equity allocation: 110 - age rule, projected to retirement."""
    current_age = int(p["current_age"])
    retirement_age = int(p.get("retirement_age", 65))
    monthly_contribution = float(p.get("monthly_contribution", 0))
    current_savings = float(p.get("current_savings", 0))
    annual_return = float(p.get("annual_return", 0.07))

    years = retirement_age - current_age
    months = years * 12
    r = annual_return / 12

    fv_savings = current_savings * (1 + r) ** months
    if r == 0:
        fv_contributions = monthly_contribution * months
    else:
        fv_contributions = monthly_contribution * ((1 + r) ** months - 1) / r

    equity_pct = max(0, min(100, 110 - retirement_age))
    return {
        "years_to_retirement": years,
        "projected_balance": round(fv_savings + fv_contributions, 2),
        "recommended_equity_pct_at_retirement": equity_pct,
        "recommended_bond_pct_at_retirement": 100 - equity_pct,
    }


def _portfolio_risk(p: dict) -> dict:
    """Basic concentration and diversity metrics for a holdings dict."""
    holdings: dict[str, float] = p["holdings"]  # {"AAPL": 0.6, "MSFT": 0.4}
    weights = list(holdings.values())
    total = sum(weights)
    norm = [w / total for w in weights]

    hhi = sum(w ** 2 for w in norm)                     # Herfindahl index
    largest = max(norm)
    top_ticker = list(holdings.keys())[norm.index(largest)]

    risk_level = "low" if hhi < 0.15 else "medium" if hhi < 0.30 else "high"
    return {
        "herfindahl_index": round(hhi, 4),
        "concentration_risk": risk_level,
        "largest_position": {"ticker": top_ticker, "weight": round(largest, 4)},
        "num_holdings": len(holdings),
    }
