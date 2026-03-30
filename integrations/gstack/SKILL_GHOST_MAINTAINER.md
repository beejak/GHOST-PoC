---
description: Maintain GHOST PoC policy (skills) and keep harness green
---

# GHOST maintainer (Claude Code / [gstack](https://github.com/garrytan/gstack)-compatible skill)

## Context

Repository: **GHOST PoC** — autonomous loop: Watcher / K8s-signal watcher → Healer on simulated `app-service` state. Policy is **only** in `skills/`.

## Before editing

- Read `skills/watcher_skills.py`, `skills/healer_skills.py`, `skills/k8s_signal_skills.py` as appropriate.  
- Read `docs/VISION_LAYERED_LEARNING.md` if changing architecture boundaries.

## Rules

1. **Never** inline `DETECTABLE_PATTERNS` or `DECISION_TABLE` in `agents/` — import from `skills/`.  
2. New heal actions: implement in `simulator/infra_state.py`, register in `ACTION_REGISTRY`, add `DECISION_TABLE` row.  
3. If `data/seed.py` changes, ensure healthy baseline still passes `any_pattern_matches_message()`.  
4. Service name stays **`app-service`** unless the whole spec is intentionally revised.

## After editing (required)

From repo root:

```bash
python data/seed.py
python harness.py
python integrations/validate.py
```

## Output

- Short summary: files touched, failure types affected, harness result (all experiments).  
- If harness fails, **revert or fix** before suggesting merge.
