"""GHOST POC harness — runs all experiments, asserts outcomes, writes SQLite metrics."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import run_baseline, run_experiment1, run_experiment2, run_experiment3
from experiments.run_experiment4 import run as run_experiment4
from experiments.run_experiment5 import run as run_experiment5
from integrations.validate import main as integration_contract_check
from metrics.feedback import log_harness_feedback
from metrics.recorder import Recorder, reset_database
from skills import healer_skills, k8s_signal_skills, watcher_skills

ASSERTIONS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "OOMKilled": lambda s: s["app-service"]["memory"] == "1Gi",
    "CrashLoopBackOff": lambda s: s["app-service"]["restart_count"] == 0,
    "StartupProbeFailed": lambda s: s["app-service"]["port"] == 8080,
    "HighLatency": lambda s: s["app-service"]["max_instances"] == 3,
}

K8S_ASSERTIONS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "ImagePullBackOff": lambda s: s["app-service"]["image"]
    == "registry/app:v1-stable",
    "ReplicaMismatch": lambda s: s["app-service"]["replicas_ready"]
    == s["app-service"]["replicas_desired"]
    == 3,
    "SchedulingBlocked": lambda s: s["app-service"]["scheduling_blocked"] is False,
    "NodeNotReady": lambda s: s["app-service"]["node_ready"] is True,
    "PodDown": lambda s: s["app-service"]["status"] == "running"
    and s["app-service"]["replicas_ready"] == s["app-service"]["replicas_desired"],
}


def _rule(width: int = 72) -> str:
    return "=" * width


async def _main() -> None:
    reset_database()

    if integration_contract_check() != 0:
        raise SystemExit("Integration contract validation failed (integrations/validate.py)")

    sep = _rule(39)

    # --- Experiment 1 ---
    r1 = Recorder("experiment1")
    try:
        rows1 = await run_experiment1.run(r1)
    finally:
        r1.close()

    # --- Experiment 2 ---
    r2 = Recorder("experiment2")
    try:
        rows2 = await run_experiment2.run(ASSERTIONS, r2)
    finally:
        r2.close()

    # --- Experiment 3 ---
    r3 = Recorder("experiment3")
    try:
        summary3 = await run_experiment3.run(r3)
    finally:
        r3.close()

    # --- Experiment 4: synthetic K8s-style structured signals ---
    r4 = Recorder("experiment4")
    try:
        rows4 = await run_experiment4(K8S_ASSERTIONS, r4)
    finally:
        r4.close()

    # --- Experiment 5: near-real noisy log stream (200 lines, 20 failures) ---
    r5 = Recorder("experiment5")
    try:
        summary5 = await run_experiment5(r5)
    finally:
        r5.close()

    # --- Console report (spec-style; ASCII for Windows consoles) ---
    print("GHOST POC - Harness Results")
    print(_rule(72))
    print()
    print("EXPERIMENT 1 - Detection Only")
    print("Scenario              Result   Detect(ms)")
    print(sep)
    for row in rows1:
        ft = row["failure_type"]
        res = row["result"]
        dms = row.get("detect_ms")
        dstr = f"{dms:.0f}" if dms is not None else "n/a"
        print(f"{ft:22}{res:8}{dstr:>10}")

    print()
    print("EXPERIMENT 2 - Full Autonomous Loop (Clean Failures)")
    print(
        "Scenario              Result   Detect(ms)  Decide(ms)  Act(ms)  MTTR(ms)"
    )
    print(sep)
    for row in rows2:
        ft = row["failure_type"]
        res = row["result"]
        if "detect_ms" in row:
            print(
                f"{ft:22}{res:8}{row['detect_ms']:>10.0f}"
                f"{row['decide_ms']:>12.0f}{row['act_ms']:>9.0f}"
                f"{row['mttr_ms']:>10.0f}"
            )
        else:
            print(f"{ft:22}{res:8}")

    print()
    print(
        "EXPERIMENT 3 - Full Loop (Mixed Stream, 100 records, 10 injected failures)"
    )
    t = summary3["total_failures"]
    det = summary3["detected"]
    fp = summary3["false_positives"]
    hc = summary3["healthy_count"]
    resolv = summary3["resolved"]
    avg = summary3["avg_mttr_ms"]
    print(f"Detected:       {det}/{t}   ({100 * det / t:.0f}%)" if t else "Detected: n/a")
    print(
        f"False positives: {fp}/{hc}   "
        f"({100 * fp / hc:.0f}%)" if hc else f"False positives: {fp}"
    )
    print(f"Resolved:       {resolv}/{t}   ({100 * resolv / t:.0f}%)" if t else "")
    print(f"Avg MTTR:       {avg:.0f}ms")
    print(sep)
    print("EXPERIMENT 4 - K8s-style signals (synthetic Pod/Node/Deployment)")
    print(
        "Scenario              Result   Detect(ms)  Decide(ms)  Act(ms)  MTTR(ms)"
    )
    print(sep)
    for row in rows4:
        ft = row["failure_type"]
        res = row["result"]
        if "detect_ms" in row:
            print(
                f"{ft:22}{res:8}{row['detect_ms']:>10.0f}"
                f"{row['decide_ms']:>12.0f}{row['act_ms']:>9.0f}"
                f"{row['mttr_ms']:>10.0f}"
            )
        else:
            print(f"{ft:22}{res:8}")
    print(sep)
    t5 = summary5["total_failures"]
    det5 = summary5["detected"]
    fp5 = summary5["false_positives"]
    hc5 = summary5["healthy_count"]
    resolv5 = summary5["resolved"]
    avg5 = summary5["avg_mttr_ms"]
    print(
        "EXPERIMENT 5 - Near-real noisy stream (200 records, 20 injected failures)"
    )
    print(f"Detected:       {det5}/{t5}   ({100 * det5 / t5:.0f}%)" if t5 else "")
    print(
        f"False positives: {fp5}/{hc5}   "
        f"({100 * fp5 / hc5:.0f}%)" if hc5 else f"False positives: {fp5}"
    )
    print(f"Resolved:       {resolv5}/{t5}   ({100 * resolv5 / t5:.0f}%)" if t5 else "")
    print(f"Avg MTTR:       {avg5:.0f}ms")
    print(sep)
    print(run_baseline.describe_baseline())
    print(sep)
    print("Full results written to metrics/results.db")

    # Outcome bundle for offline learning / orchestration (see docs/VISION_LAYERED_LEARNING.md)
    e1_ok = all(r["result"] == "PASS" for r in rows1)
    e2_ok = all(r["result"] == "PASS" for r in rows2)
    e3_ok = (
        summary3["detected"] == summary3["total_failures"]
        and summary3["false_positives"] == 0
        and summary3["resolved"] == summary3["total_failures"]
    )
    e4_ok = all(r["result"] == "PASS" for r in rows4)
    e5_ok = (
        summary5["detected"] == summary5["total_failures"]
        and summary5["false_positives"] == 0
        and summary5["resolved"] == summary5["total_failures"]
    )
    run_id = log_harness_feedback(
        {
            "layers_observed": [
                "log_substring",
                "log_mixed_stream",
                "k8s_structured_signal",
                "log_near_real_noisy",
            ],
            "experiment1_all_pass": e1_ok,
            "experiment2_all_pass": e2_ok,
            "experiment3_all_pass": e3_ok,
            "experiment4_all_pass": e4_ok,
            "experiment5_all_pass": e5_ok,
            "harness_all_pass": e1_ok and e2_ok and e3_ok and e4_ok and e5_ok,
            "exp3_detected": summary3["detected"],
            "exp3_total_injected": summary3["total_failures"],
            "exp3_false_positives": summary3["false_positives"],
            "exp5_detected": summary5["detected"],
            "exp5_total_injected": summary5["total_failures"],
            "exp5_false_positives": summary5["false_positives"],
            "policy_versions": {
                "watcher_skills": watcher_skills.AGENT_VERSION,
                "healer_skills": healer_skills.AGENT_VERSION,
                "k8s_signal_skills": k8s_signal_skills.AGENT_VERSION,
            },
        }
    )
    print(f"Feedback ledger run_id: {run_id}  (table: feedback_rows)")

    # Hard failures for Definition of Done
    if not e1_ok:
        raise SystemExit("Experiment 1 failed")
    if not e2_ok:
        raise SystemExit("Experiment 2 failed")
    if not e3_ok:
        if summary3["detected"] != summary3["total_failures"]:
            raise SystemExit("Experiment 3 detection incomplete")
        if summary3["false_positives"] != 0:
            raise SystemExit("Experiment 3 false positives")
        raise SystemExit("Experiment 3 resolution incomplete")
    if not e4_ok:
        raise SystemExit("Experiment 4 failed")
    if not e5_ok:
        if summary5["detected"] != summary5["total_failures"]:
            raise SystemExit("Experiment 5 detection incomplete")
        if summary5["false_positives"] != 0:
            raise SystemExit("Experiment 5 false positives")
        raise SystemExit("Experiment 5 resolution incomplete")


if __name__ == "__main__":
    asyncio.run(_main())
