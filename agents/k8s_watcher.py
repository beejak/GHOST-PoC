"""Structured K8s-style signal reader — imports rules only from k8s_signal_skills."""

from __future__ import annotations

import time
from typing import Any

from blackboard.event_bus import EventBus
from skills.k8s_signal_skills import classify_signal
from skills.watcher_skills import severity_is_watched


async def analyze_k8s_signal_and_publish(
    record: dict[str, Any],
    bus: EventBus,
    stream_index: int | None = None,
) -> float | None:
    """
    If record.signal matches a rule, emit the same event shape as the log Watcher.
    """
    if not severity_is_watched(record.get("severity")):
        return None

    signal = record.get("signal")
    t0 = time.perf_counter()
    failure_type = classify_signal(signal) if isinstance(signal, dict) else None
    if failure_type is None:
        return None

    raw = {**record}
    if stream_index is not None:
        raw["stream_index"] = stream_index
    event = {
        "failure_type": failure_type,
        "severity": record["severity"],
        "service": record.get("service", "app-service"),
        "message": record.get("message", ""),
        "timestamp": time.time(),
        "raw_log": raw,
    }
    await bus.publish(event)
    return time.perf_counter() - t0
