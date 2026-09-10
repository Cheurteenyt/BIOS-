"""T1 reversible write layer — dry-run by default, two keys, rollback.

Volume 4 doctrine (ch. 4), now implemented for exactly two write targets:
  cpu.epp.set    the Energy Performance Preference of every CPU
  fans.curve.set the Smart Fan curve of an ASUS Super I/O (nct67xx family)

Mechanical rules — enforced by code, not by good will:
  1. DRY-RUN BY DEFAULT. Without `confirm=True` nothing is written; the
     return value is the exact plan (current values, targets, diff).
  2. TWO KEYS. A real write requires an explicit confirm flag from the
     caller (CLI --confirm / MCP confirm param). One flag, no timeout
     trickery, no "force".
  3. BACKUP BEFORE WRITE. Every applied write pushes the previous state to
     the rollback store (XDG state / omarchy-firmware / rollback /). The
     undo verb restores it, itself journaled as "rolled-back".
  4. MECHANICAL CURVE GUARD. A fan curve MUST end at pwm=255 and its last
     point MUST stay at or below 90 °C: no agent can cap cooling at the top
     of the range. A curve that tries is refused before any write.
  5. ONLY THE DECLARED TARGETS. EPP touches only EPP files; fan curves
     touch only pwm/point attributes of a supported Super I/O. There is no
     generic "write this file" path, and no T2/T3 call path exists.

The boundary (CLI / MCP) journals every call with its status:
dry-run | applied | rolled-back | refused.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from . import journal

# ---- sysfs roots (env-injectable: tests run on a temp tree) ----------------


def _cpu_root() -> Path:
    return Path(os.environ.get("FW_SYSFS_CPU") or "/sys/devices/system/cpu")


def _hwmon_root() -> Path:
    return Path(os.environ.get("FW_SYSFS_HWMON") or "/sys/class/hwmon")


def _rollback_dir() -> Path:
    d = journal.state_dir() / "rollback"
    d.mkdir(parents=True, exist_ok=True)
    return d


class ActionRefused(Exception):
    """A T1 action refused BEFORE any write — the message is the reason."""


def _read(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _write(p: Path, value: str) -> None:
    try:
        p.write_text(value, encoding="utf-8")
    except OSError as exc:
        raise ActionRefused(f"write refused on {p}: {exc}") from None


def _backup(name: str, values: dict[str, str]) -> int:
    """Append one backup frame to the rollback store; return its id."""
    p = _rollback_dir() / f"{name}.json"
    frames = []
    if p.exists():
        try:
            frames = json_loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a corrupt store never blocks a backup
            frames = []
    frames.append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "targets": values})
    p.write_text(json_dumps(frames[-10:]), encoding="utf-8")  # keep the last 10
    return len(frames) - 1


def _pop_backup(name: str) -> dict:
    p = _rollback_dir() / f"{name}.json"
    if not p.exists():
        raise ActionRefused("no rollback frame stored for this target")
    try:
        frames = json_loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ActionRefused(f"rollback store unreadable: {exc}") from None
    if not frames:
        raise ActionRefused("rollback store empty — nothing to restore")
    return frames[-1]


# small json shims so this module reads cleanly -------------------------------


def json_loads(s: str):
    import json
    return json.loads(s)


def json_dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)


# --------------------------------------------------------------- cpu.epp.set


EPP_ROLLBACK = "epp"


def _epp_targets(cpu_root: Path) -> list[Path]:
    return sorted(cpu_root.glob("cpu[0-9]*/cpufreq/energy_performance_preference"))


def epp_set(value: str | None = None, confirm: bool = False,
            undo: bool = False, cpu_root: Path | None = None) -> dict:
    """Set the EPP hint of every CPU. Dry-run by default; undo supported."""
    root = Path(cpu_root) if cpu_root is not None else _cpu_root()

    if undo:
        if confirm:
            frame = _pop_backup(EPP_ROLLBACK)
            restored = {}
            refused = []
            for path_s, old in frame["targets"].items():
                p = Path(path_s)
                if not p.exists():
                    refused.append(f"{path_s} (gone since backup)")
                    continue
                _write(p, old)
                restored[path_s] = old
            return {"tool": "cpu.epp.set", "action": "undo",
                    "status": "rolled-back",
                    "restored": restored,
                    "refused": refused,
                    "note": "previous EPP values restored from the rollback store"}
        return {"tool": "cpu.epp.set", "action": "undo", "status": "dry-run",
                "plan": "restore the last backed-up EPP values (rollback "
                        "store, latest frame) — re-run with confirm=True"}

    if not value:
        raise ActionRefused("cpu.epp.set requires a value (one of the "
                            "available preferences) — or undo=True")

    available = (_read(root / "cpu0" / "cpufreq" /
                       "energy_performance_available_preferences") or "").split()
    if not available:
        raise ActionRefused(
            "EPP is not exposed on this machine "
            "(no energy_performance_available_preferences under "
            f"{root}/cpu0/cpufreq) — amd-pstate/intel_pstate may be inactive; "
            "nothing to adjust")
    if value not in available:
        raise ActionRefused(
            f"invalid EPP value '{value}' — available: {', '.join(available)}")

    targets = _epp_targets(root)
    if not targets:
        raise ActionRefused("no EPP target file found — nothing to adjust")
    current = {str(p): _read(p) or "" for p in targets}
    already = all(v == value for v in current.values())

    plan = {
        "action": "epp.set", "value": value,
        "available": available,
        "targets": [str(p) for p in targets],
        "current_values": current,
        "diff": {k: {"from": v, "to": value}
                 for k, v in current.items() if v != value},
    }
    if already:
        return {"tool": "cpu.epp.set", "status": "dry-run",
                "note": f"all CPUs already at '{value}' — nothing to do",
                **plan}
    if not confirm:
        return {"tool": "cpu.epp.set", "status": "dry-run",
                "note": "DRY RUN — nothing written; re-run with "
                        "confirm=True (CLI: --confirm) to apply",
                **plan}

    backup_id = _backup(EPP_ROLLBACK, current)
    applied, refused = {}, []
    for p, v in current.items():
        if v == value:
            continue
        try:
            _write(Path(p), value)
            applied[p] = value
        except ActionRefused as exc:
            refused.append(str(exc))
    return {"tool": "cpu.epp.set", "status": "applied", "backup_id": backup_id,
            "value": value, "applied": applied, "refused": refused,
            "undo": "cpu epp undo --confirm restores the previous values"}


# ------------------------------------------------------------ fans.curve.set


FANS_ROLLBACK = "fans"
# The supported Super I/O family (ASUS boards — the project's target): the
# nct67xx driver exposes pwm{N}_auto_point{K}_temp/_pwm and mode 5 = the
# hardware curve. Other families are refused honestly, never guessed.
_NCT_FAMILY = "nct"


def _chip_dir(hwmon_root: Path, name: str) -> Path:
    try:
        for d in sorted(hwmon_root.iterdir()):
            nm = _read(d / "name")
            if nm == name:
                return d
    except OSError:
        pass
    raise ActionRefused(
        f"hwmon chip '{name}' not found under {hwmon_root} — "
        "run `fw.diag.settings` to list the exposed chips")


def _point_attrs(pwm_dir: Path, pwm_n: int) -> int:
    """Count the auto_point slots the driver exposes for this pwm output."""
    k = 1
    while (pwm_dir / f"pwm{pwm_n}_auto_point{k}_temp").exists() and \
            (pwm_dir / f"pwm{pwm_n}_auto_point{k}_pwm").exists():
        k += 1
    return k - 1


def _validate_curve(points: list[dict]) -> None:
    """Mechanical guards — refused before ANY write (rule 4)."""
    if not isinstance(points, list) or not (2 <= len(points) <= 7):
        raise ActionRefused("a curve needs between 2 and 7 points")
    prev_t = None
    for pt in points:
        if not isinstance(pt, dict) or "temp" not in pt or "pwm" not in pt:
            raise ActionRefused("each point needs 'temp' (°C) and 'pwm' (0-255)")
        t, p = pt["temp"], pt["pwm"]
        if not isinstance(t, int) or not isinstance(p, int):
            raise ActionRefused("temp and pwm must be integers")
        if not (20 <= t <= 90):
            raise ActionRefused(f"point temp {t} °C outside 20-90 °C")
        if not (0 <= p <= 255):
            raise ActionRefused(f"point pwm {p} outside 0-255")
        if prev_t is not None and t <= prev_t:
            raise ActionRefused(
                f"curve temps must strictly ascend ({t} follows {prev_t})")
        prev_t = t
    if points[-1]["pwm"] != 255:
        raise ActionRefused(
            "mechanical guard: the last curve point MUST be pwm=255 — no "
            "agent may cap cooling at the top of the range")
    if points[-1]["temp"] > 90:
        raise ActionRefused(
            "mechanical guard: the last curve point must stay at or below "
            "90 °C (Tjmax headroom)")


def fans_curve_set(curve: dict | None = None, confirm: bool = False,
                   undo: bool = False, hwmon_root: Path | None = None) -> dict:
    """Write a Smart Fan curve on an nct67xx-class chip. Dry-run by default."""
    root = Path(hwmon_root) if hwmon_root is not None else _hwmon_root()

    if undo:
        if confirm:
            frame = _pop_backup(FANS_ROLLBACK)
            restored, refused = {}, []
            for path_s, old in frame["targets"].items():
                p = Path(path_s)
                if not p.exists():
                    refused.append(f"{path_s} (gone since backup)")
                    continue
                _write(p, old)
                restored[path_s] = old
            return {"tool": "fans.curve.set", "action": "undo",
                    "status": "rolled-back", "restored": restored,
                    "refused": refused}
        return {"tool": "fans.curve.set", "action": "undo", "status": "dry-run",
                "plan": "restore the last backed-up fan curve (enable + "
                        "auto points) — re-run with confirm=True"}

    if not isinstance(curve, dict):
        raise ActionRefused(
            "fans.curve.set needs a curve object: "
            '{"hwmon": "nct6798", "pwm": 1, "points": '
            '[{"temp": 40, "pwm": 90}, ..., {"temp": 85, "pwm": 255}]}')

    chip_name = curve.get("hwmon")
    pwm_n = curve.get("pwm")
    points = curve.get("points")
    if not chip_name or not isinstance(pwm_n, int):
        raise ActionRefused("curve needs 'hwmon' (chip name) and 'pwm' "
                            "(output number, int)")
    _validate_curve(points)

    chip = _chip_dir(root, str(chip_name))
    real_name = _read(chip / "name") or ""
    if not real_name.startswith(_NCT_FAMILY):
        raise ActionRefused(
            f"chip '{real_name}' is outside the supported nct67xx family — "
            "refusing to guess another vendor's auto-point semantics "
            "(open an issue with your `hwmon` chip name)")
    pwm_val = _read(chip / f"pwm{pwm_n}")
    if pwm_val is None:
        raise ActionRefused(
            f"{chip.name}/pwm{pwm_n} not exposed — this output does not exist")
    slots = _point_attrs(chip, pwm_n)
    if slots < 2:
        raise ActionRefused(
            f"chip exposes no auto_point attributes for pwm{pwm_n} — no "
            "hardware curve writable from the OS; refusing to fake one")
    if len(points) > slots:
        raise ActionRefused(
            f"the curve has {len(points)} points but the chip exposes only "
            f"{slots} slot(s) — refusing to silently drop points (the "
            "mandatory pwm=255 tail could disappear); trim the curve")

    enable_path = chip / f"pwm{pwm_n}_enable"
    writes: list[dict] = []
    if enable_path.exists():
        writes.append({"attr": str(enable_path), "from": _read(enable_path) or "",
                       "to": "5"})
    for k in range(1, slots + 1):
        if k <= len(points):
            pt = points[k - 1]
        else:  # fill the remaining slots: hold the last point (255 at top)
            pt = {"temp": points[-1]["temp"], "pwm": 255}
        for suffix, val in (("temp", pt["temp"]), ("pwm", pt["pwm"])):
            p = chip / f"pwm{pwm_n}_auto_point{k}_{suffix}"
            writes.append({"attr": str(p), "from": _read(p) or "",
                           "to": str(val)})

    current = {w["attr"]: w["from"] for w in writes}
    if all(w["from"] == w["to"] for w in writes):
        return {"tool": "fans.curve.set", "status": "dry-run",
                "note": "the requested curve is already in place — nothing "
                        "to write",
                "chip": real_name, "pwm": pwm_n, "points": points}

    if not confirm:
        return {"tool": "fans.curve.set", "status": "dry-run",
                "note": "DRY RUN — nothing written; re-run with "
                        "confirm=True (CLI: --confirm) to apply",
                "chip": real_name, "pwm": pwm_n,
                "points": points, "slots": slots,
                "plan_writes": writes}

    backup_id = _backup(FANS_ROLLBACK, current)
    applied, refused = 0, []
    # points first, mode switch last: the fan keeps its previous behaviour
    # until the whole curve is in place.
    for w in sorted(writes, key=lambda w: w["attr"].endswith("_enable")):
        try:
            _write(Path(w["attr"]), w["to"])
            applied += 1
        except ActionRefused as exc:
            refused.append(str(exc))
    return {"tool": "fans.curve.set", "status": "applied",
            "backup_id": backup_id, "chip": real_name, "pwm": pwm_n,
            "applied_writes": applied, "refused": refused,
            "undo": "fans curve undo --confirm restores the previous curve"}


def fans_curve_show(hwmon_root: Path | None = None) -> dict:
    """Read-only view of the fan outputs and their current modes/points."""
    root = Path(hwmon_root) if hwmon_root is not None else _hwmon_root()
    chips = []
    try:
        dirs = sorted(root.iterdir())
    except OSError as exc:
        raise ActionRefused(f"hwmon root unreadable ({root}): {exc}") from None
    for d in dirs:
        name = _read(d / "name")
        if not name:
            continue
        outs = {}
        for f in sorted(d.glob("pwm[0-9]")):
            n = f.stem
            slots = _point_attrs(d, int(n[3:]))
            enable_raw = _read(d / f"{n}_enable")
            try:
                mode = {0: "none (full speed)", 1: "manual",
                        2: "chip automatic",
                        5: "hardware curve (smart fan)"}.get(int(enable_raw or -1),
                                                            enable_raw)
            except ValueError:
                mode = enable_raw
            outs[n] = {
                "value": _read(f),
                "enable": enable_raw,
                "mode": mode,
                "curve_slots": slots,
            }
        if outs:
            chips.append({"name": name, "hwmon_dir": d.name, "outputs": outs})
    return {"tool": "fans.curve.show", "chips": chips}
