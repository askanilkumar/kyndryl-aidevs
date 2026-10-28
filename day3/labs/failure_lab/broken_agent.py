"""FAILURE LAB - this file has 5 faults. YOUR JOB: find them and fix them.

How to check your work (any of these):
    * open the Failure Lab tab in the Studio and press "Run check"
    * python -m failure_lab.checks            (runs all 5 and prints PASS / FAIL)
    * pytest tests/test_day3.py -k Failure

Fix faults 1, 2, 3 first. Faults 4 and 5 are the stretch.
Only edit this file. The helpers you may want are in agentlib/ (config, memory, guard).
"""
import json

from agentlib import config, memory, guard   # noqa: F401  (guard is for fault 5)


# ------------------------------------------------------------------ memory (faults 1 and 2)
def _key(user, session):
    return f"chat:{session}"


def add_message(user, session, role, content):
    r = memory.get_redis()
    r.rpush(_key(user, session), json.dumps({"role": role, "content": content}))


def get_history(user, session):
    r = memory.get_redis()
    return [json.loads(x) for x in r.lrange(_key(user, session), 0, -1)]


# ------------------------------------------------------------------ the agent loop (fault 3)
def run_agent(plan_fn, tool_fn, question):
    """plan_fn(question, observations) -> {"tool":..., "args":...}  or  {"final": "..."}
    tool_fn(name, args) -> {"answer": "..."}
    Returns {"answer": str, "steps": int, "stop_reason": str}
    """
    observations = []
    steps = 0
    while True:
        plan = plan_fn(question, observations)
        if "final" in plan:
            return {"answer": plan["final"], "steps": steps, "stop_reason": ""}
        observations.append(tool_fn(plan["tool"], plan.get("args", {})))
        steps += 1


# ------------------------------------------------------------------ calling a tool (fault 4, stretch)
def call_tool(tool_fn, name, args):
    return tool_fn(name, args)


# ------------------------------------------------------------------ building the prompt (fault 5, stretch)
def build_prompt(question, ticket_text):
    """Returns (prompt, flagged). `flagged` must be True when the ticket text tries to give orders."""
    prompt = f"Customer question: {question}\nTicket note: {ticket_text}\nAnswer using the note."
    return prompt, False
