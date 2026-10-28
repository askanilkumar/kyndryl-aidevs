import pandas as pd
import streamlit as st

from agentlib import finops

from . import common


def render(ctx):
    S = st.session_state
    st.header("4 · Agent Run: watch every step")
    st.caption("Each line is one box of the graph finishing. After every line the whole state is saved (💾). "
               "Tokens and dollars are counted per step.")
    q = common.pick_preset("run", "Two things at once")
    if st.button("▶️ Run the agent", type="primary"):
        s = common.run_live(ctx, q)
        common.show_result(s)
        if s["phase"] == "await_approval":
            S.pending = s
            st.info("⏸️ A risky write needs a human. Open tab 5 → Approvals.")
    elif S.last:
        st.markdown("**Last run**")
        for ev in S.last["events"]:
            common.event_row(ev)
        common.show_result(S.last)

    st.divider()
    st.subheader("💰 FinOps: what did this session cost?")
    if not S.runs:
        st.info("Run a few questions. The table fills up.")
        return
    df = pd.DataFrame(S.runs)
    df["model"] = df["model"].astype(str)
    st.dataframe(df.rename(columns={"tokens_in": "tok in", "tokens_out": "tok out", "usd": "cost $"}),
                 width="stretch", hide_index=True)
    actual, routed, saving = finops.what_if_routed(S.runs)
    c = st.columns(3)
    c[0].metric("Total so far", f"${actual:.4f}")
    c[1].metric("If simple FAQs used the small model", f"${routed:.4f}", f"-{saving}%", delta_color="normal")
    answered = [r for r in S.runs if r["stop"] == "answered"]
    c[2].metric("Cost per answered question", f"${(actual / len(answered)):.5f}" if answered else "-")
    st.caption("Prices are EXAMPLES from agentlib/config.py (USD per 1M tokens). Put your real gateway prices there. "
               "This is Day 1's routing idea, now measured on a real agent.")
