#!/usr/bin/env python3
"""Normalize lab capture files into GHOST replay format.

Input:
  --events <events.json>  (from kubectl get events -o json)
  --logs <logs.txt>       (from kubectl logs)

Output:
  --out-records <normalized.json>
  --out-gt <ground_truth.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.healer_skills import DECISION_TABLE


def _event_to_record(e: dict[str, Any]) -> dict[str, Any] | None:
    reason = str(e.get("reason", ""))
    msg = str(e.get("message", ""))
    obj = e.get("involvedObject", {}) if isinstance(e.get("involvedObject"), dict) else {}
    kind = str(obj.get("kind", ""))
    name = str(obj.get("name", "app-service"))

    signal: dict[str, Any] | None = None
    failure_type: str | None = None

    if reason in {"ImagePullBackOff", "ErrImagePull"}:
        failure_type = "ImagePullBackOff"
        signal = {"record_type": "Pod", "phase": "Pending", "reason": reason}
    elif reason == "FailedScheduling":
        failure_type = "SchedulingBlocked"
        signal = {"record_type": "Pod", "phase": "Pending", "reason": reason}
    elif reason == "NodeNotReady" or "NotReady" in msg:
        failure_type = "NodeNotReady"
        signal = {"record_type": "Node", "condition": "NotReady", "name": name}
    elif reason == "BackOff":
        low_msg = msg.lower()
        if "pulling image" in low_msg or "errimagepull" in low_msg or "image pull" in low_msg:
            # Kubernetes often emits reason=BackOff with message "Back-off pulling image ..."
            # Treat this as image pull failure so structured signal rules can classify it.
            failure_type = "ImagePullBackOff"
            signal = {"record_type": "Pod", "phase": "Pending", "reason": "ImagePullBackOff"}
        else:
            failure_type = "CrashLoopBackOff"
    elif reason == "Unhealthy" and (
        "probe failed" in msg.lower() or "connection refused" in msg.lower()
    ):
        failure_type = "StartupProbeFailed"
    elif "oomkilled" in msg.lower() or "out of memory" in msg.lower():
        failure_type = "OOMKilled"

    if failure_type is None:
        return None

    severity = "WARNING" if failure_type == "HighLatency" else "ERROR"
    rec: dict[str, Any] = {
        "severity": severity,
        "service": "app-service",
        "message": f"{reason}: {msg}" if reason else msg,
        "labels": {"reason": failure_type, "source": "k8s_event", "kind": kind},
    }
    if signal is not None:
        rec["signal"] = signal
    return rec


def _logs_to_records(log_text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in log_text.splitlines():
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        sev = "INFO"
        if any(k in low for k in ("error", "failed", "timeout", "oom", "back-off", "crash")):
            sev = "ERROR"
        elif any(k in low for k in ("warn", "latency", "slow")):
            sev = "WARNING"
        out.append(
            {
                "severity": sev,
                "service": "app-service",
                "message": line,
                "labels": {"source": "pod_log"},
            }
        )
    return out


def _build_ground_truth(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gt: list[dict[str, Any]] = []
    for idx, rec in enumerate(records):
        reason = rec.get("labels", {}).get("reason")
        if reason in DECISION_TABLE:
            action, params = DECISION_TABLE[reason]
            gt.append(
                {
                    "index": idx,
                    "failure_type": reason,
                    "expected_action": action,
                    "expected_params": params,
                }
            )
    return gt


def main() -> None:
    p = argparse.ArgumentParser(description="Normalize k8s lab capture to GHOST JSON.")
    p.add_argument("--events", type=Path, required=True)
    p.add_argument("--logs", type=Path, required=True)
    p.add_argument("--out-records", type=Path, required=True)
    p.add_argument("--out-gt", type=Path, required=True)
    args = p.parse_args()

    events_raw = json.loads(args.events.read_text(encoding="utf-8"))
    items = events_raw.get("items", []) if isinstance(events_raw, dict) else []
    event_records: list[dict[str, Any]] = []
    for e in items:
        if isinstance(e, dict):
            rec = _event_to_record(e)
            if rec:
                event_records.append(rec)

    log_records = _logs_to_records(args.logs.read_text(encoding="utf-8"))
    records = event_records + log_records
    gt = _build_ground_truth(records)

    args.out_records.parent.mkdir(parents=True, exist_ok=True)
    args.out_gt.parent.mkdir(parents=True, exist_ok=True)
    args.out_records.write_text(json.dumps(records, indent=2), encoding="utf-8")
    args.out_gt.write_text(json.dumps(gt, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "records": len(records),
                "ground_truth": len(gt),
                "events_kept": len(event_records),
                "logs_kept": len(log_records),
                "out_records": str(args.out_records),
                "out_gt": str(args.out_gt),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
