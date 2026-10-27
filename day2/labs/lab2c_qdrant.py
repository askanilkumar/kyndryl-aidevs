"""LAB 2C - Store vectors in Qdrant and search. Run:  python lab2c_qdrant.py"""
from qdrant_client import QdrantClient, models
from rag import llm
from rag.kb import load_kb, chunk_docs

docs = [d for d in load_kb() if d.status == "current"]
chunks = chunk_docs(docs, "section")
vectors = llm.embed([c.text for c in chunks])

client = QdrantClient(":memory:")                       # a vector database inside Python (no server)
client.create_collection("netnova", vectors_config=models.VectorParams(size=vectors.shape[1], distance=models.Distance.COSINE))
client.upsert("netnova", points=[
    models.PointStruct(id=i, vector=vectors[i].tolist(), payload={"doc_id": c.doc_id, "title": c.title, "roles": c.roles, "text": c.text})
    for i, c in enumerate(chunks)])
print(f"Stored {len(chunks)} chunks in Qdrant. Mode: {llm.mode_name()}\n")

TOP_K = 3                      # TRY: 1, 3, 6
ROLE = None                    # TRY: "prepaid"  (shows only chunks that role may see)

while True:
    q = input("Ask (Enter to stop): ").strip()
    if not q:
        break
    flt = models.Filter(must=[models.FieldCondition(key="roles", match=models.MatchValue(value=ROLE))]) if ROLE else None
    hits = client.query_points("netnova", query=llm.embed([q])[0].tolist(), limit=TOP_K, query_filter=flt).points
    for h in hits:
        print(f"  {h.score:.2f}  {h.payload['doc_id']:9s} {h.payload['text'][:90]}...")
    print()
# THINK: ask 'Which cafeteria serves vegan food?'. The search still returns results. What does that tell you about needing a guard?
