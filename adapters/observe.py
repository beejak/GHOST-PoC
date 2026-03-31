#!/usr/bin/env python3
"""Read-only path: stream JSON log records from a file, run Watcher only, print events as JSON lines.

No Healer, no infra mutation. Use for shadowing production-shaped files locally.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.watcher import analyze_and_publish
from blackboard.event_bus import EventBus
from data.generator import stream_file


async def _run(path: Path) -> None:
    bus = EventBus()
    async for stream_index, rec in stream_file(path, interval_seconds=0.0):
        det_s = await analyze_and_publish(rec, bus, stream_index=stream_index)
        if det_s is None:
            continue
        event = await bus.consume()
        line = {
            "stream_index": stream_index,
            "detect_s": det_s,
            "failure_type": event["failure_type"],
            "severity": event["severity"],
            "service": event["service"],
            "message_preview": (event["message"] or "")[:200],
        }
        print(json.dumps(line, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(description="Watcher-only observe mode (JSON array file).")
    p.add_argument(
        "file",
        type=Path,
        help="Path to JSON array of log records (e.g. data/mixed_stream.json)",
    )
    args = p.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Not a file: {args.file}")
    asyncio.run(_run(args.file))


if __name__ == "__main__":
    main()
