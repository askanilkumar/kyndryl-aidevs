"""Tab 1: MCP server inspector."""
import streamlit as st
import mcp_client as mcp


def render():
    st.subheader("MCP server — the one wire protocol")
    st.caption("Start it in Terminal A:  `python mcp_server.py`  (keep it running)")

    up = mcp.ping()
    if up:
        st.success("MCP server is UP at http://127.0.0.1:8765")
    else:
        st.error("MCP server is DOWN. Open a terminal and run: `python mcp_server.py`")
        return

    st.markdown("#### Tools the server exposes (`/tools/list`)")
    try:
        tools = mcp.list_tools()
    except Exception as e:
        st.error(f"Could not read tools: {e}")
        return
    st.dataframe(
        [{"name": t["name"], "risk": t["risk"], "description": t["description"]} for t in tools],
        use_container_width=True, hide_index=True,
    )

    st.markdown("#### Call a tool by hand (`/tools/call`)")
    names = [t["name"] for t in tools]
    tool = st.selectbox("Tool", names, key="mcp_hand_tool")
    arg_map = {
        "kb_search": {"query": "soft restart procedure", "role": "engineer"},
        "ticket_lookup": {"incident_id": "INC-5102"},
        "tower_status": {"tower_id": "TWR-CHN-11"},
        "plan_change": {"customer_id": "C-1002", "new_plan_id": "PLAN-202"},
    }
    import json as _j
    args_txt = st.text_area("Args (JSON)", value=_j.dumps(arg_map.get(tool, {}), indent=2),
                            key=f"mcp_hand_args_{tool}", height=120)
    if st.button("Call", key="mcp_hand_call"):
        try:
            args = _j.loads(args_txt)
            r = mcp.call_tool(tool, args)
            st.json(r)
        except Exception as e:
            st.error(e)

    st.info("Point: this app does not import kb.py. It only knows the MCP endpoints. "
            "Swap the server for a real one, nothing else changes.")
