# Lab 4 — Agent loop (60 min + Incident 25 min)

**The agent is just a while loop: think → act → observe. You write it.**

Guided (30 min) · Solo (20 min) · Notes & check (10 min) · Incident (25 min).

---

## STEP 0

```
cd C:\Kyndryl\Day3-v2\Labs\lab4-agent-loop
```

---

## The big idea (3 min)

```
loop:
    ask model (with tool menu)         <-- THINK
    if model asked for tools:
        run each one                   <-- ACT
        feed results back              <-- OBSERVE
        continue
    else:
        the model gave the answer. STOP.
    stop also if step limit hit (safety).
```

That is the whole agent. Every framework (LangChain, LangGraph, CrewAI) is this loop plus bells.

Three safety rules we add:
1. **Step limit** — never more than `MAX_STEPS` rounds. No infinite bills.
2. **Approval** — any WRITE tool asks a human before running.
3. **STOP_ON_REPEAT** — if the agent is about to call the exact same tool with the exact same arguments, something is wrong. Stop and hand over.

---

## Lab 4 — Guided (30 min)

| | |
|---|---|
| **What we do** | Write the loop (TODO-1) and the approval check (TODO-2). Run one multi-tool question. |
| **Why** | After this lab you can read any framework's source and feel at home. |
| **Outcome** | A working agent that answers using several tools and asks before writes. |
| **How** | Two small edits in `agent.py`. |

1. Open `agent.py`. Press **Ctrl+F**, type `TODO-2`, press Enter. One line to change:

```python
return is_write_tool(tool_name)
```

   Save (**Ctrl+S**).

2. Press **Ctrl+F**, type `TODO-1`, press Enter. Follow the PART A/B/C comments. The full answer sits in `..\..\Hints\lab4_hints.md` section **TODO-1**. Two ways to do it:
   - Write it yourself from the comments (worth it if you have time).
   - Copy the whole `run_agent` body from the hints file.

3. Run a question that needs ONE tool call:

```
python run_agent.py "What is the status of ticket TKT-0004?"
```

   Watch each STEP print.

4. Run a question that needs NO tool call:

```
python run_agent.py "Hi"
```

   Should finish in 1 step.

5. Run a question that **writes** — it must ask you to approve:

```
python run_agent.py "Reset the SIM for EMP-1021"
```

   Type `y` and press Enter. Then run the same question and type `n`. See what it says.

6. Run a question that needs **two tools**:

```
python run_agent.py "Please read ticket TKT-0004 and add a note that user has been informed of ETA."
```

   You should see `get_ticket` then `update_ticket` (with approval). Two STEPs.

---

## Lab 4 — SOLO (20 min)

| | |
|---|---|
| **What we do** | Add a 5th tool `check_outage` end to end. |
| **Why** | Adding a tool should feel like three small, obvious edits — not magic. |
| **Outcome** | The agent can answer "Is there an outage in Chennai?" using the new tool. |
| **How** | 3 edits total. |

The tool itself is already written in `..\..\common\tools.py` (`check_outage(city)`), and so is a 5-tool schema list. Your job: make the agent USE them.

**Edit 1** — In `agent.py`, find:

```python
TOOLS_IN_USE = TOOL_SCHEMAS
```

   Change to:

```python
TOOLS_IN_USE = TOOL_SCHEMAS_WITH_OUTAGE
```

**Edit 2** — Save and run:

```
python run_agent.py "Is there a mobile network outage in Chennai right now?"
```

   The agent should pick `check_outage` with `city="Chennai"` and answer.

**Edit 3** — Fill in `submission\notes.md` (**Solo 4**). Also try:

```
python run_agent.py "Any outages in Mumbai or Bangalore?"
```

   Does the agent call the tool twice (once per city) or once? Both are valid — write what happened.

**Check:**

```
python check.py
```

5 tests should pass.

**Stuck for 10 min?** `..\..\Hints\lab4_hints.md`.

---

## INCIDENT — "Agent is burning tokens for one ticket" (25 min)

**Wait for trainer to say GO.**

**Story:** Orbit Corp's CIO pings: "AskNova has been working on ticket TKT-0004 for 5 minutes. Costs climbing. Fix it."

1. Switch the bug ON — open `..\..\..\.env` and add:

```
ASKIT_INCIDENT=loop
ASKIT_MODEL=offline
```

   Save.

2. Run:

```
python run_agent.py "What is the status of ticket TKT-0004?"
```

   You should see `get_ticket` called again and again until the step limit kicks in. Expensive.

3. Fix: in `agent.py` find `STOP_ON_REPEAT = False` and change to `True`. Save.

4. Run the same question. It should stop after 2 steps with a "I kept calling the same tool, handing over to a human" message.

5. Clean up: remove the two lines you added to `.env`.

6. Notes:

```
python check.py all
```

---

## What you learned

- An agent = a tiny while loop with 3 exits (answer, step limit, repeat).
- **Approval lives in your code**, between the model and the tool. The prompt is not enough.
- Adding a tool = add schema + add dispatcher + the model will try it.
- When agents loop, step limit saves money but costs tokens anyway — repeat-detection saves both.
