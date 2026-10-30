"""Lab 4 check:  python -m pytest tests/test_lab4.py -q"""
from asknova import config, release


def test_v2_passes_the_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RELEASES_FILE", tmp_path / "releases.json")
    out = release.release("v2")
    bad = [r for r in out["report"]["rows"] if not r["passed"]]
    assert out["status"] == "approved", f"v2 is rejected: {bad}  -> fix prompts/system_v2.txt (TODO Lab 4)"


def test_rollback(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RELEASES_FILE", tmp_path / "releases.json")
    release.release("v1")
    state = release.load()
    state["history"].append({"version": "v9", "status": "approved"})
    state["active"] = "v9"
    release.save(state)
    assert release.rollback()["active"] == "v1"
