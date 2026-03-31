#!/usr/bin/env python3
"""Lab runner: stream a JSON log array through Watcher + Healer against simulator state.

  python adapters/lab_run.py [--dry-run] data/mixed_stream.json

--dry-run  Log chosen actions but do not call ACTION_REGISTRY (infra unchanged).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.healer import heal_once
from agents.watcher import analyze_and_publish
from blackboard.event_bus import EventBus
from data.generator import stream_file
from simulator.infra_state import baseline_state


async def _run(path: Path, *, dry_run: bool) -> None:
    infra = baseline_state()
    bus = EventBus()
    stats: dict[str, Any] = {
        "records": 0,
        "detections": 0,
        "dry_run": dry_run,
        "outcomes": [],
    }
    async for stream_index, rec in stream_file(path, interval_seconds=0.0):
        stats["records"] += 1
        det_s = await analyze_and_publish(rec, bus, stream_index=stream_index)
        if det_s is None:
            continue
        stats["detections"] += 1
        detect_ms = det_s * 1000
        outcome = await heal_once(bus, infra, dry_run=dry_run)
        mttr_ms = detect_ms + outcome["decide_ms"] + outcome["act_ms"]
        stats["outcomes"].append(
            {
                "index": stream_index,
                "failure_type": outcome["failure_type"],
                "action_taken": outcome["action_taken"],
                "success": outcome["success"],
                "mttr_ms": mttr_ms,
                "dry_run": outcome.get("dry_run", False),
            }
        )
    print(json.dumps(stats, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="Lab: full loop on JSON log array.")
    p.add_argument(
        "file",
        type=Path,
        help="Path to JSON array of log records",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not mutate simulator (skip action execution)",
    )
    args = p.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Not a file: {args.file}")
    asyncio.run(_run(args.file, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
