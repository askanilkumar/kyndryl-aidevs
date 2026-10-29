"""Tab 0: Journey. Big picture + what each other tab shows."""
import streamlit as st


def render():
    st.subheader("Day 4 journey — governed agent, end to end")
    st.markdown("""
We built an agent on Day 3. It could call Python functions directly. That is fine for a demo.
In production you want:

1. **MCP** — a standard way for an agent to talk to many tool servers.
2. **Registry** — one place that lists every tool, its risk, who may call it.
3. **RBAC** — the agent only sees tools its role is allowed to use.
4. **HITL** — a human approves anything risky before it happens.
5. **Audit** — every proposal, denial, approval, execution is logged.

Walk the tabs left to right:
""")
    st.markdown("""
| Tab | What it is | What you do |
|---|---|---|
| **1 · MCP Server** | The server that exposes 4 tools over HTTP | Ping it, list tools, call one by hand |
| **2 · Agent + Registry** | The LangGraph agent that uses MCP | Pick a role, run a prompt, see RBAC in action |
| **3 · Approvals + Audit** | Pending approvals + append-only audit log | Approve / reject risky actions, read the trail |
| **4 · Solo Lab** | Field-ops incident INC-5102 | Solve it inside the rules |
""")
    st.info("Terminal A keeps `python mcp_server.py` running. This Streamlit app is Terminal B. "
            "That is the whole architecture.")

    st.divider()
    st.markdown("### Four habits we keep carrying")
    c1, c2, c3, c4 = st.columns(4)
    c1.success("**Security**\nLeast privilege by default")
    c2.info("**FinOps**\nEvery tool call is counted")
    c3.warning("**Guardrails**\nHigh risk ⇒ human in loop")
    c4.success("**Evals**\nAudit is the eval source")
