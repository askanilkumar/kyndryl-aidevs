"""
NetNova Field Ops MCP server.

MCP (Model Context Protocol) lets an agent talk to many tool servers over
ONE wire protocol. Real MCP supports stdio and HTTP transports. We use
HTTP so you can curl it and see what is happening.

Run:  python mcp_server.py
Then open http://127.0.0.1:8765/tools/list  in a browser.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uvicorn
import json
from pathlib import Path

from kb import search_kb, CUSTOMERS, TOWERS, INCIDENTS

app = FastAPI(title="NetNova Field Ops MCP server")

STATE_FILE = Path(__file__).with_name("mcp_state.json")


def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"towers": TOWERS, "customers": CUSTOMERS, "incidents": INCIDENTS}


def _save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2))


# ---------------- Tool definitions (what the agent sees) ----------------
TOOLS = [
    {
        "name": "kb_search",
        "description": "Search the NetNova knowledge base (plans, FAQs, NOC runbooks). Returns up to 3 articles.",
        "risk": "low",
        "args": {"query": "string", "role": "string (viewer|engineer|supervisor)"},
    },
    {
        "name": "ticket_lookup",
        "description": "Look up an incident ticket by id (e.g. INC-5102).",
        "risk": "low",
        "args": {"incident_id": "string"},
    },
    {
        "name": "tower_status",
        "description": "Read current status of a tower by id (e.g. TWR-CHN-11).",
        "risk": "low",
        "args": {"tower_id": "string"},
    },
    {
        "name": "plan_change",
        "description": "Change the plan of a customer. Supervisor-only. REQUIRES APPROVAL.",
        "risk": "high",
        "args": {"customer_id": "string", "new_plan_id": "string"},
    },
]


# ---------------- MCP-style endpoints ----------------
class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = {}


@app.get("/tools/list")
def tools_list():
    return {"tools": TOOLS}


@app.post("/tools/call")
def tools_call(call: ToolCall):
    name = call.name
    args = call.args or {}

    if name == "kb_search":
        q = args.get("query", "")
        role = args.get("role", "viewer")
        return {"ok": True, "result": search_kb(q, role)}

    if name == "ticket_lookup":
        s = _load_state()
        inc = s["incidents"].get(args.get("incident_id", ""))
        if not inc:
            return {"ok": False, "error": "incident not found"}
        return {"ok": True, "result": inc}

    if name == "tower_status":
        s = _load_state()
        tw = s["towers"].get(args.get("tower_id", ""))
        if not tw:
            return {"ok": False, "error": "tower not found"}
        return {"ok": True, "result": tw}

    if name == "plan_change":
        s = _load_state()
        cid = args.get("customer_id", "")
        new_plan = args.get("new_plan_id", "")
        if cid not in s["customers"]:
            return {"ok": False, "error": "customer not found"}
        old = s["customers"][cid]["plan"]
        s["customers"][cid]["plan"] = new_plan
        _save_state(s)
        return {"ok": True, "result": {"customer": cid, "old_plan": old, "new_plan": new_plan}}

    return {"ok": False, "error": f"unknown tool: {name}"}


@app.get("/")
def home():
    return {"service": "NetNova MCP server", "tools": len(TOOLS),
            "try": ["/tools/list", "/tools/call (POST)"]}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
