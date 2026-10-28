"""LAB 1b - Same memory, but in Redis. Now it survives a restart.

(Redis here is 'fakeredis': a pure-Python Redis. The commands are exactly the real ones.)

RUN:   python lab1b_redis_memory.py      <- run it TWICE and compare the output
THEN:  change the key name 'demo:chat' to 'demo:chat2'. What happens to the old messages?
"""
import json

from agentlib import memory

r = memory.get_redis()
KEY = "demo:chat"

before = r.lrange(KEY, 0, -1)
print(f"messages already in Redis when we started: {len(before)}")

r.rpush(KEY, json.dumps({"role": "user", "content": "Hi, my name is Anil"}))     # RPUSH = add to the end of a list
r.rpush(KEY, json.dumps({"role": "assistant", "content": "Nice to meet you, Anil"}))
r.expire(KEY, 120)                                                               # EXPIRE = forget after 120 s

print("LRANGE  :", [json.loads(x)["content"] for x in r.lrange(KEY, 0, -1)])
print("LLEN    :", r.llen(KEY), "messages")
print("TTL     :", r.ttl(KEY), "seconds left before Redis forgets this")
print("TYPE    :", r.type(KEY))

memory.save_snapshot()      # write memory to disk so the next run can load it
print("\nRun this script again: the list is longer, because Redis remembered.")

from agentlib.habits import footer   # noqa: E402
footer()
