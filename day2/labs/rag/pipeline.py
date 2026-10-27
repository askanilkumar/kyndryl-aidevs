"""The RAG pipeline. Every feature is a switch in Config, so you can turn them on one by one and measure."""
import time
from dataclasses import dataclass, field, replace
from .kb import load_kb, chunk_docs
from .index import Index
from .text import ID_RE
from . import llm

REFUSAL = "I don't know based on the knowledge base."


@dataclass
class Config:
    chunking: str = "fixed"        # fixed | section
    mode: str = "vector"           # vector | keyword | hybrid
    metadata_filter: bool = False  # role + status=current
    rewrite: bool = False
    rerank: bool = False
    multihop: bool = False
    guard: bool = False            # say "I don't know" when nothing is close enough
    grounded_prompt: bool = False  # strict prompt with rule 6 (context is data, not instructions)
    scan_injection: bool = False   # quarantine documents that carry hidden instructions
    top_k: int = 4
    candidates: int = 10
    guard_threshold: float = 0.0   # 0 = auto (picked from the provider)
    fixed_size: int = 40


PRESETS = {
    "Baseline": Config(),
    "+ Metadata filter": Config(metadata_filter=True),
    "+ Section chunks + hybrid": Config(metadata_filter=True, chunking="section", mode="hybrid"),
    "Full pipeline": Config(metadata_filter=True, chunking="section", mode="hybrid", rewrite=True, rerank=True,
                            multihop=True, guard=True, grounded_prompt=True, scan_injection=True),
}


def threshold(cfg):
    if cfg.guard_threshold:
        return cfg.guard_threshold
    return 0.28 if llm.online() else 0.30


class KB:
    """Holds documents and builds one index per chunking strategy."""

    def __init__(self, docs=None):
        self.docs = docs if docs is not None else load_kb()
        self._idx = {}

    def add(self, doc):
        self.docs.append(doc)
        self._idx = {}

    def index(self, cfg):
        key = (cfg.chunking, cfg.fixed_size)
        if key not in self._idx:
            self._idx[key] = Index(chunk_docs(self.docs, cfg.chunking, cfg.fixed_size))
        return self._idx[key]


@dataclass
class Result:
    question: str
    role: str
    answer: str = ""
    sources: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    refused: bool = False
    seconds: float = 0.0
    usd: float = 0.0
    query_used: str = ""


def _src(c, cos, score):
    return dict(cid=c.cid, doc_id=c.doc_id, title=c.title, section=c.section, text=c.text, roles=c.roles,
                status=c.status, version=c.version, flagged=c.flagged, cos=round(cos, 3), score=round(score, 3))


def run(kb, question, cfg, role="postpaid"):
    t0, u0 = time.time(), llm.snapshot()
    res = Result(question, role, query_used=question)
    idx = kb.index(cfg)
    flt = dict(role=role if cfg.metadata_filter else None, only_current=cfg.metadata_filter, no_flagged=cfg.scan_injection)
    q = question
    if cfg.rewrite:
        q = llm.rewrite(question)
        res.query_used = q
        res.trace.append(f"Rewrite: '{question}' -> '{q}'")
    qvec = llm.embed([q])[0]
    n = cfg.candidates

    vec = idx.vector(qvec, n, **flt) if cfg.mode in ("vector", "hybrid") else []
    kw = idx.keyword(q, n, **flt) if cfg.mode in ("keyword", "hybrid") else []
    if cfg.mode == "vector":
        ranked = [(c, s) for c, s in vec]
    elif cfg.mode == "keyword":
        ranked = [(c, s) for c, s in kw]
    else:   # hybrid: reciprocal rank fusion
        fused = {}
        for lst in (vec, kw):
            for r, (c, _) in enumerate(lst):
                fused[c.cid] = fused.get(c.cid, 0) + 1 / (60 + r + 1)
        by = {c.cid: c for lst in (vec, kw) for c, _ in lst}
        ranked = sorted(((by[k], v) for k, v in fused.items()), key=lambda x: -x[1])
    res.trace.append(f"Retrieve ({cfg.mode}, {cfg.chunking} chunks, filter={'on' if cfg.metadata_filter else 'off'}): {len(ranked)} candidates")

    cands = [dict(c=c, score=s) for c, s in ranked[:n]]
    if cfg.rerank and cands:
        pool = [_src(x["c"], idx.cosine(qvec, x["c"]), x["score"]) for x in cands]
        scores = llm.rerank(question, pool)
        for x, sc in zip(cands, scores):
            x["score"] = sc / 10.0
        cands.sort(key=lambda x: -x["score"])
        res.trace.append("Rerank: re-scored candidates, best first")
    top = cands[: cfg.top_k]

    if cfg.multihop and top:
        have = {x["c"].cid for x in top}
        seen_docs = {x["c"].doc_id for x in top}
        extra = []
        for x in top[:3]:
            for tok in ID_RE.findall(x["c"].text):
                if tok in seen_docs or tok == x["c"].doc_id:
                    continue
                hit = idx.keyword(tok, 3, exclude_docs=(x["c"].doc_id,), **flt)
                hit = [(c, s) for c, s in hit if c.cid not in have and c.doc_id != x["c"].doc_id]
                if hit:
                    c, s = hit[0]
                    extra.append(dict(c=c, score=0.5))
                    have.add(c.cid)
                    seen_docs.add(c.doc_id)
                    res.trace.append(f"Multi-hop: '{tok}' mentioned in {x['c'].doc_id} -> also fetched {c.doc_id}")
        top = top + extra

    res.sources = [_src(x["c"], idx.cosine(qvec, x["c"]), x["score"]) for x in top]
    best = max([s["cos"] for s in res.sources], default=0.0)
    if cfg.guard and (not top or best < threshold(cfg)):
        res.answer, res.refused = REFUSAL, True
        res.trace.append(f"Guard: best similarity {best:.2f} < {threshold(cfg):.2f} -> refuse")
    else:
        res.answer = llm.answer(question, res.sources, grounded=cfg.grounded_prompt)
        res.refused = REFUSAL.lower()[:20] in res.answer.lower()
        res.trace.append(f"Generate ({'strict prompt' if cfg.grounded_prompt else 'naive prompt'}) from {len(res.sources)} chunks")
    res.seconds = round(time.time() - t0, 2)
    res.usd = llm.delta(u0)["usd"]
    return res
