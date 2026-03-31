#!/usr/bin/env python3
"""CLI wrapper for experiments.run_experiment_external."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.run_experiment_external import run
from metrics.recorder import Recorder


async def _main(data: Path, gt: Path | None, dry_run: bool, record: bool) -> None:
    recorder = Recorder("experiment_external") if record else None
    try:
        summary = await run(
            data,
            ground_truth_path=gt,
            recorder=recorder,
            dry_run=dry_run,
        )
    finally:
        if recorder:
            recorder.close()
    print(json.dumps(summary, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(description="Replay external normalized data through GHOST.")
    p.add_argument("--data", type=Path, required=True, help="Normalized JSON array records")
    p.add_argument("--ground-truth", type=Path, default=None, help="Optional GT JSON")
    p.add_argument("--dry-run", action="store_true", help="Skip infra mutation in healer")
    p.add_argument("--record", action="store_true", help="Write rows into metrics/results.db")
    args = p.parse_args()
    if not args.data.is_file():
        raise SystemExit(f"Missing data file: {args.data}")
    if args.ground_truth and not args.ground_truth.is_file():
        raise SystemExit(f"Missing ground truth file: {args.ground_truth}")
    asyncio.run(_main(args.data, args.ground_truth, args.dry_run, args.record))


if __name__ == "__main__":
    main()
