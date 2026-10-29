"""Lab 1C — Swap dict for Redis. Same chat, different store.

Shows:
  - fakeredis works like real Redis (same commands) with no server to install.
  - Two different sessions see two different histories (per-user isolation).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner
from memory import RedisMemory

print(model_banner())
mem = RedisMemory()  # fakeredis under the hood

def chat_as(session_id, user_text):
    mem.add(session_id, "user", user_text)
    reply = chat(mem.history(session_id))
    mem.add(session_id, "assistant", reply["text"])
    return reply["text"]

print()
print("=== Session A: Anil ===")
print("BOT:", chat_as("sess-A", "Hi, I am Anil. I have the Platinum plan."))
print("BOT:", chat_as("sess-A", "What plan am I on?"))

print()
print("=== Session B: Ravi (different person, different session) ===")
print("BOT:", chat_as("sess-B", "Hi, I am Ravi. I have the Prepaid Smart plan."))
print("BOT:", chat_as("sess-B", "What plan am I on?"))

print()
print(f"Session A history: {len(mem.history('sess-A'))} turns")
print(f"Session B history: {len(mem.history('sess-B'))} turns")
print()
print("Each user got only their own turns. That is 'per-user memory'.")
