"""LAB 3a - Save progress after every step, so a crash loses nothing.

RUN:   python lab3a_checkpoint_resume.py
THEN:  (1) change CRASH_AT to 0, then 2. Where does it crash? What does the checkpoint contain?
       (2) Look at the Redis key printed below. Why does it have a TTL?
"""
from agentlib import agent, memory

USER, SESSION = "cust-1001", "lab3a"
CRASH_AT = 1       # the process "dies" when it is about to run the tool at this step (0 = first tool, 1 = second)

print(f"Run 1: the agent will crash at step {CRASH_AT}\n")
st = agent.ask(USER, SESSION, "Check ticket TKT-2001 and tell me how to fix slow internet",
               flags={"crash_at": CRASH_AT})
print("crashed?      ", st["crashed"], "-", st.get("crash_message"))
print("events so far :", [e["node"] for e in st["events"]])

key = memory.ckpt_key(USER, SESSION)
print(f"\ncheckpoint key: {key}   ttl={memory.get_redis().ttl(key)}s")
ck = agent.load_checkpoint(USER, SESSION)
print("checkpoint says: phase =", ck["phase"], "| step =", ck["step"], "| events saved =", len(ck["events"]))

print("\nRun 2: RESUME from the checkpoint (the work done so far is NOT repeated)\n")
st2 = agent.resume(USER, SESSION)
for ev in st2["events"]:
    print(f"{ev['n']:>2}. [{ev['node']:<7}] {ev['summary']}")
print("\nFINAL:", st2["answer"])

from agentlib.habits import footer   # noqa: E402
footer(st2)
