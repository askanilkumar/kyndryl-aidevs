# Day 4 — Governed Agent (MCP · Registry · RBAC · HITL · Audit)

## Run order
```
Terminal A:  python mcp_server.py        (keep running)
Terminal B:  streamlit run app.py
```

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit app, 5 tabs |
| `mcp_server.py` | FastAPI MCP server, 4 tools |
| `mcp_client.py` | tiny HTTP client the agent uses |
| `agent.py` | LangGraph agent: plan → guard → execute |
| `rbac.py` | registry lookup + audit log |
| `llm.py` | gateway (if key given) or offline stand-in |
| `kb.py` | small telecom KB |
| `registry.json` | **policy** — who may call what |
| `tabs/` | 5 Streamlit tab modules |
| `solo_lab/scenario.md` | Solo lab brief |
| `tests/` | 11 pytest cases |

## Keys
No `.env`. Paste `GATEWAY_BASE_URL` + `GATEWAY_KEY` into the Streamlit sidebar. Offline mode works with no key.
