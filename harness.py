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
from metrics.recorder import Recorder, reset_database

ASSERTIONS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "OOMKilled": lambda s: s["app-service"]["memory"] == "1Gi",
    "CrashLoopBackOff": lambda s: s["app-service"]["restart_count"] == 0,
    "StartupProbeFailed": lambda s: s["app-service"]["port"] == 8080,
    "HighLatency": lambda s: s["app-service"]["max_instances"] == 3,
}


def _rule(width: int = 72) -> str:
    return "=" * width


async def _main() -> None:
    reset_database()

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
    print(run_baseline.describe_baseline())
    print(sep)
    print("Full results written to metrics/results.db")

    # Hard failures for Definition of Done
    if any(r["result"] != "PASS" for r in rows1):
        raise SystemExit("Experiment 1 failed")
    if any(r["result"] != "PASS" for r in rows2):
        raise SystemExit("Experiment 2 failed")
    if summary3["detected"] != summary3["total_failures"]:
        raise SystemExit("Experiment 3 detection incomplete")
    if summary3["false_positives"] != 0:
        raise SystemExit("Experiment 3 false positives")
    if summary3["resolved"] != summary3["total_failures"]:
        raise SystemExit("Experiment 3 resolution incomplete")


if __name__ == "__main__":
    asyncio.run(_main())
