"""LAB 2B - Meaning as numbers. Run:  python lab2b_embeddings.py"""
import numpy as np
from rag import llm

sentences = [
    "I want my money back for a wrong bill",       # 0
    "How do I get a refund?",                      # 1
    "What is the cricket score today?",            # 2
    "My internet is very slow",                    # 3
    "Mobile data speed is poor at home",           # 4
]
vecs = llm.embed(sentences)
print("Mode:", llm.mode_name(), "| each sentence became", vecs.shape[1], "numbers\n")
sim = vecs @ vecs.T          # cosine similarity (the vectors are unit length)
print("Similarity (1.00 = same meaning):")
for i, s in enumerate(sentences):
    print(f"{i}  " + "  ".join(f"{sim[i, j]:.2f}" for j in range(len(sentences))) + f"   {s}")
print("\nFirst 8 numbers of sentence 0:", np.round(vecs[0][:8], 3))
if not llm.online():
    print("\nNOTE: offline mode only sees shared words, so 0 vs 1 looks weak. With the OpenAI key it should be clearly higher.")
# TRY: add 2 sentences of your own. Which pair is closest?
