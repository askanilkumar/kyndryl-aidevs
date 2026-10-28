"""Run this before the lab: python check_setup.py
Checks the OpenAI key (chat, JSON replies, embeddings). With no key the app still runs in Offline mode."""
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")   # a .env in this folder: OPENAI_API_KEY=sk-...

from rag.llm import LLM  # noqa: E402


def check(llm):
    t = time.time()
    v = llm.embed(["hello"], op="check")[0]
    print(f"OK embeddings  {llm.embed_model}: dim={len(v)} ({time.time() - t:.1f}s)")
    t = time.time()
    msg, row = llm.chat([{"role": "user", "content": 'Reply with JSON {"ok": true}'}], op="check", json_mode=True)
    print(f"OK chat        {llm.chat_model}: {msg.content!r} tokens={row['input_tokens']}+{row['output_tokens']} ({time.time() - t:.1f}s)")


if os.getenv("OPENAI_API_KEY"):
    try:
        check(LLM(os.getenv("OPENAI_API_KEY"), cache_dir=".cache_check"))
        print("All good. Start the app with: python -m streamlit run app.py")
    except Exception as e:
        print(f"OpenAI FAILED: {str(e)[:300]}")
        print("The app still runs: choose Offline in the sidebar.")
else:
    print("No OPENAI_API_KEY found. That is fine: the app runs in Offline mode (stand-in models).")
    print("To go live, copy .env.example to .env and add your key, or paste it in the app sidebar.")
    print("Start the app with: python -m streamlit run app.py")
