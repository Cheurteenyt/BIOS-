"""report — the supervised-loop digest (P4).

The P4 exit criterion is measurable: "5 days of loop without false
positive nor unconfirmed write". Measuring it requires a digest of what
the loop actually did — this is it. `omarchy-firmware report` reads the
access journal (JSONL) and aggregates, per day:

  - every T0 call, tool by tool (the loop's heartbeat);
  - every T1/T2 status: dry-run, applied, staged, rolled-back, refused,
    refused-by-design (the "no unconfirmed write" evidence);
  - errors and their tools;
  - the KB freshness (is the timeline the audit reasons on current?);
  - the pending staging transaction, if any.

A report is a VIEW: like `journal`, it does not journal itself — an
aggregation of the record is not an access to the firmware. The false
positive review stays a human judgement: the report surfaces every
finding the loop raised, day by day, and the human marks the ones that
did not survive contact with reality. That annotated journal IS the
P4 evidence.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

from . import cve_watch, journal, stage


def _read_all() -> list[dict]:
    p = journal.journal_path()
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):  # same discipline as journal.show
            out.append(parsed)
    return out


def collect(days: int = 5) -> dict:
    entries = _read_all()
    per_day: dict[str, dict] = {}

    def day_bucket(day: str) -> dict:
        if day not in per_day:
            per_day[day] = {
                "calls": 0, "errors": 0,
                "tools": defaultdict(int),
                "statuses": defaultdict(int),
            }
        return per_day[day]

    for e in entries:
        day = str(e.get("ts", ""))[:10] or "unknown"
        b = day_bucket(day)
        b["calls"] += 1
        b["tools"][e.get("tool", "?")] += 1
        b["statuses"][e.get("status", "?")] += 1
        if e.get("status") == "error":
            b["errors"] += 1

    window = {}
    for day in sorted(per_day, reverse=True)[: max(1, days)]:
        b = per_day[day]
        window[day] = {
            "calls": b["calls"],
            "errors": b["errors"],
            "tools": dict(sorted(b["tools"].items())),
            "statuses": dict(sorted(b["statuses"].items())),
        }

    totals = defaultdict(int)
    for b in per_day.values():
        for s, n in b["statuses"].items():
            totals[s] += n

    t1_frames = {
        name: info["frames"]
        for name, info in _t1_peek().items()
    }
    transaction = stage._read_transaction()
    kb = cve_watch.kb_info()

    verdict = (
        f"{len(per_day)} day(s) journaled, {sum(b['calls'] for b in per_day.values())} "
        f"call(s); writes: {totals.get('applied', 0)} applied, "
        f"{totals.get('staged', 0)} staged, {totals.get('rolled-back', 0)} rolled back, "
        f"{totals.get('refused', 0) + totals.get('refused-by-design', 0)} refused; "
        f"{totals.get('error', 0)} error(s); KB {kb.get('age_days')} d old "
        f"({kb.get('source')})."
    )
    return {
        "tool": "loop.report",
        "window_days": days,
        "days": window,
        "totals_by_status": dict(sorted(totals.items())),
        "t1_rollback_frames": t1_frames,
        "staging_transaction": (
            {"status": transaction.get("status"),
             "guid": transaction.get("guid"),
             "to": transaction.get("to")}
            if transaction else None),
        "kb": kb,
        "verdict": verdict,
        "note": ("view only — a report does not journal itself. The P4 "
                 "criterion is reviewed by a human: for each raised "
                 "finding, mark whether it survived verification."),
    }


def _t1_peek() -> dict:
    root = journal.state_dir() / "rollback"
    out = {}
    for name in ("epp", "fans"):
        p = Path(root) / f"{name}.json"
        n = 0
        if p.exists():
            try:
                frames = json.loads(p.read_text(encoding="utf-8"))
                n = len(frames) if isinstance(frames, list) else 0
            except (OSError, json.JSONDecodeError):
                n = 0
        out[name] = {"frames": n}
    return out
