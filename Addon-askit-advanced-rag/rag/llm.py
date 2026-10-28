"""Thin wrapper over the model provider that records tokens, cost and latency for every call.
Providers: "openai" (needs an OpenAI API key) and "offline" (no keys: deterministic stand-ins so the app still runs)."""
import hashlib, json, os, re, time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from datetime import datetime
import numpy as np

from .config import PRICES, DEFAULT_CHAT_MODEL, DEFAULT_EMBED_MODEL


_DEFAULT_CACHE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache"))


class UsageLog:
    def __init__(self):
        self.rows = []

    def add(self, op, model, tin, tout, latency_ms, prices=None, note=""):
        p = (prices or PRICES).get(model) or (prices or PRICES).get(re.sub(r"^(us|eu|apac)\.", "", model), (0.0, 0.0))
        cost = tin / 1e6 * p[0] + tout / 1e6 * p[1]
        row = dict(time=datetime.now().strftime("%H:%M:%S"), operation=op, model=model,
                   input_tokens=int(tin), output_tokens=int(tout), cost_usd=round(cost, 6),
                   latency_ms=int(latency_ms), note=note)
        self.rows.append(row)
        return row


def _extract_json(text):
    """Models sometimes wrap JSON in ``` fences or add a sentence. Return just the JSON object."""
    t = (text or "").strip()
    m = re.search(r"\{.*\}", t, re.S)
    return m.group(0) if m else t


class LLM:
    """provider: "openai" | "offline" | None. None = "openai" if an api_key is given, else offline."""

    def __init__(self, api_key=None, chat_model=None, embed_model=None, prices=None, log=None, cache_dir=None,
                 provider=None):
        self.provider = provider or ("openai" if api_key else "offline")
        self.offline = self.provider == "offline"
        chat_model = chat_model or DEFAULT_CHAT_MODEL
        embed_model = embed_model or DEFAULT_EMBED_MODEL
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.prices = prices or PRICES
        self.log = log or UsageLog()
        self.cache_dir = cache_dir or _DEFAULT_CACHE   # inside the lab folder, whatever the current folder is
        os.makedirs(self.cache_dir, exist_ok=True)
        self.client = None
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)

    # ---------- embeddings (cached on disk: re-runs cost nothing) ----------
    def _cache_path(self):
        name = "offline" if self.offline else re.sub(r"[^A-Za-z0-9._-]", "_", self.embed_model)   # Windows: no ':' in file names
        return os.path.join(self.cache_dir, f"emb_{name}.json")

    def embed(self, texts, op="embed"):
        path = self._cache_path()
        try:
            with open(path, encoding="utf-8") as f:
                cache = json.load(f)
        except (OSError, ValueError):   # no cache yet, or a half-written one
            cache = {}
        keys = [hashlib.sha1(t.encode()).hexdigest() for t in texts]
        missing = [(k, t) for k, t in zip(keys, texts) if k not in cache]
        if missing:
            t0 = time.perf_counter()
            if self.offline:
                for k, t in missing:
                    cache[k] = _hash_embed(t)
                self.log.add(op, "offline-hash", sum(len(t) // 4 for _, t in missing), 0,
                             (time.perf_counter() - t0) * 1000, self.prices, f"{len(missing)} texts")
            else:
                resp = self.client.embeddings.create(model=self.embed_model, input=[t for _, t in missing])
                for (k, _), d in zip(missing, resp.data):
                    cache[k] = d.embedding
                self.log.add(op, self.embed_model, resp.usage.prompt_tokens, 0,
                             (time.perf_counter() - t0) * 1000, self.prices, f"{len(missing)} texts")
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cache, f)
            os.replace(tmp, path)
        return np.array([cache[k] for k in keys], dtype=float)

    # ---------- chat ----------
    def chat(self, messages, op="generate", json_mode=False, tools=None, model=None):
        """Returns (message, usage_row). message has .content and .tool_calls (OpenAI object)."""
        model = model or self.chat_model
        t0 = time.perf_counter()
        kwargs = dict(model=model, messages=messages)
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if tools:
            kwargs["tools"] = tools
        if model.startswith("gpt-5"):  # reasoning model: keep "thinking" short for fast lookups
            kwargs["reasoning_effort"] = "minimal"
        resp = self.client.chat.completions.create(**kwargs)
        u = resp.usage
        row = self.log.add(op, model, u.prompt_tokens, u.completion_tokens,
                           (time.perf_counter() - t0) * 1000, self.prices)
        return resp.choices[0].message, row

    def log_offline(self, op, prompt_text, output_text, t0):
        return self.log.add(op, "offline", len(prompt_text) // 4, len(output_text) // 4,
                            (time.perf_counter() - t0) * 1000, self.prices)


def _hash_embed(text, dim=256):
    """Offline stand-in for embeddings: hashed bag of words (NOT semantic)."""
    v = np.zeros(dim)
    for w in text.lower().split():
        w = "".join(c for c in w if c.isalnum())
        if w:
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % dim] += 1
    n = np.linalg.norm(v)
    return (v / n).tolist() if n else v.tolist()
