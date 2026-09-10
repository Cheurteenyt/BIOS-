# Changelog

All notable changes to `omarchy-firmware`. The tool contract (tiers,
tool names, refusal behaviour) is frozen between phases: changes are
additive, and every tool keeps its refusal test.

## 0.3.0 — Phase 3: full T0 diagnostics + T1 reversible writes

**Added**
- `fw.diag.storage` (T0): NVMe SMART health (media errors, spare, wear,
  unsafe shutdowns), SATA SMART (reallocated, pending, offline
  uncorrectable, UDMA CRC), PCIe link state of NVMe controllers
  (LnkCap/LnkSta downgrade detection).
- `fw.diag.gpu` (T0): Xid error history from the kernel log (critical
  class: 79/94/95), thermal slowdown from clocks event reasons, BAR1 size
  as Resizable BAR evidence, VGA link width downgrade.
- `fw.diag.ram` (T0): rated vs configured speed per DIMM (names the
  XMP/EXPO/DOCP-never-enabled case), mixed modules, EDAC
  corrected/uncorrected error counters, honest ECC-absence reporting.
- `fw.diag.settings` (T0): observable BIOS settings audit — Secure Boot
  (efivarfs), CPU virtualization flag + /dev/kvm, IOMMU (cmdline +
  groups), EPP current/available, cpufreq governor, fan control mode
  (pwm_enable), TPM presence; settings invisible from the OS are listed
  under `needs_bios_check`, never guessed.
- T1 write layer (`lib/firmware_hal/actions.py`): `cpu.epp.set` and
  `fans.curve.set` under the two-key rule — dry-run by default, explicit
  confirm, backup store + undo, mechanical curve guards (last point
  pwm=255 at ≤ 90 °C; points > slots refused; nct67xx family only).
- MCP server grown to 11 tools (9 T0 + 2 T1 with typed parameters);
  `tests/mcp_smoke.py` proves the handshake, the tool list and the T1
  dry-run over a real stdio session.
- CLI: `diag storage|gpu|ram|settings`, `cpu epp set|undo`,
  `fans curve set|undo|show`; `_guard_t1` journals dry-run / applied /
  rolled-back / refused statuses.
- Bins: `omarchy-firmware-diag-{storage,gpu,ram,settings}` with
  `# omarchy:*` metadata.
- Fixtures: `b450-plus` extended to a full "issues" set (SMART SATA,
  lspci with degraded NVMe link, nvidia-smi, dmesg with Xid, dmidecode
  memory, settings); new `b450-plus-clean` set — the symmetric
  "healthy → zero findings" proof.
- CI (`.github/workflows/ci.yml`): contract suite on Python 3.11/3.13 +
  MCP conformance smoke on every push.

**Contract** — 13 declared tools: 9 T0 + 2 T1 implemented, 2 T2 declared
and refused, T3 has no call path. Test suite 82 → 177 checks.

## 0.2.0 — Phase 2: physical thermal diagnostics

- `fw.diag.thermal` (T0): 12 signatures (pump-dead, interface-degraded
  via R_th, fan-zero-rpm, coolant-hot, instant-rise, runaway,
  thermal-protection-active with power fold-back, vrm-hot, v12-low,
  refroidissement-insuffisant, capteur-chaud, gradual-degradation via
  baseline), bounded active probe, XDG baseline, 8 deterministic 5950X
  scenarios, `omarchy-firmware-doctor` bin, optional systemd user
  service + timer (never enabled by install).

## 0.1.0 — Phase 1: the T0 audit base

- `fw.audit.status`, `fw.audit.cve`, `fw.boot.inspect`, `fw.update.check`
  (T0), access journal, tier contract with structural refusals, MCP
  server (5 tools), fixtures for two ASUS boards, AM4 CVE knowledge base
  (fTPM stutter, LogoFAIL, Sinkclose, VU#382314, CVE-2026-6726/6727).
