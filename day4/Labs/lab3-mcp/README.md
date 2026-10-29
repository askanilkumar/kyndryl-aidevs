# Lab 3 — MCP (60 min)

**MCP = Model Context Protocol. A standard way to publish tools so any agent can call them.**

Guided (30 min) · Solo (20 min) · Notes & check (10 min).

---

## STEP 0

```
cd C:\Kyndryl\Day3-v2\Labs\lab3-mcp
```

---

## The big idea (3 min)

In Lab 2 the tool was a Python function **in the same process** as the agent. That is fine for a demo. Not fine when:
- The tool lives on another server.
- The tool is written in another language.
- Three different agents (yours, your partner's, Claude Desktop) all want the same tool.

**MCP** is a tiny protocol that solves this. Think USB-C for tools:
- One standard shape ("list tools", "call tool").
- Agents and tools can be built by different people, in different languages.
- Your agent code does not change when the tool moves.

Today we wrap one tool as a server (`mcp_server.py`), then our agent calls it over MCP. Same 4-step round trip as Lab 2 — the only thing that changes is **step 3**.

---

## Lab 3 — Guided (30 min)

| | |
|---|---|
| **What we do** | Wrap `search_kb` as an MCP server. Our agent calls it over MCP. |
| **Why** | You will meet MCP everywhere (Claude Desktop, VS Code, enterprise agents). This is what one looks like inside. |
| **Outcome** | You can show the server, the Inspector, and a tool call going through it. |
| **How** | 1 server file + 1 client file, both tiny. |

1. Open `mcp_server.py`. It is **~15 lines**. Read it. The `@mcp.tool()` decorator is the one new thing.
2. (Optional, nice-looking.) In a **second terminal** run the MCP Inspector — a web page that shows the tool list and lets you call tools manually:

```
fastmcp dev mcp_server.py
```

   Open the URL it prints (usually http://localhost:5173). You should see one tool `search_kb`. Click it, type a query, see the result.
   When done, press **Ctrl+C** to stop the Inspector.

3. In the main terminal, run the client. It launches the server as a subprocess, lists its tools, then runs a question:

```
python run_3.py
python run_3.py "What is the status of ticket TKT-0004?"
```

   The first question works (`search_kb` is exposed). The second one fails because `get_ticket` is NOT exposed yet — that is your solo.

**Where the magic is NOT:** compare `run_3.py` with Lab 2's `run_2a.py`. The 4-step shape is identical. Only step 3 changed — the tool now runs over MCP.

---

## Lab 3 — SOLO (20 min)

| | |
|---|---|
| **What we do** | Expose `get_ticket` as a second MCP tool. |
| **Why** | Adding a tool to a server is almost nothing. You should feel how small the change is. |
| **Outcome** | The ticket question in step 3 now works through MCP. |
| **How** | Delete 2 `#` characters, save, run. |

1. Open `mcp_server.py`. Find the block marked **SOLO 3**. Delete the two `#` characters in front of `@mcp.tool()` and the function body. Save.
2. Run the ticket question again:

```
python run_3.py "What is the status of ticket TKT-0004?"
```

   You should see the server now advertises 2 tools, and the ticket is returned.

3. (Optional) relaunch the Inspector (`fastmcp dev mcp_server.py`) and click the new tool.
4. Fill in `submission\notes.md` (**Solo 3** section).

**Check:**

```
python check.py
```

4 tests should pass.

**Stuck for 10 min?** Open `..\..\Hints\lab3_hints.md`.

---

## What you learned

- MCP = tool-over-a-wire. Same shape as Lab 2 (request → run → result).
- `@mcp.tool()` publishes a Python function as an MCP tool.
- The **Inspector** is the browser view of any MCP server — great for showing a client.
- Changing an agent's tool from "local function" to "MCP tool" changes **step 3 only**.
