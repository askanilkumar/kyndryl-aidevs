"""
LLM wrapper. Gateway if GATEWAY_BASE_URL + GATEWAY_KEY set in the
Streamlit sidebar; else offline deterministic stand-in.

The agent gets back a 'plan': either {"tool": ..., "args": {...}}
or {"final": "..."}  — plain JSON. We parse tolerantly: even if the
model wraps it in markdown or adds reasoning, we grab the JSON object.
"""
import json, re, os
from typing import Any


def _extract_json(text: str) -> dict | None:
    """Grab the first {...} block from mixed text."""
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def plan_online(prompt: str, base_url: str, api_key: str, model: str = "kimi-k2.7-code") -> dict:
    """Ask the gateway model for a plan."""
    from openai import OpenAI
    client = OpenAI(base_url=base_url.rstrip("/"), api_key=api_key)
    system = (
        "You are a field-ops agent. You MUST reply with ONE JSON object only.\n"
        "Either: {\"tool\": \"<tool_name>\", \"args\": {...}, \"thought\": \"<short>\"}\n"
        "Or:     {\"final\": \"<answer to user>\"}\n"
        "Available tools: kb_search(query, role), ticket_lookup(incident_id), "
        "tower_status(tower_id), plan_change(customer_id, new_plan_id).\n"
        "No markdown. No extra prose."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": prompt}],
        temperature=0.0,
    )
    text = resp.choices[0].message.content or ""
    parsed = _extract_json(text)
    if parsed:
        return parsed
    return {"final": text.strip() or "I could not form a plan."}


def plan_offline(prompt: str, history: list[dict]) -> dict:
    """
    Deterministic stand-in. Keyword routing — enough to show the loop
    end-to-end without a key. Won't repeat a successful call.
    """
    p = prompt.lower()
    done_tools = {h.get("tool") for h in history if "DENIED" not in str(h.get("result", "")) and "REJECTED" not in str(h.get("result", ""))}
    denied_tools = {h.get("tool") for h in history if "DENIED" in str(h.get("result", ""))}
    # Mark denied as "done" so we don't retry
    done_tools |= denied_tools

    # Order: incident -> tower -> KB (runbook) -> optional plan_change
    # 1. Incident lookup (if INC in prompt and not done)
    inc = re.search(r"(INC-\d+)", prompt, re.I)
    if inc and "ticket_lookup" not in done_tools:
        return {"tool": "ticket_lookup", "args": {"incident_id": inc.group(1).upper()},
                "thought": "Pull incident details first."}
    # 2. Tower status
    tw = re.search(r"(TWR-[A-Z]+-\d+)", prompt, re.I)
    if (tw or "tower" in p) and "tower_status" not in done_tools:
        tower_id = tw.group(1).upper() if tw else "TWR-CHN-11"
        return {"tool": "tower_status", "args": {"tower_id": tower_id},
                "thought": "Check tower health."}
    # 3. Runbook / plan info
    if "kb_search" not in done_tools and any(k in p for k in [
        "procedure", "runbook", "escalation", "how do", "steps", "plan", "compensate", "goodwill"
    ]):
        role_hint = "engineer" if any(k in p for k in ["procedure", "runbook", "escalation"]) else "viewer"
        return {"tool": "kb_search", "args": {"query": prompt, "role": role_hint},
                "thought": "Look up the runbook / plan info."}
    # 4. Plan change (only once, only if explicitly asked and nothing has done it)
    if ("plan_change" not in done_tools) and any(k in p for k in ["change", "goodwill", "compensate", "upgrade"]):
        cust = re.search(r"(C-\d+)", prompt, re.I)
        plan = re.search(r"(PLAN-\d+)", prompt, re.I)
        if cust:
            return {"tool": "plan_change",
                    "args": {"customer_id": cust.group(1).upper(),
                             "new_plan_id": (plan.group(1).upper() if plan else "PLAN-202")},
                    "thought": "Apply plan upgrade as goodwill."}
    # 5. First call default
    if not history:
        return {"tool": "kb_search", "args": {"query": prompt, "role": "engineer"},
                "thought": "Try the KB first."}
    # 6. Done
    summary = ", ".join(f"{h['tool']}" for h in history)
    return {"final": f"Investigation complete. Steps taken: {summary}. Hand off to NOC lead with the audit trail."}


def get_plan(prompt: str, history: list[dict], gw_url: str | None, gw_key: str | None,
             model: str = "kimi-k2.7-code") -> dict:
    if gw_url and gw_key:
        try:
            return plan_online(prompt, gw_url, gw_key, model)
        except Exception as e:
            return {"final": f"[gateway error, falling back offline] {e}"}
    return plan_offline(prompt, history)
