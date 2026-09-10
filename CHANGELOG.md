# Changelog

All notable changes to `omarchy-firmware`. The tool contract (tiers,
tool names, refusal behaviour) is frozen between phases: changes are
additive, and every tool keeps its refusal test.

## 0.4.0 — Phase 4: the supervised loop (CVE watch + human-gated T2 staging)

**Added**
- `fw.cve.watch` (T0, MCP tool #12): knowledge-base freshness (generated
  date, age, entry count, sha256, packaged vs override), exposure replay,
  drift since the previous watch (added/changed/removed entry ids), and a
  fwupd advisory cross-check — CVE ids in release notes correlated against
  the KB; unknown ones are listed as candidates for the next KB revision.
  Never touches the network.
- KB updater (`omarchy-firmware-cve-update`, `lib/firmware_hal/kb_update.py`):
  the two-key rule applied to DATA — stage (`--file`/`--from`) validates
  the schema and shows the sha256, `--confirm --sha256 HEX` activates the
  local override (mismatch = supply-chain refusal), `--revert` restores,
  `--status` shows what is in force. Journaled as `kb.update`.
- T2 staging (`omarchy-firmware update stage`, `lib/firmware_hal/stage.py`):
  HUMAN-only CLI (not in the MCP surface). Dry-run plan by default with six
  explicit gates (exact GUID, updatable, candidate, version differs, power,
  mandatory `--reason`); `--confirm` executes the exact command through an
  injectable fwupdmgr (`FW_FWUPD_BIN`), writes a transaction record, never
  reboots; `--cancel` revokes until reboot and reports `/system-update`.
  A motherboard outside LVFS is refused with the AM4 gap and the EZ Flash
  human path named.
- `fw.rollback` (`omarchy-firmware update rollback`,
  `lib/firmware_hal/rollback.py`): refusal-by-design with the honest
  inventory — T1 rollback frames, pending transaction, fwupd history,
  FlashBack machine truth. Journaled `refused-by-design`, exit 0.
- Loop report (`omarchy-firmware report --days N`): the supervised-loop
  digest — per-day calls/tools/statuses, errors, KB age, rollback frames,
  pending transaction. View-only, does not journal itself.
- Weekly watch units (`omarchy-firmware-watch.{service,timer}`, installed
  INACTIVE): the CVE watch on a weekly schedule, same one-shot frugality.
- `docs/first-run.md`: the day-0 drill + the 5-day supervised-loop
  protocol that measures the P4 exit criterion on the real machine.
- Fixture `fwupd-history.json` + a candidate advisory (CVE-2026-4478) in
  `fwupd-updates.json`; CVE knowledge-base texts translated to English.

**Changed**
- Contract grown to fourteen tools (10 T0 + 2 T1 + 2 T2 declared); the
  T2 refusals now carry their human-path pointers (`T2_HINTS`).
- Test suite 177 → 233 checks; MCP smoke proves 12 tools and a real
  `fw.cve.watch` call.

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
