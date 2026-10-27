"""Run this first:  python check_setup.py   -> every line should say OK."""
import importlib, os, sys
ok = True
for m in ["streamlit", "openai", "qdrant_client", "numpy", "pandas", "dotenv"]:
    try:
        importlib.import_module(m); print("OK   package", m)
    except Exception as e:
        ok = False; print("FAIL package", m, "->", e, "\n     fix: python -m pip install -r requirements.txt")
from rag import llm
from rag.kb import load_kb
docs = load_kb()
print("OK   knowledge base:", len(docs), "documents")
print("MODE:", llm.mode_name())
if llm.online():
    try:
        v = llm.embed(["hello"]); print("OK   embeddings work, vector size", v.shape[1])
        print("OK   chat works:", llm.plain_chat("Say OK")[:40])
    except Exception as e:
        ok = False; print("FAIL OpenAI call ->", str(e)[:200], "\n     check OPENAI_API_KEY in the .env file")
else:
    print("NOTE no OPENAI_API_KEY found. Labs still run in OFFLINE mode (simple stand-ins). Ask the trainer for the key.")
print("\nALL GOOD" if ok else "\nFIX THE FAIL LINES ABOVE")
