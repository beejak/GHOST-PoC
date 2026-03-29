"""Experiment 1: Watcher only — detection on clean_failures.json."""

from __future__ import annotations

import json
from pathlib import Path

from agents.watcher import analyze_and_publish
from blackboard.event_bus import EventBus
from metrics.recorder import Recorder

ROOT = Path(__file__).resolve().parent.parent
DATA_CLEAN = ROOT / "data" / "clean_failures.json"


async def run(recorder: Recorder | None = None) -> list[dict]:
    raw = json.loads(DATA_CLEAN.read_text(encoding="utf-8"))
    results: list[dict] = []
    for rec in raw:
        bus = EventBus()
        t = await analyze_and_publish(rec, bus, stream_index=None)
        if t is None:
            results.append(
                {
                    "failure_type": rec.get("labels", {}).get("reason", "unknown"),
                    "detect_ms": None,
                    "result": "FAIL",
                    "expected": rec.get("labels", {}).get("reason"),
                }
            )
            continue
        evt = await bus.consume()
        detected = evt["failure_type"]
        expected = rec["labels"]["reason"]
        ok = detected == expected
        detect_ms = t * 1000
        if recorder:
            recorder.record_detection(detected, detect_ms, stream_index=None)
        results.append(
            {
                "failure_type": expected,
                "detect_ms": detect_ms,
                "result": "PASS" if ok else "FAIL",
                "detected_as": detected,
            }
        )
    return results
