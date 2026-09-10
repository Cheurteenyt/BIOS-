"""firmware_hal — the agent ↔ firmware base of the omarchy-firmware suite.

Phase 1 (vol. 2): the four T0 audit tools.
Phase 2 (vol. 3, "What the BIOS cannot see"): physical diagnostics by
sensor correlation, still T0.

    fw.audit.status    T0   full inventory (board, BIOS, boot, fwupd)
    fw.audit.cve       T0   version / known-CVE cross-check (vol. 1, ch. 5)
    fw.boot.inspect    T0   UKI/Limine chain, efibootmgr entries, snapshots
    fw.update.check    T0   local fwupd state, 15-min cache, no network
    fw.diag.thermal    T0   thermal signatures: pump, paste, VRM, drift

Structural rules (unchanged):
  - read-only: no write code path exists in this package;
  - every call is journaled (journal.jsonl, XDG state);
  - the CLI is the functional reference; the MCP server is only a typed
    wrapper around it (one implementation, three consumers);
  - collectors and diagnostics run without hardware via fixtures and
    scenarios (--fixture-dir / diag quick --scenario);
  - frugality: no resident intelligence. The doctor is a one-shot
    (optional systemd timer), the agent is called only on anomaly.
"""

__version__ = "0.2.0"

PHASE = "P2 — read-only + thermal diagnostics"
