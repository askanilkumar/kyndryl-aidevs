# Kyndryl Day 3 (v2) — Memory · Tool calling · MCP · Agent

**One-day coaching session, 1:1 format. 2:00 — 8:00 PM.**

- Trainer runs the session page from `Content\index.html` (no slides).
- Participant works through 4 labs in `Labs\lab1-memory`, `lab2-tool-calling`, `lab3-mcp`, `lab4-agent-loop`.
- Each lab = one README, 2-3 Python files, 1 TODO, 4-6 tests, hints.
- Hints and full answers in `Hints\lab_hints.md`.

## Participant setup (once)

```
cd C:\Kyndryl\Day3-v2
python -m pip install -r requirements.txt
copy .env.example .env
```

Fill in **either** `GATEWAY_BASE_URL + GATEWAY_KEY` **or** `OPENAI_API_KEY`. If neither is filled, the labs still run in offline mode (deterministic stand-in, no cost).

Then check:

```
python check_setup.py
```

Should print `Model: ...` and end with `All set.`

## Rhythm per cycle (60 min)

- 10 min concept (trainer talks against the session page)
- 30 min guided lab (trainer + participant together)
- 20 min solo (participant alone, trainer available)

## Trainer prep (15 min)

- `python check_setup.py` on your laptop
- Open the session page in a browser side-by-side with VS Code
- Have `..\Hints\lab_hints.md` open in a second tab for yourself
