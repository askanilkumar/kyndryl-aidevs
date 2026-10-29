# Solo Lab — Incident INC-5102

**Time:** 14:30 IST · **Zone:** Chennai North · **Severity:** P1

Three cell towers (TWR-CHN-11, TWR-CHN-12, TWR-CHN-13) are DOWN. Customer care is receiving a spike in calls. NOC lead has handed the triage to you.

You are logged in as **supervisor**.

## What to do
1. Confirm the incident — `ticket_lookup` → INC-5102.
2. Check each tower's state — `tower_status`.
3. Pull the right runbook — `kb_search` for "mass outage escalation".
4. Customer **C-1002 (Priya Shah)** called in angry. Apply a goodwill upgrade — `plan_change` to PLAN-202. Approve it as the human.
5. Download `audit.jsonl` and point out:
   - no unauthorised call,
   - approval line before executed line for `plan_change`,
   - incident touched only once.

## Pass gates (shown live in Tab 4)
- `ticket_lookup` executed
- `tower_status` executed
- `kb_search` executed
- `plan_change` proposed
- `plan_change` approved
- `plan_change` executed

## Stretch — pick any ONE
A. Add a 5th tool `tower_restart(tower_id)` — high risk, supervisor-only, requires approval.
B. Tighten over-permission in `registry.json` and defend in 3 lines.
C. Prove the audit trail closes the incident cleanly.

## Submission
`submission/day4_notes.md` — role split, one risk added to registry, one removed.
