import streamlit as st

from agentlib import agent

from . import common


def card(label, value, color=None):
    st.markdown(f"<div class='bigcard'><div style='color:#5b6b8c;font-size:0.9rem'>{label}</div>"
                f"<div style='font-size:1.15rem;font-weight:700;color:{color or 'inherit'}'>{value}</div></div>",
                unsafe_allow_html=True)


def render(ctx):
    st.header("2 · Think before you move")
    st.caption("The agent writes its plan FIRST. A guard reads the plan. Only then does anything run. Nothing below executes a tool.")
    q = common.pick_preset("think", "Risky: upgrade plan")
    later = st.checkbox("Pretend the first step (plan_lookup) already ran, so I can see the risky step",
                        value=("upgrade" in q.lower()), key=f"later_{abs(hash(q))}")
    if st.button("🧠 Show the plan only (do NOT run)", type="primary"):
        obs = [{"tool": "plan_lookup", "args": {}, "answer": "Customer is on Basic 199.", "found": True}] if (later and "upgrade" in q.lower()) else None
        p = agent.plan_preview(ctx["user"], ctx["session"], q, use_gateway=ctx["use_gateway"], observations=obs)
        st.session_state["preview"] = {"q": q, **p}
    p = st.session_state.get("preview")
    if not p:
        st.info("Press the button. Try 'Risky: upgrade plan' with the checkbox ticked, then 'Attack: injection'.")
        return
    st.subheader(f"Goal: “{p['q']}”")
    if p["blocked"]:
        card("Input guard", f"BLOCKED before the model even saw it: {p['reason']}", "#c0392b")
        return
    plan = p["plan"]
    if "final" in plan:
        card("Decision", "No tool needed. The agent is ready to answer.")
        card("Why", plan.get("thought", ""))
        return
    c = st.columns(2)
    with c[0]:
        card("1 · Tool chosen", f"{plan['tool']}  {plan.get('args') or ''}")
        card("2 · Why (the agent's own words)", plan.get("thought", ""))
    with c[1]:
        risk = p["risk"]
        card("3 · Risk level", risk, "#c0392b" if "HIGH" in risk else "#0f7b3a")
        card("4 · Guard verdict", ("ALLOWED" if p["guard_ok"] else "BLOCKED: " + p["guard_reason"]) +
             ("  ·  waits for a human" if p["needs_approval"] else ""),
             "#0f7b3a" if p["guard_ok"] else "#c0392b")
    st.caption(f"Cost of THINKING this one step: ${p['usd']:.5f}")
    st.markdown("---")
    a, b = st.columns([1, 3])
    if a.button("▶️ Approve this plan and run it"):
        s = common.run_live(ctx, p["q"])
        common.show_result(s)
        if s["phase"] == "await_approval":
            st.session_state.pending = s
            st.info("It paused for a human. Go to tab 5 → Approvals to decide.")
    b.markdown("**Why this matters:** a plan you can read is a plan you can review, test and audit. "
               "If the agent could not explain its next move, you could not trust it with a write.")
