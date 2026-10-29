"""NetNova Telecom KB - small, carried from Day 3 with telecom-ops flavour."""

KB = [
    # Customer-facing plan docs
    {"id": "PLAN-201", "role_tag": "public", "title": "Postpaid Plan Standard",
     "text": "Postpaid Standard: 25 GB/month, 100 min free voice, Rs. 499/month. Rollover not allowed."},
    {"id": "PLAN-202", "role_tag": "public", "title": "Postpaid Plan Pro",
     "text": "Postpaid Pro: 75 GB/month, unlimited voice, Rs. 899/month. 5G included at no extra cost."},
    # Internal NOC runbooks
    {"id": "RUN-301", "role_tag": "internal", "title": "Tower Soft Restart Procedure",
     "text": "Soft restart a cell tower when KPIs degrade. Pre-check: active calls < 50. Procedure: issue RESTART command via EMS. Expected downtime 90s. Risk: HIGH if traffic > 1000 active calls."},
    {"id": "RUN-302", "role_tag": "internal", "title": "Mass Outage Escalation",
     "text": "If 3+ towers in one zone are down, raise P1 ticket and notify NOC lead. Customer comms sent only after root cause confirmed. Do not promise ETA before NOC confirms."},
    {"id": "RUN-303", "role_tag": "internal", "title": "Plan Change Approval",
     "text": "Any plan change on a customer account must be approved by a supervisor. Engineer can PROPOSE but not EXECUTE. Audit log entry mandatory."},
    # Incident examples
    {"id": "INC-5100", "role_tag": "internal", "title": "Historical: Chennai North outage, Aug 2026",
     "text": "4 towers down due to fiber cut. Resolution: NOC dispatched field team, towers restored in 4 hrs. Lesson: automate tower health polling."},
    # Public FAQ
    {"id": "FAQ-401", "role_tag": "public", "title": "Billing Dispute Window",
     "text": "Customers can raise a billing dispute within 30 days of bill date. After 30 days, dispute is rejected."},
    {"id": "FAQ-402", "role_tag": "public", "title": "5G Coverage",
     "text": "5G is available in Chennai, Bangalore, Hyderabad, Mumbai, Delhi NCR. Rolling out in Kolkata, Pune, Ahmedabad."},
]

CUSTOMERS = {
    "C-1001": {"name": "Rohan Mehta", "plan": "PLAN-201", "balance_due": 0, "city": "Chennai"},
    "C-1002": {"name": "Priya Shah",  "plan": "PLAN-202", "balance_due": 240, "city": "Chennai"},
    "C-1003": {"name": "Arjun Rao",   "plan": "PLAN-201", "balance_due": 0, "city": "Bangalore"},
}

TOWERS = {
    "TWR-CHN-11": {"zone": "Chennai North", "status": "DOWN", "active_calls": 0, "last_restart": "2026-10-25"},
    "TWR-CHN-12": {"zone": "Chennai North", "status": "DOWN", "active_calls": 0, "last_restart": "2026-10-25"},
    "TWR-CHN-13": {"zone": "Chennai North", "status": "DOWN", "active_calls": 0, "last_restart": "2026-10-25"},
    "TWR-CHN-21": {"zone": "Chennai South", "status": "UP",   "active_calls": 1240, "last_restart": "2026-09-15"},
    "TWR-BLR-11": {"zone": "Bangalore East","status": "UP",   "active_calls": 870, "last_restart": "2026-10-01"},
}

INCIDENTS = {
    "INC-5102": {"zone": "Chennai North", "description": "3 towers down (TWR-CHN-11,12,13). Customer calls spiking.", "status": "OPEN", "severity": "P1"},
    "INC-5103": {"zone": "Bangalore East", "description": "Intermittent 5G drop reported by 12 customers.", "status": "OPEN", "severity": "P3"},
}


def search_kb(query: str, role: str = "viewer"):
    """Simple keyword search. Internal docs filtered out for 'viewer'."""
    q = query.lower().strip()
    out = []
    for a in KB:
        if role == "viewer" and a["role_tag"] == "internal":
            continue
        hay = (a["title"] + " " + a["text"]).lower()
        score = sum(1 for w in q.split() if w in hay)
        if score > 0:
            out.append({"id": a["id"], "title": a["title"], "text": a["text"], "score": score})
    out.sort(key=lambda x: -x["score"])
    return out[:3]
