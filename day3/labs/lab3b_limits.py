"""LAB 3b - Every loop needs two limits: a MAX STEPS guard and a MAX COST budget.

We use a deliberately confused model ("loop": True) that never stops asking for the same tool.

RUN:   python lab3b_limits.py
THEN:  (1) change MAX_STEPS to 3. (2) change BUDGET to 0.0004 and see which limit fires first.
       (3) what should the CUSTOMER see when a limit fires? Read the answer text. Would you change it?
"""
from agentlib import agent

MAX_STEPS = 6
BUDGET = 0.05      # dollars for this question

st = agent.ask("cust-1001", "lab3b", "How do I fix slow internet?", flags={"loop": True},
               max_steps=MAX_STEPS, budget=BUDGET)
for ev in st["events"]:
    print(f"{ev['n']:>2}. [{ev['node']:<7}] {ev['summary'][:90]:<90} ${ev['usd']:.5f}")
print(f"\nstop_reason = {st['stop_reason']!r}   steps = {st['step']}   spent = ${st['usd']:.5f} of ${BUDGET}")
print("customer sees:", st["answer"])

from agentlib.habits import footer   # noqa: E402
footer(st)
