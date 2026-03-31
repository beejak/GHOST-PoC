"""Experiment 5: Near-real noisy mixed stream (200 records, 20 failures) vs ground truth."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.healer import heal_once
from agents.watcher import analyze_and_publish
from blackboard.event_bus import EventBus
from data.generator import stream_file
from metrics.recorder import Recorder
from simulator.infra_state import baseline_state

ROOT = Path(__file__).resolve().parent.parent
DATA_NEAR = ROOT / "data" / "near_real_stream.json"
DATA_GT = ROOT / "data" / "near_real_ground_truth.json"

NEAR_HEALTHY = 180


async def run(recorder: Recorder | None = None) -> dict[str, Any]:
    gt_raw = json.loads(DATA_GT.read_text(encoding="utf-8"))
    gt_by_index: dict[int, dict[str, Any]] = {g["index"]: g for g in gt_raw}
    failure_indices = set(gt_by_index.keys())

    infra = baseline_state()
    bus = EventBus()

    detections: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []

    async for stream_index, rec in stream_file(DATA_NEAR, interval_seconds=0.0):
        det_s = await analyze_and_publish(rec, bus, stream_index=stream_index)
        if det_s is None:
            continue
        detect_ms = det_s * 1000

        def on_outcome(o: dict[str, Any]) -> None:
            if recorder:
                recorder.record_outcome(o)

        outcome = await heal_once(bus, infra, on_outcome=on_outcome)
        mttr_ms = detect_ms + outcome["decide_ms"] + outcome["act_ms"]

        failure_type = outcome["failure_type"]
        detections.append(
            {
                "index": stream_index,
                "failure_type": failure_type,
                "detect_ms": detect_ms,
            }
        )
        outcomes.append(
            {
                "index": stream_index,
                "failure_type": failure_type,
                "outcome": outcome,
                "mttr_ms": mttr_ms,
            }
        )
        if recorder:
            recorder.record_detection(
                failure_type, detect_ms, stream_index=stream_index
            )

    matched = 0
    for idx, gt in gt_by_index.items():
        det = next((d for d in detections if d["index"] == idx), None)
        if det and det["failure_type"] == gt["failure_type"]:
            matched += 1

    false_positives = sum(
        1 for d in detections if d["index"] not in failure_indices
    )

    resolved = 0
    for idx, gt in gt_by_index.items():
        oc = next((o for o in outcomes if o["index"] == idx), None)
        if not oc:
            continue
        o = oc["outcome"]
        if (
            o["success"]
            and o["action_taken"] == gt["expected_action"]
            and o["action_params"] == gt["expected_params"]
        ):
            resolved += 1

    mttr_values = [o["mttr_ms"] for o in outcomes]
    avg_mttr = sum(mttr_values) / len(mttr_values) if mttr_values else 0.0

    return {
        "detected": matched,
        "total_failures": len(gt_by_index),
        "false_positives": false_positives,
        "healthy_count": NEAR_HEALTHY,
        "resolved": resolved,
        "avg_mttr_ms": avg_mttr,
        "detections": detections,
    }
