"""Tab 4: Solo Lab — field-ops incident INC-5102."""
import streamlit as st
from rbac import read_audit, load_registry
import mcp_client as mcp


SCENARIO = """
### Scenario — Supervisor on shift
**Time:** 14:30 IST. **Zone:** Chennai North.
**Incident INC-5102** is OPEN at P1.
Three cell towers (TWR-CHN-11, 12, 13) are DOWN. Customer call volume to care is spiking.
NOC lead has asked you — a **supervisor** — to:

1. Confirm the incident details and the state of each tower.
2. Decide the right action from the runbook library.
3. For customer `C-1002` (Priya Shah) who called in angry, apply a goodwill
   plan upgrade — but only if the registry says a supervisor can.

### Rules (enforced by the agent + registry)
- You are logged in as **supervisor** in Tab 2.
- Every action is written to `audit.jsonl`.
- `plan_change` is high-risk — it will pause for your explicit approval even though you are supervisor.
- An **engineer** cannot approve or execute `plan_change`. Try switching roles to see what happens.
"""

CHECKLIST = [
    ("ticket_lookup called", "ticket_lookup", "executed"),
    ("tower_status called at least once", "tower_status", "executed"),
    ("kb_search called for a runbook", "kb_search", "executed"),
    ("plan_change proposed", "plan_change", "proposed"),
    ("plan_change approved by human", "plan_change", "approved"),
    ("plan_change executed", "plan_change", "executed"),
]


def _pass(rows, tool, event):
    return any(r["tool"] == tool and r["event"] == event for r in rows)


def render():
    st.subheader("Solo lab — close incident INC-5102, inside the rules")
    st.markdown(SCENARIO)

    if not mcp.ping():
        st.error("Start the MCP server first:  `python mcp_server.py`")
        return

    st.divider()
    st.markdown("#### Your gates")
    rows = read_audit(500)
    passed = 0
    for label, tool, event in CHECKLIST:
        ok = _pass(rows, tool, event)
        if ok:
            passed += 1
            st.success(f"✅ {label}")
        else:
            st.error(f"❌ {label}")
    st.progress(passed / len(CHECKLIST))

    st.divider()
    st.markdown("#### Stretch (optional)")
    st.markdown("""
1. **Add a 5th tool** `tower_restart(tower_id)` — register as `high` risk, supervisor-only, requires approval.
   Add it in `mcp_server.py`, `registry.json`, and in the agent's system prompt in `llm.py`.
2. **Tighten over-permission** — `ticket_lookup` is allowed to engineers today. Decide if it should be viewer-safe or not. Edit `registry.json` and defend your choice.
3. **Prove the audit trail** closes the incident — download `audit.jsonl`, open it, point out which lines show (a) no unauthorized call, (b) approval before execution, (c) incident touched only once.
""")
    reg = load_registry()
    with st.expander("Registry (current)"):
        st.json(reg)
