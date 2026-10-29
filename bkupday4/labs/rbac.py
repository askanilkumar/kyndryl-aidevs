"""RBAC + audit log. Dead simple, deliberately readable."""
import json, time
from pathlib import Path

REGISTRY = Path(__file__).with_name("registry.json")
AUDIT = Path(__file__).with_name("audit.jsonl")


def load_registry():
    return json.loads(REGISTRY.read_text())


def can_call(role: str, tool: str) -> tuple[bool, str]:
    reg = load_registry()
    t = reg["tools"].get(tool)
    if not t:
        return False, f"tool '{tool}' not in registry"
    if role not in t["allowed_roles"]:
        return False, f"role '{role}' not allowed on '{tool}' (needs one of {t['allowed_roles']})"
    return True, "ok"


def requires_approval(tool: str) -> bool:
    reg = load_registry()
    return reg["tools"].get(tool, {}).get("requires_approval", False)


def audit(event: str, role: str, tool: str, args: dict, outcome: str, detail: str = ""):
    row = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,       # proposed | denied | approved | rejected | executed | error
        "role": role,
        "tool": tool,
        "args": args,
        "outcome": outcome,   # allow | block | ok | fail
        "detail": detail,
    }
    with AUDIT.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def read_audit(limit: int = 100):
    if not AUDIT.exists():
        return []
    lines = AUDIT.read_text().strip().splitlines()
    return [json.loads(x) for x in lines[-limit:]]


def clear_audit():
    if AUDIT.exists():
        AUDIT.unlink()
