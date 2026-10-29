"""Lab 3 tests. All local — no model call needed."""
import asyncio, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
ROOT = LAB.parent.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(ROOT / "common"))

from fastmcp import Client

SERVER = str(LAB / "mcp_server.py")


def _tools():
    async def go():
        async with Client(SERVER) as c:
            return [t.name for t in await c.list_tools()]
    return asyncio.run(go())


def _call(name, args):
    async def go():
        async with Client(SERVER) as c:
            r = await c.call_tool(name, args)
            content = getattr(r, "content", None) or (r if isinstance(r, (list, tuple)) else None)
            if content:
                t = getattr(content[0], "text", None)
                if t is not None:
                    return t
            d = getattr(r, "data", None)
            return str(d) if d is not None else str(r)
    return asyncio.run(go())


def test_search_kb_tool_is_exposed():
    assert "search_kb" in _tools()


def test_search_kb_returns_a_match():
    out = _call("search_kb", {"query": "activate esim"})
    assert "KB-002" in out


def test_solo3_get_ticket_tool_is_exposed():
    """SOLO 3: uncomment the get_ticket @mcp.tool() in mcp_server.py.
    This test will pass once you have."""
    assert "get_ticket" in _tools(), "SOLO 3 not done yet — expose get_ticket as an MCP tool"


def test_solo3_get_ticket_returns_a_ticket():
    out = _call("get_ticket", {"ticket_id": "TKT-0004"})
    assert "TKT-0004" in out and "EMP-1021" in out
