"""The search index: Qdrant (vectors) + BM25 (keywords) over the same chunks."""
import math
from collections import Counter
import numpy as np
from qdrant_client import QdrantClient, models
from .text import tokens
from . import llm


class Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.pos = {c.cid: i for i, c in enumerate(chunks)}
        self.vecs = llm.embed([c.text for c in chunks])
        self.client = QdrantClient(":memory:")          # lives in RAM, no server, no Docker
        self.col = "kb"
        self.client.create_collection(self.col, vectors_config=models.VectorParams(size=self.vecs.shape[1], distance=models.Distance.COSINE))
        self.client.upsert(self.col, points=[
            models.PointStruct(id=i, vector=self.vecs[i].tolist(),
                               payload=dict(doc_id=c.doc_id, roles=c.roles, status=c.status, flagged=c.flagged))
            for i, c in enumerate(chunks)])
        # BM25 statistics
        self.toks = [tokens(c.text) for c in chunks]
        self.df = Counter(t for ts in self.toks for t in set(ts))
        self.avg = sum(len(t) for t in self.toks) / max(1, len(self.toks))

    # -------- filters
    def _ok(self, c, role, only_current, no_flagged):
        if role and role not in c.roles:
            return False
        if only_current and c.status != "current":
            return False
        if no_flagged and c.flagged:
            return False
        return True

    def _filter(self, role, only_current, no_flagged):
        must, must_not = [], []
        if role:
            must.append(models.FieldCondition(key="roles", match=models.MatchValue(value=role)))
        if only_current:
            must.append(models.FieldCondition(key="status", match=models.MatchValue(value="current")))
        if no_flagged:
            must.append(models.FieldCondition(key="flagged", match=models.MatchValue(value=False)))
        return models.Filter(must=must) if must else None

    # -------- vector search (Qdrant)
    def vector(self, qvec, k=10, role=None, only_current=False, no_flagged=False):
        res = self.client.query_points(self.col, query=qvec.tolist(), limit=k,
                                       query_filter=self._filter(role, only_current, no_flagged)).points
        return [(self.chunks[p.id], float(p.score)) for p in res]

    # -------- keyword search (BM25)
    def keyword(self, query, k=10, role=None, only_current=False, no_flagged=False, exclude_docs=()):
        q = tokens(query)
        n = len(self.chunks)
        out = []
        for i, c in enumerate(self.chunks):
            if not self._ok(c, role, only_current, no_flagged) or c.doc_id in exclude_docs:
                continue
            tf = Counter(self.toks[i])
            s = 0.0
            for t in q:
                if t in tf:
                    idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(self.toks[i]) / self.avg))
            if s > 0:
                out.append((c, s))
        out.sort(key=lambda x: -x[1])
        return out[:k]

    def cosine(self, qvec, chunk):
        return float(np.dot(qvec, self.vecs[self.pos[chunk.cid]]))
