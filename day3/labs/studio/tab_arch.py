import streamlit as st

from .arch import active_for, arch_svg

DEMO = [("Customer asks", {"user", "inguard"}), ("think: write a plan", {"think", "gateway", "memory"}),
        ("guard: check the plan", {"guard"}), ("human: approve a risky write", {"guard", "human"}),
        ("act: run the tool", {"act", "tools"}), ("observe: read result, save checkpoint", {"observe", "memory"}),
        ("finish: output guard", {"outguard", "user"})]


def render(ctx):
    S = st.session_state
    st.header("1 · Architecture: who talks to whom")
    events = (S.last or {}).get("events", [])
    if events:
        st.caption("Replay your last run. Move the slider and watch the boxes light up.")
        i = st.slider("Event number", 1, len(events), 1, key="arch_ev")
        ev = events[i - 1]
        active, note = active_for(ev), ""
        st.markdown(f"**{ev['n']}. {ev['node']}**: {ev['summary']}")
    else:
        st.caption("No run yet. Step through a typical request (run a question in tab 4 to replay a real one).")
        i = st.select_slider("Walk through", options=list(range(len(DEMO))), format_func=lambda k: DEMO[k][0], key="arch_demo")
        active, note = DEMO[i][1], ""
    st.iframe(arch_svg(active, note), height=690)
    c1, c2, c3 = st.columns(3)
    c1.markdown("**The model never touches a tool.**  It only writes a plan. The *guard* decides, the *act* box runs.")
    c2.markdown("**State is saved after every box.**  Crash anywhere, load the last checkpoint, continue.")
    c3.markdown("**Habits wrap every box.**  Secure keys, a cost meter, guardrails and evals are part of the design, not add-ons.")
    with st.expander("Think about it: where would you add a new tool? Where would a Day 4 MCP server plug in?"):
        st.write("A new tool = one new function + one line in the registry + one line in the guard's allow-list. "
                 "On Day 4 the *Tools* box becomes an MCP server, and the guard keeps checking every call.")
