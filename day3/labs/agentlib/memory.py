"""Memory for the NetNova agent, on Redis (fakeredis here: same commands, pip-only).

Two kinds of memory:
  short-term : the chat so far            -> a Redis LIST   key  chat:<user>:<session>
  long-term  : facts about the customer   -> a Redis HASH   key  profile:<user>

Four habits are built in (look for them):
  1. every key contains the user id        (security: no session bleed)
  2. every key has a TTL                   (privacy + cost: nothing lives forever)
  3. short-term history is trimmed to N    (cost: fewer tokens per call)
  4. forget_user() erases everything       (privacy: right to be forgotten)
"""
import atexit
import json
import time

import fakeredis

from . import config

_r = None


def get_redis():
    """One shared connection. Loads the last snapshot so memory survives restarts."""
    global _r
    if _r is None:
        _r = fakeredis.FakeRedis(decode_responses=True)
        _load_snapshot(_r)
        atexit.register(save_snapshot)
    return _r


def use_real_redis(url: str):
    """Optional: point the same code at a real Redis (redis://host:6379/0)."""
    global _r
    import redis  # pip install redis
    _r = redis.Redis.from_url(url, decode_responses=True)
    return _r


# ---------- snapshot (so Lab scripts can show "remembers across sessions") ----------
def save_snapshot(path=None):
    r = get_redis() if _r is None else _r
    path = path or config.SNAPSHOT
    dump = {}
    for k in r.keys("*"):
        t = r.type(k)
        ttl = r.ttl(k)
        item = {"type": t, "expires_at": (time.time() + ttl) if ttl and ttl > 0 else None}
        if t == "string":
            item["value"] = r.get(k)
        elif t == "list":
            item["value"] = r.lrange(k, 0, -1)
        elif t == "hash":
            item["value"] = r.hgetall(k)
        else:
            continue
        dump[k] = item
    try:
        path.write_text(json.dumps(dump))
    except Exception:
        pass


def _load_snapshot(r):
    try:
        dump = json.loads(config.SNAPSHOT.read_text())
    except Exception:
        return
    now = time.time()
    for k, item in dump.items():
        exp = item.get("expires_at")
        if exp is not None and exp <= now:
            continue
        v = item["value"]
        if item["type"] == "string":
            r.set(k, v)
        elif item["type"] == "list" and v:
            r.rpush(k, *v)
        elif item["type"] == "hash" and v:
            r.hset(k, mapping=v)
        if exp is not None:
            r.expire(k, max(1, int(exp - now)))


# ---------- key names ----------
def chat_key(user: str, session: str) -> str:
    return f"chat:{user}:{session}"          # <-- the user id is part of the key


def profile_key(user: str) -> str:
    return f"profile:{user}"


def ckpt_key(user: str, session: str) -> str:
    return f"ckpt:{user}:{session}"


# ---------- short-term memory ----------
def add_message(user, session, role, content, max_messages=None, ttl=None):
    r = get_redis()
    key = chat_key(user, session)
    r.rpush(key, json.dumps({"role": role, "content": content}))
    r.ltrim(key, -(max_messages or config.MAX_MESSAGES), -1)   # keep the last N only
    r.expire(key, ttl or config.TTL_SHORT)                      # and let it expire
    save_snapshot()


def get_history(user, session):
    return [json.loads(x) for x in get_redis().lrange(chat_key(user, session), 0, -1)]


# ---------- long-term memory ----------
def set_profile(user, ttl=None, **facts):
    r = get_redis()
    key = profile_key(user)
    r.hset(key, mapping={k: str(v) for k, v in facts.items()})
    r.expire(key, ttl or config.TTL_PROFILE)
    save_snapshot()


def get_profile(user):
    return get_redis().hgetall(profile_key(user))


# ---------- privacy ----------
def forget_user(user):
    """Erase every key that belongs to this user. Returns how many keys were deleted."""
    r = get_redis()
    keys = [k for k in r.keys("*") if k.split(":")[1:2] == [user]]
    if keys:
        r.delete(*keys)
    save_snapshot()
    return len(keys)


# ---------- for the Memory Inspector ----------
def inspect_keys(user=None):
    r = get_redis()
    rows = []
    for k in sorted(r.keys("*")):
        parts = k.split(":")
        if user and parts[1:2] != [user]:
            continue
        t = r.type(k)
        size = r.llen(k) if t == "list" else (r.hlen(k) if t == "hash" else len(r.get(k) or ""))
        rows.append({"key": k, "type": t, "items": size, "ttl_s": r.ttl(k)})
    return rows
