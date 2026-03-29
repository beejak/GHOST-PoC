"""SQLite writer for detections, outcomes, and experiment metadata."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "results.db"

DDL = """
CREATE TABLE IF NOT EXISTS detection_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment TEXT NOT NULL,
    failure_type TEXT NOT NULL,
    stream_index INTEGER,
    detect_ms REAL NOT NULL,
    created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outcome_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment TEXT NOT NULL,
    failure_type TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    success INTEGER NOT NULL,
    decide_ms REAL,
    act_ms REAL,
    mttr_ms REAL,
    stream_index INTEGER,
    created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    started_at REAL NOT NULL,
    meta TEXT
);
"""


class Recorder:
    def __init__(self, experiment: str) -> None:
        self.experiment = experiment
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH)
        self._conn.executescript(DDL)
        self._conn.execute(
            "INSERT INTO experiment_runs (name, started_at, meta) VALUES (?, ?, ?)",
            (experiment, time.time(), None),
        )
        self._conn.commit()

    def record_detection(
        self,
        failure_type: str,
        detect_ms: float,
        stream_index: int | None = None,
    ) -> None:
        self._conn.execute(
            """INSERT INTO detection_rows
            (experiment, failure_type, stream_index, detect_ms, created)
            VALUES (?, ?, ?, ?, ?)""",
            (
                self.experiment,
                failure_type,
                stream_index,
                detect_ms,
                time.time(),
            ),
        )
        self._conn.commit()

    def record_outcome(self, outcome: dict[str, Any]) -> None:
        self._conn.execute(
            """INSERT INTO outcome_rows
            (experiment, failure_type, action_taken, success, decide_ms, act_ms,
             mttr_ms, stream_index, created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                self.experiment,
                outcome["failure_type"],
                outcome["action_taken"],
                1 if outcome["success"] else 0,
                outcome.get("decide_ms"),
                outcome.get("act_ms"),
                outcome.get("decide_ms", 0) + outcome.get("act_ms", 0),
                outcome.get("stream_index"),
                time.time(),
            ),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def reset_database() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
