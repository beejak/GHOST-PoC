"""Stream log records from JSON files for async experiments."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, AsyncIterator

async def stream_file(
    path: Path | str,
    *,
    interval_seconds: float = 0.0,
) -> AsyncIterator[tuple[int, dict[str, Any]]]:
    """Yield (stream_index, record) for each entry in a JSON array file."""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected JSON array in {p}")
    delay = interval_seconds
    for i, rec in enumerate(raw):
        if delay > 0:
            await asyncio.sleep(delay)
        if not isinstance(rec, dict):
            raise TypeError(f"Record at index {i} is not an object")
        yield i, rec
