"""fw.update.stage — firmware update staging, the human-gated T2 (P4).

A staged update is an OS-mediated firmware transaction: fwupd downloads
and queues a capsule, and the firmware is flashed by fwupd itself during
the NEXT reboot. Staging is therefore reversible-until-reboot; flashing
is not reversible at all. The line between the two is exactly the T2
line, and this module enforces it mechanically:

  - the plan (dry-run) is the DEFAULT and the only thing the agent can
    produce: it resolves the device by exact GUID, checks every gate and
    prints the exact command — nothing is executed;
  - `--confirm` is a HUMAN gesture on the CLI. The MCP surface refuses
    fw.update.stage with a pointer here: the agent proposes, the human
    applies;
  - every gate is explicit and journaled; a staged update must carry its
    reason (--reason) — a firmware flash without a stated "why" is a
    bad-action by definition (vol. 4 barrage B);
  - this tool NEVER reboots, never passes --assume-yes style flags, and
    writes exactly one transaction record to XDG state.

On a desktop AM4 board the expected result is the honest refusal: the
motherboard is not LVFS-manageable (vol. 1, ch. 4 coverage gap), so
staging refuses and points to the human path (EZ Flash, T3). Devices
fwupd DOES manage (SSDs, SSD controllers, some GPUs) exercise the real
path — that is what the fixtures simulate.

Tests inject a fake fwupdmgr through FW_FWUPD_BIN; without it, fixture
mode refuses to execute anything (no real command may leak into a
fixture run).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from . import fwupd, journal

_TRANSACTION = "stage-transaction.json"


class StageRefused(Exception):
    """A gate failed — staging does not proceed, and says exactly why."""


def _bin() -> str:
    return os.environ.get("FW_FWUPD_BIN") or "fwupdmgr"


def _transaction_path() -> Path:
    return journal.state_dir() / _TRANSACTION


def _power_state() -> dict:
    """Best-effort AC read — a desktop AM4 usually has no battery entry."""
    root = Path("/sys/class/power_supply")
    try:
        supplies = list(root.glob("*"))
    except OSError:
        supplies = []
    if not supplies:
        return {"state": "unknown",
                "note": "no power_supply entries — desktop assumption"}
    for s in supplies:
        try:
            if (s / "online").read_text().strip() == "1":
                return {"state": "ac-present", "note": str(s.name)}
        except OSError:
            continue
    batteries = [s for s in supplies if "bat" in s.name.lower()]
    if batteries:
        return {"state": "on-battery",
                "note": "internal-device staging on battery is refused"}
    return {"state": "unknown", "note": ",".join(s.name for s in supplies)}


def plan(guid: str, fixture_dir=None, reason: str | None = None) -> dict:
    """Resolve + check, execute nothing. The dry-run IS the deliverable."""
    devices = fwupd._devices(fixture_dir)
    dev = next((d for d in devices
                if (d.get("guid") or "").lower() == guid.lower().strip()), None)

    gates: list[dict] = []

    def gate(name: str, result: str, detail: str) -> dict:
        g = {"name": name, "result": result, "detail": detail}
        gates.append(g)
        return g

    if dev is None:
        gate("device-found", "fail",
             f"no fwupd device with GUID {guid} — exact GUID required, "
             "never a fuzzy match (list them with fw.update.check / "
             "`fwupdmgr get-devices --json`)")
        return _plan_refused(guid, gates, fixture_dir)

    gate("device-found", "pass", f"{dev.get('name')} ({dev.get('version')})")

    if not dev.get("updatable"):
        name = (dev.get("name") or "").lower()
        if "system firmware" in name or "board" in name:
            gate("device-updatable", "fail",
                 "this motherboard is NOT LVFS-manageable (vol. 1, ch. 4 "
                 "coverage gap on desktop AM4): there is nothing fwupd can "
                 "stage. The update path is the vendor BIOS file flashed by "
                 "EZ Flash — a T3 operation the human executes, with the "
                 "agent producing the walkthrough.")
        else:
            gate("device-updatable", "fail",
                 "fwupd lists this device but not as updatable")
        return _plan_refused(guid, gates, fixture_dir, device=dev)
    gate("device-updatable", "pass", "device declared updatable by fwupd")

    upd = fwupd.check_updates(fixture_dir, refresh=False)
    cand = next((u for u in upd.get("updates", [])
                 if u.get("device") == dev.get("name")), None)
    if cand is None:
        gate("candidate-found", "fail",
             "no update announced for this device (fwupd get-updates)")
        return _plan_refused(guid, gates, fixture_dir, device=dev)
    gate("candidate-found", "pass",
         f"{cand.get('current')} -> {cand.get('candidate')}"
         + (f" [{cand.get('urgency')}]" if cand.get("urgency") else ""))

    if str(cand.get("candidate")) == str(cand.get("current")):
        gate("version-differs", "fail",
             "candidate equals current version — nothing to stage")
        return _plan_refused(guid, gates, fixture_dir, device=dev)
    gate("version-differs", "pass", "candidate differs from current")

    power = _power_state()
    gate("power", "pass" if power["state"] != "on-battery" else "fail",
         power["state"] + " — " + power["note"])

    gate("motivation", "pass" if (reason or "").strip() else "pending",
         "staging reason (--reason)" if (reason or "").strip()
         else "REQUIRED at confirm: a firmware flash without a stated why "
              "is refused (bad-action barrage, vol. 4)")

    hard_fail = any(g["result"] == "fail" for g in gates)
    transaction = _read_transaction()

    plan_out = {
        "tool": "fw.update.stage",
        "tier": "T2",
        "status": "refused" if hard_fail else "dry-run",
        "device": dev,
        "candidate": cand,
        "gates": gates,
        "command": [_bin(), "install", guid.strip()],
        "rollback_reality": (
            "staging is reversible until the reboot that flashes it; after "
            "the flash, single-BIOS AM4 has NO runtime rollback — recovery "
            "is USB BIOS FlashBack, a human operation. `omarchy-firmware "
            "update rollback` prints the honest inventory."),
        "pending_transaction": transaction.get("status") if transaction else None,
        "note": ("gates failed — nothing staged"
                 if hard_fail else
                 "plan only, nothing executed. Staging is HUMAN-only: run "
                 "this command yourself with --confirm --reason '...'"),
    }
    return plan_out


def _plan_refused(guid, gates, fixture_dir, device=None) -> dict:
    return {
        "tool": "fw.update.stage",
        "tier": "T2",
        "status": "refused",
        "device": device or {"guid": guid},
        "gates": gates,
        "note": "gates failed — nothing staged, nothing executed",
    }


def _read_transaction() -> dict | None:
    try:
        data = json.loads(_transaction_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def apply(guid: str, reason: str | None, fixture_dir=None) -> dict:
    """The human-confirmed path. ALL gates must pass; motivation mandatory."""
    p = plan(guid, fixture_dir, reason=reason)
    hard_fail = [g for g in p["gates"] if g["result"] == "fail"]
    if hard_fail:
        p["note"] = "refused at apply: " + "; ".join(
            f"{g['name']}: {g['detail']}" for g in hard_fail)
        return p
    pending = [g for g in p["gates"] if g["result"] == "pending"]
    if pending:  # motivation missing — the one gate apply cannot waive
        p["status"] = "refused"
        p["note"] = ("refused at apply: " + pending[0]["detail"])
        return p
    if fixture_dir is not None and not os.environ.get("FW_FWUPD_BIN"):
        raise StageRefused(
            "fixture mode forbids a real fwupdmgr execution — set "
            "FW_FWUPD_BIN to a fake binary for tests")

    cmd = p["command"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        ok = proc.returncode == 0
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()[:600]
    except FileNotFoundError:
        ok, output = False, f"{cmd[0]} not found on this machine"
    except subprocess.TimeoutExpired:
        ok, output = False, f"{cmd[0]} did not answer within 600 s"

    if ok:
        transaction = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "status": "staged",
            "guid": guid.strip(),
            "device": p["device"].get("name"),
            "from": p["candidate"].get("current"),
            "to": p["candidate"].get("candidate"),
            "reason": (reason or "").strip(),
            "command": cmd,
            "fwupd_output": output,
            "note": "applies at next reboot by fwupd itself; this tool "
                    "NEVER reboots. Cancel: omarchy-firmware update "
                    "stage --cancel (before rebooting).",
        }
        try:
            _transaction_path().write_text(
                json.dumps(transaction, ensure_ascii=False, indent=1),
                encoding="utf-8")
        except OSError as exc:
            return {"tool": "fw.update.stage", "tier": "T2",
                    "status": "error",
                    "note": f"fwupd succeeded but the transaction record "
                            f"could not be written: {exc}"}
        p.update({
            "status": "staged",
            "transaction": transaction,
            "note": "STAGED — the firmware will be flashed at the next "
                    "reboot by fwupd. Reboot only when YOU decide to.",
        })
    else:
        p.update({"status": "error", "fwupd_output": output,
                  "note": "fwupd failed — nothing staged, nothing flashed"})
    return p


def cancel() -> dict:
    """Mark a pending transaction cancelled. Journaled by the CLI boundary
    (the same convention as every other module — the boundary records,
    the module stays pure)."""
    t = _read_transaction()
    if not t or t.get("status") != "staged":
        return {
            "tool": "fw.update.stage", "tier": "T2", "status": "refused",
            "note": ("no pending staging transaction recorded here. fwupd "
                     "may still hold its own state: check "
                     "`fwupdmgr get-updates` and whether /system-update "
                     "exists before rebooting."),
        }
    t["status"] = "cancelled"
    t["cancelled_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    try:
        _transaction_path().write_text(
            json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    system_update = Path("/system-update")
    return {
        "tool": "fw.update.stage", "tier": "T2", "status": "cancelled",
        "transaction": t,
        "system_update_symlink_exists": os.path.lexists(system_update),
        "note": ("transaction marked cancelled. If /system-update exists, "
                 "fwupd queued an offline update: verify what it points to "
                 "BEFORE any reboot; on some fwupd versions "
                 "`fwupdmgr clear-offline-updates` exists — confirm with "
                 "`fwupdmgr --help`. Nothing was rebooted."),
    }


def history(fixture_dir=None) -> dict:
    """fwupd's own update history — the record of what was already flashed."""
    try:
        from . import system
        text = system.run(["fwupdmgr", "get-history", "--json"],
                          fixture_dir, "fwupd_history")
        data = json.loads(text)
        devs = data.get("Devices", data) if isinstance(data, dict) else data
        events = []
        for d in devs or []:
            events.append({
                "device": d.get("Name"),
                "from": d.get("VersionOld") or d.get("VersionLowest"),
                "to": d.get("VersionNew") or d.get("Version"),
                "state": d.get("UpdateState"),
                "when": d.get("ModifiedDate") or d.get("Created"),
            })
        return {"available": True, "events": events,
                "source": "fwupdmgr get-history --json"}
    except Exception:  # noqa: BLE001 — stated, never hidden
        return {"available": False,
                "note": "fwupd history unavailable on this machine"}
