"""The 4 AskNova tools (same as Day 4). Read tools run freely, write tools need approval."""
import json
from .data import CUSTOMERS, TICKETS, KB


def search_kb(query: str) -> str:
    words = [w for w in query.lower().split() if len(w) > 2]
    hits = []
    for doc in KB:
        text = (doc["title"] + " " + doc["text"]).lower()
        score = sum(1 for w in words if w in text)
        if score:
            hits.append((score, doc))
    hits.sort(key=lambda x: -x[0])
    if not hits:
        return "No KB article found."
    return "\n".join(f"[{d['id']}] {d['title']}: {d['text']}" for _, d in hits[:2])


def get_ticket(ticket_id: str) -> str:
    t = TICKETS.get(ticket_id.upper())
    if not t:
        return f"Ticket {ticket_id} not found."
    return json.dumps({"ticket": ticket_id.upper(), **t})


def update_ticket(ticket_id: str, status: str) -> str:
    t = TICKETS.get(ticket_id.upper())
    if not t:
        return f"Ticket {ticket_id} not found."
    t["status"] = status
    return f"Ticket {ticket_id.upper()} status set to {status}."


def reset_sim(customer_id: str) -> str:
    c = CUSTOMERS.get(customer_id.upper())
    if not c:
        return f"Customer {customer_id} not found."
    c["sim"] = "active"
    return f"SIM reset started for {customer_id.upper()}. Takes about 10 minutes."


TOOLS = {"search_kb": search_kb, "get_ticket": get_ticket,
         "update_ticket": update_ticket, "reset_sim": reset_sim}
WRITE_TOOLS = {"update_ticket", "reset_sim"}     # these change data -> need approval
ALLOWED_TOOLS = set(TOOLS)                      # guardrail: the agent may call ONLY these


def _spec(name, desc, props):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": {k: {"type": "string", "description": v} for k, v in props.items()},
                       "required": list(props)}}}


TOOL_SPECS = [
    _spec("search_kb", "Search the NetNova help articles.", {"query": "what to search for"}),
    _spec("get_ticket", "Read one support ticket.", {"ticket_id": "like INC-5001"}),
    _spec("update_ticket", "Change a ticket status (WRITE action).", {"ticket_id": "like INC-5001", "status": "open or resolved"}),
    _spec("reset_sim", "Reset a customer's SIM (WRITE action).", {"customer_id": "like C-101"}),
]


def call_tool(name: str, args: dict) -> str:
    try:
        return TOOLS[name](**args)
    except Exception as e:  # a bad argument should not crash the agent
        return f"Tool error: {e}"
