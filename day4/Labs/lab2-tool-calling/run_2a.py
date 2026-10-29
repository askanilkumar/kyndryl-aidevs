"""Lab 2A — ONE tool call, by hand.

The model does NOT run any tool. It only asks for one.
We watch the whole round trip in 4 printed steps.

Usage:
    python run_2a.py
    python run_2a.py "What is the status of ticket TKT-0004?"
    python run_2a.py "Hi"
    python run_2a.py "Reset the SIM for EMP-1021"
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner
from tools import TOOL_SCHEMAS, run_tool

print(model_banner())
print()

question = " ".join(sys.argv[1:]) or "What is the status of ticket TKT-0004?"

print("STEP 1 — your question")
print("  ", question)

# ---- Call 1: send the question + the tool menu. The model may ask for a tool.
messages = [
    {"role": "system", "content": "You are AskNova, NetNova's helpdesk assistant. Use tools when they help."},
    {"role": "user", "content": question},
]
first = chat(messages, tools=TOOL_SCHEMAS)

if not first["tool_calls"]:
    # The model answered directly, no tool needed.
    print()
    print("STEP 2 — model asked for NO tool. It answered directly:")
    print("  ", first["text"])
    sys.exit(0)

call = first["tool_calls"][0]
print()
print("STEP 2 — model wants a tool")
print(f"  name = {call['name']}")
print(f"  args = {call['arguments']}")
print(f"  id   = {call['id']}")

# ---- Our code runs the tool. (The model never did.)
result = run_tool(call["name"], call["arguments"])

print()
print("STEP 3 — WE ran the tool, here is its output")
print("  ", result.replace("\n", "\n   "))

# ---- Call 2: give the result BACK to the model. Note the matching id.
messages.append({"role": "assistant", "tool_calls": [{
    "id": call["id"], "type": "function",
    "function": {"name": call["name"], "arguments": __import__("json").dumps(call["arguments"])},
}]})
messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})

second = chat(messages, tools=TOOL_SCHEMAS)

print()
print("STEP 4 — final answer")
print("  ", second["text"])
