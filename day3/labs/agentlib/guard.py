"""Guardrails + security checks. Small, readable rules (not magic).

Three places a guard sits:
  INPUT   scan text for prompt-injection tricks before the model sees it
  TOOL    allow-list, argument checks, "only your own account"
  OUTPUT  mask personal data, never leak internal notes or another customer
"""
import re

ALLOWED_TOOLS = {"rag_search", "ticket_lookup", "plan_lookup", "change_plan"}
RISKY_TOOLS = {"change_plan"}                     # writes need a human
VALID_PLANS = {"Basic 199", "Plus 499", "Max 999"}

INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|above|prior) (instructions|rules)",
    r"disregard (all |any )?(the )?(previous|above|prior)",
    r"reveal (the |your )?(system )?prompt",
    r"you are now",
    r"without (asking|approval|confirmation)",
    r"do not (ask|tell) (the )?(user|human|customer)",
    r"(upgrade|change) .* to max 999 .*(free|no charge)",
]

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "aadhaar": re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)"),
    "card": re.compile(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)"),
}


def scan_injection(text: str):
    """Return the list of suspicious patterns found in `text` (empty = looks fine)."""
    t = (text or "").lower()
    return [p for p in INJECTION_PATTERNS if re.search(p, t)]


def mask_pii(text: str) -> str:
    """Replace phone / email / Aadhaar / card numbers with masked tags. Use before LOGGING."""
    out = text or ""
    for name in ("card", "aadhaar", "email", "phone"):      # longest patterns first
        out = PII_PATTERNS[name].sub(f"[{name.upper()} MASKED]", out)
    return out


def check_tool(plan: dict, user: str):
    """Return (ok, reason). Runs BEFORE any tool is executed."""
    tool, args = plan.get("tool"), plan.get("args", {}) or {}
    if tool not in ALLOWED_TOOLS:
        return False, f"tool '{tool}' is not on the allow-list"
    cust = args.get("customer")
    if cust and cust != user:
        return False, f"you may only access your own account ({user}), not {cust}"
    if tool == "change_plan" and args.get("new_plan") not in VALID_PLANS:
        return False, f"unknown plan '{args.get('new_plan')}' (valid: {sorted(VALID_PLANS)})"
    if tool == "ticket_lookup" and not re.fullmatch(r"TKT-\d{4}", str(args.get("ticket_id", ""))):
        return False, "ticket id must look like TKT-2001"
    return True, "ok"


def risk_of(plan: dict) -> str:
    if plan.get("tool") in RISKY_TOOLS:
        return "HIGH (changes money/plan) - needs human approval"
    if plan.get("tool") in ALLOWED_TOOLS:
        return "low (read only)"
    return "unknown"


def check_output(answer: str, user: str):
    """Return (safe_answer, findings). Masks PII and blocks internal / other-customer data."""
    findings = []
    safe = answer or ""
    if "INTERNAL" in safe:
        findings.append("internal note in answer")
        safe = "I can't share internal notes. Please contact support for more help."
    others = [c for c in re.findall(r"cust-\d{4}", safe) if c != user]
    if others:
        findings.append(f"another customer's id in answer: {sorted(set(others))}")
        safe = re.sub(r"cust-\d{4}", lambda m: m.group(0) if m.group(0) == user else "[OTHER CUSTOMER]", safe)
    masked = mask_pii(safe)
    if masked != safe:
        findings.append("personal data masked")
    return masked, findings
