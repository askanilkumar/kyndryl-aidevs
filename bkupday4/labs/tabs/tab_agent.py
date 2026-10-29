"""Tab 2: Agent + Registry. Pick role, run prompt, watch RBAC."""
import streamlit as st
import json
from pathlib import Path

from agent import S, run_agent
from rbac import load_registry
import mcp_client as mcp


def render():
    st.subheader("Agent + Registry — RBAC in action")

    if not mcp.ping():
        st.error("MCP server is down. Start it in Terminal A: `python mcp_server.py`")
        return

    reg = load_registry()

    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### Registry (`registry.json`)")
        rows = [{"tool": n, **t} for n, t in reg["tools"].items()]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("Edit `registry.json` on disk and reload — this is your policy file.")

    with right:
        st.markdown("#### Run the agent")
        role = st.selectbox("You are logged in as", ["viewer", "engineer", "supervisor"],
                            index=1, key="agent_role")
        prompt = st.text_area("What should the agent do?",
                              value="Look up incident INC-5102 and check tower TWR-CHN-11.",
                              key="agent_prompt", height=100)
        presets = {
            "incident + tower (engineer-safe)": "Look up incident INC-5102 and check tower TWR-CHN-11.",
            "escalation runbook": "What is the mass outage escalation procedure?",
            "high-risk plan change": "Change customer C-1002 to PLAN-202 as goodwill compensation.",
            "viewer tries engineer tool": "Look up incident INC-5102.",
        }
        pick = st.selectbox("Or try a preset", list(presets), key="agent_preset")
        if st.button("Use preset", key="agent_use_preset"):
            st.session_state["agent_prompt"] = presets[pick]
            st.rerun()

        if st.button("Run agent", type="primary", key="agent_run"):
            state = S(
                user_prompt=prompt, role=role,
                gw_url=st.session_state.get("gw_url") or None,
                gw_key=st.session_state.get("gw_key") or None,
                model=st.session_state.get("gw_model") or "kimi-k2.7-code",
            )
            with st.spinner("Agent working..."):
                out = run_agent(state)
            st.session_state["agent_state"] = out
            st.rerun()

    out = st.session_state.get("agent_state")
    if not out:
        return
    st.divider()
    st.markdown("#### Agent trace")
    if out.pending_approval:
        st.warning(f"⏸ PAUSED for approval: `{out.pending_approval['tool']}` "
                   f"with args `{out.pending_approval['args']}` — go to the Approvals tab.")
    for i, h in enumerate(out.history, 1):
        with st.expander(f"Step {i}: {h['tool']}({h['args']})"):
            st.write(h["result"])
    if out.final:
        st.success(f"Final: {out.final}")
