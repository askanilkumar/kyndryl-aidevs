"""
NetNova LLM provider.

Order of preference:
  1. Gateway  (central LiteLLM, uses GATEWAY_BASE_URL + GATEWAY_KEY from .env)
  2. OpenAI   (uses OPENAI_API_KEY from .env)
  3. Offline  (deterministic rule-based stand-in, no key)

Exposes:
  chat(messages, tools=None) -> dict with keys: text, tool_calls, usage, raw
  TOOL_SCHEMAS                -> list of OpenAI-style tool schemas (if a lab needs them)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv  # type: ignore
    # Load from CWD, then from the repo root if we find one.
    load_dotenv()
    for p in (Path.cwd(), *Path.cwd().parents):
        if (p / ".env").exists():
            load_dotenv(p / ".env", override=False)
            break
except Exception:
    pass


# ---------- public config ----------

GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "").rstrip("/")
GATEWAY_KEY = os.getenv("GATEWAY_KEY", "")
GATEWAY_MODEL = os.getenv("CHAT_MODEL", "chat-llm")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MODE_OVERRIDE = os.getenv("ASKIT_MODEL", "").strip().lower()  # "", "offline", "openai", "gateway"


def active_mode() -> str:
    """Returns one of: 'gateway', 'openai', 'offline'. Resolved exactly once per import."""
    global _MODE
    if _MODE is not None:
        return _MODE
    if MODE_OVERRIDE in ("offline", "openai", "gateway"):
        _MODE = MODE_OVERRIDE
    elif GATEWAY_BASE_URL and GATEWAY_KEY:
        _MODE = "gateway"
    elif OPENAI_API_KEY:
        _MODE = "openai"
    else:
        _MODE = "offline"
    return _MODE


_MODE: str | None = None


def model_banner() -> str:
    """One-line banner labs print at startup, DXC-style."""
    m = active_mode()
    if m == "gateway":
        return f"Model: gateway ({GATEWAY_MODEL} via {GATEWAY_BASE_URL})"
    if m == "openai":
        return f"Model: openai ({OPENAI_MODEL})"
    return "Model: offline  (deterministic stand-in, no key)"


# ---------- public chat() ----------

def chat(messages: list[dict], tools: list[dict] | None = None,
         temperature: float = 0.0, max_tokens: int = 400) -> dict:
    """Call the model. Returns a dict:
       { "text": str, "tool_calls": [ {id,name,arguments(dict)} ], "usage": {in,out}, "raw": any }
    Tool calls use OpenAI-style schemas. The offline provider emits deterministic plans.
    """
    m = active_mode()
    if m == "gateway":
        return _openai_compat_chat(
            base_url=GATEWAY_BASE_URL + "/v1" if not GATEWAY_BASE_URL.endswith("/v1") else GATEWAY_BASE_URL,
            api_key=GATEWAY_KEY,
            model=GATEWAY_MODEL,
            messages=messages, tools=tools,
            temperature=temperature, max_tokens=max_tokens,
        )
    if m == "openai":
        return _openai_compat_chat(
            base_url="https://api.openai.com/v1",
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            messages=messages, tools=tools,
            temperature=temperature, max_tokens=max_tokens,
        )
    return _offline_chat(messages=messages, tools=tools)


# ---------- OpenAI-compatible path (gateway or OpenAI) ----------

def _openai_compat_chat(base_url, api_key, model, messages, tools, temperature, max_tokens):
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError(f"openai package not installed: {e}")
    client = OpenAI(base_url=base_url, api_key=api_key)
    kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    r = client.chat.completions.create(**kwargs)
    choice = r.choices[0].message
    out = {"text": choice.content or "", "tool_calls": [], "usage": {}, "raw": r}
    if getattr(choice, "tool_calls", None):
        for tc in choice.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {"_raw": tc.function.arguments}
            out["tool_calls"].append({"id": tc.id, "name": tc.function.name, "arguments": args})
    if getattr(r, "usage", None):
        out["usage"] = {"in": r.usage.prompt_tokens, "out": r.usage.completion_tokens}
    return out


# ---------- Offline deterministic provider ----------

def _offline_chat(messages, tools):
    """Rule-based mock. Looks at the LAST USER message to pick a tool, if any.
    Enough to run every lab in this folder without any key.
    """
    user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_text = m.get("content") or ""
            break
    q = (user_text or "").lower()

    # Build a small "memory" view from prior user turns so the offline provider
    # can demo the point of Lab 1 (memory really does help).
    prior_user_text = " \n ".join(
        (m.get("content") or "") for m in messages[:-1] if m.get("role") == "user"
    )
    pmem = prior_user_text  # keep case for name capture
    pmem_low = pmem.lower()

    def _recall_name():
        import re
        m = re.search(r"\b(?:my name is|i am|i'm)\s+([A-Z][a-z]+)", pmem)
        return m.group(1) if m else None

    def _recall_plan():
        import re
        m = re.search(r"\b(platinum|gold|prepaid[\s\w]*|postpaid[\s\w]*)\b", pmem_low)
        if m: return m.group(1).title().strip()
        return None

    # "What is my name / plan" — answerable only if prior turns stated them.
    if any(k in q for k in ["my name", "who am i", "what plan", "which plan", "am i on", "remember"]):
        name = _recall_name()
        plan = _recall_plan()
        if name or plan:
            bits = []
            if name: bits.append(f"your name is {name}")
            if plan: bits.append(f"you are on the {plan} plan")
            return {"text": "From what you told me: " + " and ".join(bits) + ".",
                    "tool_calls": [], "usage": {"in": 25, "out": 20}, "raw": None}
        # No history was given.
        return {"text": "I don't know — you have not told me yet.",
                "tool_calls": [], "usage": {"in": 15, "out": 15}, "raw": None}

    tool_names = [t["function"]["name"] for t in (tools or [])]

    def _tc(name, args):
        return {"id": "call_offline_1", "name": name, "arguments": args}

    # If a tool-result just came back, write a short final answer.
    if messages and messages[-1].get("role") == "tool":
        prev_result = messages[-1].get("content") or ""
        return {"text": _summarise_result(prev_result), "tool_calls": [], "usage": {"in": 20, "out": 30}, "raw": None}

    # Try to match to tools.
    if "reset_sim" in tool_names and ("reset" in q or "reactivate" in q) and "sim" in q.replace("esim", ""):
        emp = _find_pattern(user_text, r"EMP-\d{4}") or "EMP-1021"
        return {"text": "", "tool_calls": [_tc("reset_sim", {"user_id": emp})], "usage": {"in": 25, "out": 15}, "raw": None}
    if "update_ticket" in tool_names and any(k in q for k in ["add note", "update ticket", "comment on ticket", "close ticket"]):
        tkt = _find_pattern(user_text, r"TKT-\d{4}") or "TKT-0004"
        return {"text": "", "tool_calls": [_tc("update_ticket", {"ticket_id": tkt, "note": "Investigated. See KB."})], "usage": {"in": 25, "out": 15}, "raw": None}
    if "get_ticket" in tool_names and ("ticket" in q or re.search(r"TKT-\d{4}", user_text or "", re.I)):
        tkt = _find_pattern(user_text, r"TKT-\d{4}") or "TKT-0004"
        return {"text": "", "tool_calls": [_tc("get_ticket", {"ticket_id": tkt})], "usage": {"in": 25, "out": 15}, "raw": None}
    if "check_outage" in tool_names and any(k in q for k in ["outage", "down", "no network", "no signal"]):
        city = _find_pattern(user_text, r"\b(Chennai|Mumbai|Delhi|Bangalore|Hyderabad|Kolkata)\b", flags=re.I) or "Chennai"
        return {"text": "", "tool_calls": [_tc("check_outage", {"city": city.title()})], "usage": {"in": 25, "out": 15}, "raw": None}
    if "search_kb" in tool_names and any(k in q for k in ["how", "what", "fix", "error", "problem", "roaming", "esim", "activate", "plan", "upgrade", "slow", "data", "unable", "cannot", "can't", "billing", "invoice"]):
        return {"text": "", "tool_calls": [_tc("search_kb", {"query": user_text})], "usage": {"in": 25, "out": 15}, "raw": None}

    # Greeting / no tool
    if any(q.startswith(g) for g in ["hi", "hello", "hey", "good morning", "good evening"]):
        return {"text": "Hello — I am AskNova. Ask me anything about your NetNova account.", "tool_calls": [], "usage": {"in": 10, "out": 15}, "raw": None}

    # Fallback: no tool, generic answer.
    return {"text": "I would need more detail to help. Could you share a ticket number or describe the issue?", "tool_calls": [], "usage": {"in": 20, "out": 20}, "raw": None}


def _find_pattern(text, pat, flags=0):
    if not text:
        return None
    m = re.search(pat, text, flags)
    return m.group(0) if m else None


def _summarise_result(result_text: str) -> str:
    """Turn a tool result into a short natural-sounding answer, offline-only."""
    t = result_text.strip()
    if "status" in t.lower() and "priority" in t.lower():
        return f"Here is what I found on the ticket. {t[:220]}"
    if "ok" in t.lower() and ("reset" in t.lower() or "activated" in t.lower()):
        return "Done. The SIM has been reset. The user should restart the device."
    if "outage" in t.lower():
        return f"There is an active outage. {t[:200]}"
    if "KB-" in t or "article" in t.lower():
        return f"According to the knowledge base: {t[:260]}"
    return f"Here is what I found: {t[:260]}"


# ---------- tool-schema helper ----------

def tool_schema(name: str, description: str, params: dict) -> dict:
    """OpenAI-style tool schema wrapper. `params` is the JSON schema `properties` block."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": params, "required": list(params.keys())},
        },
    }
