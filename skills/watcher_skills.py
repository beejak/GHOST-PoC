# skills/watcher_skills.py

from __future__ import annotations

AGENT_NAME = "watcher"
AGENT_VERSION = "1.1.0"

# What the Watcher looks for.
# Each entry: failure_type -> list of substrings (store lowercase).
# Match: ANY substring matches message under case-insensitive containment (Unicode casefold).
# Ordering is significant: first matching type wins — list more specific / higher-signal
# patterns before broader ones within each type, and types in a stable priority order.
#
# Rationale: container runtimes (Kubernetes, Docker, Nomad, ECS-style logs, PaaS) use
# different wording; case-insensitive matching avoids bias toward one vendor's casing.
DETECTABLE_PATTERNS = {
    "OOMKilled": [
        "oomkilled",
        "oom kill",
        "out of memory",
        "exceeded memory limit",
        "memory cgroup",
        "cgroup memory",
        "killed due to memory",
        "memory limit exceeded",
    ],
    "CrashLoopBackOff": [
        "crashloopbackoff",
        "crash loop",
        "back-off restarting",
        "backoff restarting",
        "restarting failed container",
        "too many restarts",
        "exponential backoff",
        "restart limit",
        "repeatedly crashing",
    ],
    "StartupProbeFailed": [
        "startup probe failed",
        "readiness probe failed",
        "startup probe timed out",
        "readiness probe timed out",
        "liveness probe failed",
        "health check failed",
        "connection refused",
    ],
    "HighLatency": [
        "exceeds threshold",
        "slow response",
        "deadline exceeded",
        "request timeout",
        "upstream timeout",
        "high latency",
        "tail latency",
        "latency spike",
    ],
}

# Severity levels the Watcher pays attention to. Others are ignored.
# Comparison is case-insensitive on the log record's severity field.
WATCHED_SEVERITIES = ["ERROR", "WARNING"]

# How often Watcher polls the log stream in seconds.
POLL_INTERVAL_SECONDS = 1

# Structure of every event Watcher puts on the queue.
EVENT_SCHEMA = {
    "failure_type": str,
    "severity":     str,
    "service":      str,
    "message":      str,
    "timestamp":    float,
    "raw_log":      dict,
}

# Hard boundaries. Watcher must never do these things.
CANNOT_DO = [
    "execute_actions",
    "modify_infra_state",
    "make_decisions",
    "call_external_apis",
]


def severity_is_watched(severity: object) -> bool:
    return isinstance(severity, str) and severity.upper() in WATCHED_SEVERITIES


def message_matches_failure_type(message: str) -> str | None:
    """Return failure_type if any pattern matches under casefold containment; else None."""
    hay = message.casefold()
    for failure_type, patterns in DETECTABLE_PATTERNS.items():
        for pattern in patterns:
            if pattern.casefold() in hay:
                return failure_type
    return None


def any_pattern_matches_message(message: str) -> bool:
    """True if message would trigger any detection (for healthy-baseline checks)."""
    return message_matches_failure_type(message) is not None
