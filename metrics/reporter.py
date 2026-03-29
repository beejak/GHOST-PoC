"""Print summary tables from metrics/results.db."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "results.db"


def print_detection_summary() -> None:
    if not DB_PATH.exists():
        print("No results database found.")
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT experiment, failure_type, stream_index, detect_ms "
        "FROM detection_rows ORDER BY id"
    ).fetchall()
    conn.close()
    for r in rows:
        print(r)


def print_outcome_summary() -> None:
    if not DB_PATH.exists():
        print("No results database found.")
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT experiment, failure_type, action_taken, success, mttr_ms "
        "FROM outcome_rows ORDER BY id"
    ).fetchall()
    conn.close()
    for r in rows:
        print(r)
