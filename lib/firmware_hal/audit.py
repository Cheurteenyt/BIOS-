"""Composite audit — the fw.audit.status tool. T0.

Aggregates board, BIOS, boot chain, fwupd and sensors into a single JSON
document that tolerates missing pieces: each section carries its own error
instead of breaking the whole. This is the skill's "first call" tool
(vol. 2, ch. 5, rule 2): where my firmware stands, in one journaled read.
"""

from __future__ import annotations

import platform

from . import boot, cve_kb, fwupd, sensors, smbios


def collect(fixture_dir=None) -> dict:
    board = smbios.collect(fixture_dir)
    bootinfo = boot.collect(fixture_dir)
    fw = fwupd.collect_devices(fixture_dir)
    sens = sensors.collect(fixture_dir)

    from . import __version__
    return {
        "tool": "fw.audit.status",
        "phase": __import__("firmware_hal", fromlist=["PHASE"]).PHASE,
        "hal_version": __version__,
        "host": {
            "hostname": platform.node(),
            "kernel": platform.release(),
            "arch": platform.machine(),
        },
        "board": {k: v for k, v in board.items()},
        "boot": {
            "chain": bootinfo.get("chain"),
            "boot_current": bootinfo.get("boot_current"),
            "boot_order": bootinfo.get("boot_order_names"),
            "entry_count": len(bootinfo.get("entries", [])),
            "snapper_snapshots": bootinfo.get("snapper_snapshots"),
            "warnings": bootinfo.get("warnings", []),
            "error": bootinfo.get("error"),
        },
        "fwupd": {
            "device_count": fw.get("device_count"),
            "motherboard_in_lvfs": fw.get("motherboard_in_lvfs"),
            "security": fw.get("security"),
            "notable": [d for d in fw.get("devices", []) if d.get("updatable")][:8],
            "error": fw.get("error"),
        },
        "sensors": {
            "chip_count": len(sens.get("chips", [])),
            "chips": sens.get("chips", []),
            "warning": sens.get("warning"),
        },
    }
