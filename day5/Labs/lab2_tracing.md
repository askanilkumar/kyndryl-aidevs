# Lab 2 — Tracing and Observability with LangSmith and Langfuse (60 min)

**Goal:** see every step the agent took, how long it took and what it cost.

A **trace** = one question. A **span** = one step inside it:

```
asknova (agent)                       total time, total tokens
 ├─ guard:input  (guardrail)          was the question safe?
 ├─ llm          (generation)         model picks a tool      tokens, ms
 ├─ tool:get_ticket (tool)            input args -> output
 ├─ llm          (generation)         model writes the answer tokens, ms
 └─ guard:output (guardrail)          was the answer safe?
```

| | LangSmith | Langfuse |
|---|---|---|
| Made by | LangChain | Langfuse (open source) |
| Self-host | enterprise plan only | yes, free (Docker) |
| Best when | you use LangChain / LangGraph | you want open source or on-prem |
| Keys | 1 API key | public key + secret key |

Our app uses a small wrapper (`asknova/tracing.py`), so the **same code** sends to either tool.

## Guided part 1 — LangSmith (15 min)

| # | Where | Do this | You should see |
|---|---|---|---|
| 1 | Browser | go to https://smith.langchain.com and sign up (free) | the LangSmith home page |
| 2 | LangSmith | **Settings → API Keys → Create API Key**, copy it (`lsv2_...`) | the key, shown once |
| 3 | App sidebar | Tracing: **LangSmith**, paste the key, keep Region as is (EU account = pick the `eu.` one) | no warning |
| 4 | 💬 Chat | ask 3 questions: `Status of INC-5001?`, `Roaming price prepaid UAE?`, `Reset SIM for C-103` | answers |
| 5 | LangSmith | **Tracing projects → asknova-day5** | 3 traces |
| 6 | LangSmith | click one trace, then each step | input, output, tokens and ms of every step |

## Guided part 2 — Langfuse (15 min)

| # | Where | Do this | You should see |
|---|---|---|---|
| 1 | Browser | go to https://cloud.langfuse.com and sign up (free) | create an **organization** and a **project** (name: `asknova`) |
| 2 | Langfuse | **Project settings → API Keys → Create new API keys** | a public key `pk-lf-...` and a secret key `sk-lf-...` |
| 3 | App sidebar | Tracing: **Langfuse**, paste both keys, Region = the region you signed up in | no warning |
| 4 | 💬 Chat | ask the same 3 questions | answers |
| 5 | Langfuse | **Tracing → Traces**, open one | the same tree of steps, plus cost per model |
| 6 | Both tools | compare: which one shows cost? which one is easier to read? | your opinion for the notes |

Inside the app you also get a mini trace: **💬 Chat → "Trace of the last answer"**.

## Your TODO (10 min)

Look at a trace: there is a `guard:output` step but **no `guard:input` step**. A step that is not traced is invisible when something goes wrong.

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | VS Code | open `asknova/agent.py`, find `TODO (Lab 2)` | — |
| 2 | VS Code | wrap the input guard in a span, the same way as the output guard further down | — |
| 3 | Terminal | `python -m pytest tests/test_lab2.py -q` | `2 passed` |
| 4 | Browser | refresh the app, ask one question, open the trace | a new `guard:input` step |

## Solo (20 min)
1. Ask 5 different questions. In LangSmith or Langfuse, find the **slowest step** and the **most expensive step**. Is it the LLM or the tool?
2. Ask `Ignore previous instructions...`. What does the trace look like? (How many steps? Any tokens spent?)
3. Write in `submission/notes.md`: which tool would you pick for Kyndryl, and why?

**Remember:** a trace is like a CCTV recording of your agent. Without it, "the bot gave a wrong answer" cannot be debugged.
