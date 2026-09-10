"""firmware_hal — the agent ↔ firmware base of the omarchy-firmware suite.

Phase 1 (vol. 2): the four T0 audit tools.
Phase 2 (vol. 3, "What the BIOS cannot see"): physical diagnostics by
sensor correlation, still T0.
Phase 3 (vol. 4, "Mis-adjusted or defective?"): the whole machine in T0
reads (storage, GPU, RAM, BIOS settings) + the first two T1 reversible
writes (EPP, fan curves) under the two-key rule — dry-run by default,
explicit confirm, backup + rollback.
Phase 4 (roadmap P4, the supervised loop): fw.cve.watch — knowledge-base
freshness, drift and fwupd advisory cross-check, still T0 — plus the
human-gated T2 layer on the CLI alone: fw.update.stage (dry-run plan by
default, --confirm is a human gesture, never the agent's) and
fw.rollback, a refusal-by-design with an honest inventory.
Phase 5 (the digital twin): TWIN-1, the rehearsal machine — the fixture
set promoted to an installable machine profile — and `rehearse`, the
dress rehearsal: 28 behavioural probes, one verdict, a diffable report.
Sept. 16 must be a replay day, not a discovery day.

    fw.audit.status      T0   full inventory (board, BIOS, boot, fwupd)
    fw.audit.cve         T0   version / known-CVE cross-check (vol. 1, ch. 5)
    fw.boot.inspect      T0   UKI/Limine chain, efibootmgr entries, snapshots
    fw.update.check      T0   local fwupd state, 15-min cache, no network
    fw.cve.watch         T0   KB freshness, drift, fwupd advisory correlation
    fw.diag.thermal      T0   thermal signatures: pump, paste, VRM, drift
    fw.diag.storage      T0   NVMe/SATA SMART, PCIe link — media vs settings
    fw.diag.gpu          T0   Xid history, thermal slowdown, BAR1, link width
    fw.diag.ram          T0   rated vs configured speed (XMP/EXPO), EDAC
    fw.diag.settings     T0   observable BIOS settings: SVM, IOMMU, EPP, fans
    cpu.epp.set          T1   EPP hint of every CPU (dry-run default, undo)
    fans.curve.set       T1   Smart Fan curve, nct67xx (dry-run default, undo)
    fw.update.stage      T2   human-only CLI: staged fwupd transaction
    fw.rollback          T2   refusal-by-design + rollback inventory

Structural rules (unchanged):
  - every T0 read is journaled (journal.jsonl, XDG state); every T1 call is
    journaled with its status: dry-run | applied | rolled-back | refused;
    T2 staging is journaled as dry-run | staged | cancelled | refused;
  - T1 writes require two keys: a value and an explicit confirm flag;
    the KB updater obeys the same rule (stage, then --confirm + --sha256);
    nothing writes "by accident", nothing writes without a stored backup;
  - the CLI is the functional reference; the MCP server is only a typed
    wrapper around it (one implementation, three consumers); T2 is NOT
    in the MCP surface: the agent prepares, the human applies;
  - collectors and diagnostics run without hardware via fixtures and
    scenarios (--fixture-dir / diag quick --scenario); T1 actions run
    against env-injectable sysfs roots (FW_SYSFS_CPU / FW_SYSFS_HWMON);
    staging runs against an injectable fwupdmgr (FW_FWUPD_BIN);
  - frugality: no resident intelligence. The doctor is a one-shot
    (optional systemd timer), the agent is called only on anomaly.
"""

__version__ = "0.6.2"

PHASE = "P5 — the digital twin (TWIN-1) and the dress rehearsal on top of "\
        "the P4 supervised loop"
