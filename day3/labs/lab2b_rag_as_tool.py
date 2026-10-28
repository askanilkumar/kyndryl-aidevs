"""LAB 2b - Your Day 2 RAG becomes ONE TOOL among several. The model chooses when to use it.

RUN:   python lab2b_rag_as_tool.py
THEN:  (1) add a new article to KB in agentlib/tools.py (id KB-070, title "Data rollover", ...)
          and ask about it. Does the agent find it?
       (2) ask "How do I fix slow internet?" then "Which plan am I on?". Which tool does each one pick?
       Later: you can swap search_kb() for your Day 2 retrieval pipeline. The agent will not notice.
"""
from agentlib import agent, tools

print("What the retrieval tool returns by itself:")
for hit in tools.search_kb("roaming charge prepaid"):
    print(f"  {hit['id']}  {hit['title']}")

print("\nNow the same question through the agent (it decides to use rag_search):")
for q in ["What is the roaming charge for prepaid?", "How do I fix slow internet?", "Which plan am I on?"]:
    st = agent.ask("cust-1001", "lab2b", q)
    used = [o["tool"] for o in st["observations"]]
    print(f"\nQ: {q}\n   tools used: {used}   cost ${st['usd']:.5f}\n   A: {st['answer'][:160]}")

print("\nSafety check: internal documents are never retrieved for customers ->",
      [h["id"] for h in tools.search_kb("escalation number NOC")] or "nothing returned (good)")

from agentlib.habits import footer   # noqa: E402
footer(st)
