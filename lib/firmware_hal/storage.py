"""Storage diagnostics — the fw.diag.storage tool. T0.

Answers "is my disk lying to me?" (vol. 4, ch. 2): NVMe and SATA health via
smartmontools, PCIe link state via lspci. Distinguishes mis-adjusted
(unsafe shutdowns, degraded link) from defective (media errors, reallocated
sectors, spare exhausted) — the two families do not have the same remedy.

Sources (each optional, each honestly reported when absent):
  smartctl -j -a /dev/nvmeN    NVMe SMART health log
  smartctl -j -a /dev/sdX      ATA SMART attributes
  lspci -vv                    LnkCap/LnkSta per PCI device

Every finding carries evidence, hypothesis, next steps and confidence, in
the same shape as the thermal findings (vol. 3) — one shape for the agent.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import system

# JEDEC speeds — a configured speed in this set is "profile not enabled".
_JEDEC = {2133, 2400, 2666, 2933, 3200}
_UNSAFE_RATIO = 0.10


def _run(cmd: list[str], fixture_dir, fixture_key: str) -> str:
    return system.run(cmd, fixture_dir, fixture_key)


def _finding(fid: str, severity: str, category: str, title: str,
             hypothesis: str, evidence: dict, next_steps: str,
             confidence: str) -> dict:
    return {
        "id": fid,
        "severity": severity,
        "category": category,
        "title": title,
        "hypothesis": hypothesis,
        "evidence": evidence,
        "next_steps": next_steps,
        "confidence": confidence,
    }


# ------------------------------------------------------------------ smartctl -

def _nvme_findings(log: dict, name: str) -> list[dict]:
    """Turn an NVMe SMART health log into findings. Read-only, no guessing."""
    out: list[dict] = []
    cycles = int(log.get("power_cycles") or 0)
    unsafe = int(log.get("unsafe_shutdowns") or 0)
    media = int(log.get("media_errors") or 0)
    spare = log.get("available_spare")
    spare_th = log.get("available_spare_threshold")
    used = log.get("percentage_used")
    temp = log.get("temperature")

    if media > 0:
        out.append(_finding(
            "storage-nvme-media-errors", "critical", "defective",
            f"{name}: media errors recorded",
            "The NAND itself has reported uncorrectable sectors — the drive is "
            "wearing out or damaged. This is a defect, not a setting.",
            {"media_errors": media, "num_err_log_entries": log.get("num_err_log_entries")},
            "Back up immediately, run a full SMART self-test, plan replacement.",
            "high"))
    if isinstance(spare, (int, float)) and isinstance(spare_th, (int, float)) \
            and spare <= spare_th:
        out.append(_finding(
            "storage-nvme-spare-low", "critical", "defective",
            f"{name}: spare capacity at the threshold",
            "The manufacturer-reserved replacement blocks are nearly exhausted: "
            "the drive can no longer remap new bad cells reliably.",
            {"available_spare": spare, "available_spare_threshold": spare_th},
            "Back up now; replace the drive. No setting fixes a worn drive.",
            "high"))
    if isinstance(used, (int, float)) and used >= 90:
        out.append(_finding(
            "storage-nvme-wear-high", "attention", "degraded",
            f"{name}: {used}% of rated endurance used",
            "Endurance is a countdown, not a fault — but 90%+ deserves a plan "
            "and a lighter write load.",
            {"percentage_used": used,
             "data_units_written": log.get("data_units_written")},
            "Check the largest writers (iotop), verify backups, plan migration.",
            "high"))
    if isinstance(temp, (int, float)) and temp >= 70:
        out.append(_finding(
            "storage-nvme-hot", "attention", "degraded",
            f"{name}: controller at {temp} °C",
            "Above 70 °C a Gen3/Gen4 drive throttles. Often a missing heatsink "
            "or a dead airflow path rather than a dying drive.",
            {"temperature_c": temp},
            "Check the M.2 heatsink and case airflow; compare under load.",
            "medium"))
    if cycles >= 100 and cycles and unsafe / cycles > _UNSAFE_RATIO:
        out.append(_finding(
            "storage-unsafe-shutdowns", "attention", "mis-adjusted",
            f"{name}: {unsafe} unsafe shutdowns out of {cycles} power cycles",
            "One crash or power-cut in ten is a habit problem (hard reset, "
            "power button held, wall switch), not a hardware fault.",
            {"unsafe_shutdowns": unsafe, "power_cycles": cycles,
             "ratio": round(unsafe / cycles, 3)},
            "Prefer proper shutdowns; check the PSU switch and UPS if frequent.",
            "high"))
    return out


def _sata_findings(doc: dict, name: str) -> list[dict]:
    out: list[dict] = []
    table = ((doc.get("ata_smart_attributes") or {}).get("table")) or []
    attr = {a.get("name"): a for a in table}
    passed = (doc.get("smart_status") or {}).get("passed")
    if passed is False:
        out.append(_finding(
            "storage-sata-failing", "critical", "defective",
            f"{name}: SMART overall status FAILED",
            "The drive declares itself failing. Treat every bit on it as "
            "endangered.",
            {"smart_status": "failed"},
            "Back up immediately, replace the drive.", "high"))

    def raw(attr_name: str) -> int:
        a = attr.get(attr_name) or {}
        r = a.get("raw") or {}
        try:
            return int(str(r.get("value", 0)))
        except (TypeError, ValueError):
            return 0

    realloc, pending = raw("Reallocated_Sector_Ct"), raw("Current_Pending_Sector")
    uncorr = raw("Offline_Uncorrectable")
    if realloc > 0:
        out.append(_finding(
            "storage-sata-reallocated", "critical", "defective",
            f"{name}: {realloc} reallocated sectors",
            "Platters/cells have already been swapped for spares — the surface "
            "is degrading. This never gets better.",
            {"reallocated_sectors": realloc,
             "pending_sectors": pending},
            "Back up immediately; plan replacement; run a long SMART test.",
            "high"))
    if pending > 0:
        out.append(_finding(
            "storage-sata-pending", "attention", "degraded",
            f"{name}: {pending} pending sectors",
            "Sectors are waiting to be decided (readable but suspicious). "
            "Sometimes a full rewrite heals them; often it is early wear.",
            {"pending_sectors": pending, "offline_uncorrectable": uncorr},
            "Run a long SMART test; rewrite the affected area (fstrim/dd); "
            "recheck the counter.",
            "medium"))
    crc = raw("UDMA_CRC_Error_Count")
    if crc > 0:
        out.append(_finding(
            "storage-sata-cable", "attention", "mis-adjusted",
            f"{name}: {crc} UDMA CRC errors",
            "Interface transmission errors — typically a worn, pinched or "
            "badly seated SATA cable, not the disk itself.",
            {"udma_crc_errors": crc},
            "Reseat or replace the SATA cable (never the drive first).",
            "high"))
    return out


def _parse_lspci(text: str) -> list[dict]:
    """Split lspci -vv output into device blocks with link + BAR evidence."""
    devices: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        if re.match(r"^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F] ", line):
            cur = {"slot": line.split()[0], "desc": line.split(maxsplit=1)[-1],
                   "lnkcap": None, "lnksta": None, "bars": []}
            devices.append(cur)
            continue
        if cur is None:
            continue
        if "LnkCap:" in line and cur["lnkcap"] is None:
            cur["lnkcap"] = line.strip()
        elif "LnkSta:" in line and cur["lnksta"] is None:
            cur["lnksta"] = " ".join(line.strip().split())
        elif re.search(r"Region \d+:", line):
            cur["bars"].append(line.strip())
    return devices


def _speed_of(text: str) -> float | None:
    m = re.search(r"Speed (\d+(?:\.\d+)?)GT/s", text or "")
    return float(m.group(1)) if m else None


def _width_of(text: str) -> int | None:
    m = re.search(r"Width x(\d+)", text or "")
    return int(m.group(1)) if m else None


def _pcie_findings(devices: list[dict]) -> tuple[list[dict], list[dict]]:
    """PCIe link findings for NVMe controllers; return (findings, nvme_devices)."""
    out: list[dict] = []
    nvme_devs = []
    for d in devices:
        if "Non-Volatile memory controller" not in (d.get("desc") or ""):
            continue
        nvme_devs.append({"slot": d["slot"], "desc": d["desc"],
                          "lnkcap": d.get("lnkcap"), "lnksta": d.get("lnksta")})
        cap_s, cap_w = _speed_of(d.get("lnkcap")), _width_of(d.get("lnkcap"))
        sta_s, sta_w = _speed_of(d.get("lnksta")), _width_of(d.get("lnksta"))
        if None in (cap_s, cap_w, sta_s, sta_w):
            continue
        degraded = (sta_w < cap_w) or (sta_s < cap_s)
        if degraded:
            out.append(_finding(
                "storage-pcie-degraded", "attention", "mis-adjusted",
                f"NVMe link downgraded: {d['slot']} runs {sta_w}x@{sta_s}GT/s "
                f"(capable of {cap_w}x@{cap_s}GT/s)",
                "The controller is not on the link it advertises: power "
                "management (ASPM) holding the link down, a riser/extender, "
                "or a badly seated M.2 — a setting or a finger, rarely a fault.",
                {"slot": d["slot"], "lnkcap": d["lnkcap"], "lnksta": d["lnksta"]},
                "Compare under load (ASPM downshifts at idle); reseat the M.2; "
                "remove risers; check the BIOS PCIe slot configuration.",
                "medium"))
    return out, nvme_devs


def collect(fixture_dir=None) -> dict:
    disks: list[dict] = []
    findings: list[dict] = []
    errors: list[str] = []
    source: list[str] = []

    # --- NVMe disks -------------------------------------------------------
    nvme_targets = []
    if fixture_dir is not None:
        if (Path(fixture_dir) / "smartctl-nvme0.json").exists():
            nvme_targets = ["/dev/nvme0"]
    else:
        try:
            nvme_targets = sorted(
                p.name for p in Path("/dev").glob("nvme[0-9]")
            ) or []
            nvme_targets = [f"/dev/{n}" for n in nvme_targets]
        except OSError:
            nvme_targets = []
    for i, dev in enumerate(nvme_targets):
        try:
            raw = _run(["smartctl", "-j", "-a", dev], fixture_dir, "smartctl_nvme")
            doc = json.loads(raw)
            log = doc.get("nvme_smart_health_information_log") or {}
            disks.append({
                "kind": "nvme", "device": dev,
                "model": doc.get("model_name"), "family": doc.get("model_family"),
                "firmware": doc.get("firmware_version"),
                "capacity_bytes": (doc.get("user_capacity") or {}).get("bytes"),
                "health": {
                    "critical_warning": log.get("critical_warning"),
                    "temperature_c": log.get("temperature"),
                    "available_spare": log.get("available_spare"),
                    "available_spare_threshold": log.get("available_spare_threshold"),
                    "percentage_used": log.get("percentage_used"),
                    "power_on_hours": log.get("power_on_hours"),
                    "power_cycles": log.get("power_cycles"),
                    "unsafe_shutdowns": log.get("unsafe_shutdowns"),
                    "media_errors": log.get("media_errors"),
                    "num_err_log_entries": log.get("num_err_log_entries"),
                },
                "smart_passed": (doc.get("smart_status") or {}).get("overall_passed"),
            })
            findings.extend(_nvme_findings(log, doc.get("model_name") or dev))
            source.append(f"smartctl {dev}")
        except (system.ToolMissing, FileNotFoundError):
            errors.append("smartmontools not available — NVMe health not readable "
                          "(install smartmontools)")
            break  # one message is enough for the family
        except (RuntimeError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{dev}: {exc}")

    # --- SATA disks (optional: a machine may have none) --------------------
    sata_targets = []
    if fixture_dir is not None:
        if (Path(fixture_dir) / "smartctl-sda.json").exists():
            sata_targets = ["/dev/sda"]
    else:
        try:
            sata_targets = [f"/dev/{p.name}" for p in Path("/dev").glob("sd[a-h]")]
        except OSError:
            sata_targets = []
    for dev in sata_targets:
        try:
            raw = _run(["smartctl", "-j", "-a", dev], fixture_dir, "smartctl_sda")
            doc = json.loads(raw)
            attrs = {a.get("name"): a for a in
                     ((doc.get("ata_smart_attributes") or {}).get("table") or [])}
            disks.append({
                "kind": "sata", "device": dev,
                "model": doc.get("model_name"), "family": doc.get("model_family"),
                "smart_passed": (doc.get("smart_status") or {}).get("passed"),
                "temperature_c": (doc.get("temperature") or {}).get("current"),
                "notable_attributes": {
                    k: (attrs.get(k) or {}).get("raw", {}).get("value")
                    for k in ("Reallocated_Sector_Ct", "Current_Pending_Sector",
                              "Offline_Uncorrectable", "UDMA_CRC_Error_Count")
                    if k in attrs
                },
            })
            findings.extend(_sata_findings(doc, doc.get("model_name") or dev))
            source.append(f"smartctl {dev}")
        except FileNotFoundError:
            pass  # no SATA disk on this machine/fixture — not an error
        except (system.ToolMissing,):
            continue  # already reported above
        except (RuntimeError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{dev}: {exc}")

    # --- PCIe links --------------------------------------------------------
    pcie_devices: list[dict] = []
    try:
        raw = _run(["lspci", "-vv"], fixture_dir, "lspci")
        devices = _parse_lspci(raw)
        pcie_findings, pcie_devices = _pcie_findings(devices)
        findings.extend(pcie_findings)
        source.append("lspci -vv")
    except FileNotFoundError:
        pass  # lspci fixture absent — tolerated
    except system.ToolMissing:
        errors.append("lspci not available — PCIe link state not checked")
    except (RuntimeError, TimeoutError) as exc:
        errors.append(f"lspci: {exc}")

    sev_rank = {"critical": 0, "attention": 1, "info": 2}
    findings.sort(key=lambda f: (sev_rank.get(f["severity"], 3), f["id"]))
    return {
        "tool": "fw.diag.storage",
        "disks": disks,
        "pcie_devices": pcie_devices,
        "findings": findings,
        "verdict": ("critical" if any(f["severity"] == "critical" for f in findings)
                    else "attention" if any(f["severity"] == "attention" for f in findings)
                    else "healthy" if disks or pcie_devices else "undetermined"),
        "errors": errors,
        "source": source,
    }
