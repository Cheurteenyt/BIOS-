"""Access journal — the T0 guard rail from volume 2 (table 6.1).

Every tool call, even read-only, is appended as JSONL to
$XDG_STATE_HOME/omarchy-firmware/journal.jsonl. The agent cannot do anything
on the firmware side without leaving a dated, replayable trace: this is the
first brick of the "the agent proposes, the HAL disposes, the human decides"
loop.
"""

from __future__ import annotations

import fcntl
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
    """Append one entry and return the written entry (never silent).

    The line is written with one os.write on an O_APPEND fd, under an
    exclusive flock: a timer run and a manual call can no longer interleave
    two half-flushed entries (the old text-mode append buffered >8 KiB
    lines across several write() calls — a long --reason was enough).
    """
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
        line = (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")
        fd = os.open(journal_path(), os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                     0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, line)  # O_APPEND + one syscall: the line is atomic
        finally:
            os.close(fd)  # releases the flock
    except OSError:
        # The journal must never block a T0 read; warn instead of crashing,
        # but the missing journal is flagged in the output.
        entry["journal_error"] = "journal could not be written"
    return entry


def show(limit: int = 50) -> list[dict]:
    p = journal_path()
    if not p.exists():
        return []
    if limit <= 0:  # `journal 0` was lines[-0:] == the WHOLE file
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):  # a stray non-object line is skipped,
            out.append(parsed)        # never allowed to crash the views
    return out
