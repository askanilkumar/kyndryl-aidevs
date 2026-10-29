"""
NetNova Field Ops Control Tower — ONE Streamlit app for all of Day 4.

Prereq (Terminal A):   python mcp_server.py
Run (Terminal B):      streamlit run app.py
"""
import streamlit as st
from tabs import tab_journey, tab_mcp, tab_agent, tab_approvals, tab_solo

st.set_page_config(page_title="NetNova Field Ops Control Tower",
                   page_icon="📡", layout="wide")

# --------------- sidebar: gateway settings (NEVER stored in files) ---------------
with st.sidebar:
    st.markdown("### Gateway (optional)")
    st.caption("Leave blank to run offline (deterministic stand-in).")
    st.session_state.setdefault("gw_url", "")
    st.session_state.setdefault("gw_key", "")
    st.session_state.setdefault("gw_model", "kimi-k2.7-code")
    st.session_state["gw_url"] = st.text_input("GATEWAY_BASE_URL (ends with /v1)", st.session_state["gw_url"])
    st.session_state["gw_key"] = st.text_input("GATEWAY_KEY", st.session_state["gw_key"], type="password")
    st.session_state["gw_model"] = st.text_input("Model", st.session_state["gw_model"])
    mode = "ONLINE (gateway)" if st.session_state["gw_url"] and st.session_state["gw_key"] else "OFFLINE (stand-in)"
    st.info(f"Mode: **{mode}**")

    st.divider()
    st.markdown("### Habits on this app")
    st.markdown("- 🔒 Least privilege (registry)\n- 💰 Every call counted (audit)\n- 🚦 High risk ⇒ HITL\n- 📊 Audit = eval source")

# --------------- tabs ---------------
st.title("📡 NetNova Field Ops Control Tower")
st.caption("Day 4 · MCP · Agent Registry · RBAC · HITL · Audit")

t0, t1, t2, t3, t4 = st.tabs(["0 · Journey", "1 · MCP Server", "2 · Agent + Registry",
                              "3 · Approvals + Audit", "4 · Solo Lab"])
with t0: tab_journey.render()
with t1: tab_mcp.render()
with t2: tab_agent.render()
with t3: tab_approvals.render()
with t4: tab_solo.render()
