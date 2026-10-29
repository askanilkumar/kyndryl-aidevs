"""Core tests. Run with: python -m pytest tests/test_day4.py -v"""
import sys, os, json
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from rbac import can_call, requires_approval, load_registry, audit, read_audit, clear_audit, AUDIT


def test_registry_loads():
    r = load_registry()
    assert "plan_change" in r["tools"]


def test_viewer_cannot_change_plan():
    ok, _ = can_call("viewer", "plan_change")
    assert ok is False


def test_supervisor_can_change_plan_but_needs_approval():
    ok, _ = can_call("supervisor", "plan_change")
    assert ok
    assert requires_approval("plan_change") is True


def test_engineer_can_read_but_not_change():
    assert can_call("engineer", "tower_status")[0]
    assert can_call("engineer", "plan_change")[0] is False


def test_audit_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr("rbac.AUDIT", tmp_path / "a.jsonl")
    import rbac
    rbac.AUDIT = tmp_path / "a.jsonl"
    rbac.audit("executed", "engineer", "kb_search", {"q": "x"}, "ok", "")
    rows = rbac.read_audit()
    assert len(rows) == 1
    assert rows[0]["tool"] == "kb_search"


def test_offline_plan_routes_incident():
    from llm import plan_offline
    p = plan_offline("Look up incident INC-5102.", [])
    assert p["tool"] == "ticket_lookup"
    assert p["args"]["incident_id"] == "INC-5102"


def test_offline_plan_routes_tower():
    from llm import plan_offline
    p = plan_offline("Check tower TWR-CHN-11.", [])
    assert p["tool"] == "tower_status"


def test_mcp_server_tools_listed():
    from mcp_server import TOOLS
    names = [t["name"] for t in TOOLS]
    for n in ["kb_search", "ticket_lookup", "tower_status", "plan_change"]:
        assert n in names


def test_plan_change_is_high_risk():
    from mcp_server import TOOLS
    pc = next(t for t in TOOLS if t["name"] == "plan_change")
    assert pc["risk"] == "high"
