# Lab 1 — Memory for a chatbot (60 min, 3 parts)

**Lab 1A: see the problem (10 min) · Lab 1B: dict memory (10 min) · Lab 1C: Redis memory (10 min) · Solo (20 min)**

---

## STEP 0. Open the right folder (do this first)

**We are doing Lab 1 now.**

1. Open **VS Code** → **File** → **Open Folder**.
2. Paste this path and click **Select Folder**:

```
C:\Kyndryl\Day3-v2\Labs\lab1-memory
```

3. Open a terminal (**Terminal** → **New Terminal**). The prompt must end with `lab1-memory`. If not, do step 2 again.
4. Make sure Day 3 setup is done once at the top folder:

```
cd C:\Kyndryl\Day3-v2
python -m pip install -r requirements.txt
copy .env.example .env
python check_setup.py
```

Then come back:

```
cd Labs\lab1-memory
```

---

## The big idea (2 min)

A plain chat call is **stateless**. The model knows nothing between calls.

To make it feel like a conversation, YOU must send the past turns every time. Those past turns are "memory".

Where you keep them matters:
- **A Python dict** — easy, dies on restart, not shared, no production value.
- **Redis** — survives restarts, shared between processes, same simple API. We use `fakeredis` so no Redis server to install today.

---

## Lab 1A — Watch the bot forget (10 min)

| | |
|---|---|
| **What we do** | Call the model twice. Second call gets no history. |
| **Why** | Prove to ourselves that the model has no memory of its own. |
| **Outcome** | You can say in one sentence why a bot "forgets". |
| **How** | `python run_1a.py` |

Run it:

```
python run_1a.py
```

You should see the bot answer the first call, then struggle on the second. Note how it had no way to know your name or plan.

---

## Lab 1B — Dict memory (10 min)

| | |
|---|---|
| **What we do** | Save every turn into a Python dict, send the whole history every call. |
| **Why** | Smallest possible memory. One class with 3 methods: `add`, `history`, `clear`. |
| **Outcome** | The bot answers "what plan am I on?" correctly. |
| **How** | `python run_1b.py` |

1. Open `memory.py`. Read `DictMemory` — it is 10 lines. Nothing to edit here.
2. Run it:

```
python run_1b.py
```

3. The second answer should now mention **Platinum** and **Anil**. The script also prints the full memory at the end.

---

## Lab 1C — Redis memory (10 min)

| | |
|---|---|
| **What we do** | Replace the dict with Redis (fakeredis). Same chat, same methods. |
| **Why** | In production you want memory that survives restarts and is shared across all your API workers. Redis is the usual answer. |
| **Outcome** | Two users (sess-A, sess-B) hold two separate histories. |
| **How** | `python run_1c.py` |

1. In `memory.py` read `RedisMemory`. One LIST per session key `askit:mem:<id>`. Each entry is JSON.
2. Run:

```
python run_1c.py
```

3. Check the last lines: both sessions have 4 turns, and neither saw the other's name.

---

## Lab 1 SOLO — Cap the memory (20 min)

| | |
|---|---|
| **What we do** | Make Redis keep only the **last 6 messages** so cost does not grow with the chat. |
| **Why** | Without a cap, every turn is more expensive than the last. The hard rule "last N messages" is the simplest safe cap. |
| **Outcome** | A chat that stays cheap and still feels contextual. |
| **How** | Edit **one argument** in `solo_1.py`, run it, write 2 lines in notes. |

1. Read `memory.py` — the trim logic is already written (two lines in `RedisMemory`). You do not change `memory.py`.
2. Open `solo_1.py`. Find:

```python
mem = RedisMemory()
```

3. Change it to:

```python
mem = RedisMemory(max_messages=6)
```

4. Save and run:

```
python solo_1.py
```

5. The bot was given 6 facts and then asked to list "every fact". With the cap on, the earlier facts are gone from memory before the final question is sent.
6. Fill in `submission\notes.md` (**Solo 1** section): what did the bot remember? What did it forget? What would happen with `max_messages=2`?

**Stretch (do only if ahead):** change the cap to 2 and run again. Note the difference.

**Run the tests:**

```
python check.py
```

Six tests should pass.

---

## When you are finished

1. `python check.py` → 6 passed.
2. Every `<fill>` in `submission\notes.md` is replaced.
3. Say in your own words what Redis gives you that a dict does not.

**Stuck for 10 min?** Open `..\..\Hints\lab1_hints.md`. It has the full answer.

---

## What you learned

- The model has **no memory** — you build it.
- **One class** (`add`, `history`, `clear`) hides two very different stores.
- **Session id** separates one user from another — never share a key.
- **Cap it**. Otherwise cost grows forever.
