"""LAB 2A - See how chunking cuts a document. Run:  python lab2a_chunking.py"""
from rag.kb import load_kb, chunk_docs

SIZE = 25     # TRY: change to 10, 60, 120
doc = [d for d in load_kb() if d.id == "PLAN-101" and d.status == "current"]

print("=== FIXED chunks of", SIZE, "words (ignores structure) ===")
for c in chunk_docs(doc, "fixed", SIZE):
    print(f"[{c.cid}] {c.text}\n")

print("=== SECTION chunks (one per heading, with title) ===")
for c in chunk_docs(doc, "section"):
    print(f"[{c.cid}] {c.text}\n")
# THINK: which fixed chunk would answer 'how much data'? Does it also contain the plan name?
