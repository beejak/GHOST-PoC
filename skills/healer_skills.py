# skills/healer_skills.py

AGENT_NAME = "healer"
AGENT_VERSION = "1.0.0"

# Decision table — single source of truth for all action mappings.
# Each entry: failure_type -> (action_name, action_params)
# Healer does not decide what to do. It looks up what to do.
DECISION_TABLE = {
    "OOMKilled": (
        "scale_memory",
        {"memory": "1Gi"}
    ),
    "CrashLoopBackOff": (
        "reset_and_redeploy",
        {"restart_count": 0, "status": "running"}
    ),
    "StartupProbeFailed": (
        "fix_port",
        {"port": 8080}
    ),
    "HighLatency": (
        "scale_instances",
        {"max_instances": 3}
    ),
}

# Maximum time Healer is allowed to spend making a decision in seconds.
DECISION_TIMEOUT_SECONDS = 5

# Maximum time a single action execution is allowed to take in seconds.
ACTION_TIMEOUT_SECONDS = 5

# What to do if no decision table entry matches the failure type.
DEFAULT_ACTION = ("log_unknown", {})

# Structure of what Healer records after every action.
OUTCOME_SCHEMA = {
    "failure_type": str,
    "action_taken": str,
    "action_params": dict,
    "success":       bool,
    "duration_ms":   float,
    "timestamp":     float,
}

# Hard boundaries. Healer must never do these things.
CANNOT_DO = [
    "read_log_stream",
    "pattern_match",
    "modify_event_bus_directly",
    "call_external_apis",
]
