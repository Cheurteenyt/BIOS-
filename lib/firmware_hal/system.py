"""System tool execution — with a fixture mode for tests and demos.

The T0 collectors wrap existing CLIs (dmidecode, efibootmgr, fwupdmgr,
snapper). Each collector accepts a fixture directory: when provided, the
expected output is read from disk instead of executed. This is how
development, tests and demonstrations work without hardware — consistent
with the repo rule: "work from evidence", never guess a machine's state.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FIXTURE_FILES = {
    "dmidecode": "dmidecode.txt",
    "dmidecode_memory": "dmidecode-memory.txt",
    "efibootmgr": "efibootmgr.txt",
    "fwupd_devices": "fwupd-devices.json",
    "fwupd_security": "fwupd-security.json",
    "fwupd_updates": "fwupd-updates.json",
    "sensors": "sensors.json",
    "smartctl_nvme": "smartctl-nvme0.json",
    "smartctl_sda": "smartctl-sda.json",
    "lspci": "lspci.txt",
    "nvidia_smi": "nvidia-smi.txt",
    "dmesg": "dmesg.txt",
    "edac": "edac.json",
}


class ToolMissing(Exception):
    """The source CLI is not installed — reported honestly, never guessed."""


def run(cmd: list[str], fixture_dir: str | Path | None = None,
        fixture_key: str | None = None, timeout: int = 30) -> str:
    """Run cmd, or read the matching fixture when fixture_dir is provided."""
    if fixture_dir is not None and fixture_key:
        p = Path(fixture_dir) / FIXTURE_FILES[fixture_key]
        if not p.exists():
            raise FileNotFoundError(f"missing fixture: {p}")
        return p.read_text(encoding="utf-8")

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        raise ToolMissing(cmd[0]) from None
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"{cmd[0]} did not answer within {timeout} s") from None

    if proc.returncode != 0:
        # dmidecode/efibootmgr sometimes output useful data even with a
        # non-zero code; fwupd is strict. We forward the reason.
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(
            f"{cmd[0]} failed (exit code {proc.returncode})"
            + (f": {err[-1]}" if err else "")
        )
    return proc.stdout
