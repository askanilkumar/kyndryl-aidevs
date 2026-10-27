"""Run:  python -m pytest tests -v     (from the lab folder). Aim for 3 passed."""
import json, os, re, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from rag import evals
from rag.kb import load_kb


def test_challenge_1():
    qs = evals.MY_QUESTIONS
    assert len(qs) >= 2, "Add at least 2 questions to MY_QUESTIONS in rag/evals.py"
    docs = {d.id: d for d in load_kb() if d.status == "current"}
    for q in qs:
        for k in ("q", "doc", "key", "role"):
            assert k in q, f"each question needs q, role, doc, key - missing {k}"
        assert q["doc"] in docs, f"doc '{q['doc']}' is not a document id in kb/"
        assert q["key"].lower() in docs[q["doc"]].body.lower(), f"key phrase '{q['key']}' is not inside {q['doc']}"
        assert q["role"] in docs[q["doc"]].roles, f"role '{q['role']}' cannot see {q['doc']}"


def test_challenge_2():
    runs = json.load(open(evals.EVAL_FILE)) if os.path.exists(evals.EVAL_FILE) else {}
    for name in ("Baseline", "+ Metadata filter", "+ Section chunks + hybrid", "Full pipeline"):
        assert name in runs, f"Run the '{name}' preset in the Evals tab"
    rep = open(os.path.join(HERE, "submission", "lab4_report.md"), encoding="utf-8").read()
    sec = rep.split("## 2.")[0]
    assert "TODO" not in sec, "Fill in section 1 of submission/lab4_report.md (replace every TODO)"


def test_challenge_3():
    rep = open(os.path.join(HERE, "submission", "lab4_report.md"), encoding="utf-8").read()
    assert "## 2." in rep
    sec = rep.split("## 2.")[1]
    assert "TODO" not in sec, "Fill in section 2 of submission/lab4_report.md (replace every TODO)"
