"""Load knowledge-base files, read their metadata, cut them into chunks, scan for hidden instructions."""
import os, re
from dataclasses import dataclass, field
from .config import KB_DIR

INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above) (rules|instructions)",
    r"assistant instruction", r"system prompt", r"do not mention this",
    r"send (your|the) otp", r"reveal .*(password|key)",
]


@dataclass
class Doc:
    id: str
    title: str
    type: str = "note"
    roles: list = field(default_factory=lambda: ["postpaid", "prepaid", "noc"])
    version: int = 1
    status: str = "current"
    updated: str = ""
    body: str = ""
    path: str = ""
    flagged: list = field(default_factory=list)   # injection scan hits


@dataclass
class Chunk:
    cid: str
    doc_id: str
    title: str
    section: str
    text: str
    roles: list
    status: str
    version: int
    flagged: bool = False


def parse_doc(raw, fallback_id="DOC", meta=None):
    meta = dict(meta or {})
    body = raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    roles = [r.strip() for r in str(meta.get("roles", "postpaid, prepaid, noc")).split(",") if r.strip()]
    d = Doc(id=meta.get("id", fallback_id), title=meta.get("title", fallback_id), type=meta.get("type", "note"),
            roles=roles, version=int(meta.get("version", 1)), status=meta.get("status", "current"),
            updated=meta.get("updated", ""), body=body.strip())
    d.flagged = scan_injection(d)
    return d


def scan_injection(doc):
    hits = []
    for p in INJECTION_PATTERNS:
        if re.search(p, doc.body, re.I):
            hits.append(p)
    return hits


def load_kb(folder=None):
    folder = folder or KB_DIR
    docs = []
    for fn in sorted(os.listdir(folder)):
        if fn.endswith(".md"):
            raw = open(os.path.join(folder, fn), encoding="utf-8").read()
            d = parse_doc(raw, fallback_id=fn[:-3])
            d.path = fn
            docs.append(d)
    return docs


def _sections(body):
    """Split a markdown body into (heading, text) pairs on '## ' headings."""
    body = re.sub(r"^# .*\n", "", body.strip(), count=1)
    parts = re.split(r"^## (.*)$", body, flags=re.M)
    out = []
    if parts[0].strip():
        out.append(("Intro", parts[0].strip()))
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1].strip()))
    return out


def chunk_docs(docs, strategy="section", size=40):
    """strategy 'fixed'  : every `size` words, ignoring structure (cuts sentences in half).
       strategy 'section': one chunk per '## ' section, with the document title and id in front."""
    chunks = []
    for d in docs:
        base = d.path or d.id
        if strategy == "fixed":
            words = re.sub(r"^## .*$", "", re.sub(r"^# .*\n", "", d.body, count=1), flags=re.M).split()
            for n, i in enumerate(range(0, len(words), size)):
                chunks.append(Chunk(f"{base}#f{n}", d.id, d.title, "", " ".join(words[i:i + size]),
                                    d.roles, d.status, d.version, bool(d.flagged)))
        else:
            for n, (head, text) in enumerate(_sections(d.body)):
                chunks.append(Chunk(f"{base}#s{n}", d.id, d.title, head, f"[{d.id}] {d.title} - {head}: {text}",
                                    d.roles, d.status, d.version, bool(d.flagged)))
    return chunks
