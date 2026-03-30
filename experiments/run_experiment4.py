"""Experiment 4: Full loop on synthetic Kubernetes-style structured signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from agents.healer import heal_once
from agents.k8s_watcher import analyze_k8s_signal_and_publish
from blackboard.event_bus import EventBus
from metrics.recorder import Recorder
from simulator.infra_state import apply_k8s_failure_preset, baseline_state

ROOT = Path(__file__).resolve().parent.parent
DATA_K8S = ROOT / "data" / "k8s_clean_signals.json"


async def run(
    assertions: dict[str, Callable[[dict[str, Any]], bool]],
    recorder: Recorder | None = None,
) -> list[dict]:
    raw = json.loads(DATA_K8S.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for rec in raw:
        reason = rec["labels"]["reason"]
        infra = baseline_state()
        apply_k8s_failure_preset(infra, reason)
        bus = EventBus()
        det = await analyze_k8s_signal_and_publish(rec, bus, stream_index=None)
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
