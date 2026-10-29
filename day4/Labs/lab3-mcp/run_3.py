"""Lab 3 — Call the MCP server.

Spawns `mcp_server.py` in a subprocess, lists its tools, then runs ONE question
through the same request/result flow we used in Lab 2 — but the tool now runs
INSIDE the MCP server, not in this process.

Usage:
    python run_3.py                                     # default question
    python run_3.py "What is the status of TKT-0004?"   # custom question
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner
from fastmcp import Client

HERE = Path(__file__).resolve().parent
SERVER = HERE / "mcp_server.py"


def _result_text(mcp_result) -> str:
    """Normalise fastmcp's CallToolResult into a plain string across versions."""
    # Newer fastmcp returns an object with .content (list of blocks) or .data
    content = getattr(mcp_result, "content", None)
    if content is None and isinstance(mcp_result, (list, tuple)):
        content = mcp_result
    if content:
        first = content[0]
        txt = getattr(first, "text", None)
        if txt is not None:
            return txt
    data = getattr(mcp_result, "data", None)
    if data is not None:
        return str(data)
    return str(mcp_result)


def mcp_tools_to_openai(mcp_tools) -> list[dict]:
    """FastMCP tool spec -> OpenAI-style schema the model expects."""
    out = []
    for t in mcp_tools:
        out.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {"type": "object", "properties": {}},
            },
        })
    return out


async def main(question: str):
    print(model_banner())
    print()

    async with Client(str(SERVER)) as client:
        # 1. Ask the server what tools it offers.
        tools = await client.list_tools()
        print("MCP SERVER advertises these tools:")
        for t in tools:
            print(f"  - {t.name}  ({t.description.splitlines()[0] if t.description else ''})")
        print()

        schemas = mcp_tools_to_openai(tools)

        # 2. Classic tool-call round trip.
        print("STEP 1 — your question")
        print("  ", question)

        messages = [
            {"role": "system", "content": "You are AskNova. Use tools when helpful."},
            {"role": "user", "content": question},
        ]
        first = chat(messages, tools=schemas)

        if not first["tool_calls"]:
            print()
            print("STEP 2 — model asked for no tool. Answer:")
            print("  ", first["text"])
            return

        call = first["tool_calls"][0]
        print()
        print(f"STEP 2 — model wants a tool  (over MCP)")
        print(f"  name = {call['name']}")
        print(f"  args = {call['arguments']}")

        # 3. Call the MCP server instead of a local function.
        mcp_result = await client.call_tool(call["name"], call["arguments"])
        tool_text = _result_text(mcp_result)

        print()
        print("STEP 3 — MCP SERVER ran the tool, returned:")
        print("  ", tool_text.replace("\n", "\n   ")[:400])

        # 4. Give the result back to the model.
        messages.append({"role": "assistant", "tool_calls": [{
            "id": call["id"], "type": "function",
            "function": {"name": call["name"], "arguments": json.dumps(call["arguments"])},
        }]})
        messages.append({"role": "tool", "tool_call_id": call["id"], "content": tool_text})
        second = chat(messages, tools=schemas)

        print()
        print("STEP 4 — final answer")
        print("  ", second["text"])


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How do I activate my new eSIM?"
    asyncio.run(main(q))
