"""Lab 1 — SOLO challenge.

Goal: cap the history so the bot never pays for a huge context.
Keep only the LAST 6 messages per session, inside Redis itself.

TODO: Open `memory.py`. Find the two lines marked `Solo 1 fills this part in`
in RedisMemory.__init__ and RedisMemory.add. Do nothing new — read them, then
run this file. You should pass if max_messages is honoured.
(Spoiler: it is already wired up. Your real job: pass `max_messages=6` below
when creating the memory, watch the output, and explain in notes.md what you see.)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner
from memory import RedisMemory

print(model_banner())

# ---- SOLO TODO: change the next line to:    mem = RedisMemory(max_messages=6)
mem = RedisMemory()
SESSION = "solo-anil"

QUESTIONS = [
    "Hi, I am Anil, Platinum plan.",
    "My registered city is Chennai.",
    "I was born in 1980.",
    "I use an iPhone 15.",
    "My favourite colour is blue.",
    "I have a ticket TKT-0004.",
    "What do you remember about me? Please list every fact.",
]

for q in QUESTIONS:
    mem.add(SESSION, "user", q)
    reply = chat(mem.history(SESSION))
    mem.add(SESSION, "assistant", reply["text"])

print()
print(f"Total messages kept in memory: {len(mem.history(SESSION))}")
print("Last turn from the bot:")
print(mem.history(SESSION)[-1]["content"])
print()
print("With the cap OFF, memory grows every turn.")
print("With max_messages=6, Redis keeps only the last 6 — the bot forgets older facts.")
print("That is a design choice: cheaper + faster but less memory. Write about this in notes.md.")
