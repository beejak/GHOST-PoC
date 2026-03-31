# Governance and operating model (template)

This document is a **neutral template** for teams extending GHOST beyond the synthetic harness. It does not change runtime behavior in the repository; it records **decisions** that reduce ambiguity during rollout.

## 1. Charter (fill in)

- **Purpose:** What incident classes are in scope for automation v1?
- **Out of scope:** What must always escalate to humans?
- **Owner:** Name the role responsible for policy (`skills/`) changes and for production enablement.
- **Success metrics:** Examples: time-to-detect, time-to-remediate on allowlisted classes, false-positive rate budget, unplanned rollback count.

## 2. Autonomy tiers

Use explicit tiers; do not skip levels without a written decision.

| Tier | Behavior | Typical gate |
|------|----------|--------------|
| 0 – Observe | Ingest signals; no heals | Read-only adapters, logging only |
| 1 – Recommend | Propose action; human or ticket executes | Shadow mode, audit trail |
| 2 – Guardrailed execute | Allowlisted actions only, caps, timeouts | Staging + harness + game day |
| 3 – Expanded | Broader policy | Sustained tier-2 metrics, rollback drills |

The PoC defaults to **synthetic tier-2-shaped** tests in CI. Real tier 0/1 is supported **locally** via `adapters/observe.py` and `adapters/lab_run.py --dry-run`.

## 3. Policy change control

- All detection and remediation rules live in **`skills/`** (and related seed data).
- Merge criteria: **`python data/seed.py`** and **`python harness.py`** pass in CI.
- Optional: link policy version to `feedback_rows` payloads (already includes `policy_versions`).

## 4. Blast radius and safety

- Maintain a written **allowlist** of actions and per-service **quotas** (restarts/hour, max scale delta).
- Require **post-action verification** before declaring success in production-shaped environments.
- Define **kill switch** (disable automation, revert to observe-only).

## 5. Data and privacy

- Do not commit raw production logs. Use `data/external/` per [`data/external/README.md`](../data/external/README.md).
- Prefer **structured** platform signals where possible to reduce substring false positives.

## 6. Game days and drills

- Schedule periodic failure injection in **non-prod** (e.g. lab cluster) and compare outcomes to harness expectations.
- Record discrepancies as tickets or harness fixture updates.

## 7. Hermes / external agents

- External tools **propose** edits; they do not replace CI or on-call judgment. See [`integrations/hermes/TOOL_POLICY.json`](../integrations/hermes/TOOL_POLICY.json).
