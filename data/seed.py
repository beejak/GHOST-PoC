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
from skills.watcher_skills import any_pattern_matches_message

DATA_DIR = Path(__file__).resolve().parent

# Synthetic structured signals (Pod/Node/Deployment) — same shape a real informer could emit later.
K8S_SIGNAL_SCENARIOS: list[dict] = [
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Pod app-7d4fb Pending: ImagePullBackOff",
        "labels": {"reason": "ImagePullBackOff", "channel": "k8s_signal"},
        "signal": {
            "record_type": "Pod",
            "phase": "Pending",
            "reason": "ImagePullBackOff",
            "namespace": "prod",
        },
    },
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Pod app-9zz ErrImagePull: manifest unknown",
        "labels": {"reason": "ImagePullBackOff", "channel": "k8s_signal"},
        "signal": {
            "record_type": "Pod",
            "phase": "Pending",
            "reason": "ErrImagePull",
            "namespace": "prod",
        },
    },
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Pod app-2k9 Pending: FailedScheduling (insufficient cpu)",
        "labels": {"reason": "SchedulingBlocked", "channel": "k8s_signal"},
        "signal": {
            "record_type": "Pod",
            "phase": "Pending",
            "reason": "FailedScheduling",
            "namespace": "prod",
        },
    },
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Node pool-1 NotReady: kubelet not reporting",
        "labels": {"reason": "NodeNotReady", "channel": "k8s_signal"},
        "signal": {
            "record_type": "Node",
            "condition": "NotReady",
            "name": "pool-1",
        },
    },
    {
        "severity": "WARNING",
        "service": "app-service",
        "message": "Deployment app-service: 0/3 replicas ready",
        "labels": {"reason": "ReplicaMismatch", "channel": "k8s_signal"},
        "signal": {
            "record_type": "Deployment",
            "replica_drift": True,
            "name": "app-service",
        },
    },
    {
        "severity": "ERROR",
        "service": "app-service",
        "message": "Pod app-abc Failed: Evicted (node pressure)",
        "labels": {"reason": "PodDown", "channel": "k8s_signal"},
        "signal": {
            "record_type": "Pod",
            "phase": "Failed",
            "reason": "Evicted",
            "namespace": "prod",
        },
    },
]

# Multiple paraphrases per failure class (mixed casing) — reduces bias toward one log vendor or template.
FAILURE_TEMPLATES: dict[str, list[str]] = {
    "OOMKilled": [
        "OOMKilled: container exceeded memory limit 512Mi",
        "cgroup: oom_kill invoked; memory cgroup limit exceeded",
        "Process killed: out of memory (rss exceeded cgroup cap)",
        "runtime: Memory limit exceeded — OOMKilled",
    ],
    "CrashLoopBackOff": [
        "Back-off restarting failed container",
        "CrashLoopBackOff: pod has restarted 5 times",
        "exponential backoff: container crashing repeatedly (exit 1)",
        "Too many restarts — applying restart limit backoff",
    ],
    "StartupProbeFailed": [
        "Startup probe failed: connection refused on port 9090",
        "READINESS probe failed after 3 attempts: connection refused",
        "Health check failed: dial tcp [::1]:9090: connection refused",
        "Startup probe timed out: target not accepting connections",
    ],
    "HighLatency": [
        "Response time 7200ms exceeds threshold 5000ms",
        "WARN: slow response from upstream (p99 breach)",
        "request timeout after 30s waiting for dependency",
        "deadline exceeded: tail latency spike on critical path",
    ],
}


def _pick_clean_failures(seed: int) -> list[dict]:
    """One row per failure type; message template chosen from diverse pool (deterministic per seed)."""
    order = ["OOMKilled", "CrashLoopBackOff", "StartupProbeFailed", "HighLatency"]
    rows = []
    for i, reason in enumerate(order):
        templates = FAILURE_TEMPLATES[reason]
        msg = templates[(seed + i * 17) % len(templates)]
        sev = "WARNING" if reason == "HighLatency" else "ERROR"
        labels: dict = {"reason": reason}
        if reason == "HighLatency":
            labels["latency_ms"] = 7200
        rows.append(
            {
                "severity": sev,
                "service": "app-service",
                "message": msg,
                "labels": labels,
            }
        )
    return rows


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
    "Duration {ms}ms within threshold",
    "Replica count stable at {n}",
    "Log rotation completed",
    "Dependency check passed",
    "Startup sequence complete",
]


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
        if not any_pattern_matches_message(msg):
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
    """10 failures: at least 2 per type (3+3+2+2); each uses a random template from its class."""
    types = (
        ["OOMKilled"] * 3
        + ["CrashLoopBackOff"] * 3
        + ["StartupProbeFailed"] * 2
        + ["HighLatency"] * 2
    )
    rng.shuffle(types)
    out = []
    for i, t in enumerate(types):
        templates = FAILURE_TEMPLATES[t]
        msg = rng.choice(templates)
        sev = "WARNING" if t == "HighLatency" else "ERROR"
        labels: dict = {"reason": t}
        if t == "HighLatency":
            labels["latency_ms"] = rng.choice([5000, 7200, 9000])
        out.append(
            _stamp_failure(
                {"severity": sev, "service": "app-service", "message": msg, "labels": labels},
                i,
                rng,
            )
        )
    return out


def _assert_healthy_baseline(records: list[dict]) -> None:
    for rec in records:
        msg = rec.get("message", "")
        if any_pattern_matches_message(msg):
            raise SystemExit(
                f"Healthy baseline assertion failed: message contains detection pattern: {msg!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    clean_src = _pick_clean_failures(args.seed)
    clean = []
    for i, rec in enumerate(clean_src):
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

    k8s_clean = []
    for i, rec in enumerate(K8S_SIGNAL_SCENARIOS):
        k8s_clean.append(
            {
                **rec,
                "id": f"k8s-clean-{i}",
                "timestamp": float(200 + i) + rng.random(),
            }
        )

    paths = {
        "clean_failures.json": clean,
        "healthy_baseline.json": healthy,
        "mixed_stream.json": stream,
        "mixed_stream_ground_truth.json": ground_truth,
        "k8s_clean_signals.json": k8s_clean,
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
    print("k8s_clean_signals.json      6 records   6 K8s-style signal scenarios")
    print(sep)
    print("Healthy baseline assertion: PASSED - zero failure patterns in healthy set")
    print("All files written to data/")


if __name__ == "__main__":
    main()
