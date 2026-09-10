"""fw.rollback — the refusal-by-design with an honest inventory (P4).

Firmware rollback is the one operation this project will never offer the
agent, by construction: on single-BIOS AM4 boards there is no runtime
path back to a previous firmware image. Pretending otherwise would put
the tool inside the "grave + irreversible" quadrant that the doctrine
keeps empty by design (vol. 4, ch. 4).

So fw.rollback is DECLARED T2 and implemented as a documented refusal:
it never rolls anything back, but it answers the question the human is
really asking — "if something goes wrong, where do I stand?" — with a
factual inventory of every rollback surface that DOES exist:

  - the T1 rollback store (EPP values, fan curves — real, tested, undo);
  - the pending staging transaction, if any (cancellable until reboot);
  - fwupd's own update history (what was flashed, from what version);
  - the machine truth: USB BIOS FlashBack / re-flashing the vendor file
    is the only firmware-level recovery, and it is a human operation.

The refusal is journaled (status "refused-by-design"), because a refusal
without a trace is a silence, and this codebase has none.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import journal, stage

_MEANING = (
    "REFUSED BY DESIGN: firmware rollback does not exist as a runtime "
    "operation on single-BIOS AM4 boards. The agent can neither request "
    "nor perform it. The recovery surfaces that DO exist are listed below.")


def _t1_store_status() -> dict:
    """Read-only peek at the T1 rollback store (never pops a frame)."""
    root = journal.state_dir() / "rollback"  # same layout as actions._rollback_dir()
    out = {}
    for name in ("epp", "fans"):
        p = root / f"{name}.json"
        frames = []
        if p.exists():
            try:
                frames = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(frames, list):
                    frames = []
            except (OSError, json.JSONDecodeError):
                frames = []
        last = frames[-1] if frames else None
        out[name] = {
            "frames": len(frames),
            "latest": last.get("ts") if isinstance(last, dict) else None,
        }
    return out


def inventory(fixture_dir=None) -> dict:
    t1 = _t1_store_status()
    transaction = stage._read_transaction()
    hist = stage.history(fixture_dir)
    return {
        "tool": "fw.rollback",
        "tier": "T2",
        "status": "refused-by-design",
        "meaning": _MEANING,
        "t1_rollback_store": t1,
        "staging_transaction": (
            {"status": transaction.get("status"),
             "guid": transaction.get("guid"),
             "from": transaction.get("from"),
             "to": transaction.get("to")}
            if transaction else None),
        "fwupd_history": hist,
        "machine_truth": [
            "T1 OS-level changes (EPP, fan curves): undo exists and is "
            "tested — cpu epp undo --confirm / fans curve undo --confirm",
            "staged-but-not-flashed fwupd update: cancellable until the "
            "reboot (update stage --cancel)",
            "flashed firmware: NO runtime rollback on this platform — "
            "recovery is USB BIOS FlashBack or re-flashing the vendor file "
            "from EZ Flash, both performed by the human alone",
        ],
        "note": "nothing was rolled back; nothing can be, by runtime. "
                "This inventory is the answer.",
    }
