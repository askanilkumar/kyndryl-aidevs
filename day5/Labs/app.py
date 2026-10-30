"""AskNova - Day 5 app.   Run:  python -m streamlit run app.py
Keys are typed in the sidebar (kept only for this browser session) or read from OS env vars on a server.
Nothing secret is ever written to a file."""
import os
from collections import Counter

import pandas as pd
import streamlit as st

from asknova import agent, config, monitor
from asknova.evals import run_evals
from asknova.guards import ATTACKS
from asknova.llm import active_version, list_versions, load_prompt
from asknova.release import load as load_releases, release, rollback
from asknova.tracing import Tracer

st.set_page_config(page_title="AskNova - Day 5", page_icon="📡", layout="wide")


# ---------- optional password gate (used when deployed on the cloud) ----------
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if APP_PASSWORD and not st.session_state.get("unlocked"):
    st.title("📡 AskNova")
    pw = st.text_input("App password", type="password")
    if pw == APP_PASSWORD:
        st.session_state.unlocked = True
        st.rerun()
    elif pw:
        st.error("Wrong password")
    st.stop()


@st.cache_resource
def openai_client(key):
    from openai import OpenAI
    return OpenAI(api_key=key)


# ---------- sidebar: keys + switches ----------
with st.sidebar:
    st.header("📡 AskNova")
    st.caption("Keys stay in this browser session only. Never put keys in files.")
    env_key = os.getenv("OPENAI_API_KEY", "")
    key = st.text_input("OpenAI API key", type="password", placeholder="sk-...  (empty = OFFLINE mode)")
    key = key or env_key
    client = openai_client(key) if key else None
    model = st.selectbox("Model", [m for m in config.PRICES if m != "offline"]) if client else "offline"
    if client:
        st.success(f"Mode: OpenAI · {model}")
    else:
        st.info("Mode: OFFLINE stand-in (no key, no cost)")

    st.subheader("🔭 Tracing (Lab 2)")
    trace_mode = st.radio("Send traces to", ["Off", "LangSmith", "Langfuse"], horizontal=True)
    keys = {}
    if trace_mode == "LangSmith":
        keys["langsmith_key"] = st.text_input("LangSmith API key", type="password") or os.getenv("LANGSMITH_API_KEY", "")
        keys["langsmith_endpoint"] = st.selectbox("Region", ["https://api.smith.langchain.com", "https://eu.api.smith.langchain.com"])
    elif trace_mode == "Langfuse":
        keys["langfuse_public"] = st.text_input("Langfuse public key (pk-lf-...)") or os.getenv("LANGFUSE_PUBLIC_KEY", "")
        keys["langfuse_secret"] = st.text_input("Langfuse secret key (sk-lf-...)", type="password") or os.getenv("LANGFUSE_SECRET_KEY", "")
        keys["langfuse_host"] = st.selectbox("Region", ["https://cloud.langfuse.com", "https://us.cloud.langfuse.com"])
    tracer_ready = trace_mode == "Off" or all(keys.values())
    if not tracer_ready:
        st.warning("Enter the keys to start tracing")
    tracer = Tracer(trace_mode.lower() if tracer_ready else "off", keys)

    st.subheader("🛡️ Guardrails (Lab 1)")
    guards_on = st.toggle("Guardrails ON", value=True)
    use_moderation = st.toggle("OpenAI moderation check", value=False, disabled=client is None)
    approve_writes = st.toggle("Supervisor approves write actions", value=False)

    st.subheader("🚀 Prompt (Lab 4)")
    versions = list_versions()
    released = active_version()
    prompt_version = st.selectbox("Prompt version", versions, index=versions.index(released) if released in versions else 0,
                                  help=f"Released version: {released}")

run_args = dict(client=client, model=model, tracer=tracer, prompt_version=prompt_version)

tab_chat, tab_attack, tab_eval, tab_mon, tab_rel = st.tabs(
    ["💬 Chat", "🛡️ Attack test", "✅ Evals", "📈 Monitor", "🚀 Release"])

# ---------- Chat ----------
with tab_chat:
    st.subheader("Ask NetNova's helpdesk agent")
    st.caption("Try: 'Status of INC-5001?' · 'Roaming price prepaid UAE?' · 'Reset SIM for C-103' · 'My data is slow'")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for turn in st.session_state.chat:
        with st.chat_message(turn["role"]):
            st.write(turn["text"])
            if turn.get("meta"):
                st.caption(turn["meta"])
    q = st.chat_input("Type a question")
    if q:
        res = agent.run(q, guards_on=guards_on, use_moderation=use_moderation,
                        approve_writes=approve_writes, **run_args)
        meta = (f"tools: {', '.join(res.tools_used) or 'none'} · tokens {res.tokens_in}+{res.tokens_out} · "
                f"${res.cost:.5f} · {res.latency_ms} ms" + (f" · 🛡️ {'; '.join(res.guard_hits)}" if res.guard_hits else "")
                + (" · 🔒 PII masked" if res.masked else "") + (f" · ⏳ needs approval" if res.needs_approval else ""))
        st.session_state.chat += [{"role": "user", "text": q}, {"role": "assistant", "text": res.answer, "meta": meta}]
        st.session_state.last_spans = [(s.name, s.kind, s.ms, s.tokens_in + s.tokens_out) for s in tracer.spans]
        st.session_state.last_url, st.session_state.last_err = tracer.trace_url, tracer.error
        st.rerun()
    if st.session_state.get("last_spans"):
        with st.expander("🔭 Trace of the last answer (each step = one span)", expanded=False):
            st.dataframe(pd.DataFrame(st.session_state.last_spans, columns=["span", "kind", "ms", "tokens"]),
                         hide_index=True, width="stretch")
            if st.session_state.get("last_url"):
                st.write("Open in your tracing tool:", st.session_state.last_url)
            if st.session_state.get("last_err"):
                st.warning(st.session_state.last_err)
    if st.button("Clear chat"):
        st.session_state.chat, st.session_state.last_spans = [], []
        st.rerun()

# ---------- Attack test ----------
with tab_attack:
    st.subheader("Can you break AskNova? 6 attacks, each must be stopped by a guard")
    st.caption("Uses the switches in the sidebar. Turn guardrails OFF to see what gets through.")
    if st.button("▶ Run the 6 attacks", type="primary"):
        rows = []
        for text, expect in ATTACKS:
            res = agent.run(text, guards_on=guards_on, use_moderation=use_moderation,
                            approve_writes=False, log=False, **run_args)
            ok = res.blocked if expect == "blocked" else res.masked
            rows.append({"attack": text, "expected": expect, "result": "✅ stopped" if ok else "❌ got through",
                         "guard": "; ".join(res.guard_hits) or ("PII masked" if res.masked else "-"),
                         "answer": res.answer})
        stopped = sum(r["result"].startswith("✅") for r in rows)
        (st.success if stopped == len(rows) else st.error)(f"{stopped} / {len(rows)} attacks stopped")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ---------- Evals ----------
with tab_eval:
    st.subheader("Evals: test the agent before you trust it")
    st.caption(f"Gate: at least {int(config.EVAL_GATE * 100)}% pass AND every safety case passes. Cases live in asknova/evals.py")
    use_judge = st.checkbox("Also use LLM-as-judge (needs OpenAI key, costs a little)", disabled=client is None)
    if st.button("▶ Run evals", type="primary"):
        rep = run_evals(use_judge=use_judge, guards_on=guards_on, **run_args)
        c1, c2, c3 = st.columns(3)
        c1.metric("Passed", f"{rep['passed']} / {rep['total']}")
        c2.metric("Pass rate", f"{rep['pass_rate']:.0%}")
        c3.metric("Safety cases", "all pass" if rep["safety_ok"] else "FAILED")
        (st.success("Gate OPEN: ok to release") if rep["gate_open"] else st.error("Gate CLOSED: do not release"))
        df = pd.DataFrame(rep["rows"])
        df["passed"] = df["passed"].map({True: "✅", False: "❌"})
        st.dataframe(df[["id", "passed", "safety", "question", "why", "judge", "answer"]], hide_index=True, width="stretch")

# ---------- Monitor ----------
with tab_mon:
    st.subheader("Monitor: what an AgentOps team watches every day")
    rows = monitor.read_log()
    s = monitor.summary(rows)
    if not rows:
        st.info("No requests yet. Ask a few questions in the Chat tab.")
    else:
        c = st.columns(6)
        c[0].metric("Requests", s["requests"])
        c[1].metric("Avg latency", f"{s['avg_latency_ms']} ms")
        c[2].metric("p95 latency", f"{s['p95_latency_ms']} ms")
        c[3].metric("Cost", f"${s['cost_usd']}")
        c[4].metric("Blocked", f"{s['block_rate']:.0%}")
        c[5].metric("Errors", f"{s['error_rate']:.0%}")
        if s["alerts"]:
            st.error("🚨 Alert: " + ", ".join(f"{a} above {monitor.ALERTS[a]}" for a in s["alerts"]))
        else:
            st.success("All within limits: " + ", ".join(f"{k} ≤ {v}" for k, v in monitor.ALERTS.items()))
        df = pd.DataFrame(rows)
        left, right = st.columns(2)
        left.caption("Latency per request (ms)")
        left.line_chart(df["latency_ms"])
        right.caption("Tool calls")
        right.bar_chart(pd.Series(Counter(t for r in rows for t in r["tools"]), dtype="int64"))
        st.caption("Last 20 requests (questions are PII-masked before logging)")
        st.dataframe(df.tail(20)[["ts", "user", "question", "model", "prompt", "latency_ms", "cost_usd", "blocked", "tools", "error"]],
                     hide_index=True, width="stretch")
    if st.button("Clear log"):
        config.LOG_FILE.unlink(missing_ok=True)
        st.rerun()

# ---------- Release ----------
with tab_rel:
    st.subheader("Release: a prompt is code - test it before it goes live")
    state = load_releases()
    st.metric("Live prompt version", state["active"])
    pick = st.selectbox("Version to release", versions, index=len(versions) - 1)
    a, b = st.columns(2)
    a.caption(f"Live: system_{state['active']}.txt")
    a.code(load_prompt(state["active"]), language="text")
    b.caption(f"Candidate: system_{pick}.txt")
    b.code(load_prompt(pick), language="text")
    c1, c2 = st.columns(2)
    if c1.button(f"▶ Run evals and release {pick}", type="primary"):
        out = release(pick, client=client, model=model)
        rep = out["report"]
        msg = f"{pick}: {out['status'].upper()} · pass rate {rep['pass_rate']:.0%} · safety {'ok' if rep['safety_ok'] else 'FAILED'}"
        (st.success if out["status"] == "approved" else st.error)(msg)
        failed = [r for r in rep["rows"] if not r["passed"]]
        if failed:
            st.dataframe(pd.DataFrame(failed)[["id", "question", "why"]], hide_index=True, width="stretch")
    if c2.button("↩ Roll back to the previous version"):
        out = rollback()
        st.info(f"Live version: {out['active']} (was {out['from']})")
    st.caption("Release history")
    st.dataframe(pd.DataFrame(load_releases()["history"]), hide_index=True, width="stretch")
