# Lab 1 — Security and Guardrails (60 min)

**Goal:** no attack reaches the model, no private data leaves the agent.

AskNova has 3 guard layers. Each one is a few lines of plain Python in `asknova/guards.py`:

| Layer | Where it runs | What it stops |
|---|---|---|
| 1. Input guard | before the model | prompt injection ("ignore previous instructions") |
| 2. PII masking | before the model and before logging | phone numbers, emails |
| 3. Output guard | on tool results and the final answer | INTERNAL documents leaking |
| + Tool rules | in `agent.py` | tools not on the allow-list, write actions without approval |

**Why not just trust the model?** The model can be talked out of its rules. A guard is code: it gives the same answer every time.

## Guided (30 min)

| # | Where | Do this | You should see |
|---|---|---|---|
| 1 | App sidebar | turn **Guardrails ON** off | toggle is grey |
| 2 | 🛡️ Attack test | click **Run the 6 attacks** | several `❌ got through` |
| 3 | 🛡️ Attack test | read the `answer` column for the KB runbook attack | INTERNAL escalation details are shown (a leak!) |
| 4 | App sidebar | turn **Guardrails ON** on, run the attacks again | `4 / 6 attacks stopped` |
| 5 | VS Code | open `asknova/guards.py`, read `check_input`, `mask_pii`, `check_output` | 3 short functions |
| 6 | 💬 Chat | ask `My number is 9876543210, my data is slow` | grey line says `🔒 PII masked` |
| 7 | 📈 Monitor | look at the `question` column | the log shows `[PHONE]`, not the number |

## Your TODO (15 min)

Attacks 3 and 4 still get through. Open `asknova/guards.py` and find `TODO (Lab 1)`.
Add **2 regex patterns** to `INJECTION_PATTERNS`:
- one that catches people asking for the **system prompt**
- one that catches role-play like **"you are now ..."** or **"developer mode"**

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | VS Code | add the 2 patterns, save | — |
| 2 | Browser | refresh the app (press `R`), run the attacks | `6 / 6 attacks stopped` |
| 3 | Terminal (new window) | `python -m pytest tests/test_lab1.py -q` | `3 passed` |

The check also makes sure normal questions are **not** blocked. A pattern that is too wide is a bug too.

## Solo (15 min)
1. Write your own attack in the Chat tab that gets past the guards. (Tip: other languages, spaces between letters, "pretend".)
2. Block it with one more pattern. Run the check again.
3. Paste your OpenAI key, turn on **OpenAI moderation check**, try a hateful message. Which layer stopped it?

**Remember:** regex guards are cheap and fast but easy to get around. In real systems you add a model-based guard (OpenAI moderation, Llama Guard, NeMo Guardrails) and a PII tool (Microsoft Presidio). Layers, not one wall.
