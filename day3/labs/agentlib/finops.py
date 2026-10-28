"""FinOps habits: every call has a price, every run has a budget.

Prices in config.PRICES are EXAMPLES (USD per 1M tokens). Replace with your gateway prices.
"""
from . import config


def estimate_tokens(text: str) -> int:
    """Rough rule: 1 token ~ 4 characters. Good enough to see the shape of the bill."""
    return max(1, len(text or "") // 4)


def price_of(model: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = config.PRICES.get(model, config.PRICES["chat-llm"])
    return (tokens_in * pin + tokens_out * pout) / 1_000_000


class CostMeter:
    """Adds up tokens and dollars for one question / one run."""

    def __init__(self, budget_usd=None):
        self.budget = config.BUDGET_USD if budget_usd is None else budget_usd
        self.tokens_in = 0
        self.tokens_out = 0
        self.usd = 0.0
        self.calls = 0

    def add(self, model, tokens_in, tokens_out):
        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        self.usd += price_of(model, tokens_in, tokens_out)
        self.calls += 1

    @property
    def over_budget(self):
        return self.usd >= self.budget

    def as_dict(self):
        return {"calls": self.calls, "tokens_in": self.tokens_in, "tokens_out": self.tokens_out,
                "usd": round(self.usd, 6), "budget": self.budget}


def pick_model(question: str) -> str:
    """Routing idea from Day 1: simple FAQ -> cheap model, multi-step work -> bigger model."""
    q = question.lower()
    multi = any(w in q for w in ("upgrade", "change", "ticket", "tkt-", "and then", "compare"))
    return "chat-llm" if multi else "local-small"


def what_if_routed(rows):
    """rows: [{'question','model','usd','tokens_in','tokens_out'}] -> (actual, routed, saving_pct)"""
    actual = sum(r["usd"] for r in rows)
    routed = sum(price_of(pick_model(r["question"]), r["tokens_in"], r["tokens_out"]) for r in rows)
    saving = 0 if actual == 0 else round(100 * (actual - routed) / actual)
    return actual, routed, saving
