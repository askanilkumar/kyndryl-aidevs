"""Thin MCP client over HTTP. Agent and Streamlit app both use this."""
import httpx

BASE = "http://127.0.0.1:8765"


def list_tools():
    r = httpx.get(f"{BASE}/tools/list", timeout=5)
    r.raise_for_status()
    return r.json()["tools"]


def call_tool(name: str, args: dict):
    r = httpx.post(f"{BASE}/tools/call", json={"name": name, "args": args}, timeout=10)
    r.raise_for_status()
    return r.json()


def ping():
    try:
        httpx.get(f"{BASE}/", timeout=2)
        return True
    except Exception:
        return False
