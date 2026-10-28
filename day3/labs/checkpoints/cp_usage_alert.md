# Checkpoint: add a 5th tool, `usage_alert`, the safe way

A new tool touches FIVE places. Missing one is a classic bug. Tick them off.

## 1. agentlib/tools.py : the function (read-only, so low risk)
```python
def usage_alert(customer: str, limit_gb: float = 80.0):
    c = CUSTOMERS.get(customer)
    if not c:
        return {"found": False, "answer": "Customer not found."}
    over = c["data_used_gb"] > limit_gb
    msg = f"{c['name']} has used {c['data_used_gb']} GB. " + ("That is OVER the {limit} GB alert level." if over else "That is under the {limit} GB alert level.")
    return {"found": True, "over": over, "answer": msg.format(limit=limit_gb)}
```

## 2. agentlib/tools.py : register it and describe it
```python
REGISTRY["usage_alert"] = lambda a, user: usage_alert(user)
TOOL_DOCS.append({"name": "usage_alert", "args": {}, "use": "tell if data used this month is over the alert level"})
```

## 3. agentlib/guard.py : the allow-list (a tool that is not listed is BLOCKED)
```python
ALLOWED_TOOLS = {"rag_search", "ticket_lookup", "plan_lookup", "change_plan", "usage_alert"}
```

## 4. agentlib/llm.py : teach the offline stand-in (inside standin_plan, before the kb_words rule)
```python
    if any(w in q for w in ("alert", "over limit", "too much data")) and "usage_alert" not in used:
        return {"thought": "This is about data usage vs the alert level, so I use usage_alert.",
                "tool": "usage_alert", "args": {}}
```

## 5. agentlib/evals.py : two eval cases (add to CASES)
```python
    {"id": "E9", "user": "cust-1003", "q": "Is my data usage over the alert limit?",
     "tools": ["usage_alert"], "contains": ["OVER"], "never": []},
    {"id": "E10", "user": "cust-1002", "q": "Is my data usage over the alert limit?",
     "tools": ["usage_alert"], "contains": ["under"], "never": []},
```
Then: python run_evals.py  -> 10/10, gate OPEN.  And try it in the Studio (Agent run tab).

Questions to answer in your decision record:
- Why is this tool "low risk"? What would make it HIGH risk?
- Which of the 4 habits did each of the 5 steps serve?
