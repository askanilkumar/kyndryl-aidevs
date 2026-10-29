# Day 3 — Hints and full answers

Only open this when you have been stuck for **10 minutes**. Try the lab first.

---

## Lab 1 — Memory

### Solo 1
In `solo_1.py` change:

```python
mem = RedisMemory()
```

to:

```python
mem = RedisMemory(max_messages=6)
```

Nothing else. The trim lives in `RedisMemory.add` (`self.r.ltrim(k, -self.max_messages, -1)`).

**What you should see:** when the final question "list every fact" runs, only the last 6 messages are in the context sent to the model. The bot can only recall the facts in those 6.

---

## Lab 2 — Tool calling

### Solo 2 — matching ids
Pick any question that triggers a tool. Example:

```
python run_2a.py "What is the status of TKT-0004?"
```

Scroll up to STEP 2 — you see:

```
id   = call_abc123xyz
```

STEP 3 does not print the id directly, but STEP 2's id is also the one used in the `tool_call_id` field we send back. So **id_toolUse** and **id_toolResult** are the SAME string: `call_abc123xyz`.

In offline mode the id is always `call_offline_1`.

---

## Lab 3 — MCP

### Solo 3 — expose get_ticket
In `mcp_server.py`, these two lines are commented out:

```python
# @mcp.tool()
# def get_ticket(ticket_id: str) -> str:
#     """Read one NetNova support ticket, e.g. TKT-0004."""
#     return _get_ticket(ticket_id)
```

Delete the two `# ` characters in front of `@mcp.tool()` and the three function lines so it looks like:

```python
@mcp.tool()
def get_ticket(ticket_id: str) -> str:
    """Read one NetNova support ticket, e.g. TKT-0004."""
    return _get_ticket(ticket_id)
```

Save. `python run_3.py "What is the status of TKT-0004?"` now works.

---

## Lab 4 — Agent loop

### TODO-2 — needs_approval (one line)

```python
def needs_approval(tool_name: str, arguments: dict) -> bool:
    return is_write_tool(tool_name)
```

### TODO-1 — run_agent (full body)

Replace the entire body of `run_agent` with this:

```python
def run_agent(question: str, verbose: bool = True) -> dict:
    messages = [
        {"role": "system", "content":
            "You are AskNova, NetNova telecom's helpdesk agent. "
            "Use the tools when they help. Keep answers short."},
        {"role": "user", "content": question},
    ]
    seen_calls: set[tuple] = set()
    total_in = total_out = 0
    final_text = ""
    steps_used = 0

    for step in range(1, MAX_STEPS + 1):
        steps_used = step

        # PART A: ask the model
        resp = chat(messages, tools=TOOLS_IN_USE)
        total_in += resp["usage"].get("in", 0)
        total_out += resp["usage"].get("out", 0)
        if verbose:
            print(f"\nSTEP {step}  (step limit {MAX_STEPS})")

        # PART C: no tool calls -> final answer
        if not resp["tool_calls"]:
            final_text = resp["text"]
            if verbose:
                print(f"  final: {final_text}")
            break

        # PART B: run each tool call
        # record the model's turn
        messages.append({"role": "assistant", "tool_calls": [{
            "id": tc["id"], "type": "function",
            "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])},
        } for tc in resp["tool_calls"]]})

        for tc in resp["tool_calls"]:
            sig = (tc["name"], json.dumps(tc["arguments"], sort_keys=True))
            if STOP_ON_REPEAT and sig in seen_calls:
                if verbose:
                    print(f"  REPEAT detected: {tc['name']}({tc['arguments']}) — handing over.")
                final_text = "I kept calling the same tool. A human will take over."
                return {"answer": final_text, "steps": steps_used,
                        "tokens_in": total_in, "tokens_out": total_out}
            seen_calls.add(sig)

            if verbose:
                print(f"  tool: {tc['name']}({tc['arguments']})")
            result = run_tool_safely(tc["name"], tc["arguments"])
            if verbose:
                print(f"  result: {result[:200]}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    else:
        if verbose:
            print(f"\n  step limit hit — handing over to a human.")

    return {
        "answer": final_text or "I could not answer in time. A human will take over.",
        "steps": steps_used,
        "tokens_in": total_in,
        "tokens_out": total_out,
    }
```

### Solo 4 — wire check_outage
In `agent.py`:

```python
TOOLS_IN_USE = TOOL_SCHEMAS
```

Change to:

```python
TOOLS_IN_USE = TOOL_SCHEMAS_WITH_OUTAGE
```

Save. The schema was pre-built in `common/tools.py` and the dispatcher already knows the function. Three edits total: schema list, run the question, write note.
