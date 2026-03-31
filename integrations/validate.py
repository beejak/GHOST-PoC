#!/usr/bin/env python3
"""Validate integration contract files and core repo paths (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    policy_path = ROOT / "integrations" / "hermes" / "TOOL_POLICY.json"
    if not policy_path.is_file():
        print("FAIL: missing", policy_path)
        return 1
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print("FAIL: invalid JSON", policy_path, e)
        return 1

    required_keys = (
        "read_globs",
        "write_globs",
        "forbid_globs",
        "required_after_skills_change",
        "ghost_invariants",
    )
    for k in required_keys:
        if k not in policy:
            print("FAIL: TOOL_POLICY.json missing key", k)
            return 1

    required_paths = [
        "skills/watcher_skills.py",
        "skills/healer_skills.py",
        "skills/k8s_signal_skills.py",
        "agents/watcher.py",
        "agents/healer.py",
        "agents/k8s_watcher.py",
        "harness.py",
        "data/seed.py",
        "integrations/gstack/SKILL_GHOST_MAINTAINER.md",
        "integrations/hermes/COORDINATOR_PROMPT_SNIPPET.md",
        "docs/GOVERNANCE.md",
        "adapters/observe.py",
        "adapters/lab_run.py",
        "experiments/run_experiment5.py",
    ]
    missing = [p for p in required_paths if not (ROOT / p).is_file()]
    if missing:
        print("FAIL: expected files missing:")
        for m in missing:
            print(" ", m)
        return 1

    # Forbid writing results db in policy (simulated prod artifact)
    forbids = policy.get("forbid_globs", [])
    if "metrics/results.db" not in forbids:
        print("WARN: recommend forbidding metrics/results.db in TOOL_POLICY.json")

    print("integrations/validate.py: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
