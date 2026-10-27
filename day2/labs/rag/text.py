"""Tiny text helpers: tokens for keyword search."""
import re

STOP = set("a an the is are was were be to of in on at for and or with my me i you your it this that do does did can how what which who when where from as by if not no".split())
SYN = {  # used ONLY by the offline stand-in embedding, to fake a little "meaning"
    "money back": "refund", "reimburse": "refund", "reimbursement": "refund",
    "cost": "price", "charge": "price", "fee": "price", "much": "price",
    "gigabytes": "data", "gb": "data", "internet": "data",
    "abroad": "roaming", "overseas": "roaming", "international": "roaming",
    "stolen": "lost", "number": "mobile",
}


def stem(w):
    for suf in ("ing", "es", "ed", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokens(s, keep_stop=False):
    raw = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", (s or "").lower())
    return [stem(t) if "-" not in t else t for t in raw if keep_stop or t not in STOP]


ID_RE = re.compile(r"\b[A-Z]{2,5}-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
