"""Day 3 pre-flight. Run from Day3-v2 folder: `python check_setup.py`"""
import sys, importlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "common"))

def ok(msg): print("  OK  ", msg)
def bad(msg): print("  FAIL", msg); return False

errs = 0
print("Day 3 setup check")
print("-" * 40)

# imports
for mod in ["openai", "fakeredis", "fastmcp", "dotenv"]:
    try:
        importlib.import_module(mod); ok(f"import {mod}")
    except Exception as e:
        bad(f"import {mod}: {e}"); errs += 1

# data
for p in ["Data/users.csv", "Data/tickets.csv", "Data/kb"]:
    if (HERE / p).exists(): ok(f"data: {p}")
    else: bad(f"missing: {p}"); errs += 1

# provider banner
try:
    from provider import model_banner, chat
    print("  ----", model_banner())
    r = chat([{"role": "user", "content": "Hi"}])
    ok(f"model replied ({len(r.get('text',''))} chars)")
except Exception as e:
    bad(f"provider: {e}"); errs += 1

# tools
try:
    from tools import search_kb, get_ticket, TOOL_SCHEMAS
    assert "esim" in search_kb("activate esim").lower()
    assert "TKT-0004" in get_ticket("TKT-0004")
    assert len(TOOL_SCHEMAS) == 4
    ok("tools work (search_kb, get_ticket, 4 schemas)")
except Exception as e:
    bad(f"tools: {e}"); errs += 1

print("-" * 40)
if errs: print(f"\n{errs} problem(s). Fix above, re-run."); sys.exit(1)
print("\nAll set.  You are ready for Lab 1.")
