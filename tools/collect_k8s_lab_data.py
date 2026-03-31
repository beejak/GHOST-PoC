#!/usr/bin/env python3
"""Collect Kubernetes events and pod logs from a lab namespace.

Outputs under data/external/runs/<run_id>/:
  - events.json
  - logs.txt
  - meta.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "data" / "external" / "runs"


def _run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out.stdout


def main() -> None:
    p = argparse.ArgumentParser(description="Collect lab events/logs via kubectl.")
    p.add_argument("--namespace", default="ghost-lab")
    p.add_argument("--selector", default="app=app-service")
    p.add_argument("--run-id", default=None)
    args = p.parse_args()

    run_id = args.run_id or time.strftime("%Y%m%d-%H%M%S")
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    events = _run(
        [
            "kubectl",
            "get",
            "events",
            "-n",
            args.namespace,
            "-o",
            "json",
            "--sort-by=.lastTimestamp",
        ]
    )
    logs = _run(
        [
            "kubectl",
            "logs",
            "-n",
            args.namespace,
            "-l",
            args.selector,
            "--all-containers=true",
            "--tail=2000",
        ]
    )

    (out_dir / "events.json").write_text(events, encoding="utf-8")
    (out_dir / "logs.txt").write_text(logs, encoding="utf-8")
    (out_dir / "meta.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "namespace": args.namespace,
                "selector": args.selector,
                "collected_at_epoch": time.time(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(str(out_dir))


if __name__ == "__main__":
    main()
