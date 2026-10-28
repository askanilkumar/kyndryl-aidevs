"""LAB 2a - An agent is: the model WRITES A PLAN, we RUN the tool, the model reads the result.

We do the loop by hand, one step at a time, so you can see every piece.

RUN:   python lab2a_tool_by_hand.py
THEN:  change QUESTION to "Which plan am I on?" and to "Check ticket TKT-2003". Does the plan change?
"""
import json

from agentlib import llm, tools
from agentlib.memory import get_profile
from agentlib.agent import login

USER = "cust-1001"
QUESTION = "What is the status of ticket TKT-2001?"
login(USER)
profile = get_profile(USER)
observations = []

for step in range(1, 4):
    plan, tin, tout, model = llm.make_plan(QUESTION, observations, profile, [])
    print(f"--- step {step}: THINK  (model={model}, {tin}+{tout} tokens)")
    print(json.dumps(plan, indent=2))
    if "final" in plan:
        print("\nFINAL ANSWER:", plan["final"])
        break
    result = tools.run_tool(plan["tool"], plan.get("args", {}), USER)           # <- WE run the tool, not the model
    print(f"--- step {step}: ACT    {plan['tool']} -> {result['answer']}\n")
    observations.append({"tool": plan["tool"], "args": plan.get("args", {}), "answer": result["answer"]})

from agentlib.habits import footer   # noqa: E402
footer()
