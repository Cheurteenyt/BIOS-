"""Access journal — the T0 guard rail from volume 2 (table 6.1).

Every tool call, even read-only, is appended as JSONL to
$XDG_STATE_HOME/omarchy-firmware/journal.jsonl. The agent cannot do anything
on the firmware side without leaving a dated, replayable trace: this is the
first brick of the "the agent proposes, the HAL disposes, the human decides"
loop.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    d = Path(base) / "omarchy-firmware"
    d.mkdir(parents=True, exist_ok=True)
    return d


def journal_path() -> Path:
    return state_dir() / "journal.jsonl"


def record(tool: str, tier: str, argv: list[str], status: str,
           summary: str, *, fixture: bool = False) -> dict:
    """Append one entry and return the written entry (never silent)."""
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tool": tool,
        "tier": tier,
        "argv": argv,
        "status": status,
        "fixture": fixture,
        "summary": summary,
    }
    try:
        with journal_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # The journal must never block a T0 read; warn instead of crashing,
        # but the missing journal is flagged in the output.
        entry["journal_error"] = "journal could not be written"
    return entry


def show(limit: int = 50) -> list[dict]:
    p = journal_path()
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
