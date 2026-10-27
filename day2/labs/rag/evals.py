"""The test set and the scoring code. LAB 4, CHALLENGE 1: add 2 questions of your own to MY_QUESTIONS."""
import json, os, time
from .config import EVAL_FILE
from .pipeline import run, PRESETS, REFUSAL
from . import llm

# q = question, role = who asks, doc = the document that holds the answer (None = not in the KB), key = phrase the answer must contain
BASE_QUESTIONS = [
    dict(q="How much data does Postpaid Max include?", role="postpaid", doc="PLAN-101", key="100 GB", tag="stale"),
    dict(q="Does the prepaid Smart 299 plan include 5G?", role="prepaid", doc="PLAN-102", key="349", tag="basic"),
    dict(q="How much is the 10-day international roaming pack?", role="prepaid", doc="ROAM-202", key="3,499", tag="audience"),
    dict(q="How much is the 10-day international roaming pack?", role="postpaid", doc="ROAM-201", key="2,999", tag="audience"),
    dict(q="What does error code E-4107 mean?", role="prepaid", doc="BILL-302", key="timed out", tag="exact"),
    dict(q="How long is my UPC code valid for porting out?", role="postpaid", doc="PORT-601", key="4 days", tag="basic"),
    dict(q="After a SIM swap, how long are SMS blocked?", role="prepaid", doc="SIM-402", key="24 hours", tag="basic"),
    dict(q="How long do I have to dispute a bill?", role="postpaid", doc="BILL-301", key="60 days", tag="basic"),
    dict(q="Which cafeteria serves vegan food on Fridays?", role="postpaid", doc=None, key="", tag="unanswerable"),
    dict(q="What is the extension of the Level 2 Transport on-call?", role="postpaid", doc=None, key="", tag="leak"),
    dict(q="What is the extension of the Level 2 Transport on-call?", role="noc", doc="ESC-901", key="4101", tag="basic"),
    dict(q="Who owns the fibre link that caused the Chennai North outage INC-4471?", role="noc", doc=["INC-4471", "ASSET-801"], key="TeraLink", tag="multihop"),
    dict(q="How fast must the NOC respond to a P1 incident?", role="noc", doc="SLA-902", key="15 minutes", tag="basic"),
]

# ------------------------------------------------------------------ TODO-1: add your 2 questions here
MY_QUESTIONS = [
    # dict(q="...", role="postpaid", doc="PLAN-102", key="a phrase that is inside that article"),
    # dict(q="...", role="noc", doc="RB-202", key="a phrase that is inside that article"),
]


def _as_list(x):
    return [] if x is None else (x if isinstance(x, list) else [x])


def score_one(kb, item, cfg, judge=False):
    r = run(kb, item["q"], cfg, item["role"])
    want = _as_list(item.get("doc"))
    docs_current = {s["doc_id"] for s in r.sources if s["status"] == "current"}
    got = {s["doc_id"] for s in r.sources}
    out = dict(q=item["q"], role=item["role"], tag=item.get("tag", "mine"), answer=r.answer, seconds=r.seconds, usd=r.usd)
    out["retrieved"] = sorted(got)
    out["stale"] = any(s["status"] != "current" for s in r.sources)
    out["leak"] = any(item["role"] not in s["roles"] for s in r.sources)
    if want:
        out["hit"] = all(d in docs_current for d in want)
        out["correct"] = item["key"].lower() in r.answer.lower() and not r.refused
        out["injected"] = False
    else:
        out["hit"] = None
        out["correct"] = r.refused           # for questions with no answer, refusing is correct
    if judge and want:
        out["judge"] = llm.judge(item["q"], r.answer, item["key"])
    return out


def run_eval(kb, cfg, name, questions=None, judge=False, save=True):
    qs = questions or (BASE_QUESTIONS + MY_QUESTIONS)
    rows = [score_one(kb, q, cfg, judge) for q in qs]
    hits = [r["hit"] for r in rows if r["hit"] is not None]
    summary = dict(
        preset=name, n=len(rows), mode=llm.mode_name(), time=time.strftime("%Y-%m-%d %H:%M"),
        retrieval_hit=round(sum(hits) / max(1, len(hits)), 2),
        answer_correct=round(sum(r["correct"] for r in rows) / len(rows), 2),
        stale_rate=round(sum(r["stale"] for r in rows) / len(rows), 2),
        leak_rate=round(sum(r["leak"] for r in rows) / len(rows), 2),
        avg_seconds=round(sum(r["seconds"] for r in rows) / len(rows), 2),
        total_usd=round(sum(r["usd"] for r in rows), 5),
        judge_avg=round(sum(r["judge"] for r in rows if "judge" in r) / max(1, sum(1 for r in rows if "judge" in r)), 2) if judge else None,
        rows=rows)
    if save:
        os.makedirs(os.path.dirname(EVAL_FILE), exist_ok=True)
        allruns = json.load(open(EVAL_FILE)) if os.path.exists(EVAL_FILE) else {}
        allruns[name] = summary
        json.dump(allruns, open(EVAL_FILE, "w"), indent=1)
    return summary


def load_runs():
    return json.load(open(EVAL_FILE)) if os.path.exists(EVAL_FILE) else {}
