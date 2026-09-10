# Changelog

All notable changes to `omarchy-firmware`. The tool contract (tiers,
tool names, refusal behaviour) is frozen between phases: changes are
additive, and every tool keeps its refusal test.

## 0.6.1 — the distribution: pinned, canaried, bit-verified

The day-0 payload now ships the way the thesis says tools should ship:
reproducible, and shown.

**Added**
- `install.sh --from <release | tag | main>`: the installer floats, the
  payload is pinned — the tagged tarball is fetched and verified against
  its published `SHA256SUMS` BEFORE anything runs; the provenance (tag +
  digest) is echoed for the day-0 log. `--from release` resolves the
  latest tag via the API, with a redirect-based fallback when the API is
  throttled; every failure is loud (bad tag, missing asset, checksum
  mismatch → refused, exit 1; unknown args → exit 2).
- GitHub release `v0.6.0`: `omarchy-firmware-0.6.0.tar.gz` (git archive
  of the annotated tag) + `SHA256SUMS` — the canonical day-0 payload,
  roundtrip-verified (public download → checksum → install → rehearsal
  green from the installed tree).

**Changed**
- CI: the MCP SDK is pinned exactly (`mcp==1.30.0`, proven against the
  smoke and the full suite's handshake path before the pin was written)
  and the runners are pinned (`ubuntu-24.04` ×3 — no floating label).
  A new weekly scheduled job, the **mcp drift canary**, installs the
  floating `mcp>=1.0,<2` range exactly as a user would and runs the same
  smoke: if the range drifts, the canary turns red before any machine
  does. `workflow_dispatch` runs it on demand.
- install.sh: the post-install smoke no longer pipes `tiers` through
  `head` — a closed pipe turned the python flush into a racy
  BrokenPipeError under `set -o pipefail`, killing finished installs
  (previous sessions won that race by scheduler luck).

**Fixed**
- `--from` failure paths: `set -e` used to kill the installer inside
  command substitutions before the guards could speak; every fetch and
  verify step now fails loudly with an actionable message, and the
  release-resolution notice goes to stderr (its stdout is captured).

- tests 277 → 281 (the pinning discipline is structural: exact SDK pin
  inside 1.x, canary present and guarded, runners pinned, install.sh
  bit-verifies before staging).

## 0.6.0 — the day-0 instruments: `rehearse-diff` + `capture`

Sept. 16 must be a replay day — so the debrief is a tool, not a
manual `jq` session. Two CLI instruments land (the 12-tool MCP
surface is untouched):

**Added**
- `rehearse-diff LEFT.json RIGHT.json` (and `--latest`, which picks the
  freshest twin + real reports from the state dir — zero paths on
  day 0): compares two rehearsal reports by stable probe id and names
  every surprise, honestly classified — `identical`, `content-shift`
  (same status, different facts — the EXPECTED day-0 harvest: real
  sensor names, real numbers), `improvement`, `regression` (pass →
  fail or probe lost — investigate), `not-comparable` (twin-only
  probes the real backend skips by design). Verdict `clean`/`review`
  grades the DAY, not the machine; content-shifts never fail a diff —
  they are the point of day 0. Exit 0/1; non-reports are REFUSED
  (exit 2), journaled even then. Schema `omarchy-firmware/rehearsal-diff@1`.
- `capture [--out PATH]`: the day-0 photograph — one read-only T0
  snapshot of what the machine really is: the ten T0 collections plus
  per-cpu EPP facts, per-chip hwmon structure (pwm values, enables,
  auto-point temps) and the environment block. Every section carries
  its provenance (`twin-sourced` vs `live`, roots named); a sensorless
  host records nulls and section errors, never guesses. No confirm
  flag exists; the only artifact is the snapshot file. The cpu/hwmon
  sections mirror the twin-sysfs shapes, so turning a surprise into a
  TWIN-1.1 fixture is a copy-edit, not a rewrite. Schema
  `omarchy-firmware/capture@1`.
- `bin/omarchy-firmware-rehearse-diff`, `bin/omarchy-firmware-capture`
  (staged by install.sh's existing bin glob).
- tests 262 → 277 (diff classes + refusals + --latest resolution;
  capture sections, provenance, twin mirroring, read-only meta-scan).

## 0.5.1 — the mcp-surface probe honours the clean SDK refusal

**Fixed**
- CI: the `test-suite` job is stdlib-only by design, so the MCP server
  performs its documented clean refusal (`mcp` package absent — exit 1,
  the message names the `mcp>=1.0,<2` pin). The rehearsal's `mcp-surface`
  probe counted that legitimate behaviour as a failure and turned the
  whole rehearsal red on both Python legs (259/262). The probe now
  accepts exactly two outcomes, both contract behaviour: the full
  handshake (exact 12-tool surface + one T0 call) where the SDK is
  installed, or the clean SDK-refusal where it is not — a hung or
  crashed server is still a failure. The deep handshake remains proven
  by the dedicated `mcp conformance` job and by day-0 on a machine with
  `python-mcp` installed.

## 0.5.0 — Phase 5: the digital twin (TWIN-1) and the dress rehearsal

Sept. 16 must be a replay day, not a discovery day. The fixture set is
promoted to a first-class machine profile and one command walks the
entire behavioural contract against it.

**Added**
- `lib/firmware_hal/twin.py` — TWIN-1: the profile of the reference
  machine (B450-PLUS / 5950X / RTX 3070 / 980 PRO / AIO 240) plus asset
  resolution (`FW_TWIN_DIR` → installed twin → repository fixtures) and
  `apply_sysfs_env()`, the deterministic T1 dry-run surface. `twin` and
  `twin --json` print the profile and where its assets resolved from.
- `omarchy-firmware rehearse [--backend twin|real]` and
  `bin/omarchy-firmware-rehearse` — the dress rehearsal: 28 behavioural
  probes (contract, T0 collections, T2 gates, T1 gates, diagnostics,
  MCP stdio session, journal, report), each with a stable id, an
  expectation and an honest observation; verdict `green`/`red` and a
  diffable JSON report (`omarchy-firmware/rehearsal@1`) under XDG state
  (last 10 kept), journaled as `rehearse`. Backend rule: structural
  expectations hold on both backends; twin-only content probes skip
  honestly on real hardware; the four scenario probes stay deterministic
  on both. No-write guarantee enforced by a suite-level scan: the
  human-confirm flag may appear only in `stage-confirm-refused`, where
  refusal IS the expected outcome.
- `twin-sysfs` fixture tree — a minimal /sys (EPP ×2 cpus, nct6798 with
  three curve slots) so T1 dry-run plans are exercisable on any host.
- `docs/digital-twin.md` — the concept, the profile, the probe table,
  the honesty statement ("the twin proves the tool, the machine proves
  the truth") and the P5 protocol (rehearse now → day 0 → diff reports).
- `docs/first-run.md` Step −1 — the dress rehearsal before the machine.

**Fixed**
- install.sh never staged the library: the first real session would have
  died on `ModuleNotFoundError` from `~/.local/bin`. install.sh now
  stages a self-contained layout (`lib/` + `twin/` under
  `~/.local/share/omarchy-firmware/`), every bin resolves it as a
  fallback, and the rehearsal was run against that installed layout,
  outside the repository, to prove it (28/28 green).
- The MCP server's missing-package message now names the version pin
  (`mcp>=1.0,<2` — 2.x renamed FastMCP) and the underlying ImportError.
- Scenario resolution is twin-aware (`diagnostics._scenario_dir()`), so
  `diag scenarios` and `selftest` work from the installed layout too.

**Changed**
- Test suite 246 → 262 checks (twin resolution, rehearsal green on
  TWIN-1, probe surface locked at 28, no-write scan, honest-skip map);
  suite and MCP smoke green on Python 3.12 and 3.13.

## 0.4.1 — Scenario hardening: the full signature surface exercised

**Added**
- 4 bundled thermal scenarios (12 total): `case-fan-dead` (S2 — a dead
  case fan the AIO hides from Tctl), `runaway` (S7 — undamped end-of-load
  slope), `heatwave` (S8 — Tjmax fold-back with a HEALTHY interface, the
  room is the cause), `hot-nvme` (S11 — a hot spot outside the CPU view).
- 13 contract checks (246 total): every new scenario must name THE fault
  and nothing else — no instant-rise where the rise is slow, no interface
  verdict where the hardware is fine.

**Fixed**
- S11 emitted one finding PER SAMPLE instead of per sensor: a 30-sample
  probe with a hot NVMe produced 30 copies of the same finding. Aggregated
  to the per-sensor max across the series (same rule as the fans dict).

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
