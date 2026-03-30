"""Fake container platform state and action implementations."""

from __future__ import annotations

import copy
from typing import Any, Callable

BASELINE = {
    "app-service": {
        "status": "running",
        "memory": "512Mi",
        "min_instances": 1,
        "max_instances": 1,
        "port": 9090,
        "restart_count": 0,
        "latency_ms": 200,
        # K8s-style fields (synthetic; used by Phase 2 signal scenarios)
        "image": "registry/app:v1-stable",
        "image_previous": "registry/app:v1-stable",
        "replicas_desired": 3,
        "replicas_ready": 3,
        "scheduling_blocked": False,
        "node_ready": True,
    }
}


def baseline_state() -> dict[str, Any]:
    return copy.deepcopy(BASELINE)


def apply_k8s_failure_preset(state: dict[str, Any], failure_type: str) -> None:
    """Mutate state to simulate the broken condition before healing (tests only)."""
    svc = state["app-service"]
    if failure_type == "ImagePullBackOff":
        svc["image"] = "registry/app:v2-missing"
        svc["image_previous"] = "registry/app:v1-stable"
    elif failure_type == "ReplicaMismatch":
        svc["replicas_desired"] = 3
        svc["replicas_ready"] = 0
    elif failure_type == "SchedulingBlocked":
        svc["scheduling_blocked"] = True
    elif failure_type == "NodeNotReady":
        svc["node_ready"] = False
    elif failure_type == "PodDown":
        svc["status"] = "failed"
        svc["replicas_desired"] = 3
        svc["replicas_ready"] = 0


def scale_memory(state: dict[str, Any], memory: str) -> None:
    state["app-service"]["memory"] = memory


def reset_and_redeploy(state: dict[str, Any], restart_count: int, status: str) -> None:
    svc = state["app-service"]
    svc["restart_count"] = restart_count
    svc["status"] = status


def fix_port(state: dict[str, Any], port: int) -> None:
    state["app-service"]["port"] = port


def scale_instances(state: dict[str, Any], max_instances: int) -> None:
    state["app-service"]["max_instances"] = max_instances


def rollback_image(state: dict[str, Any]) -> None:
    svc = state["app-service"]
    svc["image"] = svc["image_previous"]


def sync_replicas(state: dict[str, Any]) -> None:
    svc = state["app-service"]
    svc["replicas_ready"] = svc["replicas_desired"]


def relax_scheduling(state: dict[str, Any]) -> None:
    state["app-service"]["scheduling_blocked"] = False


def recover_node(state: dict[str, Any]) -> None:
    state["app-service"]["node_ready"] = True


def restore_workload(state: dict[str, Any]) -> None:
    svc = state["app-service"]
    svc["status"] = "running"
    svc["replicas_ready"] = svc["replicas_desired"]


def log_unknown(state: dict[str, Any]) -> None:
    pass


ACTION_REGISTRY: dict[str, Callable[..., None]] = {
    "scale_memory": scale_memory,
    "reset_and_redeploy": reset_and_redeploy,
    "fix_port": fix_port,
    "scale_instances": scale_instances,
    "rollback_image": rollback_image,
    "sync_replicas": sync_replicas,
    "relax_scheduling": relax_scheduling,
    "recover_node": recover_node,
    "restore_workload": restore_workload,
    "log_unknown": log_unknown,
}
