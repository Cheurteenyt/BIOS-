"""Boot chain collector — efibootmgr + ESP + Snapper snapshots. T0.

Answers "is my boot chain healthy?": NVRAM entries read via efibootmgr -v,
BootOrder, existence of referenced files on the ESP, heuristic detection of
the Omarchy Limine + UKI chain, and Snapper snapshot count when snapper is
installed. No NVRAM write — exactly what Phase 1 allows (T2 comes later,
with human confirmation).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import system

_EFIBOOTMGR_CMD = ["efibootmgr", "-v"]

_ENTRY_RE = re.compile(r"^Boot([0-9A-Fa-f]{4})(\*|\s)\s(.*)$")
_FILE_RE = re.compile(r"File\((\\[^)]+\.efi)\)", re.IGNORECASE)


def _esp_mountpoint() -> str | None:
    """Find the ESP: /boot (Omarchy direct mount) then /boot/efi."""
    for cand in ("/boot", "/boot/efi"):
        if Path(cand, "EFI").is_dir() or Path(cand, "vmlinuz").exists():
            return cand
    return None


def _entry_kind(name: str, file_path: str | None) -> str:
    n = (name + " " + (file_path or "")).lower()
    if "microsoft" in n or "windows" in n:
        return "windows"
    if "limine" in n:
        return "limine (bootloader)"
    if "uki" in n or "/linux/" in n:
        return "uki linux"
    if "omarchy" in n:
        return "omarchy"
    if "uefi os" in n or "fallback" in n:
        return "fallback uefi"
    return "other"


def _parse(text: str) -> dict:
    """Raw parse of efibootmgr -v output (testable without hardware)."""
    out: dict = {"entries": [], "warnings": []}
    order: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^BootOrder:\s*([0-9A-Fa-f,]+)", line)
        if m:
            order = m.group(1).split(",")
        m = re.match(r"^BootCurrent:\s*([0-9A-Fa-f]{4})", line)
        if m:
            out["boot_current"] = m.group(1)
        m = re.match(r"^Timeout:\s*(\d+)", line)
        if m:
            out["timeout_seconds"] = int(m.group(1))

        em = _ENTRY_RE.match(line)
        if em:
            num, active, rest = em.group(1), em.group(2) == "*", em.group(3)
            if "\t" in rest:
                name, devpath = rest.split("\t", 1)
            else:
                name, devpath = rest, ""
            fm = _FILE_RE.search(devpath)
            file_path = fm.group(1) if fm else None
            out["entries"].append({
                "num": num,
                "name": name.strip(),
                "active": active,
                "file": file_path,
                "device_path": devpath.strip(),
                "kind": _entry_kind(name, file_path),
            })

    out["boot_order"] = order
    out["boot_order_names"] = [
        next((e["name"] for e in out["entries"] if e["num"] == n), f"Boot{n}")
        for n in order
    ]

    # Omarchy chain: Limine loaded from the ESP, UKI under EFI/Linux.
    kinds = {e["kind"] for e in out["entries"]}
    out["chain"] = (
        "Limine + UKI (Omarchy direct-boot profile)"
        if any("limine" in k for k in kinds)
        else "undetermined — see entries"
    )

    # Consistency check: BootCurrent should be first in BootOrder.
    cur = out.get("boot_current")
    if cur and order and cur != order[0]:
        out["warnings"].append(
            f"BootCurrent {cur} is not first in BootOrder "
            f"({order[0]}) — check the firmware boot policy"
        )
    return out


def collect(fixture_dir=None) -> dict:
    """Full boot inventory; every field tolerates absence, explicitly."""
    try:
        text = system.run(_EFIBOOTMGR_CMD, fixture_dir, "efibootmgr")
    except system.ToolMissing:
        return {"error": "efibootmgr missing (pacman -S efibootmgr)", "source": "efibootmgr"}
    except (RuntimeError, FileNotFoundError, TimeoutError) as exc:
        return {"error": str(exc), "source": "efibootmgr"}

    out = _parse(text)
    out["source"] = "efibootmgr -v"

    # Existence check of referenced files (never in fixture mode: the test
    # machine has no real ESP, the field would be misleading).
    esp = None if fixture_dir is not None else _esp_mountpoint()
    out["esp_mount"] = esp or "unknown (fixture mode or ESP not identified)"
    for e in out["entries"]:
        if e["file"] and esp:
            p = Path(esp) / e["file"].lstrip("\\").replace("\\", "/")
            e["file_on_esp"] = p.exists()
        else:
            e["file_on_esp"] = None

    # Snapper snapshots (read-only; absent = reported, not an error).
    out["snapper_snapshots"] = None
    if fixture_dir is None:
        try:
            proc = subprocess.run(
                ["snapper", "--csvout", "list", "--disable-used-space"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            rows = [l for l in (proc.stdout or "").splitlines() if l.strip()]
            out["snapper_snapshots"] = max(0, len(rows) - 2) if rows else 0
        except FileNotFoundError:
            out["warnings"].append("snapper missing — snapshot count skipped")
        except subprocess.TimeoutExpired:
            pass
    else:
        out["warnings"].append("fixture mode — Snapper count and ESP existence skipped")
    return out
