"""RAM diagnostics — the fw.diag.ram tool. T0.

Answers "is my memory running at what I paid for?" (vol. 4, ch. 2): the
classic AM4 case is a 3600 MT/s kit running at JEDEC 2133 MT/s because the
XMP/EXPO/DOCP profile was never enabled in the BIOS — a mis-adjustment the
BIOS itself never mentions, worth several percent to tens of percent of
performance. Defects (uncorrected errors via EDAC) are named separately.

Sources:
  dmidecode -t memory    rated vs configured speed per DIMM (SMBIOS type 17)
  /sys/devices/system/edac/mc    corrected/uncorrected error counters

"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import system
from .storage import _finding

# Speeds below the kit's rated speed that betray a JEDEC-default run.
_JEDEC = {1600, 1866, 2133, 2400, 2666, 2933, 3200}


def _run(cmd: list[str], fixture_dir, fixture_key: str) -> str:
    return system.run(cmd, fixture_dir, fixture_key)


def _parse_dmidecode_memory(text: str) -> dict:
    """Parse `dmidecode -t memory`: array (type 16) + devices (type 17)."""
    out: dict = {"arrays": [], "dimms": []}
    cur_dimm: dict | None = None
    cur_array: dict | None = None

    def _val(line: str) -> str:
        return line.split(":", 1)[1].strip()

    for line in text.splitlines():
        if "DMI type 16," in line:
            cur_array = {"locator": None, "max_capacity": None, "ecc": None,
                         "devices": None}
            out["arrays"].append(cur_array)
            continue
        if "DMI type 17," in line:
            cur_dimm = {"locator": None, "size": None, "type": None,
                        "rated_speed": None, "configured_speed": None,
                        "manufacturer": None, "part_number": None}
            out["dimms"].append(cur_dimm)
            continue
        if line.startswith("\t") and ":" in line:
            key, val = line.strip().split(":", 1)
            val = val.strip()
            if cur_array is not None and cur_dimm is None:
                if key == "Maximum Capacity":
                    cur_array["max_capacity"] = val
                elif key == "Error Correction Type":
                    cur_array["ecc"] = val
                elif key == "Number Of Devices":
                    try:
                        cur_array["devices"] = int(val)
                    except ValueError:
                        pass
            if cur_dimm is not None:
                if key == "Size":
                    m = re.match(r"(\d+)\s*GB", val)
                    cur_dimm["size_gb"] = int(m.group(1)) if m else None
                    cur_dimm["size"] = val
                elif key == "Locator":
                    cur_dimm["locator"] = val
                elif key == "Type" and cur_dimm["type"] is None:
                    cur_dimm["type"] = val
                elif key == "Speed":
                    m = re.search(r"(\d+)\s*MT/s", val)
                    cur_dimm["rated_speed"] = int(m.group(1)) if m else None
                    cur_dimm["rated"] = val
                elif key == "Configured Memory Speed":
                    m = re.search(r"(\d+)\s*MT/s", val)
                    cur_dimm["configured_speed"] = int(m.group(1)) if m else None
                    cur_dimm["configured"] = val
                elif key == "Manufacturer":
                    cur_dimm["manufacturer"] = val
                elif key == "Part Number":
                    cur_dimm["part_number"] = val
    out["dimms"] = [d for d in out["dimms"] if d.get("locator")]
    return out


def _edac_counts(fixture_dir) -> tuple[list[dict], list[str]]:
    """EDAC corrected/uncorrected counters. Absent = honest note, no finding."""
    errors: list[str] = []
    if fixture_dir is not None:
        try:
            doc = json.loads(system.run([], fixture_dir, "edac"))
            return doc.get("mc", []), errors
        except FileNotFoundError:
            return [], errors
        except (RuntimeError, json.JSONDecodeError, ValueError):
            return [], errors
    mcs: list[dict] = []
    base = Path("/sys/devices/system/edac/mc")
    try:
        for d in sorted(base.glob("mc*")):
            ce = ue = None
            for k, store in (("ce_count", "ce"), ("ue_count", "ue")):
                p = d / k
                if p.exists():
                    try:
                        val = int(p.read_text().strip())
                    except (OSError, ValueError):
                        val = None
                    if k == "ce_count":
                        ce = val
                    else:
                        ue = val
            mcs.append({"id": d.name, "ce_count": ce, "ue_count": ue})
    except OSError:
        pass
    return mcs, errors


def collect(fixture_dir=None) -> dict:
    errors: list[str] = []
    source: list[str] = []
    findings: list[dict] = []
    dimms: list[dict] = []
    arrays: list[dict] = []

    # --- SMBIOS type 17 ------------------------------------------------------
    try:
        doc = _parse_dmidecode_memory(
            _run(["dmidecode", "-t", "memory"], fixture_dir, "dmidecode_memory"))
        dimms = doc["dimms"]
        arrays = doc["arrays"]
        source.append("dmidecode -t memory")
    except (system.ToolMissing, FileNotFoundError):
        errors.append("dmidecode memory table not readable — rated/configured "
                      "speeds unknown (install dmidecode or add the fixture)")
    except (RuntimeError, TimeoutError) as exc:
        errors.append(f"dmidecode: {exc}")

    populated = [d for d in dimms if (d.get("size_gb") or 0) > 0]
    empty = [d for d in dimms if not (d.get("size_gb") or 0) > 0 and d.get("locator")]

    # --- findings from the speed table ---------------------------------------
    misconfigured = [d for d in populated
                     if d.get("configured_speed") and d.get("rated_speed")
                     and d["configured_speed"] < d["rated_speed"]
                     and d["configured_speed"] in _JEDEC]
    if misconfigured:
        per = [{"locator": d["locator"], "rated": d["rated_speed"],
                "configured": d["configured_speed"]} for d in misconfigured]
        findings.append(_finding(
            "ram-xmp-off", "attention", "mis-adjusted",
            f"{len(misconfigured)} module(s) running at JEDEC default instead "
            f"of rated speed ({per[0]['rated']} MT/s kit at "
            f"{per[0]['configured']} MT/s)",
            "The memory profile (XMP on Intel, EXPO/DOCP on AMD) is not "
            "enabled in the BIOS: the kit falls back to the safe JEDEC speed. "
            "Purely a setting — the hardware is fine.",
            {"modules": per},
            "Enable the XMP/EXPO/DOCP profile in the BIOS (not observable "
            "from the OS), then re-run this tool.",
            "high"))
    if len({d.get("rated_speed") for d in populated}) > 1 or \
            len({d.get("size_gb") for d in populated}) > 1:
        findings.append(_finding(
            "ram-mixed-modules", "info", "mis-adjusted",
            "Modules differ in size or rated speed",
            "Mixed kits work, but the controller runs everything at the "
            "slowest common setting — and dual-channel may degrade.",
            {"modules": [{"locator": d["locator"], "size_gb": d.get("size_gb"),
                          "rated_speed": d.get("rated_speed")} for d in populated]},
            "Prefer matched pairs; check which module forces the lower speed.",
            "medium"))

    # --- EDAC counters ---------------------------------------------------------
    mcs, err2 = _edac_counts(fixture_dir)
    errors.extend(err2)
    ue_total = sum(int(m.get("ue_count") or 0) for m in mcs)
    ce_total = sum(int(m.get("ce_count") or 0) for m in mcs)
    if mcs:
        source.append("edac (sysfs)")
        if ue_total > 0:
            findings.append(_finding(
                "ram-uncorrected-errors", "critical", "defective",
                f"{ue_total} uncorrected memory error(s) (EDAC)",
                "Data was corrupted and could not be repaired: the module (or "
                "its seat, or its voltage) is failing. This is a defect.",
                {"ue_count": ue_total, "controllers": mcs},
                "Identify the DIMM (ras-mc-ctl --error-count), memtest the "
                "pair, replace the culprit.",
                "high"))
        elif ce_total >= 100:
            findings.append(_finding(
                "ram-corrected-errors", "attention", "degraded",
                f"{ce_total} corrected memory error(s) (EDAC)",
                "Errors are being repaired on the fly — often the first months "
                "of a marginal module, or too aggressive tuning.",
                {"ce_count": ce_total, "controllers": mcs},
                "Re-run at stock speed/voltage; log the counter over days "
                "(baseline); memtest if it climbs.",
                "medium"))

    total_gb = sum(d.get("size_gb") or 0 for d in populated)
    ecc_type = (arrays[0] or {}).get("ecc") if arrays else None
    sev_rank = {"critical": 0, "attention": 1, "info": 2}
    findings.sort(key=lambda f: (sev_rank.get(f["severity"], 3), f["id"]))
    return {
        "tool": "fw.diag.ram",
        "total_installed_gb": total_gb or None,
        "slots": {"populated": len(populated), "empty": len(empty),
                  "locators": [d["locator"] for d in dimms]},
        "ecc": {"smbios_type": ecc_type,
                "edac_controllers": mcs,
                "available": bool(mcs)},
        "modules": [{"locator": d.get("locator"), "size": d.get("size"),
                     "type": d.get("type"), "rated_speed": d.get("rated_speed"),
                     "configured_speed": d.get("configured_speed"),
                     "manufacturer": d.get("manufacturer"),
                     "part_number": d.get("part_number")} for d in dimms],
        "findings": findings,
        "verdict": ("critical" if any(f["severity"] == "critical" for f in findings)
                    else "attention" if any(f["severity"] == "attention" for f in findings)
                    else "healthy" if populated else "undetermined"),
        "errors": errors,
        "source": source,
    }
