"""omarchy-firmware MCP server — a typed wrapper around the CLI. T0 + T1.

"No framework, no root daemon: a user process and listed scripts, in the
spirit of the repo" (vol. 2, ch. 9). The server speaks stdio (MCP JSON-RPC),
consumable by the thirteen Omarchy harnesses (claude, codex, opencode…)
via the standard MCP configuration.

Contractual (project rule, vol. 2 ch. 9 + vol. 3 ch. 5 + vol. 4 ch. 4):
  - every tool declares its tier — nine T0 (audit + diagnostics) and two T1
    (reversible writes under the two-key rule);
  - any out-of-scope tool is structurally refused, not judged;
  - T1 dry-run is the DEFAULT: without `confirm: true` the agent only gets
    the plan — the write never happens;
  - every call is journaled like its CLI equivalent;
  - no T3 (flash) call path exists, not even an elegant refusal.

Optional dependency: `pip install mcp` (or `pacman -S python-mcp`).
Without it, the CLI remains fully functional.
"""

from __future__ import annotations

import json
import sys

from . import actions, audit, boot, cve_kb, diagnostics, fwupd, gpu, journal, ram, settings as settings_mod, storage, tiers

_SERVER_NAME = "omarchy-firmware"


def _tool_specs() -> list[dict]:
    """Specifications of the eleven tools — the visible face of the contract."""
    return [
        {
            "name": "fw.audit.status",
            "risk_tier": "T0",
            "description": (
                "Full firmware inventory: motherboard, BIOS, socket, boot chain, "
                "fwupd devices, HSI posture, sensors. The first call to make "
                "('where does my firmware stand?'). Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.audit.cve",
            "risk_tier": "T0",
            "description": (
                "BIOS version / known AM4 CVE cross-check (fTPM stutter, LogoFAIL, "
                "Sinkclose, VU#382314, CVE-2026-6726/6727). Statuses owned as date "
                "inferences. Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.boot.inspect",
            "risk_tier": "T0",
            "description": (
                "Boot chain: efibootmgr entries, BootOrder vs BootCurrent, file "
                "existence on the ESP, Limine + UKI detection, Snapper snapshots. "
                "Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.update.check",
            "risk_tier": "T0",
            "description": (
                "Local firmware update state via fwupd (15-min cache, no network "
                "without human request). On a desktop AM4 board, the motherboard's "
                "absence from the LVFS is the expected result and is reported as such."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.diag.thermal",
            "risk_tier": "T0",
            "description": (
                "Physical diagnostics by sensor correlation (vol. 3): tells apart "
                "dead pump, degraded paste/mounting (R_th), stopped radiator fan, "
                "hot VRM, low 12 V rail, gradual degradation. Passive by default; "
                "active mode via CLI (diag probe). Every finding carries evidence, "
                "hypothesis, next steps and confidence. Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.diag.storage",
            "risk_tier": "T0",
            "description": (
                "Storage health (vol. 4): NVMe SMART (media errors, spare, wear, "
                "unsafe shutdowns), SATA SMART (reallocated/pending sectors, CRC "
                "errors), PCIe link state of NVMe controllers. Names the fault "
                "and separates defective from mis-adjusted. Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.diag.gpu",
            "risk_tier": "T0",
            "description": (
                "GPU health (vol. 4): Xid error history from the kernel log, "
                "thermal slowdown from clocks event reasons, BAR1 size (Resizable "
                "BAR evidence), PCIe link width. Correlates nvidia-smi, dmesg and "
                "lspci. Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.diag.ram",
            "risk_tier": "T0",
            "description": (
                "Memory audit (vol. 4): rated vs configured speed per DIMM (names "
                "the classic 'XMP/EXPO/DOCP never enabled' case), mixed modules, "
                "EDAC corrected/uncorrected error counters. Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "fw.diag.settings",
            "risk_tier": "T0",
            "description": (
                "Observable BIOS settings audit (vol. 4): Secure Boot, CPU "
                "virtualization flag, IOMMU, EPP current value, fan control mode, "
                "TPM. Settings not visible from the OS are listed under "
                "needs_bios_check, never guessed. Read-only, journaled."
            ),
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "cpu.epp.set",
            "risk_tier": "T1",
            "description": (
                "T1 reversible write: set the Energy Performance Preference of "
                "every CPU (e.g. 'balance_performance'). DRY-RUN BY DEFAULT: "
                "without confirm=true the tool returns the plan only. With "
                "confirm=true the write is applied and the previous values are "
                "stored for undo=true. Every call is journaled."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "value": {"type": "string",
                              "description": "EPP value, e.g. balance_performance"},
                    "confirm": {"type": "boolean", "default": False,
                                "description": "false = dry-run plan only (default)"},
                    "undo": {"type": "boolean", "default": False,
                             "description": "restore the last backed-up values"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "fans.curve.set",
            "risk_tier": "T1",
            "description": (
                "T1 reversible write: write a hardware fan curve on an nct67xx "
                "Super I/O. DRY-RUN BY DEFAULT. Mechanical guard: the last point "
                "MUST be pwm=255 at <=90 °C — no curve may cap cooling at the top. "
                "With confirm=true the curve is applied after a backup; undo=true "
                "restores it. Every call is journaled."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "curve": {
                        "type": "object",
                        "description": ('{"hwmon": "nct6798", "pwm": 1, "points": '
                                        '[{"temp": 40, "pwm": 90}, {"temp": 85, '
                                        '"pwm": 255}]}'),
                    },
                    "confirm": {"type": "boolean", "default": False,
                                "description": "false = dry-run plan only (default)"},
                    "undo": {"type": "boolean", "default": False,
                             "description": "restore the last backed-up curve"},
                },
                "additionalProperties": False,
            },
        },
    ]


def _run_tool(name: str, params: dict | None = None) -> dict:
    import os
    params = params or {}
    tier = tiers.assert_phase1(name)  # refuses out-of-scope with the exact reason
    fx = os.environ.get("FW_FIXTURE_DIR") or None  # tests/acceptance without hardware
    scenario = os.environ.get("FW_DIAG_SCENARIO") or None  # thermal scenario without hardware

    if name == "fw.diag.thermal":
        data = diagnostics.quick(scenario=scenario, fixture_dir=fx, record=False)
        data["journal_entry"] = journal.record(
            name, tier, [name], "ok", str(data.get("verdict"))[:160],
            fixture=(fx is not None or scenario is not None))
        return data

    if name in ("cpu.epp.set", "fans.curve.set"):
        if name == "cpu.epp.set":
            data = actions.epp_set(
                value=params.get("value"),
                confirm=bool(params.get("confirm")),
                undo=bool(params.get("undo")))
        else:
            data = actions.fans_curve_set(
                curve=params.get("curve"),
                confirm=bool(params.get("confirm")),
                undo=bool(params.get("undo")))
        data["journal_entry"] = journal.record(
            name, tier, [name], data.get("status", "dry-run"),
            str(data.get("note") or data.get("status"))[:160],
            fixture=fx is not None)
        return data

    fn = {
        "fw.audit.status": lambda: audit.collect(fx),
        "fw.audit.cve": lambda: cve_kb.collect(fx),
        "fw.boot.inspect": lambda: boot.collect(fx),
        "fw.update.check": lambda: fwupd.check_updates(fx, refresh=False),
        "fw.diag.storage": lambda: storage.collect(fx),
        "fw.diag.gpu": lambda: gpu.collect(fx),
        "fw.diag.ram": lambda: ram.collect(fx),
        "fw.diag.settings": lambda: settings_mod.collect(fx),
    }[name]
    data = fn()
    data["journal_entry"] = journal.record(
        name, tier, [name], "ok",
        str(data.get("verdict") or data.get("status") or "inventory completed")[:160],
        fixture=fx is not None,
    )
    return data


def build_server():
    """Build the FastMCP server; ImportError propagates to the caller."""
    from mcp.server.fastmcp import FastMCP  # lazy import — optional dependency

    mcp = FastMCP(_SERVER_NAME)

    for spec in _tool_specs():
        name = spec["name"]
        if name == "cpu.epp.set":
            def _epp(value: str, confirm: bool = False, undo: bool = False) -> str:
                """Set the CPU EPP hint — dry-run by default."""
                return json.dumps(_run_tool("cpu.epp.set",
                                            {"value": value, "confirm": confirm,
                                             "undo": undo}),
                                  ensure_ascii=False, indent=2)
            _epp.__name__ = "cpu_epp_set"
            _epp.__doc__ = spec["description"]
            mcp.tool(name=name, description=spec["description"])(_epp)
            continue
        if name == "fans.curve.set":
            def _curve(curve: dict, confirm: bool = False, undo: bool = False) -> str:
                """Write a fan curve (nct67xx) — dry-run by default."""
                return json.dumps(_run_tool("fans.curve.set",
                                            {"curve": curve, "confirm": confirm,
                                             "undo": undo}),
                                  ensure_ascii=False, indent=2)
            _curve.__name__ = "fans_curve_set"
            _curve.__doc__ = spec["description"]
            mcp.tool(name=name, description=spec["description"])(_curve)
            continue

        def _make(n=name):
            def _tool() -> str:
                return json.dumps(_run_tool(n), ensure_ascii=False, indent=2)
            _tool.__name__ = n.replace(".", "_")
            _tool.__doc__ = spec["description"]
            return _tool

        mcp.tool(name=name, description=spec["description"])(_make())

    return mcp


def serve() -> int:
    try:
        mcp = build_server()
    except ImportError:
        print(
            "The MCP server requires the 'mcp' package.\n"
            "  pip install mcp      (or pacman -S python-mcp)\n"
            "The CLI remains usable without it: omarchy-firmware selftest",
            file=sys.stderr,
        )
        return 1
    mcp.run()  # stdio transport — one user process, nothing more
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(serve())
