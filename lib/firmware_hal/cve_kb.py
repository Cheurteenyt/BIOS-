"""Version / known-CVE cross-check — the fw.audit.cve tool. T0.

The knowledge base (data/cve_am4.json) carries the timeline from volume 1,
ch. 5: fTPM stutter (2022), LogoFAIL (2023), Sinkclose CVE-2023-31315
(2024), VU#382314 (2025), CVE-2026-6726/6727 (2026). The judgement is a
date-based reasoning, owned as such: we separate what is proven (version,
date read from SMBIOS) from what is inferred (likely exposure) — the
Omarchy skill style rule, "work from evidence", applied to firmware.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import smbios
from .journal import state_dir

DATA = Path(__file__).parent / "data" / "cve_am4.json"

_OVERRIDE = "cve-kb-override.json"


def _override_path() -> Path:
    """Local KB override (XDG state) — written only by the two-key updater."""
    return state_dir() / _OVERRIDE


def active_path() -> Path:
    """The KB file actually in force: local override first, packaged fallback."""
    ov = _override_path()
    if ov.exists():
        try:
            if json.loads(ov.read_text(encoding="utf-8")).get("entries"):
                return ov
        except (OSError, json.JSONDecodeError):
            pass  # a corrupt override falls back to the packaged KB
    return DATA


def kb_source() -> str:
    return "override" if active_path() == _override_path() else "packaged"


def load_kb() -> dict:
    try:
        return json.loads(active_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # last resort: the packaged KB, whatever it takes — a watch or audit
        # must never crash because of a bad local override.
        return json.loads(DATA.read_text(encoding="utf-8"))


def _date_of(board: dict) -> str | None:
    return board.get("bios_date")


def _status(entry: dict, bios_date: str | None) -> tuple[str, str]:
    """(status, rationale) — never a "safe" without proof."""
    fixed_from = entry.get("fixed_from_bios_date")
    if fixed_from is None:
        return ("unknown — fix still rolling out",
                "no firm fix date: check the vendor advisory")
    if not bios_date:
        return ("unknown — BIOS date unreadable",
                "SMBIOS provided no usable date; cross-check the support page")
    if bios_date >= fixed_from:
        return ("probably fixed",
                f"BIOS dated {bios_date} >= fix threshold {fixed_from} "
                f"({entry.get('fixed_hint', 'n/a')}) — an inference, not an attestation")
    return ("potentially exposed",
            f"BIOS dated {bios_date} < fix threshold {fixed_from} "
            f"({entry.get('fixed_hint', 'n/a')})")


def collect(fixture_dir=None, kb: dict | None = None) -> dict:
    if kb is None:
        kb = load_kb()
    board = smbios.collect(fixture_dir)
    if board.get("error"):
        return {"error": f"board not identified: {board['error']}", "findings": []}

    bios_date = _date_of(board)
    findings = []
    for entry in kb["entries"]:
        status, why = _status(entry, bios_date)
        findings.append({
            "id": entry["id"],
            "title": entry["title"],
            "year": entry["year"],
            "severity": entry.get("severity"),
            "status": status,
            "rationale": why,
            "reference": entry.get("reference"),
        })

    exposed = [f for f in findings if f["status"].startswith("potentially")]
    unknown = [f for f in findings if f["status"].startswith("unknown")]
    verdict = (
        f"{len(exposed)} potential exposure(s), {len(unknown)} unknown status(es) "
        f"out of {len(findings)} entries — a BIOS update is a T3 operation: "
        "the agent produces the EZ Flash walkthrough, the human executes."
        if exposed or unknown else
        "no potential exposure identified on the current knowledge base."
    )
    return {
        "board": {
            "vendor": board.get("board_vendor"),
            "product": board.get("board_product"),
            "bios_version": board.get("bios_version"),
            "bios_date": bios_date,
            "socket": board.get("cpu_socket"),
        },
        "kb_scope": kb["scope"],
        "kb_generated": kb["generated"],
        "findings": findings,
        "verdict": verdict,
    }
