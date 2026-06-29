"""Unit tests for deterministic finance math — no network, no LLM."""
import pytest
from src.tools.finance_math import calculate


def test_compound_interest_basic():
    result = calculate("compound_interest", {"principal": 1000, "annual_rate": 0.10, "years": 1})
    assert abs(result["future_value"] - 1104.71) < 0.10


def test_compound_interest_zero_rate():
    result = calculate("compound_interest", {"principal": 500, "annual_rate": 0.0, "years": 5})
    assert result["future_value"] == 500.0


def test_amortization_monthly_payment():
    result = calculate("amortization", {"principal": 200000, "annual_rate": 0.06, "term_months": 360})
    assert abs(result["monthly_payment"] - 1199.10) < 1.0


def test_glide_path_returns_equity_pct():
    result = calculate("glide_path", {"current_age": 30, "retirement_age": 65, "monthly_contribution": 500})
    assert "recommended_equity_pct_at_retirement" in result
    assert 0 <= result["recommended_equity_pct_at_retirement"] <= 100


def test_portfolio_risk_high_concentration():
    result = calculate("portfolio_risk", {"holdings": {"AAPL": 0.9, "MSFT": 0.1}})
    assert result["concentration_risk"] == "high"


def test_portfolio_risk_low_concentration():
    holdings = {f"T{i}": 0.1 for i in range(10)}
    result = calculate("portfolio_risk", {"holdings": holdings})
    assert result["concentration_risk"] == "low"


def test_unknown_operation():
    result = calculate("unknown_op", {})
    assert "error" in result
