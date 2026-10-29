"""Lab 1B — Give the bot a memory with a plain dict.

Same two user turns as 1A, but now we save every turn into DictMemory
and send the whole history each time.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner
from memory import DictMemory

print(model_banner())
mem = DictMemory()
SESSION = "demo-user-anil"

def say(user_text: str) -> str:
    mem.add(SESSION, "user", user_text)
    # Send ALL past turns, not just the latest one.
    reply = chat(mem.history(SESSION))
    mem.add(SESSION, "assistant", reply["text"])
    return reply["text"]

print()
print("=" * 60)
print("Call 1")
print("=" * 60)
print("YOU: Hi, my name is Anil and I use the Platinum plan.")
print("BOT:", say("Hi, my name is Anil and I use the Platinum plan."))

print()
print("=" * 60)
print("Call 2")
print("=" * 60)
print("YOU: What is my name and which plan am I on?")
print("BOT:", say("What is my name and which plan am I on?"))

print()
print(f"Memory now holds {len(mem.history(SESSION))} turns:")
for i, m in enumerate(mem.history(SESSION), 1):
    print(f"  {i:>2}. {m['role']:>9}  |  {m['content'][:70]}")
