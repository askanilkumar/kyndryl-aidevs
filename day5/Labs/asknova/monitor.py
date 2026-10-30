"""Lab 3 - Monitoring. Every request writes one line to logs/requests.jsonl.
The Monitor tab reads this file and shows the numbers an AgentOps team watches."""
import json
import time

from . import config

# Alert rules (simple thresholds). Change them and watch the Monitor tab turn red/green.
ALERTS = {"error_rate": 0.10, "p95_latency_ms": 8000, "block_rate": 0.50, "cost_usd": 1.00}


def log_request(*, user, question, res, model, prompt_version):
    config.LOG_FILE.parent.mkdir(exist_ok=True)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "user": user, "question": question[:200],
           "model": model, "prompt": prompt_version, "latency_ms": res.latency_ms,
           "tokens_in": res.tokens_in, "tokens_out": res.tokens_out, "cost_usd": round(res.cost, 6),
           "blocked": res.blocked, "guards": res.guard_hits, "tools": res.tools_used,
           "needs_approval": bool(res.needs_approval), "error": res.error}
    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def read_log() -> list:
    if not config.LOG_FILE.exists():
        return []
    return [json.loads(line) for line in config.LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def summary(rows: list) -> dict:
    if not rows:
        return {"requests": 0}
    lat = sorted(r["latency_ms"] for r in rows)
    n = len(rows)
    s = {"requests": n,
         "avg_latency_ms": int(sum(lat) / n),
         "p95_latency_ms": lat[min(n - 1, int(0.95 * n))],
         "cost_usd": round(sum(r["cost_usd"] for r in rows), 4),
         "tokens": sum(r["tokens_in"] + r["tokens_out"] for r in rows),
         "block_rate": round(sum(r["blocked"] for r in rows) / n, 2),
         "error_rate": round(sum(bool(r["error"]) for r in rows) / n, 2)}
    s["alerts"] = [k for k, limit in ALERTS.items() if s.get(k, 0) > limit]
    return s
