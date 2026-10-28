"""The architecture diagram (SVG). Boxes light up for the node that is running."""

NAVY, MUTED = "#1b2333", "#5b6b8c"
FILL = {"io": "#eef2fb", "guard": "#fff0dc", "agent": "#efeaff", "tool": "#e3f5ea", "mem": "#e0f3f4", "model": "#f1e8fb",
        "human": "#ffe3e3"}


def active_for(ev=None):
    """Which boxes are in use for this event?"""
    if not ev:
        return set()
    node, summ = ev["node"], ev["summary"]
    if node == "think":
        a = {"think", "gateway", "memory"}
        if "INPUT GUARD" in summ:
            a = {"inguard", "think"}
        if ev["step"] == 0 and ev["n"] == 1:
            a |= {"user", "inguard"}
        return a
    if node == "guard":
        a = {"guard"}
        if any(w in summ for w in ("WAITING", "APPROVED", "REJECTED")):
            a.add("human")
        return a
    if node == "act":
        return {"act", "tools"}
    if node == "observe":
        return {"observe", "memory"}
    if node == "finish":
        return {"outguard", "user"}
    return set()


def _box(i, x, y, w, h, title, sub, kind, active):
    fill = "#fff1b8" if i in active else FILL[kind]
    stroke = "#e08a00" if i in active else MUTED
    sw = 5 if i in active else 2
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" text-anchor="middle" font-size="20" font-weight="700" fill="{NAVY}">{title}</text>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + 22}" text-anchor="middle" font-size="15" fill="{MUTED}">{sub}</text>')


def _arrow(d, both=False, dash=False):
    ms = ' marker-start="url(#a)"' if both else ""
    da = ' stroke-dasharray="7 6"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="2.5"{da} marker-end="url(#a)"{ms}/>'


def arch_svg(active=frozenset(), note=""):
    A = set(active)
    s = [f'<svg viewBox="0 0 1100 670" xmlns="http://www.w3.org/2000/svg" font-family="Aptos Narrow, Segoe UI, Arial, sans-serif" style="width:100%;background:#ffffff;border-radius:12px">',
         f'<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{MUTED}"/></marker></defs>']
    # agent container
    s.append(f'<rect x="350" y="120" width="400" height="330" rx="18" fill="#faf8ff" stroke="#7a68d8" stroke-width="2.5" stroke-dasharray="9 6"/>')
    s.append(f'<text x="490" y="438" font-size="17" font-weight="700" fill="#4b3aa8">AGENT · LangGraph</text>')
    s.append(f'<text x="550" y="292" text-anchor="middle" font-size="15" fill="{MUTED}">loops until a final answer,</text>')
    s.append(f'<text x="550" y="313" text-anchor="middle" font-size="15" fill="{MUTED}">max steps or budget</text>')
    s.append(f'<text x="550" y="334" text-anchor="middle" font-size="15" font-weight="700" fill="#4b3aa8">state saved after every box</text>')
    # arrows (drawn first so boxes sit on top)
    s += [_arrow("M145 290 H175"), _arrow("M315 290 H360 V200 H385"),                      # user -> inguard -> think
          _arrow("M535 200 H570"), _arrow("M645 235 V340"), _arrow("M570 375 H535"), _arrow("M460 340 V235"),
          _arrow("M460 90 V165"), _arrow("M645 90 V165"),                              # gateway, human
          _arrow("M720 375 H790", both=True),                                          # act <-> tools
          _arrow("M460 410 V490", both=True),                                          # observe <-> memory
          _arrow("M750 290 H785"),                                                     # agent -> output guard
          _arrow("M935 290 H1060 V590 H80 V330")]                                      # back to the customer
    s.append(f'<text x="560" y="582" font-size="15" fill="{MUTED}">answer back to the customer</text>')
    # boxes
    s.append(_box("user", 15, 250, 130, 80, "Customer", "asks a question", "io", A))
    s.append(_box("inguard", 175, 250, 140, 80, "Input guard", "injection scan", "guard", A))
    s.append(_box("think", 385, 165, 150, 70, "think", "write a plan", "agent", A))
    s.append(_box("guard", 570, 165, 150, 70, "guard", "check + risk", "guard", A))
    s.append(_box("act", 570, 340, 150, 70, "act", "run the tool", "agent", A))
    s.append(_box("observe", 385, 340, 150, 70, "observe", "read the result", "agent", A))
    s.append(_box("outguard", 785, 250, 150, 80, "Output guard", "mask PII, no leaks", "guard", A))
    s.append(_box("gateway", 385, 20, 150, 70, "Gateway", "LiteLLM · chat-llm", "model", A))
    s.append(_box("human", 560, 20, 170, 70, "Human", "approves writes", "human", A))
    s.append(_box("tools", 790, 340, 250, 80, "Tools", "rag · ticket · plan · change", "tool", A))
    s.append(_box("memory", 345, 490, 230, 76, "Memory (Redis)", "chat · facts · checkpoints", "mem", A))
    s.append(_box("finops", 610, 490, 200, 76, "FinOps meter", "tokens · $ · budget", "io", set()))
    s.append(_box("evals", 840, 490, 200, 76, "Eval gate", "tests before release", "io", set()))
    # culture band
    s.append(f'<rect x="20" y="610" width="1060" height="46" rx="12" fill="#eef7f0" stroke="#9cc9a9" stroke-width="1.5"/>')
    s.append(f'<text x="550" y="640" text-anchor="middle" font-size="19" font-weight="700" fill="#1f5f36">Habits wrapped around every box:   🔒 Secure   ·   💰 FinOps   ·   🛡️ Guardrails   ·   ✅ Evals</text>')
    if note:
        s.append(f'<text x="20" y="480" font-size="17" font-weight="700" fill="#b36a00">{note}</text>')
    s.append("</svg>")
    return "".join(s)
