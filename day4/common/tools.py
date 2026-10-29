"""
NetNova helpdesk — the 4 tools AskNova can call.

They are plain Python functions. The agent calls them.
We also publish OpenAI-style schemas via `TOOL_SCHEMAS` for native tool calling,
and a dispatcher `run_tool(name, args)` for use inside the agent loop.

Everything reads from the small CSV + Markdown data in ../Data/.
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

# ---- data loading (one-time) ----

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "Data"
if not DATA.exists():
    # Allow callers that sit inside a Labs/<lab>/ folder to find it.
    DATA = HERE.parent.parent / "Data"


def _load_tickets() -> dict:
    out = {}
    with open(DATA / "tickets.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["ticket_id"]] = row
    return out


def _load_users() -> dict:
    out = {}
    with open(DATA / "users.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["user_id"]] = row
    return out


def _load_kb() -> list[dict]:
    out = []
    for p in sorted((DATA / "kb").glob("*.md")):
        txt = p.read_text(encoding="utf-8")
        out.append({"id": p.stem, "text": txt})
    return out


TICKETS = _load_tickets()
USERS = _load_users()
KB = _load_kb()


# ---- the 4 tools ----


def search_kb(query: str) -> str:
    """Keyword search over NetNova KB articles. Returns the best 1-2 matches as text."""
    q = (query or "").lower()
    if not q:
        return "No query."
    scored = []
    for a in KB:
        words = [w for w in re.split(r"[^a-z0-9]+", q) if len(w) > 2]
        s = sum(a["text"].lower().count(w) for w in words)
        if s:
            scored.append((s, a))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return "No matching KB article."
    hits = [a for _, a in scored[:2]]
    return "\n\n---\n\n".join(f"[{h['id']}]\n{h['text']}" for h in hits)


def get_ticket(ticket_id: str) -> str:
    """Reads one NetNova support ticket by id, e.g. TKT-0004."""
    t = TICKETS.get(ticket_id.upper().strip())
    if not t:
        return f"ERROR: ticket {ticket_id} not found."
    return (f"Ticket: {t['ticket_id']}\nUser: {t['user_id']} ({t['user_name']})\n"
            f"Category: {t['category']}\nPriority: {t['priority']}\n"
            f"Status: {t['status']}\nSummary: {t['summary']}")


def update_ticket(ticket_id: str, note: str) -> str:
    """Appends a note to a ticket. WRITE action."""
    t = TICKETS.get(ticket_id.upper().strip())
    if not t:
        return f"ERROR: ticket {ticket_id} not found."
    t["notes"] = (t.get("notes", "") + " | " + note).strip(" |")
    t["status"] = "In Progress"
    return f"OK: added note to {t['ticket_id']}; status now In Progress."


def reset_sim(user_id: str) -> str:
    """Resets a SIM / line reactivation. WRITE action (destructive — asks for approval in Lab 4)."""
    u = USERS.get(user_id.upper().strip())
    if not u:
        return f"ERROR: user {user_id} not found."
    return f"OK: SIM reactivated for {u['name']} ({u['user_id']}, {u['plan']}). User must restart device."


def check_outage(city: str) -> str:
    """Returns active outages for a city (added by participant in Solo 4 — pre-shipped here for the autograder)."""
    outages = {
        "Chennai": "Partial 4G outage in Velachery area since 11:30 IST. ETA 2h. Internal: ESC-901 raised.",
        "Mumbai": "No active outages.",
        "Delhi": "No active outages.",
        "Bangalore": "Scheduled maintenance on 5G tower cluster KOR-07, 02:00-04:00 IST tomorrow.",
        "Hyderabad": "No active outages.",
        "Kolkata": "No active outages.",
    }
    return outages.get(city.title(), "No active outages.")


# ---- registry (used by lab2+ and agent) ----

REGISTRY = {
    "search_kb": search_kb,
    "get_ticket": get_ticket,
    "update_ticket": update_ticket,
    "reset_sim": reset_sim,
    "check_outage": check_outage,
}


# ---- OpenAI-compatible schemas ----

def _schema(name, desc, props):
    return {"type": "function",
            "function": {"name": name, "description": desc,
                         "parameters": {"type": "object", "properties": props, "required": list(props.keys())}}}


TOOL_SCHEMAS = [
    _schema("search_kb", "Search NetNova knowledge base articles.",
            {"query": {"type": "string", "description": "Natural-language question"}}),
    _schema("get_ticket", "Read one NetNova support ticket.",
            {"ticket_id": {"type": "string", "description": "e.g. TKT-0004"}}),
    _schema("update_ticket", "Append a note to a ticket and move status to In Progress.",
            {"ticket_id": {"type": "string"}, "note": {"type": "string"}}),
    _schema("reset_sim", "Reactivate a user's SIM/line. Write action.",
            {"user_id": {"type": "string", "description": "e.g. EMP-1021"}}),
]


# Lab 4 solo adds the 5th schema — exposed here as well so the autograder can pre-check.
TOOL_SCHEMAS_WITH_OUTAGE = TOOL_SCHEMAS + [
    _schema("check_outage", "Return active outages in a NetNova city.",
            {"city": {"type": "string"}})
]


def run_tool(name: str, arguments: dict) -> str:
    """Dispatch a tool call. Returns the tool's output as a string (always a string)."""
    fn = REGISTRY.get(name)
    if not fn:
        return f"ERROR: unknown tool {name}."
    try:
        return str(fn(**(arguments or {})))
    except TypeError as e:
        return f"ERROR: bad arguments for {name}: {e}"
    except Exception as e:
        return f"ERROR: {name} crashed: {e}"


WRITE_TOOLS = {"update_ticket", "reset_sim"}


def is_write_tool(name: str) -> bool:
    return name in WRITE_TOOLS
