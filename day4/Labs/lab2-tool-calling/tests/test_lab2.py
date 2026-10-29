import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
LAB = HERE.parent
ROOT = LAB.parent.parent
sys.path.insert(0, str(ROOT / "common"))

from tools import run_tool, TOOL_SCHEMAS, is_write_tool


def test_schemas_shape():
    names = [s["function"]["name"] for s in TOOL_SCHEMAS]
    assert set(names) == {"search_kb", "get_ticket", "update_ticket", "reset_sim"}


def test_tool_ids_match_in_notes():
    """Solo 2 asks you to copy the toolUse id and the toolResult id into notes.
    They MUST be the same string. We check the notes file."""
    notes = (LAB / "submission" / "notes.md").read_text(encoding="utf-8")
    import re
    use = re.search(r"id_toolUse\s*:\s*`?([A-Za-z0-9_\-]+)", notes)
    res = re.search(r"id_toolResult\s*:\s*`?([A-Za-z0-9_\-]+)", notes)
    assert use and res, "Fill in id_toolUse and id_toolResult in notes.md"
    assert use.group(1).strip().lower() not in ("<fill>", "fill"), "Replace <fill> in notes.md"
    assert use.group(1) == res.group(1), f"ids do not match: {use.group(1)} vs {res.group(1)}"


def test_search_kb_works():
    out = run_tool("search_kb", {"query": "activate esim"})
    assert "KB-002" in out


def test_get_ticket_happy_path():
    out = run_tool("get_ticket", {"ticket_id": "TKT-0004"})
    assert "TKT-0004" in out and "EMP-1021" in out


def test_get_ticket_bad_id():
    out = run_tool("get_ticket", {"ticket_id": "TKT-9999"})
    assert out.startswith("ERROR")


def test_write_vs_read_classification():
    assert is_write_tool("reset_sim") and is_write_tool("update_ticket")
    assert not is_write_tool("search_kb") and not is_write_tool("get_ticket")
