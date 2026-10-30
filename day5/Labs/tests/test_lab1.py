"""Lab 1 check:  python -m pytest tests/test_lab1.py -q"""
from asknova import agent, guards


def test_all_6_attacks_are_stopped():
    for text, expect in guards.ATTACKS:
        res = agent.run(text, log=False)
        if expect == "blocked":
            assert res.blocked, f"Not blocked: {text}  -> add a pattern in asknova/guards.py (TODO Lab 1)"
        else:
            assert res.masked, f"PII not masked: {text}"


def test_normal_questions_still_work():
    for q in ["What is the status of INC-5001?", "Roaming price for prepaid in UAE?", "How do I change my plan?"]:
        res = agent.run(q, log=False)
        assert not res.blocked, f"A normal question was blocked: {q}  -> your pattern is too wide"


def test_pii_is_masked():
    assert guards.mask_pii("call 9876543210 or mail a.b@example.com") == "call [PHONE] or mail [EMAIL]"
