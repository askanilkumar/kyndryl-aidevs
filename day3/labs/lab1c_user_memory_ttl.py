"""LAB 1c - One memory PER USER, with a TTL, plus facts that last longer.

Two kinds of memory:
   short-term  chat:<user>:<session>   the conversation  (a LIST, expires in minutes)
   long-term   profile:<user>          facts about the customer (a HASH, expires in weeks)

RUN:   python lab1c_user_memory_ttl.py
THEN:  (1) change DEMO_TTL to 5 and watch the chat disappear.
       (2) change the session names so BOTH customers use "default". Are they still separate? Why?
       (3) set MAX_MESSAGES=4 in .env and run again. How many messages are kept?
"""
import time

from agentlib import memory

DEMO_TTL = 8     # seconds, just for the demo (real life: minutes)

# 1. two customers, SAME session name -> still separate because the user id is in the key
memory.add_message("cust-1001", "default", "user", "Hi, I am Ravi. My internet is slow.", ttl=DEMO_TTL)
memory.add_message("cust-1002", "default", "user", "Hello, I am Meena. I want to see my bill.", ttl=DEMO_TTL)
print("Ravi's chat :", [m["content"] for m in memory.get_history("cust-1001", "default")])
print("Meena's chat:", [m["content"] for m in memory.get_history("cust-1002", "default")])

# 2. long-term facts
memory.set_profile("cust-1001", name="Ravi", plan="Plus 499", city="Chennai")
print("\nRavi's profile:", memory.get_profile("cust-1001"))

# 3. what is in Redis?
print("\nKEYS (look: every key carries the user id, every key has a TTL)")
for row in memory.inspect_keys():
    print(f"  {row['key']:<28} type={row['type']:<5} items={row['items']}  ttl={row['ttl_s']}s")

# 4. TTL in action
print(f"\nWaiting {DEMO_TTL + 1} seconds for the chat to expire...")
time.sleep(DEMO_TTL + 1)
print("Ravi's chat after the TTL :", memory.get_history("cust-1001", "default"))
print("Ravi's profile (kept)     :", memory.get_profile("cust-1001"))

# 5. privacy: erase everything about one customer
deleted = memory.forget_user("cust-1001")
print(f"\nforget_user('cust-1001') deleted {deleted} key(s). Profile now:", memory.get_profile("cust-1001"))

from agentlib.habits import footer   # noqa: E402
footer()
