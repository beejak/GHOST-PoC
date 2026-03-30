# skills/k8s_signal_skills.py
"""Declarative rules for synthetic Kubernetes-style control-plane signals (not a live cluster)."""

from __future__ import annotations

from typing import Any

AGENT_NAME = "k8s_signal_watcher"
AGENT_VERSION = "1.0.0"

# Ordered rules: first full match wins. `match` applies to the `signal` object on each record.
# Mirrors common EKS/GKE/AKS-style status fields without binding to one vendor's event text.
SIGNAL_RULES: list[tuple[str, dict[str, Any]]] = [
    ("ImagePullBackOff", {"record_type": "Pod", "reason": "ImagePullBackOff"}),
    ("ImagePullBackOff", {"record_type": "Pod", "reason": "ErrImagePull"}),
    ("SchedulingBlocked", {"record_type": "Pod", "reason": "FailedScheduling"}),
    ("NodeNotReady", {"record_type": "Node", "condition": "NotReady"}),
    ("ReplicaMismatch", {"record_type": "Deployment", "replica_drift": True}),
    ("PodDown", {"record_type": "Pod", "phase": "Failed", "reason": "Evicted"}),
]

CANNOT_DO = [
    "read_application_logs",
    "pattern_match_log_lines",
    "call_kubernetes_api",
    "modify_event_bus_directly",
]


def classify_signal(signal: dict[str, Any]) -> str | None:
    if not isinstance(signal, dict):
        return None
    for failure_type, match in SIGNAL_RULES:
        if all(signal.get(k) == v for k, v in match.items()):
            return failure_type
    return None
