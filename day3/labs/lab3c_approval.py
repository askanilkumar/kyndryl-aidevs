"""LAB 3c - A human approves risky actions. Reading is free; WRITING needs a yes.

RUN:   python lab3c_approval.py            (it will ask you to approve)
       python lab3c_approval.py approve     (no question, approves)
       python lab3c_approval.py reject
THEN:  (1) reject it and read the final answer. (2) Open agentlib/guard.py: what makes a tool 'risky'?
       (3) Make rag_search risky too. What happens when you ask a plain question?  (undo it afterwards!)
"""
import sys

from agentlib import agent, tools

tools.reset_plans()
st = agent.ask("cust-1002", "lab3c", "Please upgrade me to Max 999")
print("phase =", st["phase"], "| stop_reason =", st["stop_reason"])
print("The agent PAUSED. Its plan:", st["plan"]["tool"], st["plan"]["args"], "\n")

arg = sys.argv[1] if len(sys.argv) > 1 else input("Approve this plan change? [y/n] ").strip().lower()
decision = "approved" if arg in ("approve", "y", "yes") else "rejected"
st = agent.decide(st, decision)

for ev in st["events"]:
    print(f"{ev['n']:>2}. [{ev['node']:<7}] {ev['summary']}")
print("\nFINAL:", st["answer"])
print("Plan in the system now:", tools.plan_state("cust-1002"))
tools.reset_plans()

from agentlib.habits import footer   # noqa: E402
footer(st)
