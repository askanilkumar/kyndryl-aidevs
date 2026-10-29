import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
ROOT = LAB.parent.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(ROOT / "common"))

from memory import DictMemory, RedisMemory


# ---- Lab 1B: dict memory keeps turns in order ----

def test_1b_dict_keeps_order():
    m = DictMemory()
    m.add("s", "user", "hello")
    m.add("s", "assistant", "hi")
    m.add("s", "user", "how are you")
    assert [x["content"] for x in m.history("s")] == ["hello", "hi", "how are you"]


def test_1b_dict_isolates_sessions():
    m = DictMemory()
    m.add("A", "user", "one")
    m.add("B", "user", "two")
    assert m.history("A") == [{"role": "user", "content": "one"}]
    assert m.history("B") == [{"role": "user", "content": "two"}]


# ---- Lab 1C: Redis-backed memory, same contract ----

def test_1c_redis_round_trip():
    m = RedisMemory()
    m.add("sess", "user", "anil")
    m.add("sess", "assistant", "hello anil")
    hist = m.history("sess")
    assert len(hist) == 2
    assert hist[0]["role"] == "user" and hist[0]["content"] == "anil"
    assert hist[1]["role"] == "assistant"


def test_1c_redis_isolates_sessions():
    m = RedisMemory()
    m.add("A", "user", "aaa")
    m.add("B", "user", "bbb")
    assert m.history("A")[0]["content"] == "aaa"
    assert m.history("B")[0]["content"] == "bbb"


def test_1c_clear():
    m = RedisMemory()
    m.add("x", "user", "y")
    m.clear("x")
    assert m.history("x") == []


# ---- Lab 1 SOLO: max_messages trimming ----

def test_solo_trim_keeps_only_last_n():
    m = RedisMemory(max_messages=3)
    for i in range(6):
        m.add("s", "user", f"msg {i}")
    kept = [h["content"] for h in m.history("s")]
    assert kept == ["msg 3", "msg 4", "msg 5"], f"expected last 3, got {kept}"
