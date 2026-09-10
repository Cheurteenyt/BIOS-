"""omarchy-firmware MCP server — a typed wrapper around the CLI. T0.

"No framework, no root daemon: a user process and listed scripts, in the
spirit of the repo" (vol. 2, ch. 9). The server speaks stdio (MCP JSON-RPC),
consumable by the thirteen Omarchy harnesses (claude, codex, opencode…)
via the standard MCP configuration.

Contractual (project rule, vol. 2 ch. 9 + vol. 3 ch. 5):
  - every tool declares its tier — here, the five T0 (audit + diagnostics);
  - any out-of-scope tool is structurally refused, not judged;
  - every call is journaled like its CLI equivalent;
  - no T3 (flash) call path exists, not even an elegant refusal.

Optional dependency: `pip install mcp` (or `pacman -S python-mcp`).
Without it, the CLI remains fully functional.
"""

from __future__ import annotations

import json

from . import audit, boot, cve_kb, diagnostics, fwupd, journal, tiers

_SERVER_NAME = "omarchy-firmware"


def _tool_specs() -> list[dict]:
    """Specifications of the five T0 tools — the visible face of the contract."""
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
    ]


def _run_tool(name: str) -> dict:
    import os
    tier = tiers.assert_phase1(name)  # refuses unknown T1/T2 with the exact reason
    fx = os.environ.get("FW_FIXTURE_DIR") or None  # tests/acceptance without hardware
    scenario = os.environ.get("FW_DIAG_SCENARIO") or None  # thermal scenario without hardware
    if name == "fw.diag.thermal":
        data = diagnostics.quick(scenario=scenario, fixture_dir=fx, record=False)
        data["journal_entry"] = journal.record(
            name, tier, [name], "ok", str(data.get("verdict"))[:160],
            fixture=(fx is not None or scenario is not None))
        return data
    fn = {
        "fw.audit.status": lambda: audit.collect(fx),
        "fw.audit.cve": lambda: cve_kb.collect(fx),
        "fw.boot.inspect": lambda: boot.collect(fx),
        "fw.update.check": lambda: fwupd.check_updates(fx, refresh=False),
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
    import sys
    sys.exit(serve())
