"""The digital twin — TWIN-1, the rehearsal machine.

The target machine (Ryzen 9 5950X, ASUS B450-PLUS, RTX 3070, NVMe 980 PRO,
AIO 240) cannot be touched before the first real session. Everything that
can be rehearsed without it must be rehearsed without it: the twin is the
bundled fixture set promoted to a first-class, installable machine profile.

The twin is honest about what it is:
  - it replays RECORDED sensor series and COLLECTIONS (dmidecode, fwupd,
    SMART…), so it proves the behavioural contract (exit codes, refusals,
    dry-run plans, journal lines), not physics;
  - it is +0 bytes on any SPI flash and idle when unused — it is a fixture
    directory, not a daemon.

Resolution order for the twin assets (first match wins):
  1. $FW_TWIN_DIR                    — explicit override (tests, CI)
  2. installed twin                  — ~/.local/share/omarchy-firmware/twin
  3. repository layout               — <repo>/tests/fixtures (development)

The same order applies to the sysfs twin (a minimal /sys tree that makes
T1 dry-runs deterministic on hosts without EPP or fan chips):
  1. already set FW_SYSFS_CPU / FW_SYSFS_HWMON   — respect the caller
  2. $FW_TWIN_DIR/sysfs                          — explicit override
  3. installed twin sysfs
  4. repository tests/fixtures/twin-sysfs
"""

from __future__ import annotations

import os
from pathlib import Path

TWIN_NAME = "TWIN-1"

PROFILE = {
    "name": TWIN_NAME,
    "story": ("rehearsal machine for the first real session — the vol. 1-4 "
              "reference build"),
    "board": "ASUS B450-PLUS GAMING (BIOS 3644, AGESA 1.2.0.12)",
    "cpu": "AMD Ryzen 9 5950X (16C/32T, AM4)",
    "gpu": "NVIDIA RTX 3070 (GSP-capable)",
    "storage": "Samsung 980 PRO 1TB (NVMe) + SATA disk",
    "cooling": "AIO 240 (pump + radiator fans) + chassis fans (nct6798)",
    "boot": "Limine + UKI chain (Omarchy)",
    "assets": {
        "fixtures": ["b450-plus", "b450-plus-clean", "b550-f-old"],
        "scenarios": 12,
        "sysfs": ["cpu (EPP)", "hwmon (nct6798)"],
    },
    "cannot_prove": (
        "real sensor names, real EPP presence, live fwupd DBus, ADC noise — "
        "these are exactly what the day-0 drill measures on the machine"),
}


def _installed_root() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser(
        "~/.local/share")
    return Path(base) / "omarchy-firmware"


def _repo_root() -> Path:
    # lib/firmware_hal/twin.py -> repository root
    return Path(__file__).resolve().parents[2]


def twin_root() -> Path | None:
    """Directory holding the twin assets (fixture sets + scenarios + sysfs)."""
    env = os.environ.get("FW_TWIN_DIR")
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    installed = _installed_root() / "twin"
    if installed.is_dir():
        return installed
    repo = _repo_root() / "tests" / "fixtures"
    if repo.is_dir():
        return repo
    return None


def resolve_fixture_dir(board: str = "b450-plus") -> str | None:
    """Fixture directory of a twin board, or None when absent."""
    root = twin_root()
    if root is None:
        return None
    p = root / board
    return str(p) if p.is_dir() else None


def resolve_scenario_dir() -> Path | None:
    """Scenario directory (12 bundled thermal series), twin-aware."""
    env = os.environ.get("FW_SCENARIO_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    root = twin_root()
    if root is None:
        return None
    p = root / "scenarios"
    return p if p.is_dir() else None


def _sysfs_candidate() -> Path | None:
    root = twin_root()
    if root is None:
        return None
    p = root / "twin-sysfs"
    return p if p.is_dir() else None


def apply_sysfs_env(force: bool = False) -> dict:
    """Point FW_SYSFS_CPU / FW_SYSFS_HWMON at the twin tree when the caller
    has not set them. Returns what was applied (for the rehearsal report)."""
    applied: dict = {}
    cand = _sysfs_candidate()
    if cand is None:
        return applied
    for var, sub in (("FW_SYSFS_CPU", "cpu"), ("FW_SYSFS_HWMON", "hwmon")):
        if os.environ.get(var) and not force:
            applied[var] = "caller-set (respected)"
            continue
        p = cand / sub
        if p.is_dir():
            os.environ[var] = str(p)
            applied[var] = str(p)
    return applied


def describe() -> dict:
    """What the twin is, where its assets resolve from — for `twin` status."""
    root = twin_root()
    fx = resolve_fixture_dir()
    scen = resolve_scenario_dir()
    return {
        "profile": PROFILE,
        "asset_root": str(root) if root else None,
        "fixture_dir": fx,
        "scenario_dir": str(scen) if scen else None,
        "scenario_count": (len(list(scen.glob("*.json"))) if scen else 0),
        "sysfs_cpu": os.environ.get("FW_SYSFS_CPU")
        or (str(_sysfs_candidate() / "cpu") if _sysfs_candidate() else None),
        "source": ("env FW_TWIN_DIR" if os.environ.get("FW_TWIN_DIR")
                   else "installed" if (_installed_root() / "twin").is_dir()
                   else "repository" if root else "MISSING"),
    }
