"""LAB 1B - Paste the WHOLE knowledge base into the prompt. Run:  python lab1b_stuff_prompt.py"""
from rag import llm
from rag.kb import load_kb

docs = load_kb()
context = "\n\n".join(f"[{d.id} version {d.version}, {d.status}] {d.title}\n{d.body}" for d in docs)
print(f"Documents: {len(docs)}   Words pasted into the prompt: {len(context.split())}")

question = "How much data does the NetNova Postpaid Max plan include?"
before = llm.snapshot()
answer = llm.answer(question, [{"text": context, "doc_id": "ALL"}], grounded=False)
cost = llm.delta(before)

print("\nQUESTION:", question)
print("ANSWER:", answer)
approx = int(len(context.split()) * 1.4)
print(f"\nTokens sent: {cost['in'] or approx} (about)   Cost of this ONE question: ${cost['usd']:.5f}")
# THINK: the KB has TWO versions of Postpaid Max (v3 = 100 GB, v2 = 75 GB). Did the model pick the right one?
# THINK: now imagine 5,000 documents. Will this still fit? What will it cost per question?
