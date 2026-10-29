"""Smoke test the Streamlit app via AppTest. Needs MCP server running."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from streamlit.testing.v1 import AppTest


def test_app_runs_with_server_down():
    at = AppTest.from_file(str(HERE / "app.py")).run(timeout=20)
    # Journey tab (default)
    assert not at.exception
    # should not crash even if MCP down


def test_journey_tab_renders():
    at = AppTest.from_file(str(HERE / "app.py")).run(timeout=20)
    md_text = " ".join(m.value for m in at.markdown)
    assert "governed agent" in md_text.lower() or "mcp" in md_text.lower()
