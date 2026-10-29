"""NetNova MCP server.

Wraps our existing Python tools behind the MCP (Model Context Protocol).
MCP is just "tool over a wire": the agent calls the server, not the Python function.

Run:
    python mcp_server.py                          # listens on stdio (default)
    fastmcp dev mcp_server.py                     # opens the MCP Inspector in a browser (nice demo)
"""

import sys
from pathlib import Path

# make common/ importable
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from fastmcp import FastMCP
from tools import search_kb as _search_kb, get_ticket as _get_ticket

mcp = FastMCP("netnova-helpdesk")


@mcp.tool()
def search_kb(query: str) -> str:
    """Search NetNova knowledge base articles."""
    return _search_kb(query)


# SOLO 3 — add a second tool below. Delete the two `#` to switch it on.
#
# @mcp.tool()
# def get_ticket(ticket_id: str) -> str:
#     """Read one NetNova support ticket, e.g. TKT-0004."""
#     return _get_ticket(ticket_id)


if __name__ == "__main__":
    # Default transport is stdio. Our client (run_3.py) talks to it that way.
    mcp.run()
