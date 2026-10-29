"""Tab 3: Approvals + audit log."""
import streamlit as st
from agent import resume_after_approval
from rbac import read_audit, clear_audit


def render():
    st.subheader("Approvals + audit — the human in the loop")

    out = st.session_state.get("agent_state")

    st.markdown("#### Pending approval")
    if out and out.pending_approval:
        p = out.pending_approval
        st.warning(f"**{p['tool']}** is high-risk and needs a human. "
                   f"Role on the request: `{out.role}`")
        st.code(f"args = {p['args']}", language="python")
        c1, c2 = st.columns(2)
        if c1.button("Approve ✅", type="primary", key="appr_yes"):
            new = resume_after_approval(out, True)
            st.session_state["agent_state"] = new
            st.rerun()
        if c2.button("Reject ❌", key="appr_no"):
            new = resume_after_approval(out, False)
            st.session_state["agent_state"] = new
            st.rerun()
    else:
        st.info("Nothing waiting. Run the agent on a high-risk action to see this fire.")

    st.divider()
    st.markdown("#### Audit log  (`audit.jsonl`)")
    rows = read_audit(200)
    if not rows:
        st.caption("Audit is empty.")
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        c1.download_button("Download audit.jsonl",
                           data="\n".join(__import__("json").dumps(r) for r in rows),
                           file_name="audit.jsonl")
        if c2.button("Clear audit", key="audit_clear"):
            clear_audit()
            st.rerun()
    st.caption("Append-only in production. Clear button is here only because this is a lab.")
