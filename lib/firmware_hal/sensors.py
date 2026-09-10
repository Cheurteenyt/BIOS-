"""hwmon sensor collector — temperatures, fans, voltages. T0.

Direct read of /sys/class/hwmon (k10temp for the AMD CCD, nct67xx for the
ASUS Super I/O). This is the only collector that does not go through a CLI:
hwmon is the canonical kernel interface, read-only, and the kernel layer of
volume 2 (fig. 6.1) is never touched other than by reading here.
"""

from __future__ import annotations

import json
from pathlib import Path

HWMON = Path("/sys/class/hwmon")


def collect(fixture_dir=None) -> dict:
    if fixture_dir is not None:
        p = Path(fixture_dir) / "sensors.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {"chips": [], "warning": "sensors fixture missing"}

    chips = []
    try:
        dirs = sorted(HWMON.iterdir())
    except OSError:
        return {"chips": [], "warning": "/sys/class/hwmon not readable"}

    for d in dirs:
        name_file = d / "name"
        if not name_file.exists():
            continue
        chip = {"name": name_file.read_text().strip(), "temps": {}, "fans": {}, "volts": {}}
        for f in sorted(d.iterdir()):
            try:
                if f.name.startswith("temp") and f.name.endswith("_input"):
                    label = f.name.replace("_input", "_label")
                    lab = (d / label).read_text().strip() if (d / label).exists() else f.name
                    chip["temps"][lab] = round(int(f.read_text().strip()) / 1000.0, 1)
                elif f.name.startswith("fan") and f.name.endswith("_input"):
                    lab = f.name
                    chip["fans"][lab] = int(f.read_text().strip())
                elif f.name.startswith("in") and f.name.endswith("_input"):
                    lab = f.name
                    chip["volts"][lab] = round(int(f.read_text().strip()) / 1000.0, 3)
            except (OSError, ValueError):
                continue  # ephemeral sensor: skipped silently
        if chip["temps"] or chip["fans"] or chip["volts"]:
            chips.append(chip)
    return {"chips": chips, "source": "/sys/class/hwmon"}
