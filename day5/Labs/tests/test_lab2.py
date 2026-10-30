"""Lab 2 check:  python -m pytest tests/test_lab2.py -q"""
from asknova import agent
from asknova.tracing import Tracer


def test_trace_has_input_guard_span():
    tracer = Tracer("off")
    agent.run("What is the status of INC-5001?", tracer=tracer, log=False)
    names = [s.name for s in tracer.spans]
    assert "guard:input" in names, f"Spans are {names}. Wrap the input guard in a span (TODO Lab 2 in asknova/agent.py)"
    assert names[0] == "asknova" and "llm" in names and "tool:get_ticket" in names


def test_spans_have_timing_and_tokens():
    tracer = Tracer("off")
    agent.run("Roaming price for prepaid in UAE?", tracer=tracer, log=False)
    llm = [s for s in tracer.spans if s.kind == "generation"]
    assert llm and all(s.tokens_in > 0 for s in llm)
