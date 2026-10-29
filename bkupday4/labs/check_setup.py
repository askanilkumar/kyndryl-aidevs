"""Verify Day 4 setup."""
import sys, importlib

def ok(msg): print(f"✅ {msg}")
def bad(msg): print(f"❌ {msg}"); sys.exit(1)

for mod in ["streamlit", "fastapi", "uvicorn", "httpx", "langgraph", "openai", "pydantic"]:
    try:
        importlib.import_module(mod); ok(f"import {mod}")
    except Exception as e:
        bad(f"missing: {mod}  ({e})  → pip install -r requirements.txt")

from pathlib import Path
for f in ["app.py", "mcp_server.py", "mcp_client.py", "agent.py", "rbac.py",
          "llm.py", "kb.py", "registry.json"]:
    p = Path(__file__).with_name(f)
    (ok(f"file {f}") if p.exists() else bad(f"missing file: {f}"))

print("\nNext steps:")
print("  Terminal A:  python mcp_server.py")
print("  Terminal B:  streamlit run app.py")
