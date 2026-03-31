"""Event handler and action executor — imports decision table only from healer_skills."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from blackboard.event_bus import EventBus
from skills.healer_skills import (
    ACTION_TIMEOUT_SECONDS,
    DECISION_TABLE,
    DECISION_TIMEOUT_SECONDS,
    DEFAULT_ACTION,
)
from simulator.infra_state import ACTION_REGISTRY


async def heal_once(
    bus: EventBus,
    infra_state: dict[str, Any],
    on_outcome: Callable[[dict[str, Any]], None] | None = None,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Consume one event, look up action, execute (or skip mutate if dry_run), return outcome."""
    event = await bus.consume()
    failure_type = event["failure_type"]

    async def decide() -> tuple[str, dict[str, Any]]:
        await asyncio.sleep(0)
        return DECISION_TABLE.get(failure_type, DEFAULT_ACTION)

    t_decide0 = time.perf_counter()
    action_name, action_params = await asyncio.wait_for(
        decide(), timeout=DECISION_TIMEOUT_SECONDS
    )
    decide_ms = (time.perf_counter() - t_decide0) * 1000

    t_act0 = time.perf_counter()

    async def run_action() -> None:
        await asyncio.sleep(0)
        if dry_run:
            return
        fn = ACTION_REGISTRY[action_name]
        fn(infra_state, **action_params)

    success = False
    try:
        await asyncio.wait_for(run_action(), timeout=ACTION_TIMEOUT_SECONDS)
        success = True
    except Exception:
        success = False
    act_ms = (time.perf_counter() - t_act0) * 1000

    outcome = {
        "failure_type": failure_type,
        "action_taken": action_name,
        "action_params": dict(action_params),
        "success": success,
        "duration_ms": decide_ms + act_ms,
        "timestamp": time.time(),
        "decide_ms": decide_ms,
        "act_ms": act_ms,
        "stream_index": event["raw_log"].get("stream_index"),
        "dry_run": dry_run,
    }
    if on_outcome:
        on_outcome(outcome)
    return outcome
