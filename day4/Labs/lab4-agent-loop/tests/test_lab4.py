import importlib, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
ROOT = LAB.parent.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(ROOT / "common"))

import agent  # noqa: E402

# force deterministic model + auto-approve so tests do not block on y/N
import os
os.environ["ASKIT_MODEL"] = "offline"
agent.AUTO_APPROVE = True
# re-import provider so it picks up the forced mode
import provider  # noqa: E402
provider._MODE = None


def test_needs_approval_todo2_done():
    assert agent.needs_approval("reset_sim", {}) is True, "TODO-2 not done"
    assert agent.needs_approval("update_ticket", {}) is True, "TODO-2 not done"
    assert agent.needs_approval("search_kb", {}) is False
    assert agent.needs_approval("get_ticket", {}) is False


def test_todo1_simple_read_question_terminates():
    out = agent.run_agent("What is the status of ticket TKT-0004?", verbose=False)
    assert "TKT-0004" in out["answer"] or "ticket" in out["answer"].lower()
    assert 1 <= out["steps"] <= agent.MAX_STEPS


def test_todo1_hi_is_zero_tool_calls():
    out = agent.run_agent("Hi", verbose=False)
    # No tool should have been invoked; one step is enough.
    assert out["steps"] == 1


def test_step_limit_is_honoured():
    old = agent.MAX_STEPS
    agent.MAX_STEPS = 1
    try:
        out = agent.run_agent("Reset the SIM for EMP-1021 and also note ticket TKT-0004", verbose=False)
        assert out["steps"] <= 1
    finally:
        agent.MAX_STEPS = old


def test_solo4_check_outage_is_wired():
    """SOLO 4: swap TOOLS_IN_USE to include check_outage. This test passes once you have."""
    names = [t["function"]["name"] for t in agent.TOOLS_IN_USE]
    assert "check_outage" in names, "SOLO 4 not done — add check_outage to TOOLS_IN_USE"
