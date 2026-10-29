"""Tab 0 · Journey: the whole Day 3 in one place. Click a step, read it, press Run."""
import subprocess
import sys
from pathlib import Path

import streamlit as st

LABS = Path(__file__).resolve().parent.parent

# kind "script" = has a Run button.  kind "tab" = go and use a Studio tab.
STEPS = [
    dict(id="s0", label="0 · Setup check", kind="script", script="check_setup.py",
         what="Check that Python, Redis and the agent work on this machine.",
         say="Before we build, we test the tools. If this says 'Agent test: ok', we are ready.",
         see="'Mode: OFFLINE stand-in model' and 'Agent test: ok'.",
         learn="Offline = a practice model that gives the same answer every time. No key needed.",
         tryit=None),
    dict(id="s1", label="1a · Memory is a list", kind="script", script="lab1a_list_memory.py",
         what="The bot 'remembers' by re-reading a Python list. We send only the last 10 messages.",
         say="The bot has no brain-memory. Every time we paste the old chat and it reads only that.",
         see="'What is my name?' works first. After 6 more questions it says 'I don't know'. After restart it also forgets.",
         learn="Memory = text we send again. Old messages fall out. A list is lost when the program stops.",
         tryit="Open lab1a_list_memory.py, change MAX_KEEP 10 to 4. Why does the last answer fail?"),
    dict(id="s2", label="1b · Memory in Redis", kind="script", script="lab1b_redis_memory.py",
         what="Same chat, but stored in Redis (a small database) so it survives a restart.",
         say="Press Run twice. Look at the first line: how many messages were already there?",
         see="1st run: 0 already there. 2nd run: 2 already there, list has 4. TTL about 120 seconds.",
         learn="Redis keeps memory outside the program. TTL = it forgets by itself after some time.",
         tryit="Press Run again and again: it keeps growing. Only the TTL can stop it. (1c adds a size limit.)"),
    dict(id="s3", label="1c · One memory per customer", kind="script", script="lab1c_user_memory_ttl.py",
         what="Ravi and Meena both use session 'default' but get separate memory. Chat expires, profile stays.",
         say="Look at the key names. The customer id is inside every key, so customers never mix.",
         see="Each sees only their own chat. Chat TTL 8s then empty. Profile kept (30 days). Forget deletes it.",
         learn="User id in the key = privacy. Chat is short-lived, profile is long-lived. Forget = one line.",
         tryit="In the file set DEMO_TTL = 5, or give both customers the same session name."),
    dict(id="s4", label="Studio · tab 3 Memory", kind="tab",
         what="See the same memory in a picture: keys, TTL countdown, masking.",
         say="We just did it in code. Now watch it live.",
         see="Phone number saved masked. 15 messages with N=5 keeps only 5. TTL counts down to 0. Forget deletes keys.",
         learn="Mask personal data before saving. Keep only the last N. Every key has a TTL.",
         tryit="Go to tab 3 · Memory: add the phone message, press 'Add 15 msgs', set a 10-second TTL and Refresh, then Forget."),
    dict(id="s5", label="2a · Tool call by hand", kind="script", script="lab2a_tool_by_hand.py",
         what="The model writes a plan (which tool, which input). Our code runs the tool. Then the model answers.",
         say="The model never touches the ticket system. It writes a note and our code does the work.",
         see="THINK (plan as JSON) then ACT (ticket_lookup) then THINK (final answer).",
         learn="An agent is a loop: think, act, look at the result, answer. The model proposes, code executes.",
         tryit="In the file change QUESTION to 'Which plan am I on?' then 'Check ticket TKT-2003'. The tool changes."),
    dict(id="s6", label="2b · RAG is one tool", kind="script", script="lab2b_rag_as_tool.py",
         what="Your Day 2 search becomes one tool among several. The agent chooses when to use it.",
         say="Knowledge question: it uses search. Account question: it uses plan lookup. Same agent.",
         see="3 questions, each with the tools used and the cost.",
         learn="RAG is a tool, not the whole product. The agent picks the right tool for the question.",
         tryit="Add a KB-070 'Data rollover' article in agentlib/tools.py and ask about it."),
    dict(id="s7", label="2c · The agent as a graph", kind="script", script="lab2c_agent_langgraph.py",
         what="The same loop drawn as boxes and arrows (a LangGraph). State is saved after each box.",
         say="Boxes = steps, arrows = what happens next. Paste the diagram text into mermaid.live to see it.",
         see="A Mermaid diagram, then the run line by line.",
         learn="A graph makes the agent loop visible and lets us save progress after every step.",
         tryit="Open agentlib/agent.py, find build_graph() and count the 5 nodes."),
    dict(id="s8", label="Studio · tabs 2 and 4", kind="tab",
         what="Preview a plan before it runs, then run the agent and see the cost.",
         say="Think first: nothing runs yet, we only read the plan. Agent run: now it really runs.",
         see="Tab 2: 4 cards for 'Risky: upgrade plan'. Tab 4: 'Two things at once' with checkpoints and a cost table.",
         learn="Every step is visible and has a cost. Risky actions are flagged before they run.",
         tryit="Tab 2 · Think first: preview 'Risky: upgrade plan'. Tab 4 · Agent run: run 'Two things at once', count the 💾."),
    dict(id="s9", label="3a · Crash and resume", kind="script", script="lab3a_checkpoint_resume.py",
         what="The agent crashes half-way. We resume from the saved checkpoint.",
         say="Like a game save point. After the crash we continue and do not repeat finished work.",
         see="Run 1 crashes. Checkpoint printed. Run 2 resumes and gives the final answer.",
         learn="Save progress after every step so a crash loses nothing. The checkpoint also has a TTL.",
         tryit="In the file change CRASH_AT to 0 then 2. Where does it die?"),
    dict(id="s10", label="3b · Step and cost limits", kind="script", script="lab3b_limits.py",
         what="A confused model keeps asking for the same tool. Two limits stop it: max steps and max money.",
         say="Without a limit, a loop never stops and the bill keeps growing.",
         see="The run stops with a stop_reason and a polite message for the customer.",
         learn="Every loop needs a step limit and a budget. Decide what the customer sees when it stops.",
         tryit="In the file set MAX_STEPS = 3, then BUDGET = 0.0004. Which limit fires first?"),
    dict(id="s11", label="3c · Human approves", kind="script", script="lab3c_approval.py", args=["approve", "reject"],
         what="Reading is free. A risky WRITE (upgrade a plan) pauses and waits for a human yes or no.",
         say="Press Approve, then run again and press Reject. Compare the final answer and the plan in the system.",
         see="Approve: plan changed. Reject: plan unchanged, and the answer says so.",
         learn="Humans approve risky writes. The guard decides which tools are risky.",
         tryit="Open agentlib/guard.py: which tools are risky and why only those?"),
    dict(id="s12", label="Studio · tab 5 Safety", kind="tab",
         what="Approvals, crash and resume, limits, 3 attacks and the eval gate, all in one tab.",
         say="Everything from Lab 3, now with buttons. Press the 3 attack buttons and read the guardrail log.",
         see="Approve/reject, crash card, limits, 3 attacks blocked, 8 eval cases.",
         learn="Safety has 3 guards (input, tool, output). Evals decide if we can ship.",
         tryit="Tab 5 · Safety & evals: ask for the upgrade and approve; run the 3 attacks; run the 8 eval cases."),
    dict(id="s13", label="Independent challenge", kind="tab",
         what="Break it, fix it, extend it, explain it. About 100 minutes, participants drive.",
         say="A: fix 3 faults. B: add a 5th tool. C: write the memory decision record.",
         see="Failure Lab: 3 checks go green. run_evals.py: 10/10, GATE: OPEN.",
         learn="Real agents fail in simple ways: shared keys, endless history, endless loops. You can fix them.",
         tryit="A: tab 6 · Failure Lab (fix F1, F2, F3, press Run check).  B: add usage_alert, then run python run_evals.py.  C: tab 7 · Lessons, fill 4 boxes, Save."),
]


def _run(script, args=()):
    try:
        p = subprocess.run([sys.executable, script, *args], cwd=LABS, capture_output=True, text=True,
                           timeout=90, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        return (p.stdout or "") + (("\n" + p.stderr) if p.returncode else "")
    except subprocess.TimeoutExpired:
        return "Timed out after 90 seconds."
    except Exception as e:  # keep the class going
        return f"Could not run: {e}"


def render(ctx):
    S = st.session_state
    st.header("0 · Day 3 Journey")
    st.info(
        "**The big picture.** Day 1 gave us a model. Day 2 gave it knowledge (RAG). "
        "**Day 3 gives it a memory and the power to act**, safely.\n\n"
        "**Remember** (Lab 1)  →  **Choose tools** (Lab 2)  →  **Stay safe** (Lab 3)  →  **Break and fix it** (Challenge)\n\n"
        "Pick a step on the left. Read it. Press **Run** (or open the tab it names).")

    left, right = st.columns([1, 3])
    labels = [s["label"] for s in STEPS]
    pick = left.radio("Steps", labels, key="journey_step", label_visibility="collapsed")
    s = STEPS[labels.index(pick)]
    i = labels.index(pick)

    with right:
        st.subheader(s["label"])
        st.markdown(f"**What we are doing:** {s['what']}")
        st.markdown(f"**Tell the class:** {s['say']}")
        if s["kind"] == "script":
            st.caption(f"Runs `python {s['script']}` for you. You can also run it in a terminal.")
            if s.get("args"):
                c = st.columns(len(s["args"]))
                for col, a in zip(c, s["args"]):
                    if col.button(f"▶ Run: {a.title()}", key=f"run_{s['id']}_{a}"):
                        with st.spinner("Running..."):
                            S[f"out_{s['id']}"] = _run(s["script"], [a])
            elif st.button("▶ Run", key=f"run_{s['id']}", type="primary"):
                with st.spinner("Running..."):
                    S[f"out_{s['id']}"] = _run(s["script"])
            out = S.get(f"out_{s['id']}")
            if out:
                st.code(out, language="text")
            with st.expander(f"📄 Show the code: {s['script']}"):
                try:
                    st.code((LABS / s["script"]).read_text(encoding="utf-8"), language="python")
                except Exception as e:
                    st.write(f"Could not read the file: {e}")
        else:
            st.warning("No script here. Open the tab named below and follow the steps.")
        st.markdown(f"**What you should see:** {s['see']}")
        st.markdown(f"**What we learn:** {s['learn']}")
        if s["tryit"]:
            st.markdown(f"**Try this:** {s['tryit']}")
        if i + 1 < len(STEPS):
            st.caption(f"Next step: **{labels[i + 1]}**")
