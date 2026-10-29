"""Lab 1A — The bot forgets. (Run this first.)

We talk to the model TWICE in a row and show that the second call has no idea
what the first one said. Then we fix it in run_1b.py.
"""

import sys
from pathlib import Path

# make common/ importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner

print(model_banner())
print()
print("=" * 60)
print("Call 1  (we tell the bot our name)")
print("=" * 60)

r1 = chat([{"role": "user", "content": "Hi, my name is Anil and I use the Platinum plan."}])
print("BOT:", r1["text"])

print()
print("=" * 60)
print("Call 2  (we ask what the bot remembers)")
print("=" * 60)

# NOTE: we do NOT pass the first turn here. Fresh call, no memory.
r2 = chat([{"role": "user", "content": "What is my name and which plan am I on?"}])
print("BOT:", r2["text"])

print()
print("See the problem? The bot cannot answer because it was never told again.")
print("Fix this in run_1b.py.")
