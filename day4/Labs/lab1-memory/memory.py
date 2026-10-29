"""
Memory — a small store for one chat session's past turns.

Two backends behind the same interface:
  - DictMemory     — in-process Python dict. Dies on restart. Good for tests.
  - RedisMemory    — fakeredis by default (pip-only), swappable to real Redis.

Public API (both classes):
    .add(session_id, role, content)
    .history(session_id)            -> list[dict]
    .clear(session_id)
"""

from __future__ import annotations

import json
from typing import Any


# ---------- backend 1: plain dict (RAM) ----------

class DictMemory:
    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def add(self, session_id: str, role: str, content: str) -> None:
        self._store.setdefault(session_id, []).append({"role": role, "content": content})

    def history(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)


# ---------- backend 2: Redis (fakeredis by default) ----------

class RedisMemory:
    """Same interface, but one Redis LIST per session.
    Keys look like:  askit:mem:<session_id>
    Each entry is a JSON string {"role": ..., "content": ...}.
    """

    PREFIX = "askit:mem:"

    def __init__(self, redis_client=None, max_messages: int | None = None):
        if redis_client is None:
            import fakeredis
            redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.r = redis_client
        self.max_messages = max_messages  # None = unlimited (Lab 1 Solo turns this on)

    def _key(self, session_id: str) -> str:
        return self.PREFIX + session_id

    def add(self, session_id: str, role: str, content: str) -> None:
        k = self._key(session_id)
        self.r.rpush(k, json.dumps({"role": role, "content": content}))
        # Solo 1 fills this part in: trim history to the last N messages.
        if self.max_messages is not None:
            # keep the last max_messages items in the list.
            self.r.ltrim(k, -self.max_messages, -1)

    def history(self, session_id: str) -> list[dict]:
        raw = self.r.lrange(self._key(session_id), 0, -1)
        return [json.loads(x) for x in raw]

    def clear(self, session_id: str) -> None:
        self.r.delete(self._key(session_id))
