"""Append-only feedback payloads for future learning / offline evaluation pipelines.

GHOST Phase 1 agents do not train online; this module records run-level summaries so
orchestrators (or batch jobs) can correlate outcomes with policy versions later.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "results.db"

DDL_FEEDBACK = """
CREATE TABLE IF NOT EXISTS feedback_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created REAL NOT NULL
);
"""


def log_harness_feedback(payload: dict[str, Any]) -> str:
    """
    Persist a JSON-serializable summary (e.g. experiment pass flags, counts).
    Returns the generated run_id.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(DDL_FEEDBACK)
        conn.execute(
            "INSERT INTO feedback_rows (run_id, payload_json, created) VALUES (?, ?, ?)",
            (run_id, json.dumps(payload, sort_keys=True), time.time()),
        )
        conn.commit()
    finally:
        conn.close()
    return run_id
