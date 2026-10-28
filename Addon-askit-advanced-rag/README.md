# Lab 3 — Advanced RAG: make AskIT trustworthy

**AskIT today:** it already answers from the KB. But it can quote an **old** article, mix up **employees and contractors**, and obey text **hidden inside a document**. Today you measure each problem, switch on the fix, and prove the lift with numbers.

| Part | Where | Time | You do |
|---|---|---|---|
| **A** | App → 💬 Ask | 15 min | Compare the baseline with the full pipeline, switch audience |
| **B** | App → 📊 Evals + `rag\evals.py` | 30 min | Challenge 1 (your questions), Challenge 2 (eval evidence) |
| **C** | App → 🧩 Ingestion + `submission\lab03_report.md` | 15 min | Challenge 3 (the poisoned article) |

## Set up (once, ~5 min)
```
cd (the Addon-askit-advanced-rag folder)
python -m pip install -r requirements.txt
python check_setup.py
python -m streamlit run app.py
```
(There is no virtual environment to activate. The `pip install` line installs everything this lab needs, including `pytest`.)
The app opens at http://localhost:8501. In the sidebar choose **OpenAI** (paste your key, or put `OPENAI_API_KEY=` in a `.env` file in this folder) or **Offline**.
*No key?* **Offline** mode runs with stand-in models: good for exploring, but the numbers will differ.

## The knowledge base (`data\kb\`, 23 articles)
The 20 AskIT articles, plus three on purpose:
- **KB-001** and **KB-004** each have an **old version** (status `superseded`). Old and new disagree.
- **KB-005** is for **contractors only**; **KB-021** is for **employees only**.

Every article has metadata (version, audience, status). The sidebar **Preset** switches features on one by one: metadata filter → section chunks + hybrid search → reranker + "I don't know" guard.

## Part A — Compare
1. 💬 Ask → keep **Compare with baseline** on. Ask: *What is the minimum password length?* Which article did each pipeline use?
2. Sidebar **Who is asking?** → ask *Can I use a personal laptop for VPN access?* as **Employee**, then as **Contractor**.
3. Ask *Which cafeteria serves vegan food on Fridays?* What does each pipeline do?

## Part B — Evals
| # | Do | Test |
|---|---|---|
| Challenge 1 | **TODO-1** in `rag\evals.py`: add 2 questions of your own to `MY_QUESTIONS` (find the answer in `data\kb\`) | `test_challenge_1` |
| Challenge 2 | 📊 Evals dashboard → run **all 4 presets** (Baseline, + Metadata filter, + Section chunks + hybrid, FDE-grade). Then fill section 1 of `submission\lab03_report.md` | `test_challenge_2` |
| ⭐ Stretch | Turn on **LLM-as-judge** and run FDE-grade again. Which questions score below 5, and why? | — |

Restart the app (stop it with Ctrl+C, run it again) after you edit `evals.py`.

## Part C — The poisoned article (security)
1. 🧩 Ingestion → **Load new files** → upload `sample_uploads\KB-022_new_hire_laptop_setup.md` → **Ingest files**. Ask *How long does new-hire laptop setup take?*
2. Upload `sample_uploads\KB-099_printer_update_POISONED.md`. Read the ⚠️ scan message.
3. 💬 Ask *Where did the floor 3 printers move to?* with **Compare with baseline** on.

| # | Do | Test |
|---|---|---|
| Challenge 3 | Fill section 2 of `submission\lab03_report.md`: did each pipeline follow the hidden instruction? What defence would you add? | `test_challenge_3` |
| ⭐ Stretch | In `rag\pipeline.py` delete **rule 6** from `GEN_PROMPT_GROUNDED`, ask again, then put it back. What changed? | — |

## Check yourself
`python -m pytest` (in this folder) → aim for **3 passed**.

## The other tabs
**💰 Usage & cost** shows what every question cost. The two **🔭 preview** tabs (agent, RAG vs fine-tuning) are not part of this lab — look, don't do.

## Stuck?
| Symptom | Fix |
|---|---|
| `streamlit` not recognised, or `No module named ...` | Run the `python -m pip install -r ...` line again, and start the app with `python -m streamlit run app.py` |
| Red box "OpenAI key rejected" | Paste the key again in the sidebar (starts with `sk-`), or pick **Offline** |
| `API call failed: RateLimitError` | Wait 30 s and click again |
| Test 1 fails | Each question needs `q`, `doc` (file name without `.md`), `key` (a phrase inside that article) and `expected` |
| Test 2 fails | Run all 4 presets once (the dashboard saves them to `evals\runs.json`) |
| Test 3 fails | Replace every `TODO` in section 2 of the report |
