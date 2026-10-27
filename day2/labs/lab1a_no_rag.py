"""LAB 1A - Ask the model WITHOUT any documents. Run:  python lab1a_no_rag.py"""
from rag import llm

print("Mode:", llm.mode_name())
question = "How much data does the NetNova Postpaid Max plan include, and what does it cost?"
print("\nQUESTION:", question)
print("\nANSWER (no documents given):\n", llm.plain_chat(question))
# TRY: change the question to ask about the prepaid Smart 299 plan. Does the model know it?
