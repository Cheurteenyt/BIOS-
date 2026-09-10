"""firmware_hal — the agent ↔ firmware base of the omarchy-firmware suite.

Phase 1 (vol. 2): the four T0 audit tools.
Phase 2 (vol. 3, "What the BIOS cannot see"): physical diagnostics by
sensor correlation, still T0.
Phase 3 (vol. 4, "Mis-adjusted or defective?"): the whole machine in T0
reads (storage, GPU, RAM, BIOS settings) + the first two T1 reversible
writes (EPP, fan curves) under the two-key rule — dry-run by default,
explicit confirm, backup + rollback.

    fw.audit.status      T0   full inventory (board, BIOS, boot, fwupd)
    fw.audit.cve         T0   version / known-CVE cross-check (vol. 1, ch. 5)
    fw.boot.inspect      T0   UKI/Limine chain, efibootmgr entries, snapshots
    fw.update.check      T0   local fwupd state, 15-min cache, no network
    fw.diag.thermal      T0   thermal signatures: pump, paste, VRM, drift
    fw.diag.storage      T0   NVMe/SATA SMART, PCIe link — media vs settings
    fw.diag.gpu          T0   Xid history, thermal slowdown, BAR1, link width
    fw.diag.ram          T0   rated vs configured speed (XMP/EXPO), EDAC
    fw.diag.settings     T0   observable BIOS settings: SVM, IOMMU, EPP, fans
    cpu.epp.set          T1   EPP hint of every CPU (dry-run default, undo)
    fans.curve.set       T1   Smart Fan curve, nct67xx (dry-run default, undo)

Structural rules (unchanged):
  - every T0 read is journaled (journal.jsonl, XDG state); every T1 call is
    journaled with its status: dry-run | applied | rolled-back | refused;
  - T1 writes require two keys: a value and an explicit confirm flag;
    nothing writes "by accident", nothing writes without a stored backup;
  - the CLI is the functional reference; the MCP server is only a typed
    wrapper around it (one implementation, three consumers);
  - collectors and diagnostics run without hardware via fixtures and
    scenarios (--fixture-dir / diag quick --scenario); T1 actions run
    against env-injectable sysfs roots (FW_SYSFS_CPU / FW_SYSFS_HWMON);
  - frugality: no resident intelligence. The doctor is a one-shot
    (optional systemd timer), the agent is called only on anomaly.
"""

__version__ = "0.3.0"

PHASE = "P3 — full T0 diagnostics + T1 reversible writes (dry-run default)"
