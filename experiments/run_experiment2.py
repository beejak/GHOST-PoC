"""Experiment 2: Full loop on clean failures with per-scenario infra reset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from agents.healer import heal_once
from agents.watcher import analyze_and_publish
from blackboard.event_bus import EventBus
from metrics.recorder import Recorder
from simulator.infra_state import baseline_state

ROOT = Path(__file__).resolve().parent.parent
DATA_CLEAN = ROOT / "data" / "clean_failures.json"


async def run(
    assertions: dict[str, Callable[[dict[str, Any]], bool]],
    recorder: Recorder | None = None,
) -> list[dict]:
    raw = json.loads(DATA_CLEAN.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for rec in raw:
        infra = baseline_state()
        bus = EventBus()
        reason = rec["labels"]["reason"]
        det = await analyze_and_publish(rec, bus, stream_index=None)
        if det is None:
            rows.append(
                {
                    "failure_type": reason,
                    "result": "FAIL",
                    "error": "not_detected",
                }
            )
            continue
        detect_ms = det * 1000

        def on_outcome(o: dict) -> None:
            if recorder:
                recorder.record_outcome(o)

        outcome = await heal_once(bus, infra, on_outcome=on_outcome)
        decide_ms = outcome["decide_ms"]
        act_ms = outcome["act_ms"]
        mttr_ms = detect_ms + decide_ms + act_ms
        assertion_fn = assertions.get(reason)
        passed = assertion_fn is not None and assertion_fn(infra) and outcome["success"]
        if recorder:
            recorder.record_detection(
                outcome["failure_type"], detect_ms, stream_index=None
            )
        rows.append(
            {
                "failure_type": reason,
                "result": "PASS" if passed else "FAIL",
                "detect_ms": detect_ms,
                "decide_ms": decide_ms,
                "act_ms": act_ms,
                "mttr_ms": mttr_ms,
            }
        )
    return rows
