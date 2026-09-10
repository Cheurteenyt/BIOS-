"""SMBIOS/DMI collector — the board, the BIOS, the CPU. dmidecode read-only.

dmidecode -t 0,1,2,4 provides: BIOS (type 0), system (type 1), motherboard
(type 2), processor (type 4). This is the platform identity the CVE
knowledge base needs — and it is what replaces the question "what is your
board exactly?": the base reads it itself, at run time.
"""

from __future__ import annotations

import re
from . import system

_DMI_CMD = ["dmidecode", "-t", "0,1,2,4", "-q"]


def _sections(text: str) -> list[tuple[int, dict[str, str]]]:
    """Split dmidecode output into (DMI type, fields) pairs."""
    out: list[tuple[int, dict[str, str]]] = []
    current_type: int | None = None
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"Handle 0x[0-9A-Fa-f]+, DMI type (\d+),", line)
        if m:
            if current_type is not None:
                out.append((current_type, fields))
            current_type, fields = int(m.group(1)), {}
            continue
        if current_type is None:
            continue
        kv = re.match(r"\s+([^:\t]+):\s*(.*)$", line)
        if kv:
            fields[kv.group(1).strip()] = kv.group(2).strip()
    if current_type is not None:
        out.append((current_type, fields))
    return out


def _first(sections, dmi_type: int, keys: list[str]) -> str | None:
    for t, f in sections:
        if t == dmi_type:
            for k in keys:
                if f.get(k):
                    return f[k]
    return None


def _parse_date(raw: str | None) -> str | None:
    """Normalize 08/12/2026 (mm/dd/yyyy, US dmidecode format) to ISO."""
    if not raw:
        return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", raw.strip())
    if m:
        mm, dd, yyyy = (int(x) for x in m.groups())
        if 1 <= mm <= 12:
            return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw.strip())
    return raw.strip() if m else None


def collect(fixture_dir=None) -> dict:
    """Return the platform identity; explicit errors, never guessing."""
    try:
        text = system.run(_DMI_CMD, fixture_dir, "dmidecode")
    except system.ToolMissing:
        return {"error": "dmidecode missing (pacman -S dmidecode)", "source": "dmidecode"}
    except (RuntimeError, FileNotFoundError, TimeoutError) as exc:
        return {"error": str(exc), "source": "dmidecode"}

    sec = _sections(text)
    board = {
        "board_vendor": _first(sec, 2, ["Manufacturer"]) or "unknown",
        "board_product": _first(sec, 2, ["Product Name"]) or "unknown",
        "board_version": _first(sec, 2, ["Version"]) or None,
        "bios_vendor": _first(sec, 0, ["Vendor"]) or "unknown",
        "bios_version": _first(sec, 0, ["Version"]) or "unknown",
        "bios_date": _parse_date(_first(sec, 0, ["Release Date"])),
        "bios_revision": _first(sec, 0, ["BIOS Revision"]),
        "system_vendor": _first(sec, 1, ["Manufacturer"]) or None,
        "system_product": _first(sec, 1, ["Product Name"]) or None,
        "cpu_model": _first(sec, 4, ["Processor Version"]) or "unknown",
        "cpu_cores": _first(sec, 4, ["Core Count"]) or None,
        "cpu_socket": _first(sec, 4, ["Processor Upgrade"]) or None,
        "source": "dmidecode -t 0,1,2,4",
    }
    # "System Product Name" is the ASUS norm: the motherboard is then the
    # only reliable identity — we say so rather than hide the flaw.
    if (board.get("system_product") or "").lower().startswith("system product"):
        board["system_note"] = "generic system identity — the motherboard (type 2) is authoritative"
    return board


def is_am4(board: dict) -> bool | None:
    """True/False when determinable; None when the socket is not readable."""
    sock = (board.get("cpu_socket") or "").upper()
    if not sock:
        return None
    return "AM4" in sock or "PGA1331" in sock
