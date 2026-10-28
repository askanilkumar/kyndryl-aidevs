"""Run the eval set. The gate says whether this version of the agent may ship.
    python run_evals.py"""
from agentlib import evals

r = evals.run_all()
for x in r["rows"]:
    c = x["checks"]
    mark = lambda ok: "ok " if ok else "BAD"     # noqa: E731
    print(f"{'PASS' if x['pass'] else 'FAIL'} {x['id']}  tools:{mark(c['tools'])} steps:{mark(c['steps'])} "
          f"answer:{mark(c['contains'])} no-leak:{mark(c['never'])}  ${x['usd']:.5f}  {x['question']}")
print(f"\n{r['passed']}/{r['total']} passed ({r['rate']:.0%}).  cost ${r['usd_total']:.4f} total, ${r['usd_per_case']:.5f} per question")
print("GATE:", "OPEN - safe to ship" if r["gate"] else "CLOSED - fix the failures first")
