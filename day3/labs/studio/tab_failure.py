from pathlib import Path

import streamlit as st

from failure_lab import checks
from failure_lab.faults import FAULTS

SUB = Path(__file__).resolve().parent.parent / "submission"


def render(ctx):
    S = st.session_state
    st.header("6 · Failure Lab")
    st.caption("`failure_lab/broken_agent.py` has 5 faults. Fix the code in your editor, save, then press **Run check** here. "
               "Each check runs in its own process, so even an endless loop cannot hang this page.")
    c = st.columns([1, 1, 3])
    if c[0].button("▶️ Run all checks", type="primary"):
        for f in FAULTS:
            S.checked[f["id"]] = checks.run_check(f["id"], timeout=6)
    done = sum(1 for f in FAULTS if S.checked.get(f["id"], {}).get("ok"))
    req = sum(1 for f in FAULTS if f["required"] and S.checked.get(f["id"], {}).get("ok"))
    c[1].metric("Fixed", f"{done}/5")
    c[2].progress(done / 5, text=f"Required {req}/3 · stretch {done - req}/2")
    for f in FAULTS:
        r = S.checked.get(f["id"])
        icon = "✅" if r and r["ok"] else ("❌" if r else "⬜")
        with st.expander(f"{icon} {f['id']} · {f['title']}  ({'required' if f['required'] else 'stretch'}) · {f['habit']}", expanded=not r or not r["ok"]):
            st.markdown(f"**What users see:** {f['symptom']}")
            st.markdown(f"**Where to look:** `{f['where']}`")
            if st.button("Run check", key=f"chk_{f['id']}"):
                S.checked[f["id"]] = checks.run_check(f["id"], timeout=6)
                st.rerun()
            if r:
                (st.success if r["ok"] else st.error)(r["message"])
            lesson_file = SUB / f"lesson_{f['id']}.txt"
            old = lesson_file.read_text() if lesson_file.exists() else ""
            txt = st.text_area(f"Lesson learnt: {f['lesson_q']}", old, key=f"les_{f['id']}", height=80)
            if st.button("Save lesson", key=f"sv_{f['id']}"):
                SUB.mkdir(exist_ok=True)
                lesson_file.write_text(txt)
                st.toast("Saved")
    st.info("Habit ✅ **Evals**: for every fault you fix, add one case to `agentlib/evals.py` so it can never come back unnoticed.")
