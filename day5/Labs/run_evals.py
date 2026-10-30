"""Run the eval set from the terminal (offline, or with OPENAI_API_KEY set as an OS env var).
Run:  python run_evals.py            or   python run_evals.py v2   (test another prompt version)"""
import os
import sys

from asknova.evals import run_evals

version = sys.argv[1] if len(sys.argv) > 1 else None
client = None
if os.getenv("OPENAI_API_KEY"):
    from openai import OpenAI
    client = OpenAI()
rep = run_evals(client=client, prompt_version=version)
for r in rep["rows"]:
    print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['id']}  {'[safety] ' if r['safety'] else ''}{r['question'][:55]:<55}  {r['why']}")
print(f"\n{rep['passed']}/{rep['total']} passed ({rep['pass_rate']:.0%}) · safety {'ok' if rep['safety_ok'] else 'FAILED'} · "
      f"gate {'OPEN' if rep['gate_open'] else 'CLOSED'}")
sys.exit(0 if rep["gate_open"] else 1)
