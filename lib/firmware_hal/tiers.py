"""Risk tiers T0-T3 — the contract from volume 2, table 5.1.

The MCP server and the CLI structurally refuse any call outside the current
scope rather than trusting the model's good will. The table below is a
contract, not a catalogue of intentions: no tool enters the server without
its declared tier and its out-of-scope refusal test.
"""

from __future__ import annotations

# The full nine-tool contract (vol. 2 table 5.1 + vol. 3, ch. 5).
# T1/T2 tools remain DECLARED but NOT implemented: any invocation fails with
# an explicit error, never a silence.
TOOL_TIERS: dict[str, str] = {
    "fw.audit.status": "T0",
    "fw.audit.cve": "T0",
    "fw.boot.inspect": "T0",
    "fw.update.check": "T0",
    "fw.diag.thermal": "T0",
    "cpu.epp.set": "T1",
    "fans.curve.set": "T1",
    "fw.update.stage": "T2",
    "fw.rollback": "T2",
}

# What this codebase actually exposes.
TIER_MEANING = {
    "T0": "read-only, journaled — free access for the agent",
    "T1": "reversible write (dry-run default, profile saved, rollback) — Phase 3",
    "T2": "NVRAM/capsule write, explicit human confirmation — Phase 4",
    "T3": "physical flash, EZ Flash — forbidden to the agent; the human executes",
}

# Tools exposed by this codebase (P1 + P2: thermal diagnostics).
IMPLEMENTED_T0 = ["fw.audit.status", "fw.audit.cve", "fw.boot.inspect",
                  "fw.update.check", "fw.diag.thermal"]

# T3 tools: no call path exists, not even an elegant refusal.
# Flashing goes through the human alone (guided EZ Flash, see vol. 2 ch. 8).
FORBIDDEN_FOREVER = ["fw.flash.write", "fw.nvram.raw.write"]


class TierRefused(Exception):
    """Raised when a tool outside the current phase scope is requested."""


def tier_of(tool: str) -> str:
    if tool not in TOOL_TIERS:
        raise TierRefused(
            f"unknown tool '{tool}' — the contract is frozen (vol. 2, table 5.1): "
            + ", ".join(sorted(TOOL_TIERS))
        )
    return TOOL_TIERS[tool]


def assert_phase1(tool: str) -> str:
    """Refuse any tool not implemented in the current phase, with the exact reason."""
    t = tier_of(tool)
    if t != "T0" or tool not in IMPLEMENTED_T0:
        from . import PHASE  # late import: avoids any ordering dependency
        raise TierRefused(
            f"'{tool}' is declared tier {t} but not implemented in the current "
            f"phase ({PHASE}). Current scope: {', '.join(IMPLEMENTED_T0)}."
        )
    return t
