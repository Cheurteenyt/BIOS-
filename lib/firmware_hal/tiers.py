"""Risk tiers T0-T3 — the contract from volume 2, table 5.1.

The MCP server and the CLI structurally refuse any call outside the current
scope rather than trusting the model's good will. The table below is a
contract, not a catalogue of intentions: no tool enters the server without
its declared tier and its out-of-scope refusal test.
"""

from __future__ import annotations

# The full fourteen-tool contract (vol. 2 table 5.1 + vol. 3 ch. 5 +
# vol. 4 + roadmap P4). T2 tools are human-only: fw.update.stage is
# implemented on the CLI alone (dry-run plan + explicit --confirm by the
# human), fw.rollback is a refusal-by-design with an inventory. Neither
# is reachable from the MCP surface. T1 tools are implemented with the
# two-key rule (dry-run by default, explicit confirm to apply).
TOOL_TIERS: dict[str, str] = {
    "fw.audit.status": "T0",
    "fw.audit.cve": "T0",
    "fw.boot.inspect": "T0",
    "fw.update.check": "T0",
    "fw.cve.watch": "T0",
    "fw.diag.thermal": "T0",
    "fw.diag.storage": "T0",
    "fw.diag.gpu": "T0",
    "fw.diag.ram": "T0",
    "fw.diag.settings": "T0",
    "cpu.epp.set": "T1",
    "fans.curve.set": "T1",
    "fw.update.stage": "T2",
    "fw.rollback": "T2",
}

# What this codebase actually exposes.
TIER_MEANING = {
    "T0": "read-only, journaled — free access for the agent",
    "T1": "reversible write: dry-run by default, explicit confirm to apply, "
          "backup + rollback store (implemented for cpu.epp.set, fans.curve.set)",
    "T2": "NVRAM/capsule transaction, HUMAN-only: fw.update.stage exists on "
          "the CLI (dry-run default, --confirm by the human), fw.rollback is "
          "a refusal-by-design with an inventory — neither is agent-callable",
    "T3": "physical flash, EZ Flash — forbidden to the agent; the human executes",
}

# Tools exposed by this codebase (P1 audits, P2 thermal, P3 machine-wide
# T0 + T1 writes, P4 watch + staging).
IMPLEMENTED_T0 = ["fw.audit.status", "fw.audit.cve", "fw.boot.inspect",
                  "fw.update.check", "fw.cve.watch", "fw.diag.thermal",
                  "fw.diag.storage", "fw.diag.gpu", "fw.diag.ram",
                  "fw.diag.settings"]
IMPLEMENTED_T1 = ["cpu.epp.set", "fans.curve.set"]

# T2: where the human finds them (never in the MCP surface).
T2_HINTS = {
    "fw.update.stage":
        "T2 staging is human-only by contract: the agent may PREPARE the "
        "plan (dry-run) with `omarchy-firmware update stage --device GUID`, "
        "the human alone applies --confirm on the CLI.",
    "fw.rollback":
        "firmware rollback does not exist as a runtime operation on "
        "single-BIOS AM4; `omarchy-firmware update rollback` prints the "
        "honest inventory instead of pretending.",
}

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
    """Refuse any tool not implemented in the current phase, with the exact reason.

    Historical name kept: the first scope was Phase 1's T0 base; the check
    now covers implemented T0 *and* implemented T1 (two-key rule handled by
    the caller).
    """
    t = tier_of(tool)
    implemented = (t == "T0" and tool in IMPLEMENTED_T0) or \
                  (t == "T1" and tool in IMPLEMENTED_T1)
    if not implemented:
        from . import PHASE  # late import: avoids any ordering dependency
        msg = (
            f"'{tool}' is declared tier {t} but not implemented in the current "
            f"phase ({PHASE}). Implemented: "
            f"T0={', '.join(IMPLEMENTED_T0)}; T1={', '.join(IMPLEMENTED_T1)}."
        )
        if t == "T2" and tool in T2_HINTS:
            msg += " " + T2_HINTS[tool]
        raise TierRefused(msg)
    return t
