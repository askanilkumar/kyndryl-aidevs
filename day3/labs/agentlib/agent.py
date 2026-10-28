"""The NetNova support agent as a LangGraph: boxes (nodes) and arrows (edges).

        START
          |
       [router] reads state["phase"]  (this is what makes RESUME possible)
          |
   +--> think  --(plan has an answer)---------------+
   |      |                                         |
   |    guard --(risky write, no approval)--> STOP, wait for a human
   |      |
   |     act   (run the tool; retry reads; quarantine suspicious text)
   |      |
   +-- observe                                  finish -> END
                                                (output guard: mask PII, no internal notes)

Every node saves a CHECKPOINT (the whole state) to Redis after it finishes.
If the process dies, we load the last checkpoint and continue. Nothing is lost.
"""
import json
import re
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from . import config, guard, memory
from .finops import price_of
from .llm import make_plan
from .tools import CUSTOMERS, run_tool


class SimulatedCrash(RuntimeError):
    """Raised on purpose to practise crash + resume."""


class AgentState(TypedDict, total=False):
    user: str
    session: str
    question: str
    profile: dict
    history: list
    phase: str            # think | guard | act | observe | finish | await_approval | done
    step: int
    plan: dict
    observations: list
    events: list
    answer: str
    stop_reason: str      # "" | max_steps | budget | blocked_input | needs_approval | crashed
    approval: Any         # None | "approved" | "rejected"
    tokens_in: int
    tokens_out: int
    usd: float
    max_steps: int
    budget: float
    flags: dict
    use_gateway: Any
    guard_log: list
    crashed: bool


def _ev(state, node, summary, detail=None, ms=0, tin=0, tout=0, usd=0.0):
    return {"n": len(state.get("events", [])) + 1, "node": node, "step": state.get("step", 0),
            "summary": summary, "detail": detail or {}, "ms": ms, "tokens_in": tin, "tokens_out": tout,
            "usd": round(usd, 6)}


# ------------------------------------------------------------------ nodes
def think(state):
    if state["step"] >= state["max_steps"]:
        return ({"phase": "finish", "stop_reason": "max_steps",
                 "answer": f"I could not finish within {state['max_steps']} steps. A human agent will follow up."},
                _ev(state, "think", f"STOP: max steps ({state['max_steps']}) reached"))
    if state["usd"] >= state["budget"]:
        return ({"phase": "finish", "stop_reason": "budget",
                 "answer": "This request used up its cost budget. A human agent will follow up."},
                _ev(state, "think", f"STOP: budget ${state['budget']:.4f} reached (spent ${state['usd']:.4f})"))
    if state["step"] == 0:
        hits = guard.scan_injection(state["question"])
        if hits:
            log = state.get("guard_log", []) + [{"where": "input", "finding": "prompt injection", "detail": hits[0]}]
            return ({"phase": "finish", "stop_reason": "blocked_input", "guard_log": log,
                     "answer": "I can't process that request."},
                    _ev(state, "think", "INPUT GUARD blocked the question (prompt injection pattern)"))
    t0 = time.time()
    plan, tin, tout, model = make_plan(state["question"], state["observations"], state["profile"],
                                       state["history"], state.get("flags"), state.get("use_gateway"))
    usd = price_of(model, tin, tout)
    upd = {"plan": plan, "tokens_in": state["tokens_in"] + tin, "tokens_out": state["tokens_out"] + tout,
           "usd": state["usd"] + usd}
    if "final" in plan:
        upd.update({"phase": "finish", "answer": plan["final"]})
        summary = "plan: I have enough, write the final answer"
    else:
        upd["phase"] = "guard"
        summary = f"plan: use {plan.get('tool')} - {plan.get('thought', '')}"
    return upd, _ev(state, "think", summary, {"plan": plan, "model": model},
                    int((time.time() - t0) * 1000), tin, tout, usd)


def guard_node(state):
    plan = state["plan"]
    ok, reason = guard.check_tool(plan, state["user"])
    if not ok:
        obs = state["observations"] + [{"tool": plan.get("tool"), "args": plan.get("args", {}),
                                        "blocked": True, "answer": reason}]
        log = state.get("guard_log", []) + [{"where": "tool", "finding": "blocked tool call", "detail": reason}]
        return ({"phase": "think", "observations": obs, "step": state["step"] + 1, "guard_log": log},
                _ev(state, "guard", f"BLOCKED: {reason}", {"plan": plan}))
    if plan["tool"] in guard.RISKY_TOOLS:
        decision = state.get("approval")
        if decision == "approved":
            return ({"phase": "act"}, _ev(state, "guard", "risky tool APPROVED by a human, go ahead", {"risk": guard.risk_of(plan)}))
        if decision == "rejected":
            obs = state["observations"] + [{"tool": plan["tool"], "args": plan.get("args", {}),
                                            "rejected": True, "answer": "rejected by human"}]
            return ({"phase": "think", "observations": obs, "step": state["step"] + 1, "approval": None},
                    _ev(state, "guard", "risky tool REJECTED by a human", {"risk": guard.risk_of(plan)}))
        return ({"phase": "await_approval", "stop_reason": "needs_approval"},
                _ev(state, "guard", "risky tool: WAITING for human approval", {"risk": guard.risk_of(plan), "plan": plan}))
    return {"phase": "act"}, _ev(state, "guard", f"allowed ({guard.risk_of(plan)})", {"plan": plan})


def _drop_suspicious_sentences(text):
    keep = [s for s in re.split(r"(?<=[.!?])\s+", text) if not guard.scan_injection(s)]
    return " ".join(keep)


def act(state):
    plan = state["plan"]
    if state.get("flags", {}).get("crash_at") == state["step"]:
        raise SimulatedCrash(f"process died while running {plan['tool']} (step {state['step']})")
    t0 = time.time()
    attempts = 3 if plan["tool"] not in guard.RISKY_TOOLS else 1     # retry reads, never blind-retry writes
    last_err = None
    for i in range(attempts):
        try:
            result = run_tool(plan["tool"], plan.get("args", {}), state["user"])
            last_err = None
            break
        except Exception as e:                                       # noqa
            last_err = e
            time.sleep(0.05 * (i + 1))
    if last_err:
        result = {"found": False, "answer": f"tool error: {last_err}"}
    log = state.get("guard_log", [])
    flagged = guard.scan_injection(json.dumps(result))
    if flagged:
        result = {**result, "answer": _drop_suspicious_sentences(result["answer"]) + " [note removed by guardrail]"}
        result.pop("note", None)
        log = log + [{"where": "tool result", "finding": "indirect prompt injection quarantined", "detail": flagged[0]}]
    upd = {"phase": "observe", "plan": {**plan, "result": result}, "guard_log": log}
    return upd, _ev(state, "act", f"ran {plan['tool']}", {"result": result}, int((time.time() - t0) * 1000))


def observe(state):
    plan = state["plan"]
    result = plan.get("result", {})
    obs = state["observations"] + [{"tool": plan["tool"], "args": plan.get("args", {}), "answer": result.get("answer", ""),
                                    "found": result.get("found", True)}]
    return ({"phase": "think", "observations": obs, "step": state["step"] + 1, "approval": None},
            _ev(state, "observe", f"saw the result of {plan['tool']}", {"answer": result.get("answer", "")}))


def finish(state):
    safe, findings = guard.check_output(state.get("answer", ""), state["user"])
    log = state.get("guard_log", [])
    for f in findings:
        log = log + [{"where": "output", "finding": f, "detail": ""}]
    return ({"phase": "done", "answer": safe, "guard_log": log},
            _ev(state, "finish", "answer checked by OUTPUT GUARD" + (f" ({'; '.join(findings)})" if findings else " (clean)")))


NODES = {"think": think, "guard": guard_node, "act": act, "observe": observe, "finish": finish}


def _wrap(name, fn):
    """After a node succeeds: add the event, save the checkpoint."""
    def run(state):
        out = fn(state)
        upd, ev = out if isinstance(out, tuple) else (out, _ev(state, name, name))
        new = {**state, **upd}
        ev["n"] = len(state.get("events", [])) + 1
        new["events"] = state.get("events", []) + [ev]
        save_checkpoint(new)
        return {**upd, "events": new["events"]}
    return run


def route(state):
    return {"think": "think", "guard": "guard", "act": "act", "observe": "observe", "finish": "finish"}.get(
        state.get("phase"), END)


def build_graph():
    g = StateGraph(AgentState)
    for name, fn in NODES.items():
        g.add_node(name, _wrap(name, fn))
    # START can begin at ANY node: it reads state["phase"]. That is what makes RESUME possible.
    g.add_conditional_edges(START, route, {**{k: k for k in NODES}, END: END})
    # After a node, only these arrows are possible (this is the picture you draw on the board):
    g.add_conditional_edges("think", route, {"guard": "guard", "finish": "finish"})
    g.add_conditional_edges("guard", route, {"act": "act", "think": "think", END: END})   # END = waiting for a human
    g.add_conditional_edges("act", route, {"observe": "observe"})
    g.add_conditional_edges("observe", route, {"think": "think"})
    g.add_conditional_edges("finish", route, {END: END})
    return g.compile()


GRAPH = build_graph()


# ------------------------------------------------------------------ checkpoints
def save_checkpoint(state):
    r = memory.get_redis()
    r.set(memory.ckpt_key(state["user"], state["session"]), json.dumps(state, default=str), ex=3600)
    memory.save_snapshot()


def load_checkpoint(user, session):
    raw = memory.get_redis().get(memory.ckpt_key(user, session))
    return json.loads(raw) if raw else None


# ------------------------------------------------------------------ public API
def login(user):
    """Long-term memory starts from what the CRM already knows (identity comes from login, not from chat)."""
    c = CUSTOMERS[user]
    if not memory.get_profile(user):
        memory.set_profile(user, name=c["name"], city=c["city"])
    return memory.get_profile(user)


def new_state(user, session, question, max_steps=None, budget=None, flags=None, use_gateway=None):
    return {"user": user, "session": session, "question": question, "profile": memory.get_profile(user),
            "history": memory.get_history(user, session), "phase": "think", "step": 0, "plan": {},
            "observations": [], "events": [], "answer": "", "stop_reason": "", "approval": None,
            "tokens_in": 0, "tokens_out": 0, "usd": 0.0, "max_steps": max_steps or config.MAX_STEPS,
            "budget": config.BUDGET_USD if budget is None else budget, "flags": flags or {},
            "use_gateway": use_gateway, "guard_log": [], "crashed": False}


def run(state, on_event=None):
    """Run the graph until it finishes, pauses for approval, or crashes. Returns the latest state."""
    seen = len(state.get("events", []))
    latest = dict(state)
    try:
        for snap in GRAPH.stream(state, stream_mode="values"):
            latest = snap
            if on_event:
                for ev in snap.get("events", [])[seen:]:
                    on_event(ev)
            seen = len(snap.get("events", []))
    except SimulatedCrash as e:
        latest = dict(latest)
        latest.update({"crashed": True, "stop_reason": "crashed", "crash_message": str(e)})
        return latest
    latest = dict(latest)
    latest["crashed"] = False
    if latest.get("phase") == "done":
        _after_run(latest)
    return latest


def resume(user, session, on_event=None):
    """Load the last checkpoint and continue. Clears the crash flag (the 'bug' is fixed)."""
    st = load_checkpoint(user, session)
    if not st:
        raise RuntimeError("no checkpoint found")
    st["flags"] = {**st.get("flags", {}), "crash_at": None}
    st["crashed"] = False
    st["stop_reason"] = ""
    return run(st, on_event)


def decide(state, decision, on_event=None):
    """Human answers the approval request ('approved' / 'rejected'), the agent carries on."""
    st = dict(state)
    st.update({"approval": decision, "phase": "guard", "stop_reason": ""})
    return run(st, on_event)


def _after_run(state):
    """Save the chat (short-term) and new facts (long-term)."""
    u, s = state["user"], state["session"]
    memory.add_message(u, s, "user", guard.mask_pii(state["question"]))          # never store raw PII
    memory.add_message(u, s, "assistant", state["answer"])
    facts = {}
    for o in state["observations"]:
        if o["tool"] == "plan_lookup" and o.get("found"):
            m = re.search(r"is on ([A-Za-z]+ \d+)", o["answer"])
            if m:
                facts["plan"] = m.group(1)
        if o["tool"] == "change_plan" and o.get("found") and not o.get("rejected") and not o.get("blocked"):
            facts["plan"] = o["args"].get("new_plan", facts.get("plan", ""))
        if o["tool"] == "ticket_lookup" and o.get("found"):
            facts["last_ticket"] = o["args"].get("ticket_id", "")
    if facts:
        memory.set_profile(u, **facts)


def ask(user, session, question, **opts):
    login(user)
    return run(new_state(user, session, question, **opts))


def plan_preview(user, session, question, flags=None, use_gateway=None, observations=None):
    """THINK BEFORE YOU MOVE: show the plan, the risk and the guard's verdict. Nothing is executed.
    `observations` lets you preview a LATER step (pretend earlier tools already ran)."""
    login(user)
    st = new_state(user, session, question, flags=flags, use_gateway=use_gateway)
    if observations:
        st["observations"] = observations
    hits = guard.scan_injection(question)
    if hits:
        return {"blocked": True, "reason": "input guard: prompt injection pattern", "plan": None}
    upd, ev = think(st)
    plan = upd.get("plan", {})
    out = {"blocked": False, "plan": plan, "event": ev, "usd": upd.get("usd", 0.0)}
    if "tool" in plan:
        ok, reason = guard.check_tool(plan, user)
        out.update({"guard_ok": ok, "guard_reason": reason, "risk": guard.risk_of(plan),
                    "needs_approval": plan["tool"] in guard.RISKY_TOOLS})
    return out
