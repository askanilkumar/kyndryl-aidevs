"""AskNova agent — the think-act-observe loop.

Two TODOs for you:
  TODO-1 (Lab 4 guided): the loop body
  TODO-2 (Lab 4 guided): say which tools need approval

Also:
  STOP_ON_REPEAT  — flip to True in the Incident
  solo 4         — add `check_outage` as the 5th tool (details in README)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from provider import chat, model_banner  # noqa: E402
from tools import (  # noqa: E402
    TOOL_SCHEMAS, TOOL_SCHEMAS_WITH_OUTAGE, run_tool, is_write_tool,
)

# -------- settings you may change --------

MAX_STEPS = 6              # stop after this many think-act rounds (safety)
STOP_ON_REPEAT = False     # Incident switch: refuse to call the exact same tool/args twice
AUTO_APPROVE = False       # set True to skip the prompt (handy in tests)

# -------- SOLO 4: swap this to TOOL_SCHEMAS_WITH_OUTAGE after you add the tool --------
TOOLS_IN_USE = TOOL_SCHEMAS


# -------- TODO-2: needs_approval ----------------------------------------
# Return True for tools that WRITE (change data). False for read-only.
# Spoiler: the common/tools.py has a helper `is_write_tool(name)` that already
# does this. Call it. One line.

def needs_approval(tool_name: str, arguments: dict) -> bool:
    # TODO-2: replace the next line with a one-liner that uses is_write_tool.
    return False
# ------------------------------------------------------------------------


def run_tool_safely(tool_name: str, arguments: dict) -> str:
    """Run a tool, but ask a human first if needs_approval() says so."""
    if needs_approval(tool_name, arguments) and not AUTO_APPROVE:
        print(f"\n  APPROVE: run {tool_name}({arguments}) ?  [y/N] ", end="", flush=True)
        answer = sys.stdin.readline().strip().lower()
        if answer not in ("y", "yes"):
            return f"DENIED by human: {tool_name} not run."
    return run_tool(tool_name, arguments)


# -------- TODO-1: the agent loop ----------------------------------------
# PART A: ask the model (give it the tool menu).
# PART B: if the model asked for tools, run each one, append tool_result; LOOP.
# PART C: if the model gave text and no tool_calls, that is the final answer. STOP.
# Also: step limit, STOP_ON_REPEAT, cost tally.

def run_agent(question: str, verbose: bool = True) -> dict:
    messages = [
        {"role": "system", "content":
            "You are AskNova, NetNova telecom's helpdesk agent. "
            "Use the tools when they help. Keep answers short."},
        {"role": "user", "content": question},
    ]
    seen_calls: set[tuple] = set()
    total_in = total_out = 0
    final_text = ""
    steps_used = 0

    for step in range(1, MAX_STEPS + 1):
        steps_used = step
        # ---------- TODO-1 PART A: call the model ----------
        # resp = chat(messages, tools=TOOLS_IN_USE)
        # total_in += resp["usage"].get("in", 0); total_out += resp["usage"].get("out", 0)
        # if verbose: print(f"\nSTEP {step}  (step limit {MAX_STEPS})")

        # ---------- TODO-1 PART C: final answer, no tool calls ----------
        # if not resp["tool_calls"]:
        #     final_text = resp["text"]
        #     if verbose: print(f"  final: {final_text}")
        #     break

        # ---------- TODO-1 PART B: run each tool call, append result ----------
        # ... run each tc in resp["tool_calls"] ...
        # ... check STOP_ON_REPEAT ...
        # ... append assistant tool_calls message, then one tool message per call ...
        # continue the loop.
        raise NotImplementedError("TODO-1 not written yet — see README Lab 4 guided section.")

    else:
        if verbose:
            print(f"\n  step limit hit — handing over to a human.")

    return {
        "answer": final_text or "I could not answer in time. A human will take over.",
        "steps": steps_used,
        "tokens_in": total_in,
        "tokens_out": total_out,
    }
# ------------------------------------------------------------------------


# -------- entry point ----------

def main():
    print(model_banner())
    if len(sys.argv) < 2:
        print('Usage:  python agent.py "your question"')
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    print(f"\nYOU: {question}\n")
    out = run_agent(question)
    print("\n" + "=" * 60)
    print(f"ANSWER   : {out['answer']}")
    print(f"STEPS    : {out['steps']}")
    print(f"TOKENS   : in={out['tokens_in']}, out={out['tokens_out']}")


if __name__ == "__main__":
    main()
