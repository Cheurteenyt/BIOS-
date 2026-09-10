"""The day-0 photograph — what the machine in front of you really is.

`capture` reads ONLY (every collector it drives is T0) and writes one
timestamped JSON snapshot. Three uses:

  1. day-0 record — the ground truth the twin approximates;
  2. twin-1.1 fodder — the cpu/hwmon sections mirror the twin-sysfs
     shapes, so turning a surprise into a new fixture is a copy-edit,
     not a rewrite;
  3. before/after — capture around a BIOS update: the diff between two
     captures is the firmware change, in facts, not impressions.

Honesty rules: every section carries its provenance ("twin-sourced" vs
"live", roots named); a sensorless host records nulls and section
errors, never guesses; no confirm flag exists and nothing here writes
to the machine — the only artifact is the snapshot file itself.
"""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

from . import audit, boot, cve_kb, cve_watch, diagnostics, fwupd, gpu, \
    journal, ram, settings as settings_mod, storage, twin

CAPTURE_SCHEMA = "omarchy-firmware/capture@1"


# ----------------------------------------------------------------- readers


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _cpu_detail(root: str | None) -> dict:
    """Per-cpu EPP facts — the exact files twin-sysfs mirrors."""
    out: dict = {"root": root, "cpus": []}
    if not root:
        return out
    for cpu_dir in sorted(Path(root).glob("cpu[0-9]*")):
        cf = cpu_dir / "cpufreq"
        out["cpus"].append({
            "cpu": cpu_dir.name,
            "epp_available": _read(cf / "energy_performance_available_preferences"),
            "epp_current": _read(cf / "energy_performance_preference"),
            "scaling_driver": _read(cf / "scaling_driver"),
        })
    return out


def _hwmon_detail(root: str | None) -> dict:
    """Per-chip fan/temperature structure — what fans.curve.set targets."""
    out: dict = {"root": root, "chips": []}
    if not root:
        return out
    base = Path(root)
    for chip in sorted(base.iterdir()):
        if not chip.is_dir():
            continue
        c: dict = {"chip": chip.name, "name": _read(chip / "name"),
                   "pwms": [], "temp_samples": {}, "fan_samples": {}}
        for pwm in sorted(chip.glob("pwm[0-9]*")):
            entry = {"pwm": pwm.name, "value": _read(pwm)}
            enable = chip / (pwm.name + "_enable")
            if enable.exists():
                entry["enable"] = _read(enable)
            c["pwms"].append(entry)
        for t in sorted(chip.glob("temp[0-9]*_input")):
            c["temp_samples"][t.name] = _read(t)
        for f in sorted(chip.glob("fan[0-9]*_input")):
            c["fan_samples"][f.name] = _read(f)
        out["chips"].append(c)
    return out


def _environment() -> dict:
    from . import __version__
    return {
        "kernel": platform.release(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "omarchy_firmware": __version__,
    }


# ---------------------------------------------------------------- sections
# The ten T0 collections in contract order. Each keeps its own shape —
# the snapshot must stay diffable against future captures and against
# the twin's fixtures.


def _sections(fx: str | None) -> list[tuple[str, object]]:
    return [
        ("board", lambda: audit.collect(fx)),
        ("cve_posture", lambda: cve_kb.collect(fx)),
        ("boot", lambda: boot.collect(fx)),
        ("fwupd_local", lambda: fwupd.check_updates(fx, refresh=False)),
        ("kb_freshness", lambda: cve_watch.collect(fx)),
        ("storage", lambda: storage.collect(fx)),
        ("gpu", lambda: gpu.collect(fx)),
        ("ram", lambda: ram.collect(fx)),
        ("settings", lambda: settings_mod.collect(fx)),
        ("thermal", lambda: diagnostics.quick(
            scenario=None, fixture_dir=fx, record=False)),
    ]


# ----------------------------------------------------------------- capture


def capture(*, out: str | None = None) -> dict:
    """One T0 photograph of this machine, written as a snapshot file."""
    fx = os.environ.get("FW_FIXTURE_DIR") or twin.resolve_fixture_dir()
    desc = twin.describe()
    applied = twin.apply_sysfs_env()
    origin = "live" if desc.get("source") == "MISSING" else "twin-sourced"

    sections: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for name, fn in _sections(fx):
        try:
            data = fn()
            if isinstance(data, dict):
                data.pop("journal_entry", None)  # the snapshot stays clean
            sections[name] = {"origin": origin, "data": data}
        except Exception as exc:  # noqa: BLE001 — a section failure is recorded
            errors[name] = f"{type(exc).__name__}: {exc}"[:120]
            sections[name] = {"origin": origin, "data": None}

    cpu_root = os.environ.get("FW_SYSFS_CPU")
    hwmon_root = os.environ.get("FW_SYSFS_HWMON")
    sections["cpu_epp"] = {"origin": origin, "data": _cpu_detail(cpu_root)}
    sections["hwmon"] = {"origin": origin, "data": _hwmon_detail(hwmon_root)}
    sections["environment"] = {"origin": "host", "data": _environment()}

    snap: dict = {
        "schema": CAPTURE_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "backend": origin,
        "twin_source": desc.get("source"),
        "twin_note": f"sysfs applied: {applied or 'none'}",
        "sections": sections,
        "section_errors": errors,
    }
    dest = (Path(out) if out else
            journal.state_dir() / "captures"
            / f"capture-{time.strftime('%Y%m%d-%H%M%S')}.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(snap, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    snap["capture_file"] = str(dest)
    journal.record(
        "capture", "T0",
        ["capture", "--out", str(dest)] if out else ["capture"], "ok",
        f"{origin}: {len(sections)} sections, {len(errors)} error(s) — "
        f"schema {CAPTURE_SCHEMA}")
    return snap


def render(snap: dict) -> str:
    """Human rendering — what was read, from where, with what roots."""
    lines = [f"== Capture — backend: {snap['backend']} "
             f"(twin source: {snap.get('twin_source')}) =="]
    for name, sec in snap["sections"].items():
        d = sec.get("data")
        if d is None:
            lines.append(f"  {name:<14} UNREADABLE — see section_errors")
        elif name == "cpu_epp":
            lines.append(f"  {name:<14} {len(d.get('cpus') or [])} cpu(s), "
                         f"root {d.get('root')}")
        elif name == "hwmon":
            names = [c.get("name") for c in d.get("chips", [])]
            lines.append(f"  {name:<14} {len(d.get('chips') or [])} chip(s) "
                         f"{names if names else ''}, root {d.get('root')}")
        elif isinstance(d, dict):
            key = d.get("verdict") or d.get("status") or f"{len(d)} keys"
            lines.append(f"  {name:<14} {str(key)[:70]}")
        else:
            lines.append(f"  {name:<14} {type(d).__name__}")
    for k, v in snap.get("section_errors", {}).items():
        lines.append(f"  error        : {k}: {v}")
    lines.append(f"capture: {snap.get('capture_file')}")
    lines.append("honesty: a capture reads, names its roots, and never "
                 "writes to the machine.")
    return "\n".join(lines)
