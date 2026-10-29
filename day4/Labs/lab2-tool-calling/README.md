# Lab 2 — Tool calling (60 min)

**The model does not run anything. It only asks. You run it.**

Guided (30 min) · Solo (20 min) · Notes & check (10 min).

---

## STEP 0

```
cd C:\Kyndryl\Day3-v2\Labs\lab2-tool-calling
```

Prompt must end with `lab2-tool-calling`. The provider and tools are shared from `..\..\common\`.

---

## The big idea (3 min)

```
you ask a question
  -> model replies: please run `search_kb({"query": "..."})`      (a REQUEST)
  -> YOUR code runs the Python function
  -> you give the result back to the model with the SAME id
  -> model reads it and writes the final answer
```

Three facts to burn in:
1. The model never executes code. It writes a request.
2. You pick the schema (name, description, parameters). The description is how the model picks.
3. The `tool_call_id` on the way out must match on the way back — like a return address.

The 4 NetNova tools you already have in `..\..\common\tools.py`:

| Name | Reads or writes? |
|---|---|
| `search_kb` | reads |
| `get_ticket` | reads |
| `update_ticket` | writes |
| `reset_sim` | writes |

---

## Lab 2 — Guided (30 min)

| | |
|---|---|
| **What we do** | Run one tool call by hand. See all 4 steps printed. |
| **Why** | After this lab you can read any framework's "agent" and know exactly what it does inside. |
| **Outcome** | You can explain who runs the tool, and why ids must match. |
| **How** | `python run_2a.py "<question>"` |

1. Read `run_2a.py` — about 50 lines, no magic.
2. Run the default:

```
python run_2a.py
```

   You should see 4 printed steps.

3. Now try each of these. **Before you run each one, say out loud which tool the model will ask for.**

```
python run_2a.py "How do I activate my eSIM?"
```

```
python run_2a.py "Hi"
```

```
python run_2a.py "Reset the SIM for EMP-1021"
```

   - `activate eSIM` → `search_kb`
   - `Hi` → **no tool** at all (model answers directly)
   - `Reset the SIM` → `reset_sim`. **Look at step 3: our code ran it immediately with no approval.** We fix this in Lab 4.

---

## Lab 2 — SOLO (20 min)

| | |
|---|---|
| **What we do** | Pick 3 of your own questions. Predict the tool. Run and compare. |
| **Why** | Tool choice is driven by **the description**, not magic. Writing bad descriptions is the #1 bug. |
| **Outcome** | You can tell when a tool choice went wrong, and why. |
| **How** | Pick, predict, run, write notes. |

1. Write 3 NetNova helpdesk questions in `submission\notes.md` under **Solo 2**. For each, write the tool you expect.
   Examples (make up your own):
   - "What is my bill for last month?" — expect `search_kb` (no billing tool) or no tool.
   - "Show me ticket TKT-0008." — expect `get_ticket`.
   - "Please note on TKT-0001 that user was charged twice." — expect `update_ticket`.
2. Run each one through `run_2a.py` and record what actually happened.
3. **Then run one more time with `--raw`** style — pick any one question and copy the `id` from STEP 2 and from STEP 3's tool result into notes. They **must** match. (Autograder checks it.)

   To get both ids visible, just scroll up — step 2 and step 3 both print `id = ...` and `tool_call_id = ...` (the second one is the id you echo back).

4. Fill `submission\notes.md`:
   - 3 question/tool predictions and the actual result
   - `id_toolUse` and `id_toolResult` (same string)
   - One line: when did the model NOT pick a tool you expected? why?

**Check:**

```
python check.py
```

6 tests should pass. If `test_tool_ids_match_in_notes` fails, your two ids don't match — recopy them.

**Stuck for 10 min?** Open `..\..\Hints\lab2_hints.md`.

---

## What you learned

- The round trip: request → run → result → answer.
- The **id** that keeps request and result paired.
- **Descriptions decide** which tool the model picks.
- Writes with no safety check are a bug waiting to happen (fixed in Lab 4).
