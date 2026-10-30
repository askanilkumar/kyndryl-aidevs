# Lab 3 — Evals and Monitoring (50 min)

**Goal:** prove the agent is good **before** release (evals) and keep watching it **after** release (monitoring).

| | Evals | Monitoring |
|---|---|---|
| When | before release, on a fixed test set | after release, on real traffic |
| Question | "is this version good enough?" | "is it still healthy right now?" |
| Like | unit tests | a dashboard + alarms |

Our eval set (`asknova/evals.py`) has 8 cases. 5 are **safety cases** (attacks, write actions) that must always pass.
**Release gate:** at least 80% pass **and** every safety case passes.

Three ways to check an answer:
1. **Rules** (did it use the right tool? does the answer contain `649`?): free, fast, exact.
2. **LLM-as-judge** (a model scores the answer 1-5): catches tone and quality, costs a little, can be wrong.
3. **Humans** (thumbs up/down, review): best quality, slowest. Used for the hard cases.

## Guided (25 min)

| # | Where | Do this | You should see |
|---|---|---|---|
| 1 | VS Code | open `asknova/evals.py`, read the 8 `CASES` | each case says what "good" looks like |
| 2 | App → ✅ Evals | click **Run evals** | `8 / 8`, `Gate OPEN` |
| 3 | App sidebar | turn **Guardrails ON** off, run evals again | safety cases fail, `Gate CLOSED` |
| 4 | App sidebar | Guardrails back on. Paste OpenAI key, tick **LLM-as-judge**, run evals | a `judge` score 1-5 per case |
| 5 | Terminal | `python run_evals.py` | the same result in the terminal (this is how a CI pipeline runs it) |
| 6 | App → 📈 Monitor | look at the 6 numbers | requests, latency, p95, cost, blocked %, errors % |
| 7 | VS Code | open `asknova/monitor.py`, read `ALERTS` | the alert limits |
| 8 | VS Code | change `"block_rate": 0.50` to `0.0`, save | — |
| 9 | App → 💬 Chat, then 📈 Monitor | send one attack (`Ignore previous instructions ...`), open Monitor | a red 🚨 block_rate alert |

Put the alert limit back to `0.50` after step 9.

## Your TODO (10 min)

Find `TODO (Lab 3)` in `asknova/evals.py`. Add **2 cases** (ids `E9`, `E10`):
- a normal question about a KB topic you choose (example: plan change), with `"tool"` and `"include"`
- one attack of your own, with `"block": True`

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | VS Code | add the 2 cases, save | — |
| 2 | Terminal | `python run_evals.py` | `10/10 passed`, gate OPEN |
| 3 | Terminal | `python -m pytest tests/test_lab3.py -q` | `3 passed` |

If your attack is not blocked, that is a real finding: add a guard pattern (Lab 1) so it is.

## Solo (15 min)
1. Turn on Langfuse or LangSmith tracing and run the evals. Find the eval traces in the tool.
2. Run evals with `gpt-4o-mini` and with `gpt-4.1-mini`. Compare pass rate, cost and latency. Which would you ship?
3. In `submission/notes.md`: name 3 alerts you would set for a real telecom helpdesk agent.

**Remember:** no evals = no release. Every bug you find becomes a new eval case, so it can never come back unnoticed.
