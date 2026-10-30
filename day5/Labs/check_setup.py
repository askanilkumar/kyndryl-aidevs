"""Step 0: check that Day 5 is ready.   Run:  python check_setup.py"""
import importlib
import sys

print("Python", sys.version.split()[0])
ok = True
for lib in ["streamlit", "openai", "pandas", "langsmith", "langfuse", "pytest"]:
    try:
        m = importlib.import_module(lib)
        print(f"  ok   {lib} {getattr(m, '__version__', '')}")
    except Exception as e:
        ok = False
        print(f"  MISSING {lib}  ->  python -m pip install -r requirements.txt")

if ok:
    from asknova import agent
    res = agent.run("What is the roaming price for prepaid in UAE?", log=False)
    print("Agent test (offline):", "ok" if "649" in res.answer else "FAILED", "-", res.answer[:80])
    print("\nNext:  python -m streamlit run app.py   (then open http://localhost:8501)")
