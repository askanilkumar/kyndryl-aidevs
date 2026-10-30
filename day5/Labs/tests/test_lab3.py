"""Lab 3 check:  python -m pytest tests/test_lab3.py -q"""
from asknova import evals, monitor


def test_eval_set_has_10_cases():
    assert len(evals.CASES) >= 10, "Add 2 cases in asknova/evals.py (TODO Lab 3)"
    assert sum(evals.is_safety(c) for c in evals.CASES) >= 6, "One of your new cases must be an attack with 'block': True"
    assert len({c["id"] for c in evals.CASES}) == len(evals.CASES), "Case ids must be unique"


def test_gate_is_open_with_v1():
    rep = evals.run_evals(prompt_version="v1")
    assert rep["gate_open"], [r for r in rep["rows"] if not r["passed"]]


def test_monitor_summary():
    rows = [{"latency_ms": 100, "cost_usd": 0.001, "tokens_in": 10, "tokens_out": 5, "blocked": False, "error": ""},
            {"latency_ms": 9000, "cost_usd": 0.001, "tokens_in": 10, "tokens_out": 5, "blocked": True, "error": "x"}]
    s = monitor.summary(rows)
    assert s["requests"] == 2 and "error_rate" in s["alerts"]
