"""Lab 4 - LLMOps / AgentOps: a prompt is code. Change it -> run evals -> release only if the gate is open -> roll back if needed.
The active prompt version lives in releases.json (the app reads it)."""
import json
import time

from . import config
from .evals import run_evals


def load() -> dict:
    try:
        return json.loads(config.RELEASES_FILE.read_text())
    except Exception:
        return {"active": "v1", "history": [{"version": "v1", "ts": "day 4", "pass_rate": None, "status": "approved"}]}


def save(state: dict):
    config.RELEASES_FILE.write_text(json.dumps(state, indent=2))


def release(version: str, *, client=None, model=config.DEFAULT_MODEL) -> dict:
    report = run_evals(client=client, model=model, prompt_version=version)
    state = load()
    status = "approved" if report["gate_open"] else "rejected"
    state["history"].append({"version": version, "ts": time.strftime("%Y-%m-%d %H:%M"),
                             "pass_rate": round(report["pass_rate"], 2), "safety_ok": report["safety_ok"],
                             "status": status})
    if status == "approved":
        state["active"] = version
    save(state)
    return {"status": status, "active": state["active"], "report": report}


def rollback() -> dict:
    state = load()
    approved = [h["version"] for h in state["history"] if h["status"] == "approved"]
    current = state["active"]
    earlier = [v for v in approved if v != current]
    if earlier:
        state["active"] = earlier[-1]
        state["history"].append({"version": state["active"], "ts": time.strftime("%Y-%m-%d %H:%M"),
                                 "pass_rate": None, "status": f"rollback from {current}"})
        save(state)
    return {"active": state["active"], "from": current}
