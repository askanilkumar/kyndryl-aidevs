# Day 5 — AskNova goes to Production

One app, five labs. You take the AskNova agent from Day 4 and make it **safe, visible, tested, releasable and deployed**.

```
   Lab 1          Lab 2           Lab 3            Lab 4            Lab 5
 Guardrails  ->  Tracing   ->  Evals + Monitor -> Release (LLMOps) -> Cloud (Azure + AWS)
 "is it safe?"  "what did it do?" "is it good?"   "can I change it?"  "can others use it?"
```

## Rules for today
- **One app, one command:** `python -m streamlit run app.py`. Every lab uses a different tab of the same app.
- **Keys go in the app sidebar only** (or an OS env var on a server). Never put a key in a file in this folder.
- Each lab has **one TODO**. Stuck for more than 10 minutes? Open `Hints/lab_hints.md`.
- Each lab ends with a check: `python -m pytest tests/test_labN.py -q`. Green = done.

## Step 0 — Setup (10 min)

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | Terminal | `cd <your repo>\day5\Labs`  (example: `cd C:\Users\azureuser\training\kyndryl-aidevs\day5\Labs`) | prompt in the Labs folder |
| 2 | Terminal | `git pull` | `day5` files arrive |
| 3 | Terminal | `python -m pip install -r requirements.txt` | installs finish without red errors |
| 4 | Terminal | `python check_setup.py` | 6 × `ok` and `Agent test (offline): ok` |
| 5 | Terminal | `python -m streamlit run app.py` | browser opens http://localhost:8501 |
| 6 | App sidebar | paste your OpenAI key in **OpenAI API key** | `Mode: OpenAI · gpt-4o-mini` |
| 7 | App → 💬 Chat | ask `What is the status of INC-5001?` | an answer and a grey line with tools, tokens, cost, ms |

No key? Leave it empty: the app runs in **OFFLINE** mode (a rule-based stand-in). Every lab still works.

## The labs

| Lab | Time | Guide | App tab | One TODO in | Check |
|---|---|---|---|---|---|
| 1 Guardrails | 60 min | `lab1_guardrails.md` | 🛡️ Attack test | `asknova/guards.py` | `python -m pytest tests/test_lab1.py -q` |
| 2 Tracing (LangSmith + Langfuse) | 60 min | `lab2_tracing.md` | 💬 Chat + sidebar | `asknova/agent.py` | `python -m pytest tests/test_lab2.py -q` |
| 3 Evals + Monitoring | 50 min | `lab3_evals_monitoring.md` | ✅ Evals, 📈 Monitor | `asknova/evals.py` | `python -m pytest tests/test_lab3.py -q` |
| 4 LLMOps / AgentOps | 40 min | `lab4_llmops.md` | 🚀 Release | `prompts/system_v2.txt` | `python -m pytest tests/test_lab4.py -q` |
| 5 Deploy to cloud | 90 min | `lab5_deploy.md` | the same app, on a public URL | no code change | open the URL |

After each lab: write 2 lines in `submission/notes.md` (what you did, what you learnt).

## Where things are

| File | What it is |
|---|---|
| `app.py` | the Streamlit app (5 tabs) |
| `asknova/agent.py` | the agent loop: guard → LLM → tool → LLM → guard |
| `asknova/guards.py` | Lab 1: input guard, PII masking, output guard |
| `asknova/tracing.py` | Lab 2: sends every step to LangSmith or Langfuse |
| `asknova/evals.py` | Lab 3: the test cases and the release gate |
| `asknova/monitor.py` | Lab 3: request log + alert rules |
| `asknova/release.py`, `prompts/` | Lab 4: versioned prompts, release, rollback |
| `deploy/asknova.service` | Lab 5: runs the app as a service on AWS EC2 |
| `tests/` | one check file per lab |
| `Hints/lab_hints.md` | full answers for every TODO |
