"""The four habits, printed at the end of every lab so they become automatic."""
from . import config


def footer(state=None, evals_rate=None):
    print("\n" + "=" * 62)
    print("HABITS CHECK")
    print("  [SECURE] every key has the user id, PII is masked before saving, secrets never in files (sidebar or OS env var)")
    if state:
        print(f"  [COST]   this run: {state['tokens_in']}+{state['tokens_out']} tokens = ${state['usd']:.5f} (budget ${state['budget']})")
        n = len(state.get("guard_log", []))
        print(f"  [GUARD]  {n} guardrail finding(s) this run")
    else:
        print(f"  [COST]   limits: last {config.MAX_MESSAGES} messages, TTL {config.TTL_SHORT}s, max {config.MAX_STEPS} steps")
        print("  [GUARD]  nothing risky ran in this lab")
    print("  [EVAL]   " + (f"last eval pass rate {evals_rate:.0%}" if evals_rate is not None else "run: python run_evals.py"))
    print("=" * 62)
