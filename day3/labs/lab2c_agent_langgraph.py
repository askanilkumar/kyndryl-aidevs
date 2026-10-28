"""LAB 2c - The same loop as a LangGraph: boxes (nodes) and arrows (edges).

RUN:   python lab2c_agent_langgraph.py
THEN:  open agentlib/agent.py and find build_graph(). Find the 5 nodes. Which node decides what happens next?
       STRETCH (independent block): add a 5th tool 'usage_alert' that says whether data used is over 80 GB.
          you need: the function in tools.py, REGISTRY + TOOL_DOCS in tools.py, ALLOWED_TOOLS in guard.py,
          and one rule in llm.standin_plan (or just use the gateway model).
"""
from agentlib import agent

print("THE GRAPH (paste this into https://mermaid.live to see the picture):\n")
print(agent.GRAPH.get_graph().draw_mermaid())

print("\nRUNNING IT. Each line is one node finishing; the state is saved after every line.\n")
st = agent.ask("cust-1001", "lab2c", "Check ticket TKT-2001 and tell me how to fix slow internet",
               )
for ev in st["events"]:
    print(f"{ev['n']:>2}. [{ev['node']:<7}] step {ev['step']}  {ev['summary']}")
print("\nFINAL:", st["answer"])
print(f"steps={st['step']}  tokens={st['tokens_in']}+{st['tokens_out']}  cost=${st['usd']:.5f}")

from agentlib.habits import footer   # noqa: E402
footer(st)
