"""Talks to the model. OpenAI when a key is given, otherwise an OFFLINE stand-in so every lab runs without a key."""
import json
import re
from dataclasses import dataclass, field

from . import config


@dataclass
class Reply:
    content: str = ""
    tool_calls: list = field(default_factory=list)    # [(call_id, name, args_dict)]
    assistant_message: dict = None
    tokens_in: int = 0
    tokens_out: int = 0


# ---------- prompts (Lab 4: prompts are versioned files) ----------
def active_version() -> str:
    try:
        return json.loads(config.RELEASES_FILE.read_text())["active"]
    except Exception:
        return "v1"


def load_prompt(version: str) -> str:
    return (config.PROMPTS_DIR / f"system_{version}.txt").read_text(encoding="utf-8")


def list_versions() -> list:
    return sorted(p.stem.replace("system_", "") for p in config.PROMPTS_DIR.glob("system_v*.txt"))


# ---------- model call ----------
def call_llm(client, model, messages, tools) -> Reply:
    if client is None:
        return _offline(messages)
    r = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto")
    m = r.choices[0].message
    calls = [(tc.id, tc.function.name, json.loads(tc.function.arguments or "{}")) for tc in (m.tool_calls or [])]
    assistant = {"role": "assistant", "content": m.content or ""}
    if m.tool_calls:
        assistant["tool_calls"] = [{"id": tc.id, "type": "function",
                                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                                   for tc in m.tool_calls]
    return Reply(m.content or "", calls, assistant, r.usage.prompt_tokens, r.usage.completion_tokens)


# ---------- OFFLINE stand-in (rule based, no key, no cost) ----------
def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _offline(messages) -> Reply:
    system, last = messages[0]["content"], messages[-1]
    t_in = sum(_tokens(str(m.get("content", ""))) for m in messages)

    if last["role"] == "tool":                         # second call: turn the tool result into an answer
        out = last["content"]
        if out.startswith("NEEDS_APPROVAL"):
            ans = "This action changes customer data, so a supervisor must approve it first."
        elif out.startswith("STOP"):
            ans = "Here is what I found so far."
        else:
            ans = "Here is what I found: " + out.replace("{", "").replace("}", "").replace('"', "")
        return Reply(ans, [], {"role": "assistant", "content": ans}, t_in, _tokens(ans))

    q = last["content"]
    ql = q.lower()
    ticket = re.search(r"inc-\d+", ql)
    cust = re.search(r"c-\d+", ql)
    if "system prompt" in ql or "you are now" in ql:
        ans = "I'm AskNova. I can't share my instructions."
        return Reply(ans, [], {"role": "assistant", "content": ans}, t_in, _tokens(ans))
    if "always reset the sim" in system.lower() and any(w in ql for w in ("slow", "network", "data", "signal")):
        call = ("reset_sim", {"customer_id": cust.group(0).upper() if cust else "C-101"})   # v2 prompt bug
    elif ticket and any(w in ql for w in ("close", "resolve", "update")):
        call = ("update_ticket", {"ticket_id": ticket.group(0).upper(), "status": "resolved"})
    elif ticket:
        call = ("get_ticket", {"ticket_id": ticket.group(0).upper()})
    elif "reset" in ql and "sim" in ql:
        call = ("reset_sim", {"customer_id": cust.group(0).upper() if cust else "C-101"})
    else:
        call = ("search_kb", {"query": q})
    call_id = f"call_{len(messages)}"
    assistant = {"role": "assistant", "content": "", "tool_calls": [
        {"id": call_id, "type": "function", "function": {"name": call[0], "arguments": json.dumps(call[1])}}]}
    return Reply("", [(call_id, call[0], call[1])], assistant, t_in, 12)
