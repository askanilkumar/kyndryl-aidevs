"""Lab 2 - Tracing. One small wrapper, three back-ends:
   off       -> spans are kept only in the app (the "Trace" panel under each answer)
   langsmith -> spans are also sent to LangSmith (smith.langchain.com)
   langfuse  -> spans are also sent to Langfuse (cloud.langfuse.com)
Every agent step is a span:  agent -> guard -> llm -> tool -> llm -> guard
"""
import time
from contextlib import contextmanager

_clients = {}   # one SDK client per key, so Streamlit reruns don't create new ones


class Span:
    def __init__(self, name, kind, input):
        self.name, self.kind, self.input = name, kind, input
        self.output, self.model, self.tokens_in, self.tokens_out = None, None, 0, 0
        self.start, self.ms = time.perf_counter(), 0
        self._ls = None   # LangSmith run
        self._lf = None   # Langfuse observation
        self.scores = {}

    def update(self, output=None, model=None, tokens_in=0, tokens_out=0):
        self.output, self.model = output, model or self.model
        self.tokens_in, self.tokens_out = tokens_in or self.tokens_in, tokens_out or self.tokens_out

    def score(self, name, value):
        """Attach a score (for example an eval result) to the whole trace."""
        self.scores[name] = value


class Tracer:
    def __init__(self, mode="off", keys=None, project="asknova-day5"):
        self.mode, self.keys, self.project = mode, keys or {}, project
        self.spans = []          # every span of the last run (shown in the app)
        self.trace_url = None
        self.error = None
        self._ls_stack = []

    # ---------- the one function the agent uses ----------
    @contextmanager
    def span(self, name, kind="span", input=None):
        s = Span(name, kind, input)
        self.spans.append(s)
        try:
            if self.mode == "langsmith":
                with self._langsmith_span(s):
                    yield s
            elif self.mode == "langfuse":
                with self._langfuse_span(s):
                    yield s
            else:
                yield s
        finally:
            s.ms = int((time.perf_counter() - s.start) * 1000)

    def new_run(self):
        self.spans, self.trace_url = [], None

    # ---------- LangSmith ----------
    def _ls_client(self):
        from langsmith import Client
        key = (self.keys.get("langsmith_key"), self.keys.get("langsmith_endpoint"))
        if key not in _clients:
            _clients[key] = Client(api_key=key[0], api_url=key[1] or "https://api.smith.langchain.com")
        return _clients[key]

    @contextmanager
    def _langsmith_span(self, s):
        """LangSmith: build a tree of runs; the whole tree is sent when the agent span ends."""
        run_type = {"agent": "chain", "generation": "llm", "tool": "tool", "guardrail": "chain"}.get(s.kind, "chain")
        try:
            from langsmith.run_trees import RunTree
            if self._ls_stack:
                rt = self._ls_stack[-1].create_child(name=s.name, run_type=run_type, inputs={"input": s.input})
            else:
                rt = RunTree(name=s.name, run_type=run_type, inputs={"input": s.input},
                             project_name=self.project, ls_client=self._ls_client())
        except Exception as e:      # tracing must never break the app
            self.error = f"LangSmith: {e}"
            yield
            return
        self._ls_stack.append(rt)
        try:
            yield
        finally:
            self._ls_stack.pop()
            try:
                outputs = {"output": s.output}
                if s.kind == "generation":
                    rt.extra.setdefault("metadata", {}).update({"ls_provider": "openai", "ls_model_name": s.model})
                    outputs["usage_metadata"] = {"input_tokens": s.tokens_in, "output_tokens": s.tokens_out,
                                                 "total_tokens": s.tokens_in + s.tokens_out}
                rt.end(outputs=outputs)
                if not self._ls_stack:                       # root span: send the whole tree
                    rt.post(exclude_child_runs=False)
                    client = self._ls_client()
                    for k, v in s.scores.items():
                        client.create_feedback(run_id=rt.id, key=k, score=v)
                    self.trace_url = "https://smith.langchain.com  (open project: " + self.project + ")"
            except Exception as e:
                self.error = f"LangSmith: {e}"

    # ---------- Langfuse ----------
    def _lf_client(self):
        from langfuse import Langfuse
        key = (self.keys.get("langfuse_public"), self.keys.get("langfuse_secret"), self.keys.get("langfuse_host"))
        if key not in _clients:
            _clients[key] = Langfuse(public_key=key[0], secret_key=key[1],
                                     host=key[2] or "https://cloud.langfuse.com")
        return _clients[key]

    @contextmanager
    def _langfuse_span(self, s):
        try:
            lf = self._lf_client()
            cm = lf.start_as_current_observation(name=s.name, as_type=s.kind, input=s.input)
            obs = cm.__enter__()
        except Exception as e:
            self.error = f"Langfuse: {e}"
            yield
            return
        err = None
        try:
            yield
        except Exception as e:
            err = e
            raise
        finally:
            try:
                if s.kind == "generation":
                    obs.update(output=s.output, model=s.model,
                               usage_details={"input": s.tokens_in, "output": s.tokens_out})
                else:
                    obs.update(output=s.output)
                for k, v in s.scores.items():
                    obs.score_trace(name=k, value=v)
                trace_id = obs.trace_id
                cm.__exit__(type(err) if err else None, err, None)
                if s.kind == "agent":
                    lf.flush()
                    self.trace_url = lf.get_trace_url(trace_id=trace_id)
            except Exception as e:
                self.error = f"Langfuse: {e}"

    def flush(self):
        for c in _clients.values():
            try:
                c.flush()
            except Exception:
                pass
