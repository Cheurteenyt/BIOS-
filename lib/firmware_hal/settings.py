"""BIOS settings audit — the fw.diag.settings tool. T0.

Answers "what is mis-adjusted?" (vol. 4, ch. 2, the six mis-adjusted items).
Strict honesty rule: only settings observable from the OS are judged. The
rest (Above 4G decoding, Resizable BAR, the memory profile, fan curves) is
listed under `needs_bios_check` — visible to the human in the BIOS setup
only, never guessed.

Observable here:
  Secure Boot state (efivarfs)          SVM/VT-x flag + /dev/kvm
  IOMMU (cmdline + groups)              EPP + cpufreq governor
  fan control mode (hwmon pwm*_enable)  fTPM/TPM presence

"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import sensors
from .storage import _finding

_EFIVAR_SECUREBOOT = ("SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c")

# Settings that exist only in the BIOS setup UI — the OS has no view.
NEEDS_BIOS_CHECK = [
    "Above 4G decoding",
    "Resizable BAR",
    "Memory profile (XMP/EXPO/DOCP) — see fw.diag.ram for the evidence",
    "Fan curves (Q-Fan Control) — the T1 layer can replace them from the OS",
    "Case fan preset / step-up intervals",
]


def _read_text(path: str | Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _secure_boot() -> dict:
    p = Path("/sys/firmware/efi/efivars") / _EFIVAR_SECUREBOOT
    try:
        raw = p.read_bytes()
        return {"readable": True, "enabled": raw[-1:] == b"\x01"}
    except OSError:
        return {"readable": False, "enabled": None,
                "note": "not booted in UEFI, or efivarfs not mounted/readable"}


def _virtualization() -> dict:
    cpuinfo = _read_text("/proc/cpuinfo") or ""
    flags = ""
    vendor = None
    for block in cpuinfo.split("\n\n"):
        if "flags" in block:
            m = [ln for ln in block.splitlines() if ln.startswith("flags")]
            if m:
                flags = m[0].split(":", 1)[1]
                break
    vm = [ln for ln in cpuinfo.splitlines() if ln.startswith("vendor_id")]
    if vm:
        vendor = vm[0].split(":", 1)[1].strip()
    flag = "svm" if vendor == "AuthenticAMD" else "vmx" if vendor == "GenuineIntel" else None
    return {
        "cpu_vendor": vendor,
        "cpu_flag": flag,
        "flag_present": bool(flag) and flag in flags.split(),
        "kvm_device_present": os.path.exists("/dev/kvm"),
    }


def _iommu() -> dict:
    cmdline = _read_text("/proc/cmdline") or ""
    try:
        groups = len(list(Path("/sys/kernel/iommu_groups").iterdir()))
    except OSError:
        groups = 0
    return {
        "kernel_cmdline": cmdline[:120],
        "iommu_param_present": any(
            t.split("=", 1)[0] == "iommu" or t == "iommu=pt" or t == "iommu=on"
            for t in cmdline.split()),
        "groups_count": groups,
    }


def _epp() -> dict:
    cpu0 = Path("/sys/devices/system/cpu/cpu0/cpufreq")
    avail = _read_text(cpu0 / "energy_performance_available_preferences")
    cur = _read_text(cpu0 / "energy_performance_preference")
    gov = _read_text(cpu0 / "scaling_governor")
    cpus = 0
    try:
        cpus = len(list(Path("/sys/devices/system/cpu").glob("cpu[0-9]*")))
    except OSError:
        pass
    return {
        "available": avail.split() if avail else [],
        "current": cur,
        "governor": gov,
        "cpus": cpus,
    }


def _fan_control() -> dict:
    chips = []
    try:
        dirs = sorted(sensors.HWMON.iterdir())
    except OSError:
        dirs = []
    for d in dirs:
        name = (d / "name")
        pwm_enable = {}
        try:
            for f in sorted(d.glob("pwm[0-9]_enable")):
                try:
                    pwm_enable[f.stem] = int(f.read_text().strip())
                except (OSError, ValueError):
                    continue
        except OSError:
            continue
        if pwm_enable:
            chips.append({"name": name.read_text().strip() if name.exists() else d.name,
                          "pwm_enable": pwm_enable})
    return {"chips": chips}


def _tpm() -> dict:
    present = Path("/sys/class/tpm/tpm0").exists()
    return {"present": present, "device": "/sys/class/tpm/tpm0" if present else None}


def collect(fixture_dir=None) -> dict:
    if fixture_dir is not None:
        p = Path(fixture_dir) / "settings.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            # same shape as every other branch: findings + verdict always exist
            return {"tool": "fw.diag.settings", "findings": [],
                    "verdict": "unavailable",
                    "error": "settings fixture missing"}
    else:
        data = {
            "secure_boot": _secure_boot(),
            "virtualization": _virtualization(),
            "iommu": _iommu(),
            "epp": _epp(),
            "fan_control": _fan_control(),
            "tpm": _tpm(),
        }

    findings: list[dict] = []
    virt = data.get("virtualization") or {}
    if virt.get("cpu_flag") and not virt.get("flag_present"):
        findings.append(_finding(
            "settings-virtualization-off", "attention", "mis-adjusted",
            f"CPU virtualization ({virt.get('cpu_flag')}) is not enabled",
            "The CPU supports virtualization but the flag is absent: the BIOS "
            "has SVM (AMD) or VT-x (Intel) turned off — WSL2/KVM/containers "
            "with VMs will refuse to run.",
            {"cpu_vendor": virt.get("cpu_vendor"),
             "flag_present": virt.get("flag_present"),
             "kvm_device_present": virt.get("kvm_device_present")},
            "Enable SVM Mode (AMD) / Intel VT-x in the BIOS, then re-check "
            "for /dev/kvm.",
            "high"))
    iommu = data.get("iommu") or {}
    if not iommu.get("iommu_param_present") and not iommu.get("groups_count"):
        findings.append(_finding(
            "settings-iommu-off", "info", "mis-adjusted",
            "IOMMU appears disabled (no kernel parameter, no groups)",
            "Without IOMMU there is no PCI passthrough (VFIO) and no DMA "
            "isolation. Default-off on many boards — relevant only to some "
            "workloads.",
            {"groups_count": iommu.get("groups_count"),
             "iommu_param_present": iommu.get("iommu_param_present")},
            "Add iommu=pt to the kernel command line, or enable it in BIOS "
            "if a passthrough is planned.",
            "medium"))
    epp = data.get("epp") or {}
    if epp.get("current") == "performance":
        findings.append(_finding(
            "settings-epp-pinned", "attention", "mis-adjusted",
            "EPP pinned to 'performance' on all CPUs",
            "With EPP=performance the scheduler stops hinting for efficiency: "
            "more heat and noise for a marginal gain — the boost algorithm "
            "already saturates under load. T1 `cpu epp set` can fix this "
            "reversibly.",
            {"current": epp.get("current"), "governor": epp.get("governor"),
             "cpus": epp.get("cpus")},
            "`omarchy-firmware cpu epp set balance_performance` (dry-run by "
            "default, add --confirm to apply).",
            "high"))
    elif epp.get("current") == "power":
        findings.append(_finding(
            "settings-epp-power", "info", "mis-adjusted",
            "EPP set to 'power' (efficiency ceiling)",
            "Legitimate on battery; on a desktop it caps responsiveness. "
            "T1 `cpu epp set` can adjust it reversibly.",
            {"current": epp.get("current")},
            "`omarchy-firmware cpu epp set balance_performance --confirm`.",
            "high"))
    fc = data.get("fan_control") or {}
    chips = fc.get("chips") or []
    enables = [v for c in chips for v in (c.get("pwm_enable") or {}).values()]
    if enables and all(v in (0, 2) for v in enables):
        findings.append(_finding(
            "settings-fans-bios-default", "info", "mis-adjusted",
            "Fans follow the firmware default curves (pwm_enable auto/BIOS)",
            "The Q-Fan default curve is usually conservative and noisy at "
            "idle. The T1 layer (`fans curve set`) can write a custom curve "
            "with dry-run and rollback — full speed at the top is mandatory "
            "by construction.",
            {"chips": chips},
            "`omarchy-firmware fans curve set --file curve.json` (dry-run by "
            "default).",
            "medium"))
    sb = data.get("secure_boot") or {}
    if sb.get("readable") and not sb.get("enabled"):
        findings.append(_finding(
            "settings-secure-boot-off", "info", "mis-adjusted",
            "Secure Boot is disabled",
            "fwupd/LVFS enforcement and some anti-tamper posture degrade "
            "without it (fwupd HSI). Omarchy's UKI chain supports it.",
            {"enabled": sb.get("enabled")},
            "Optional: re-enable Secure Boot after checking the enrolled keys.",
            "medium"))

    sev_rank = {"critical": 0, "attention": 1, "info": 2}
    findings.sort(key=lambda f: (sev_rank.get(f["severity"], 3), f["id"]))
    return {
        "tool": "fw.diag.settings",
        **data,
        "needs_bios_check": NEEDS_BIOS_CHECK,
        "findings": findings,
        "verdict": ("attention" if any(f["severity"] == "attention" for f in findings)
                    else "healthy" if not findings else "healthy"),
        "source": ["efivarfs", "/proc/cpuinfo", "/proc/cmdline",
                   "/sys/devices/system/cpu", "hwmon", "/sys/class/tpm"]
        if fixture_dir is None else ["fixture"],
    }
