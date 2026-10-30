"""The AskNova agent loop (Day 4) + guardrails (Lab 1) + tracing (Lab 2) + monitoring log (Lab 3).

Flow of one question:
   input guard -> mask PII -> [ LLM -> tool -> LLM ... ] (max 5 steps) -> output guard -> answer
"""
import json
import time
from dataclasses import dataclass, field

from . import config, guards, monitor
from .llm import active_version, call_llm, load_prompt
from .tools import ALLOWED_TOOLS, TOOL_SPECS, WRITE_TOOLS, call_tool
from .tracing import Tracer


@dataclass
class Result:
    answer: str = ""
    blocked: bool = False
    guard_hits: list = field(default_factory=list)   # which guard fired and why
    masked: bool = False
    tools_used: list = field(default_factory=list)
    needs_approval: list = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    steps: int = 0
    error: str = ""


def run(question, *, client=None, model=config.DEFAULT_MODEL, tracer=None, prompt_version=None,
        guards_on=True, use_moderation=False, approve_writes=False, user="participant", log=True):
    tracer = tracer or Tracer("off")
    tracer.new_run()
    prompt_version = prompt_version or active_version()
    res = Result()
    t0 = time.perf_counter()
    if client is None:
        model = "offline"

    with tracer.span("asknova", "agent", input=question) as root:
        try:
            text = question
            if guards_on:
                # ---- Layer 1: input guard ----
                # TODO (Lab 2): wrap the next 2 lines in a span, exactly like the output guard below:
                #     with tracer.span("guard:input", "guardrail", input=question) as g:
                #         ... and call g.update(output=...) at the end
                check = guards.check_input(question)
                if not check.ok:
                    res.guard_hits.append(f"input: {check.reason}")
                if check.ok and use_moderation and client is not None:
                    mod = guards.moderation(client, question)
                    if not mod.ok:
                        res.guard_hits.append(f"input: {mod.reason}")
                if res.guard_hits:
                    res.blocked, res.answer = True, guards.SAFE_REPLY
                    root.update(output=res.answer)
                    return _finish(res, t0, model, prompt_version, question, user, log, root)

                # ---- Layer 2: mask PII before the model sees it ----
                text = guards.mask_pii(question)
                res.masked = text != question

            messages = [{"role": "system", "content": load_prompt(prompt_version)},
                        {"role": "user", "content": text}]
            last_call = None
            for step in range(config.MAX_STEPS):
                res.steps = step + 1
                with tracer.span("llm", "generation", input=messages[-1]["content"]) as s:
                    reply = call_llm(client, model, messages, TOOL_SPECS)
                    s.update(output=reply.content or str(reply.tool_calls), model=model,
                             tokens_in=reply.tokens_in, tokens_out=reply.tokens_out)
                res.tokens_in += reply.tokens_in
                res.tokens_out += reply.tokens_out

                if not reply.tool_calls:                       # the model gave a final answer
                    res.answer = reply.content
                    break

                messages.append(reply.assistant_message)
                for call_id, name, args in reply.tool_calls:
                    this_call = (name, json.dumps(args, sort_keys=True))
                    if this_call == last_call:                # same call twice in a row = loop (Day 4 bug)
                        out = "STOP: same tool call repeated. Answer with what you have."
                    elif name not in ALLOWED_TOOLS:          # guardrail: tool allow-list
                        out = f"Tool {name} is not allowed."
                        res.guard_hits.append(f"tool: {name} not allowed")
                    elif name in WRITE_TOOLS and not approve_writes:
                        out = f"NEEDS_APPROVAL: {name} {args} must be approved by a supervisor first."
                        res.needs_approval.append(f"{name} {args}")
                    else:
                        with tracer.span(f"tool:{name}", "tool", input=args) as t:
                            out = call_tool(name, args)
                            # ---- Layer 3a: tool output guard (stop INTERNAL docs reaching the model) ----
                            tg = guards.check_output(out) if guards_on else guards.GuardResult(True)
                            if not tg.ok:
                                res.guard_hits.append(f"tool output: {tg.reason}")
                                out = "[REDACTED: this document is not for customers]"
                            t.update(output=out)
                    last_call = this_call
                    res.tools_used.append(name)
                    messages.append({"role": "tool", "tool_call_id": call_id, "content": out})
            else:
                res.answer = res.answer or "I could not finish in 5 steps. A human agent will follow up."

            if guards_on:
                # ---- Layer 3b: output guard on the final answer ----
                with tracer.span("guard:output", "guardrail", input=res.answer) as g:
                    out_check = guards.check_output(res.answer)
                    if not out_check.ok:
                        res.guard_hits.append(f"output: {out_check.reason}")
                        res.answer = guards.SAFE_REPLY
                    res.answer = guards.mask_pii(res.answer)
                    g.update(output="ok" if out_check.ok else out_check.reason)
            res.blocked = bool(res.guard_hits)
        except Exception as e:                                # errors are logged, not shown as a crash
            res.error = f"{type(e).__name__}: {e}"
            res.answer = "Sorry, something went wrong. Please try again."
        root.update(output=res.answer)
        return _finish(res, t0, model, prompt_version, question, user, log, root)


def _finish(res, t0, model, prompt_version, question, user, log, root):
    res.latency_ms = int((time.perf_counter() - t0) * 1000)
    res.cost = config.cost_usd(model, res.tokens_in, res.tokens_out)
    root.update(output=res.answer, model=model, tokens_in=res.tokens_in, tokens_out=res.tokens_out)
    if log:
        monitor.log_request(user=user, question=guards.mask_pii(question), res=res,
                            model=model, prompt_version=prompt_version)
    return res
