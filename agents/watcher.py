"""Log reader and pattern matcher — imports patterns only from watcher_skills."""

from __future__ import annotations

import time
from typing import Any

from blackboard.event_bus import EventBus
from skills.watcher_skills import DETECTABLE_PATTERNS, WATCHED_SEVERITIES


async def analyze_and_publish(
    record: dict[str, Any],
    bus: EventBus,
    stream_index: int | None = None,
) -> float | None:
    """
    If record matches a failure pattern, publish an event and return
    detection duration in seconds; otherwise return None.
    """
    if record.get("severity") not in WATCHED_SEVERITIES:
        return None

    msg = record.get("message", "")
    t0 = time.perf_counter()

    for failure_type, patterns in DETECTABLE_PATTERNS.items():
        for pattern in patterns:
            if pattern in msg:
                raw = {**record}
                if stream_index is not None:
                    raw["stream_index"] = stream_index
                event = {
                    "failure_type": failure_type,
                    "severity": record["severity"],
                    "service": record.get("service", "app-service"),
                    "message": msg,
                    "timestamp": time.time(),
                    "raw_log": raw,
                }
                await bus.publish(event)
                return time.perf_counter() - t0

    return None
