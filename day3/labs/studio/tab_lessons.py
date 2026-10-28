from pathlib import Path

import streamlit as st

from agentlib import config, finops
from failure_lab.faults import FAULTS

SUB = Path(__file__).resolve().parent.parent / "submission"

PRACTICES = [
    ("🔒", "Every memory key contains the user id"),
    ("🔒", "Secrets never live in files, code or chat: type them in the app"),
    ("🔒", "Personal data is masked BEFORE it is logged or stored"),
    ("💰", "Every key has a TTL; history is trimmed to the last N messages"),
    ("💰", "Every run has a step limit AND a cost budget"),
    ("💰", "Measure cost per answered question, then route simple questions to a cheaper model"),
    ("🛡️", "Plan first, show the plan, then act"),
    ("🛡️", "Text from tools and documents is DATA, never instructions"),
    ("🛡️", "Risky writes need a human approval; reads can be retried, writes are not blindly retried"),
    ("✅", "Every bug you fix becomes an eval case"),
    ("✅", "Nothing ships until the eval gate is open"),
    ("📜", "Every step is logged and can be replayed (checkpoints + events)"),
]


def render(ctx):
    S = st.session_state
    st.header("7 · Lessons learnt")
    a, b = st.columns(2)
    with a:
        st.subheader("Best-practice checklist")
        ticked = 0
        for i, (icon, txt) in enumerate(PRACTICES):
            ticked += st.checkbox(f"{icon} {txt}", key=f"bp_{i}")
        st.progress(ticked / len(PRACTICES), text=f"{ticked}/{len(PRACTICES)} habits you can defend")
    with b:
        st.subheader("What went wrong today (your words)")
        any_l = False
        for f in FAULTS:
            p = SUB / f"lesson_{f['id']}.txt"
            if p.exists() and p.read_text().strip():
                any_l = True
                st.markdown(f"**{f['id']} · {f['title']}**  \n{p.read_text().strip()}")
        if not any_l:
            st.info("Write a lesson in the Failure Lab tab after each fix. They appear here.")

    st.divider()
    st.subheader("Memory decision record (half a page)")
    st.caption("A decision record explains WHY, so the next engineer does not undo it by accident.")
    avg = (sum(r["usd"] for r in S.runs) / len(S.runs)) if S.runs else 0.0004
    d = SUB / "memory_decision_record.md"
    saved = d.read_text() if d.exists() else ""
    c1, c2 = st.columns(2)
    store = c1.text_area("1. What do we store (short-term, long-term)? What do we NEVER store?",
                         "Short-term: last N chat messages. Long-term: name, city, plan, last ticket. Never: card numbers, raw phone numbers, passwords.", height=110)
    ttl = c2.text_area("2. TTL and N, and why those numbers?", f"N = {config.MAX_MESSAGES} messages, chat TTL = {config.TTL_SHORT // 60} min, facts TTL = {config.TTL_PROFILE // 86400} days. Because ...", height=110)
    who = c1.text_area("3. Who can read it, and how is it erased?", "Only the customer's own session (user id in every key). forget_user() erases everything on request.", height=110)
    cost = c2.text_area("4. Cost and quality gate", f"About ${avg * 1000:.2f} per 1,000 questions at today's prices. Eval gate: at least 85% pass and zero leaks before release.", height=110)
    md = f"# Memory decision record\n\n## 1. What we store\n{store}\n\n## 2. TTL and N\n{ttl}\n\n## 3. Access and erasure\n{who}\n\n## 4. Cost and quality gate\n{cost}\n"
    if st.button("💾 Save decision record", type="primary"):
        SUB.mkdir(exist_ok=True)
        d.write_text(md)
        st.success(f"Saved to {d.name}")
    st.download_button("⬇️ Download as .md", md, file_name="memory_decision_record.md")
    if saved:
        st.caption("A saved version exists in submission/memory_decision_record.md")
