"""GPU diagnostics — the fw.diag.gpu tool. T0.

Answers "is my GPU sick or just capped?" (vol. 4, ch. 2). Correlates three
independent sources, none of which is trusted alone:
  nvidia-smi -q      clocks event reasons, temperatures, BAR1, driver/GSP
  dmesg (or journal) NVRM Xid errors — the GPU's own post-mortem lines
  lspci -vv          the physical PCIe link (width downgraded = riser/seat)

Like storage and thermal: every finding carries evidence, hypothesis, next
steps and confidence; nothing is named without a source line to show.
"""

from __future__ import annotations

import re

from . import system
from .storage import _finding, _parse_lspci, _speed_of, _width_of

# Xid 79 (GPU fell off the bus), 94/95 (uncontained errors) — the
# "pull the plug" class; everything else is attention, not panic.
_XID_CRITICAL = {79, 94, 95}


def _run(cmd: list[str], fixture_dir, fixture_key: str) -> str:
    return system.run(cmd, fixture_dir, fixture_key)


def _parse_nvidia_smi(text: str) -> dict:
    """Parse the text output of `nvidia-smi -q` — the fields we reason on."""
    out: dict = {"driver": None, "gsp_firmware": None, "product": None,
                 "temp_c": None, "power_limit_w": None, "power_draw_w": None,
                 "bar1_total_mib": None, "clock_events": {},
                 "vbios": None, "uuid": None}
    m = re.search(r"Driver Version\s*:\s*(\S+)", text)
    if m:
        out["driver"] = m.group(1)
    m = re.search(r"GSP Firmware Version\s*:\s*(\S+)", text)
    if m:
        out["gsp_firmware"] = m.group(1)
    m = re.search(r"Product Name\s*:\s*(.+)", text)
    if m:
        out["product"] = m.group(1).strip()
    m = re.search(r"VBIOS Version\s*:\s*(\S+)", text)
    if m:
        out["vbios"] = m.group(1)
    m = re.search(r"UUID\s*:\s*(\S+)", text)
    if m:
        out["uuid"] = m.group(1)
    m = re.search(r"GPU Current Temp\s*:\s*(\d+)\s*C", text)
    if m:
        out["temp_c"] = int(m.group(1))
    m = re.search(r"Power Draw\s*:\s*([\d.]+)\s*W", text)
    if m:
        out["power_draw_w"] = float(m.group(1))
    m = re.search(r"Enforced Power Limit\s*:\s*([\d.]+)\s*W", text)
    if m:
        out["power_limit_w"] = float(m.group(1))
    m = re.search(r"BAR1 Memory Usage\s*\n\s*Total\s*:\s*(\d+)\s*MiB", text)
    if m:
        out["bar1_total_mib"] = int(m.group(1))

    # Clocks Event Reasons block — Active/Not Active per reason.
    m = re.search(r"Clocks Event Reasons\s*\n(.*?)(?=\n\s{4}\S|\Z)", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            reason, _, state = line.strip().partition(":")
            reason = reason.strip()
            state = state.strip()
            if reason and state in ("Active", "Not Active"):
                out["clock_events"][reason] = (state == "Active")
    return out


def _parse_xid(text: str) -> list[dict]:
    """Extract NVRM Xid lines: `NVRM: Xid (PCI:0000:01:00): 13, ...`."""
    out = []
    for line in text.splitlines():
        m = re.search(r"Xid \(PCI:([0-9a-fA-F: .]+)\):\s*(\d+)(.*)", line)
        if m:
            out.append({"bus": m.group(1).strip(), "code": int(m.group(2)),
                        "detail": m.group(3).strip()[:160], "line": line.strip()[:200]})
    return out


def collect(fixture_dir=None) -> dict:
    status: dict = {"tool": "fw.diag.gpu"}
    findings: list[dict] = []
    errors: list[str] = []
    source: list[str] = []

    # --- nvidia-smi (optional: AMD/intel machines report differently) ------
    smi: dict = {}
    try:
        smi = _parse_nvidia_smi(_run(["nvidia-smi", "-q"], fixture_dir, "nvidia_smi"))
        source.append("nvidia-smi -q")
        status["nvidia"] = smi
        events = smi.get("clock_events") or {}
        if events.get("HW Slowdown : Thermal") or \
                events.get("HW Slowdown : Thermal Braking"):
            brake = "HW Slowdown : Thermal Braking" in events and \
                    events["HW Slowdown : Thermal Braking"]
            findings.append(_finding(
                "gpu-thermal-slowdown",
                "critical" if brake else "attention", "degraded",
                "GPU is thermally slowed by its own firmware",
                "The GPU clock is being cut because silicon or memory hits its "
                "thermal ceiling — cooling, paste or case airflow, not the "
                "driver.",
                {"clock_events": {k: v for k, v in events.items() if v},
                 "gpu_temp_c": smi.get("temp_c")},
                "Clean the heatsink/fans, verify mounting pressure and paste, "
                "compare with the thermal diagnostics (fw.diag.thermal).",
                "high" if brake else "medium"))
        bar1 = smi.get("bar1_total_mib")
        if isinstance(bar1, int) and bar1 <= 256:
            findings.append(_finding(
                "gpu-bar1-small", "info", "mis-adjusted",
                f"BAR1 limited to {bar1} MiB — Resizable BAR likely disabled",
                "With Above 4G decoding + Resizable BAR the CPU can map the "
                "whole VRAM; at 256 MiB the BIOS default (not a fault) is "
                "active and some games lose a few percent.",
                {"bar1_total_mib": bar1},
                "Optional: enable 'Above 4G Decoding' and 'Resizable BAR' in "
                "BIOS (not observable from the OS).",
                "medium"))
    except (system.ToolMissing, FileNotFoundError):
        errors.append("nvidia-smi not available — NVIDIA state not readable "
                      "(driver not installed or no NVIDIA GPU)")
    except (RuntimeError, TimeoutError) as exc:
        errors.append(f"nvidia-smi: {exc}")

    # --- kernel log: Xid errors --------------------------------------------
    try:
        xids = _parse_xid(_run(["dmesg"], fixture_dir, "dmesg"))
        source.append("dmesg")
        status["xid_errors"] = xids
        if xids:
            codes = {x["code"] for x in xids}
            crit = codes & _XID_CRITICAL
            findings.append(_finding(
                "gpu-xid-errors",
                "critical" if crit else "attention", "defective",
                f"{len(xids)} Xid error(s) in the kernel log "
                f"(codes {sorted(codes)})",
                "Xid 13 = graphics engine fault (workload or overclock), "
                "62 = internal micro-controller halt, 79 = the GPU fell off "
                "the bus (power/riser/seat). The GPU spoke: this is not a "
                "silent setting issue.",
                {"codes": sorted(codes), "last": xids[-1]["line"]},
                ("Xid 79/94/95: reseat the card, test the PCIe power connectors, "
                 "remove risers — before suspecting the card itself."
                 if crit else
                 "Check clocks/voltage stability (stock vs OC), driver version, "
                 "and whether the fault follows one workload."),
                "high" if crit else "medium"))
    except FileNotFoundError:
        pass  # dmesg fixture absent — tolerated
    except system.ToolMissing:
        errors.append("dmesg not accessible (kernel.dmesg_restrict?) — Xid "
                      "history not readable; try sudo dmesg or journalctl -k")
    except (RuntimeError, TimeoutError) as exc:
        errors.append(f"dmesg: {exc}")

    # --- PCIe link of the VGA device ----------------------------------------
    try:
        devices = _parse_lspci(_run(["lspci", "-vv"], fixture_dir, "lspci"))
        source.append("lspci -vv")
        vga = [d for d in devices
               if "VGA compatible controller" in (d.get("desc") or "")]
        status["pcie"] = [{"slot": d["slot"], "desc": d["desc"],
                           "lnkcap": d.get("lnkcap"), "lnksta": d.get("lnksta"),
                           "region1": next((b for b in d["bars"]
                                            if b.startswith("Region 1:")), None)}
                          for d in vga]
        for d in vga:
            cap_w, sta_w = _width_of(d.get("lnkcap")), _width_of(d.get("lnksta"))
            sta_s = _speed_of(d.get("lnksta"))
            if cap_w and sta_w and sta_w < cap_w:
                findings.append(_finding(
                    "gpu-pcie-degraded", "attention", "mis-adjusted",
                    f"GPU link width degraded: x{sta_w} instead of x{cap_w}",
                    "The card does not get the lanes it was designed for: a "
                    "riser, a badly seated card, a BIOS slot setting or lane "
                    "bifurcation — a physical/setting problem, rarely a defect.",
                    {"slot": d["slot"], "lnkcap": d["lnkcap"], "lnksta": d["lnksta"]},
                    "Reseat the card; remove the riser; check the BIOS PCIe "
                    "slot configuration and bifurcation.",
                    "medium"))
    except FileNotFoundError:
        pass
    except system.ToolMissing:
        pass  # already surfaced by storage if relevant
    except (RuntimeError, TimeoutError) as exc:
        errors.append(f"lspci: {exc}")

    sev_rank = {"critical": 0, "attention": 1, "info": 2}
    findings.sort(key=lambda f: (sev_rank.get(f["severity"], 3), f["id"]))
    status.update({
        "findings": findings,
        "verdict": ("critical" if any(f["severity"] == "critical" for f in findings)
                    else "attention" if any(f["severity"] == "attention" for f in findings)
                    else "healthy" if (smi or source) else "undetermined"),
        "errors": errors,
        "source": source,
    })
    return status
