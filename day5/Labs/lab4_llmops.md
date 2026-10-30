# Lab 4 — LLMOps / AgentOps: release a prompt safely (40 min)

**Goal:** treat a prompt like code. Change → test → release → roll back if needed.

In normal software, nobody edits code on the live server. For AI apps the "code" is also the **prompt**, the **model** and the **tools**. A small prompt change can break the agent. So:

```
 edit prompt v2  ->  run evals  ->  gate OPEN?  -- yes -> release v2 (live)
                                         |
                                         no  -> rejected, v1 stays live
 problem in production? -> roll back to the last good version in 1 click
```

| LLMOps / AgentOps habit | In our app |
|---|---|
| Version everything | `prompts/system_v1.txt`, `system_v2.txt` |
| Test before release | the eval gate from Lab 3 |
| Record every release | `releases.json` (history) |
| Fast rollback | **Roll back** button |
| Watch after release | 📈 Monitor (prompt version is logged with every request) |
| Control cost | model choice + tokens per answer (Lab 2 traces) |

## Guided (20 min)

| # | Where | Do this | You should see |
|---|---|---|---|
| 1 | App → 🚀 Release | read the 2 prompts side by side | v2 adds a new rule and a closing line |
| 2 | 🚀 Release | pick `v2`, click **Run evals and release v2** | `v2: REJECTED`, safety FAILED, E1 tried `reset_sim` |
| 3 | 🚀 Release | look at the history table | v2 is recorded as rejected, live version is still v1 |
| 4 | App sidebar | choose Prompt version `v2`, ask in Chat `I am C-101, my data is slow` | the agent tries a SIM reset (needs approval) — this is the bug |
| 5 | Terminal | `python run_evals.py v2` | the same failure, exit code 1 (a pipeline would stop here) |

## Your TODO (10 min)

The bad rule is in `prompts/system_v2.txt`: *"Always reset the SIM when a customer reports slow data..."*.
A SIM reset is a **write action**. The agent must never do it just because data is slow.

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | VS Code | open `prompts/system_v2.txt`, replace the bad rule with a safe one (search the help articles first) | — |
| 2 | 🚀 Release | **Run evals and release v2** | `v2: APPROVED`, live version = v2 |
| 3 | Terminal | `python -m pytest tests/test_lab4.py -q` | `2 passed` |
| 4 | 🚀 Release | click **Roll back to the previous version** | live version = v1 again |

## Solo (10 min)
1. Release v2 again. Ask 3 questions in Chat. In 📈 Monitor, check the `prompt` column: which version answered?
2. Make a `prompts/system_v3.txt` that answers in Hindi or Tamil if the customer writes in it. Release it through the gate.
3. In `submission/notes.md`: what else should be versioned and gated, besides the prompt? (hint: model, tools, guard patterns, KB)

**Remember:** "It worked on my laptop" is not a release process. Version → eval gate → release → monitor → rollback.
