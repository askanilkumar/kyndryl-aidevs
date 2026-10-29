"""Run this first:  python check_setup.py"""
import importlib
import sys

ok = True
for pkg in ("streamlit", "fakeredis", "langgraph", "openai", "pytest"):
    try:
        importlib.import_module(pkg)
        print(f"  ok   {pkg}")
    except Exception as e:
        ok = False
        print(f"  MISSING {pkg}  ->  python -m pip install -r requirements.txt")

from agentlib import config, agent  # noqa: E402

print(f"\nPython {sys.version.split()[0]}")
print("Mode:", "OFFLINE stand-in model (no key needed)" if not config.online() else "GATEWAY (" + config.CHAT_MODEL + ")")
st = agent.ask("cust-1001", "setup-check", "What is the roaming charge for prepaid?")
print("Agent test:", "ok" if "Rs 49" in st["answer"] else "FAILED", f"(steps={st['step']}, cost=${st['usd']:.5f})")
print("\nAll good. Next: Lab 1a  ->  python lab1a_list_memory.py   (terminal only, no Streamlit yet)" if ok else "\nFix the MISSING items above first.")
