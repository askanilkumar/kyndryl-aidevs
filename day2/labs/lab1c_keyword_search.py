"""LAB 1C - Your first retriever: count the words that match. Run:  python lab1c_keyword_search.py"""
from rag import llm
from rag.kb import load_kb
from rag.text import tokens

docs = [d for d in load_kb() if d.status == "current"]


def search(question, k=3):
    q = set(tokens(question))
    scored = []
    for d in docs:
        score = len(q & set(tokens(d.title + " " + d.body)))   # how many question words appear in the document
        scored.append((score, d))
    scored.sort(key=lambda x: -x[0])
    return scored[:k]


while True:
    question = input("\nAsk a question (or press Enter to stop): ").strip()
    if not question:
        break
    top = search(question)
    for score, d in top:
        print(f"  score {score:2d}  {d.id}  {d.title}")
    if top[0][0] == 0:
        print("  Nothing matched. Keyword search only finds the SAME words.")
        continue
    context = [{"text": f"[{d.id}] {d.body}", "doc_id": d.id} for _, d in top]
    print("ANSWER:", llm.answer(question, context, grounded=True))

# TRY 1: 'How much data in the Postpaid Max plan?'   -> works (same words)
# TRY 2: 'How many gigabytes do I get on my top monthly plan?' -> fails (different words, same meaning). That is why we need embeddings.
