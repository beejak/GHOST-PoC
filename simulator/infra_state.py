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
    }
}


def baseline_state() -> dict[str, Any]:
    return copy.deepcopy(BASELINE)


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


def log_unknown(state: dict[str, Any]) -> None:
    pass


ACTION_REGISTRY: dict[str, Callable[..., None]] = {
    "scale_memory": scale_memory,
    "reset_and_redeploy": reset_and_redeploy,
    "fix_port": fix_port,
    "scale_instances": scale_instances,
    "log_unknown": log_unknown,
}
