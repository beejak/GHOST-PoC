# skills/healer_skills.py

from __future__ import annotations

from typing import Any, Callable

AGENT_NAME = "healer"
AGENT_VERSION = "1.2.0"

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
    # Synthetic K8s-style signal classes (structured signals, not live API calls)
    "ImagePullBackOff": (
        "rollback_image",
        {}
    ),
    "ReplicaMismatch": (
        "sync_replicas",
        {}
    ),
    "SchedulingBlocked": (
        "relax_scheduling",
        {}
    ),
    "NodeNotReady": (
        "recover_node",
        {}
    ),
    "PodDown": (
        "restore_workload",
        {}
    ),
}

# Maximum time Healer is allowed to spend making a decision in seconds.
DECISION_TIMEOUT_SECONDS = 5

# Maximum time a single action execution is allowed to take in seconds.
ACTION_TIMEOUT_SECONDS = 5

# What to do if no decision table entry matches the failure type.
DEFAULT_ACTION = ("log_unknown", {})


def _verify_oom(s: dict[str, Any]) -> bool:
    return s["app-service"]["memory"] == "1Gi"


def _verify_crash(s: dict[str, Any]) -> bool:
    return s["app-service"]["restart_count"] == 0


def _verify_probe(s: dict[str, Any]) -> bool:
    return s["app-service"]["port"] == 8080


def _verify_latency(s: dict[str, Any]) -> bool:
    return s["app-service"]["max_instances"] == 3


def _verify_image(s: dict[str, Any]) -> bool:
    svc = s["app-service"]
    return svc["image"] == "registry/app:v1-stable"


def _verify_replicas(s: dict[str, Any]) -> bool:
    svc = s["app-service"]
    return svc["replicas_ready"] == svc["replicas_desired"] == 3


def _verify_scheduling(s: dict[str, Any]) -> bool:
    return s["app-service"]["scheduling_blocked"] is False


def _verify_node(s: dict[str, Any]) -> bool:
    return s["app-service"]["node_ready"] is True


def _verify_pod_down(s: dict[str, Any]) -> bool:
    svc = s["app-service"]
    return (
        svc["status"] == "running"
        and svc["replicas_ready"] == svc["replicas_desired"]
    )


# After a mutating action completes, infra must satisfy this predicate or the heal is a failure.
# Same predicates power harness assertions (single source of truth).
POST_HEAL_VERIFIERS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "OOMKilled": _verify_oom,
    "CrashLoopBackOff": _verify_crash,
    "StartupProbeFailed": _verify_probe,
    "HighLatency": _verify_latency,
    "ImagePullBackOff": _verify_image,
    "ReplicaMismatch": _verify_replicas,
    "SchedulingBlocked": _verify_scheduling,
    "NodeNotReady": _verify_node,
    "PodDown": _verify_pod_down,
}

# Structure of what Healer records after every action.
OUTCOME_SCHEMA = {
    "failure_type": str,
    "action_taken": str,
    "action_params": dict,
    "success": bool,
    "verify_ok": bool,
    "duration_ms": float,
    "timestamp": float,
}

# Hard boundaries. Healer must never do these things.
CANNOT_DO = [
    "read_log_stream",
    "pattern_match",
    "modify_event_bus_directly",
    "call_external_apis",
]
