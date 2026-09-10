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
"live", roots named) and its measured cost in ms — the frugality budget
is a claim, so the photograph measures itself; a sensorless host records
nulls and section errors, never guesses; no confirm flag exists and
nothing here writes to the machine — the only artifact is the snapshot
file itself, and the embedded watch/fwupd sections run with their own
state persistence off (the drift baseline and the update cache are NOT
touched by a photograph).

Two forms:
  capture          — twin-aware (development, demos): when twin assets
                     resolve they are photographed, and the snapshot says
                     so LOUDLY (capture_note), because photographing
                     TWIN-1 while believing one photographs the machine is
                     exactly the day-0 mistake this tool exists to prevent;
  capture --live   — the day-0 form: twin assets (fixtures, sysfs tree)
                     are ignored, the roots are the real /sys. The P5
                     protocol step 2 is `omarchy-firmware capture --live`.

One explicit extra: capture --spi-read adds the spi_map section — a
read-only cartography of the flash chip itself (flashrom -r, 0 bytes
written, see spi_map.py). It is NEVER taken by default: an SPI read is
a declared deep probe, not an ambient tool, and it is not part of the
MCP surface either.
"""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

from . import audit, boot, cve_kb, cve_watch, diagnostics, fwupd, gpu, \
    journal, ram, settings as settings_mod, spi_map, storage, twin
from .atomic import atomic_write_text

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
        ("fwupd_local", lambda: fwupd.check_updates(fx, refresh=False,
                                                    persist_cache=False)),
        ("kb_freshness", lambda: cve_watch.collect(fx, record=False)),
        ("storage", lambda: storage.collect(fx)),
        ("gpu", lambda: gpu.collect(fx)),
        ("ram", lambda: ram.collect(fx)),
        ("settings", lambda: settings_mod.collect(fx)),
        ("thermal", lambda: diagnostics.quick(
            scenario=None, fixture_dir=fx, record=False)),
    ]


# ----------------------------------------------------------------- capture


def capture(*, out: str | None = None, live: bool = False,
            spi_read: bool = False) -> dict:
    """One T0 photograph, written as a snapshot file.

    live=False (default): twin-aware — when twin assets resolve, they are
    photographed and the snapshot says so loudly (capture_note).
    live=True: photograph THIS machine — twin fixtures and the twin sysfs
    tree are ignored, the detail roots are the real /sys. Day 0 wants
    --live: the twin is installed beside the tool precisely on the machine
    this flag exists to photograph.
    spi_read=True: add the spi_map section — an explicit, read-only
    cartography of the flash chip (0 bytes written). Never the default.
    """
    if live:
        fx = None
        desc: dict = {"source": "MISSING"}
        applied: dict = {}
        cpu_root = "/sys/devices/system/cpu"
        hwmon_root = "/sys/class/hwmon"
        origin = "live"
    else:
        fx = os.environ.get("FW_FIXTURE_DIR") or twin.resolve_fixture_dir()
        desc = twin.describe()
        saved_sysfs = {v: os.environ.get(v)
                       for v in ("FW_SYSFS_CPU", "FW_SYSFS_HWMON")}
        applied = twin.apply_sysfs_env()
        origin = "live" if desc.get("source") == "MISSING" else "twin-sourced"
        cpu_root = os.environ.get("FW_SYSFS_CPU")
        hwmon_root = os.environ.get("FW_SYSFS_HWMON")

    def _run(name: str, fn, *args) -> None:
        t0 = time.perf_counter()
        try:
            data = fn(*args)
            if isinstance(data, dict):
                data.pop("journal_entry", None)  # the snapshot stays clean
            sec = {"origin": origin, "data": data}
        except Exception as exc:  # noqa: BLE001 — a section failure is recorded
            errors[name] = f"{type(exc).__name__}: {exc}"[:120]
            sec = {"origin": origin, "data": None}
        sec["ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        sections[name] = sec

    try:
        sections: dict[str, dict] = {}
        errors: dict[str, str] = {}
        for name, fn in _sections(fx):
            _run(name, fn)
        _run("cpu_epp", _cpu_detail, cpu_root)
        _run("hwmon", _hwmon_detail, hwmon_root)
        _run("environment", _environment)
        if spi_read:
            _run("spi_map", lambda: spi_map.collect())
            if "spi_map" in sections:
                sections["spi_map"]["origin"] = "spi-read (0 bytes written)"
    finally:
        if not live:
            twin.restore_sysfs_env(saved=saved_sysfs)

    snap: dict = {
        "schema": CAPTURE_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "backend": origin,
        "live": live,
        "spi_read": spi_read,
        "twin_source": desc.get("source"),
        "twin_note": f"sysfs applied: {applied or 'none'}",
        "sections": sections,
        "section_errors": errors,
    }
    if origin == "twin-sourced":
        snap["capture_note"] = (
            "twin assets resolved automatically — this is TWIN-1's "
            "photograph, not this machine's; day 0 wants `capture --live`")
    if spi_read:
        snap["spi_note"] = ("SPI read requested explicitly (--spi-read): "
                            "read-only, 0 bytes written, not part of the "
                            "default photograph")
    dest = (Path(out) if out else
            journal.state_dir() / "captures"
            / f"capture-{time.strftime('%Y%m%d-%H%M%S')}.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(dest, json.dumps(snap, ensure_ascii=False, indent=2))
    snap["capture_file"] = str(dest)
    argv = ["capture"]
    if live:
        argv.append("--live")
    if spi_read:
        argv.append("--spi-read")
    if out:
        argv += ["--out", str(dest)]
    journal.record(
        "capture", "T0", argv, "ok",
        f"{origin}: {len(sections)} sections, {len(errors)} error(s) — "
        f"schema {CAPTURE_SCHEMA}")
    return snap


def render(snap: dict) -> str:
    """Human rendering — what was read, from where, with what roots."""
    lines = [f"== Capture — backend: {snap['backend']} "
             f"(twin source: {snap.get('twin_source')}) =="]
    if snap.get("capture_note"):
        lines.append(f"  NOTE: {snap['capture_note']}")
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
        elif name == "spi_map" and isinstance(d, dict):
            if d.get("status") == "ok":
                s2 = d.get("summary") or {}
                lines.append(f"  {name:<14} {s2.get('fv_count', 0)} FV(s), "
                             f"{s2.get('dxe_drivers', 0)} DXE, "
                             f"{s2.get('smm_drivers', 0)} SMM — read-only "
                             "SPI, 0 bytes written")
            else:
                lines.append(f"  {name:<14} UNAVAILABLE — "
                             f"{str(d.get('reason'))[:70]}")
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
