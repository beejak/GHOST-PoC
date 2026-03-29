# skills/watcher_skills.py

AGENT_NAME = "watcher"
AGENT_VERSION = "1.0.0"

# What the Watcher looks for.
# Each entry: failure_type -> list of strings.
# Match fires if ANY string in the list appears in the log message (OR logic).
# Generic container runtime signatures — workload-agnostic.
DETECTABLE_PATTERNS = {
    "OOMKilled":          ["OOMKilled", "exceeded memory limit", "killed process"],
    "CrashLoopBackOff":   ["Back-off restarting", "CrashLoopBackOff", "restart limit"],
    "StartupProbeFailed": ["Startup probe failed", "readiness probe failed",
                           "connection refused", "health check failed"],
    "HighLatency":        ["latency", "response time", "exceeds threshold", "timeout"],
}

# Severity levels the Watcher pays attention to. Others are ignored.
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
