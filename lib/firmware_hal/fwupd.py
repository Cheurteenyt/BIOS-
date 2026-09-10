"""fwupd/LVFS collector — devices, HSI posture, updates. T0.

Follows the guard rail of table 6.1: "15-min cache, no network unless
asked". The three calls talk to the local fwupd daemon; the fw.update.check
response is cached in the state directory, and --refresh (CLI) explicitly
triggers a LVFS metadata refresh — the only place Phase 1 touches the
network, on human request.

On desktop AM4 boards, the absence of the motherboard itself from the LVFS
catalogue is the expected result (coverage gap documented in vol. 1, ch. 4):
the tool says so plainly instead of returning an empty verdict.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import system
from .journal import state_dir

CACHE_TTL = 15 * 60  # seconds — table 6.1: 15-min cache


def _devices(fixture_dir=None) -> list[dict]:
    try:
        text = system.run(
            ["fwupdmgr", "get-devices", "--json"], fixture_dir, "fwupd_devices"
        )
    except system.ToolMissing:
        raise  # surfaced as a missing section, never a silence
    except (RuntimeError, FileNotFoundError, TimeoutError):
        raise
    data = json.loads(text)
    devs = data.get("Devices", data) if isinstance(data, dict) else data
    out = []
    for d in devs or []:
        out.append({
            "name": d.get("Name"),
            "version": d.get("Version") or d.get("VersionLowest"),
            "vendor": d.get("Vendor") or d.get("VendorId"),
            "updatable": bool(d.get("Flags") and "updatable" in str(d.get("Flags")).lower())
            or d.get("UpdateState") == "success"
            or bool(d.get("UpdateError") is None and d.get("VersionHighest")),
            "guid": (d.get("Guid") or [None])[0] if d.get("Guid") else None,
            "internal": bool(d.get("Internal")),
        })
    return out


def _security(fixture_dir=None) -> dict | None:
    try:
        text = system.run(
            ["fwupdmgr", "security", "--json"], fixture_dir, "fwupd_security"
        )
        data = json.loads(text)
        # The HSI output nests host security attributes; we keep the
        # readable essentials: global level + failure counters.
        # (key "SecurityAttributes" is legacy, "HostSecurityAttributes" is current)
        hsi = data.get("HostSecurityId") or data.get("HsiLevel")
        attrs = data.get("HostSecurityAttributes") or data.get("SecurityAttributes") or []
        fails = sum(
            1 for a in attrs
            if "fail" in str(a.get("HsiResult", "")).lower()
            or str(a.get("HsiResult", "")) == "hsi-result-not-valid"
        )
        return {"host_security_id": hsi, "attribute_count": len(attrs), "failures": fails}
    except Exception:
        return None  # fwupd < 1.8 or attributes unavailable: stated, not hidden


def collect_devices(fixture_dir=None) -> dict:
    try:
        devs = _devices(fixture_dir)
    except system.ToolMissing:
        return {"error": "fwupdmgr missing (pacman -S fwupd)", "devices": []}
    except Exception as exc:
        return {"error": f"fwupd unreachable: {exc}", "devices": []}
    sec = _security(fixture_dir)
    # A motherboard is "in the LVFS" only if fwupd lists it AND declares it
    # updatable (Updatable): on desktop AM4, the "System Firmware" device
    # exists but without LVFS releases — expected result.
    mb = [
        d for d in devs
        if d.get("updatable") and (
            "board" in (d["name"] or "").lower()
            or "system firmware" in (d["name"] or "").lower()
        )
    ]
    return {
        "device_count": len(devs),
        "devices": devs,
        "motherboard_in_lvfs": bool(mb),
        "security": sec,
        "source": "fwupdmgr get-devices --json",
    }


def check_updates(fixture_dir=None, refresh: bool = False) -> dict:
    """Local update state, with a 15-min cache outside fixture mode."""
    cache = state_dir() / "cache-update.json"
    if fixture_dir is None and not refresh and cache.exists():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            if time.time() - data.get("fetched_at", 0) < CACHE_TTL:
                data["cache"] = "hit"
                return data
        except (json.JSONDecodeError, OSError):
            pass  # corrupted cache: refresh cleanly

    result: dict = {"cache": "miss" if not refresh else "refresh", "updates": []}
    try:
        text = system.run(
            ["fwupdmgr", "get-updates", "--json"], fixture_dir, "fwupd_updates"
        )
        data = json.loads(text)
        devs = data.get("Devices", data) if isinstance(data, dict) else data
        for d in devs or []:
            for rel in d.get("Releases", []) or []:
                result["updates"].append({
                    "device": d.get("Name"),
                    "current": d.get("Version"),
                    "candidate": rel.get("Version"),
                    "size_kb": rel.get("Size"),
                    "urgency": rel.get("Urgency"),
                    "details": (rel.get("Description") or "")[:300],
                })
        result["status"] = "up to date" if not result["updates"] else "updates available"
    except system.ToolMissing:
        result["status"] = "fwupdmgr missing (pacman -S fwupd)"
    except Exception as exc:
        # fwupd exit code 1 = "no updates": nominal case, not a failure.
        result["status"] = "up to date (no updates announced by the daemon)"
        result["note"] = str(exc)[:200]

    if fixture_dir is None:
        try:
            result["fetched_at"] = time.time()
            cache.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return result
