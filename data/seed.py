"""Generate synthetic log datasets for GHOST POC."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.healer_skills import DECISION_TABLE
from skills.watcher_skills import DETECTABLE_PATTERNS

DATA_DIR = Path(__file__).resolve().parent

CLEAN_FAILURES = [
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "OOMKilled: container exceeded memory limit 512Mi",
        "labels": {"reason": "OOMKilled"},
    },
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Back-off restarting failed container",
        "labels": {"reason": "CrashLoopBackOff"},
    },
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Startup probe failed: connection refused on port 9090",
        "labels": {"reason": "StartupProbeFailed"},
    },
    {
        "severity": "WARNING",
        "service": "app-service",
        "message": "Response time 7200ms exceeds threshold 5000ms",
        "labels": {"reason": "HighLatency", "latency_ms": 7200},
    },
]

HEALTHY_TEMPLATES = [
    "Request processed in {ms}ms",
    "Health check passed on port {port}",
    "Container started successfully",
    "Scaling event completed. Instances: {n}",
    "Connected to upstream service",
    "Graceful shutdown initiated",
    "Configuration reloaded successfully",
    "Liveness probe passed",
    "Cache warmed. Entries: {n}",
    "Scheduled task completed in {ms}ms",
    "Memory usage nominal: {pct}% of limit",
    "CPU utilisation: {pct}%",
    "Disk usage: {pct}% of allocated",
    "Outbound connection established",
    "Request queue depth: {n}",
    "Response time {ms}ms within threshold",
    "Replica count stable at {n}",
    "Log rotation completed",
    "Dependency check passed",
    "Startup sequence complete",
]


def _all_detection_substrings() -> list[str]:
    out: list[str] = []
    for patterns in DETECTABLE_PATTERNS.values():
        out.extend(patterns)
    return out


def _violates_healthy(message: str) -> bool:
    return any(p in message for p in _all_detection_substrings())


def _make_healthy_record(rng: random.Random, seq_id: int) -> dict:
    for _ in range(500):
        template = rng.choice(HEALTHY_TEMPLATES)
        if "{ms}" in template:
            msg = template.format(ms=rng.randint(1, 499))
        elif "{port}" in template:
            msg = template.format(port=rng.choice([8080, 8443, 3000, 5000]))
        elif "{n}" in template:
            msg = template.format(n=rng.randint(1, 20))
        elif "{pct}" in template:
            msg = template.format(pct=rng.randint(1, 99))
        else:
            msg = template
        if not _violates_healthy(msg):
            return {
                "severity": "INFO",
                "service": "app-service",
                "message": msg,
                "labels": {"healthy": True},
                "id": f"h-{seq_id}",
                "timestamp": rng.random() * 1e9,
            }
    raise RuntimeError("Could not generate a healthy record without pattern overlap")


def _stamp_failure(rec: dict, seq_id: int, rng: random.Random) -> dict:
    out = {**rec, "id": f"f-{seq_id}", "timestamp": rng.random() * 1e9}
    return out


def _failure_catalog(rng: random.Random) -> list[dict]:
    """10 failures: at least 2 per type (3+3+2+2)."""
    types = (
        ["OOMKilled"] * 3
        + ["CrashLoopBackOff"] * 3
        + ["StartupProbeFailed"] * 2
        + ["HighLatency"] * 2
    )
    rng.shuffle(types)
    by_reason = {c["labels"]["reason"]: c for c in CLEAN_FAILURES}
    return [_stamp_failure(by_reason[t], i, rng) for i, t in enumerate(types)]


def _assert_healthy_baseline(records: list[dict]) -> None:
    for rec in records:
        msg = rec.get("message", "")
        if _violates_healthy(msg):
            raise SystemExit(
                f"Healthy baseline assertion failed: message contains detection pattern: {msg!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    clean = []
    for i, rec in enumerate(CLEAN_FAILURES):
        clean.append(
            {
                **rec,
                "id": f"clean-{i}",
                "timestamp": float(i) + rng.random(),
            }
        )

    healthy = [_make_healthy_record(rng, i) for i in range(50)]
    _assert_healthy_baseline(healthy)

    failures = _failure_catalog(rng)
    healthy_for_mix = [_make_healthy_record(rng, 1000 + i) for i in range(90)]

    mixed: list[dict | None] = [None] * 100
    slots = list(range(100))
    rng.shuffle(slots)
    inject_slots = sorted(slots[:10])
    rest_slots = sorted(slots[10:])

    for slot, frec in zip(inject_slots, failures):
        mixed[slot] = frec
    for slot, hrec in zip(rest_slots, healthy_for_mix):
        mixed[slot] = hrec

    stream = mixed
    assert None not in stream

    ground_truth = []
    for idx, rec in enumerate(stream):
        reason = rec.get("labels", {}).get("reason")
        if reason in DECISION_TABLE:
            action, params = DECISION_TABLE[reason]
            ground_truth.append(
                {
                    "index": idx,
                    "failure_type": reason,
                    "expected_action": action,
                    "expected_params": params,
                }
            )

    paths = {
        "clean_failures.json": clean,
        "healthy_baseline.json": healthy,
        "mixed_stream.json": stream,
        "mixed_stream_ground_truth.json": ground_truth,
    }
    for name, data in paths.items():
        (DATA_DIR / name).write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    sep = "=" * 39
    print("GHOST POC - Synthetic Data Generation")
    print(sep)
    print(f"Random seed:         {args.seed}")
    print(sep)
    print("clean_failures.json       4 records   4 failure events")
    print("healthy_baseline.json    50 records   0 failure events")
    print("mixed_stream.json       100 records  10 failure events")
    print("mixed_stream_ground_truth.json  10 entries")
    print(sep)
    print("Healthy baseline assertion: PASSED - zero failure patterns in healthy set")
    print("All files written to data/")


if __name__ == "__main__":
    main()
