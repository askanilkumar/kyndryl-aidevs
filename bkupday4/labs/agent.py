"""
Field-ops agent. LangGraph graph: plan -> guard -> execute -> loop.

The 'guard' step is where RBAC and approval checks live. Nothing calls
a tool without passing the guard. HITL approval is handled by returning
a 'pending_approval' state the UI picks up.
"""
from dataclasses import dataclass, field
from typing import Any
from langgraph.graph import StateGraph, END

import mcp_client as mcp
from llm import get_plan
from rbac import can_call, requires_approval, audit


@dataclass
class S:
    user_prompt: str = ""
    role: str = "engineer"
    history: list[dict] = field(default_factory=list)   # [{tool, args, result}]
    plan: dict | None = None
    pending_approval: dict | None = None                # {tool, args}
    final: str = ""
    steps: int = 0
    max_steps: int = 6
    gw_url: str | None = None
    gw_key: str | None = None
    model: str = "kimi-k2.7-code"


def node_plan(state: S) -> dict:
    next_steps = (state.steps or 0) + 1
    if next_steps > state.max_steps:
        return {"steps": next_steps,
                "plan": {"final": f"Step limit {state.max_steps} reached. Stopping."}}
    ctx = state.user_prompt
    if state.history:
        ctx += "\n\nPrevious tool results:\n" + "\n".join(
            f"- {h['tool']}({h['args']}) -> {str(h['result'])[:300]}" for h in state.history
        )
    plan = get_plan(ctx, state.history, state.gw_url, state.gw_key, state.model)
    return {"plan": plan, "steps": next_steps}


def node_guard(state: S) -> dict:
    plan = state.plan or {}
    if "final" in plan:
        return {"final": plan["final"]}
    tool = plan.get("tool")
    args = plan.get("args", {})
    allowed, reason = can_call(state.role, tool or "")
    if not allowed:
        audit("denied", state.role, tool or "?", args, "block", reason)
        hist = state.history + [{"tool": tool, "args": args, "result": f"DENIED: {reason}"}]
        return {"history": hist}
    if requires_approval(tool):
        audit("proposed", state.role, tool, args, "allow", "awaiting approval")
        return {"pending_approval": {"tool": tool, "args": args}}
    # safe to execute
    return {}


def node_execute(state: S) -> dict:
    plan = state.plan or {}
    tool = plan.get("tool")
    args = plan.get("args", {})
    if not tool:
        return {}
    try:
        r = mcp.call_tool(tool, args)
        audit("executed", state.role, tool, args, "ok" if r.get("ok") else "fail", str(r)[:200])
        hist = state.history + [{"tool": tool, "args": args, "result": r.get("result", r)}]
        return {"history": hist, "plan": None}
    except Exception as e:
        audit("error", state.role, tool, args, "fail", str(e))
        hist = state.history + [{"tool": tool, "args": args, "result": f"ERROR: {e}"}]
        return {"history": hist, "plan": None}


def route_after_guard(state: S) -> str:
    if state.final:
        return END
    if state.pending_approval:
        return END                # pause; UI will resume
    plan = state.plan or {}
    if "final" in plan:
        return END
    # denied -> loop back to plan with the rejection in history
    if state.history and str(state.history[-1].get("result", "")).startswith("DENIED"):
        return "plan"
    return "execute"


def route_after_execute(state: S) -> str:
    if (state.steps or 0) >= state.max_steps:
        return END
    return "plan"


def build_graph():
    g = StateGraph(S)
    g.add_node("plan", node_plan)
    g.add_node("guard", node_guard)
    g.add_node("execute", node_execute)
    g.set_entry_point("plan")
    g.add_edge("plan", "guard")
    g.add_conditional_edges("guard", route_after_guard, {"plan": "plan", "execute": "execute", END: END})
    g.add_conditional_edges("execute", route_after_execute, {"plan": "plan", END: END})
    return g.compile()


def run_agent(state: S) -> S:
    graph = build_graph()
    out = graph.invoke(state)
    return S(**out) if isinstance(out, dict) else out


def resume_after_approval(state: S, approved: bool) -> S:
    """Called by the UI once the human decides."""
    if not state.pending_approval:
        return state
    tool = state.pending_approval["tool"]
    args = state.pending_approval["args"]
    if approved:
        audit("approved", state.role, tool, args, "allow", "human approved")
        r = mcp.call_tool(tool, args)
        audit("executed", state.role, tool, args, "ok" if r.get("ok") else "fail", str(r)[:200])
        state.history.append({"tool": tool, "args": args, "result": r.get("result", r)})
    else:
        audit("rejected", state.role, tool, args, "block", "human rejected")
        state.history.append({"tool": tool, "args": args, "result": "REJECTED by human"})
    state.pending_approval = None
    state.plan = None
    # continue the loop (resume uses a fresh step budget on top of what's done)
    state.steps = 0
    return run_agent(state)
