"""Replay external normalized records against GHOST Watcher/Healer.

Usage (example):
  python tools/run_external_replay.py --data data/external/runs/<id>/normalized.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.healer import heal_once
from agents.k8s_watcher import analyze_k8s_signal_and_publish
from agents.watcher import analyze_and_publish
from blackboard.event_bus import EventBus
from data.generator import stream_file
from metrics.recorder import Recorder
from simulator.infra_state import baseline_state
from skills.healer_skills import DECISION_TABLE


def _derive_ground_truth(
    records: list[dict[str, Any]],
) -> tuple[dict[int, dict[str, Any]], int]:
    gt_by_index: dict[int, dict[str, Any]] = {}
    healthy = 0
    for idx, rec in enumerate(records):
        reason = rec.get("labels", {}).get("reason")
        if reason in DECISION_TABLE:
            action, params = DECISION_TABLE[reason]
            gt_by_index[idx] = {
                "index": idx,
                "failure_type": reason,
                "expected_action": action,
                "expected_params": params,
            }
        else:
            healthy += 1
    return gt_by_index, healthy


async def run(
    data_path: Path | str,
    *,
    ground_truth_path: Path | str | None = None,
    recorder: Recorder | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    p = Path(data_path)
    records = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("External data must be a JSON array")

    if ground_truth_path is not None:
        gt_raw = json.loads(Path(ground_truth_path).read_text(encoding="utf-8"))
        gt_by_index: dict[int, dict[str, Any]] = {g["index"]: g for g in gt_raw}
        healthy_count = len(records) - len(gt_by_index)
    else:
        gt_by_index, healthy_count = _derive_ground_truth(records)

    failure_indices = set(gt_by_index.keys())
    infra = baseline_state()
    bus = EventBus()
    detections: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []

    async for stream_index, rec in stream_file(p, interval_seconds=0.0):
        if isinstance(rec.get("signal"), dict):
            det_s = await analyze_k8s_signal_and_publish(rec, bus, stream_index=stream_index)
        else:
            det_s = await analyze_and_publish(rec, bus, stream_index=stream_index)
        if det_s is None:
            continue

        detect_ms = det_s * 1000

        def on_outcome(o: dict[str, Any]) -> None:
            if recorder:
                recorder.record_outcome(o)

        outcome = await heal_once(bus, infra, on_outcome=on_outcome, dry_run=dry_run)
        mttr_ms = detect_ms + outcome["decide_ms"] + outcome["act_ms"]
        failure_type = outcome["failure_type"]
        detections.append(
            {"index": stream_index, "failure_type": failure_type, "detect_ms": detect_ms}
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
            recorder.record_detection(failure_type, detect_ms, stream_index=stream_index)

    matched = 0
    for idx, gt in gt_by_index.items():
        det = next((d for d in detections if d["index"] == idx), None)
        if det and det["failure_type"] == gt["failure_type"]:
            matched += 1

    false_positives = sum(1 for d in detections if d["index"] not in failure_indices)

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
        "healthy_count": healthy_count,
        "resolved": resolved,
        "avg_mttr_ms": avg_mttr,
        "detections": detections,
        "data_path": str(p),
        "ground_truth_source": str(ground_truth_path) if ground_truth_path else "derived_from_labels",
        "dry_run": dry_run,
    }
