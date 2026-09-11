# Changelog

All notable changes to `omarchy-firmware`. The tool contract (tiers,
tool names, refusal behaviour) is frozen between phases: changes are
additive, and every tool keeps its refusal test.

## Unreleased — the sixth ring and lever D

Same session as the cleanup; still docs-only. The tool surface is
untouched: 15 tools, MCP smoke 12, 323 checks green.

**Investigation (ring 6 — the IFR grammar, spec-fresh)**
- Ring 5's locked opcode layer resolved by re-deriving the grammar from
  the EDK2 spec headers (`UefiInternalFormRepresentation.h`, fetched
  from tianocore/edk2 — zero memory-encoded constants): FORMS = 0x02 /
  STRINGS = 0x04, and `EFI_IFR_OP_HEADER { OpCode:8, Length:7, Scope:1 }`
  — the scope bit of the second byte is what broke every naive match.
  Ring 5's ledger self-corrects: it had walked STRING packages with an
  opcode grammar, and its "memory table refuted" was itself the error.
- Validation upgraded to the strongest possible: a forms package counts
  only if the opcode walk consumes its body EXACTLY. 21/21 packages
  close exactly on all three builds (plain, secboot, snakeoil).
- The facade now priced in QUESTIONS, not sentences: plain = 146
  questions / 58 pages across 11 modules; secboot = 208 / 79 —
  SecureBootConfigDxe alone is 62 questions, the biggest form carrier,
  existing only in the secboot builds (the trust stays NVRAM data,
  ring 5). BdsDxe carries zero forms: its 95 strings feed UiApp.
- Artifacts: `lab/ovmf-ifr-census.json` (per-module ops/questions/
  options/pages), `lab/findings-sixth-ring.md`; `docs/open-questions.md`
  Q1 updated with the question-counting instrument (vendor-ready for
  day-0); the list-header closure of IFR carriers stays flagged open.

**Added (lever D — packaging)**
- `packaging/PKGBUILD` — the Arch-native delivery shape, pinned to the
  v0.7.1 tag digest (`2b327f9c…`), doctrine-inherited: units staged
  inactive, no `post_install`, nothing in `/usr/share/omarchy`, nothing
  in `$HOME`, +0 octet. The staged-tree + `/usr/bin` symlinks design
  works with the frozen `realpath`-based lib resolution (a naive
  `/usr/lib` layout would be broken by construction — documented in
  `docs/packaging.md`).
- `docs/packaging.md` — the two delivery shapes compared, the design
  finding, build/verify commands, and the honest status: not yet built
  on an Arch box (this sandbox is Debian); the first `makepkg` run is a
  post-day-0 task.

## Unreleased — the omarchy-grade cleanup

Docs-only hygiene pass, audited against the upstream Omarchy repository
(`omacom/omarchy`). The tool surface is untouched: 15 tools, MCP smoke
12, 323 checks green.

**Changed**
- The four-volume study no longer ships as in-repo PDFs (9.3 MB, 84 % of
  the working tree weight): the English edition stays on the `study-en`
  release (bit-identical), the French originals are archived on the new
  [`study-fr` release](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-fr).
  `*.pdf` is gitignored; `docs/research/README.md` and the README
  provenance link to the releases. The repo is text + code, the same
  choice Omarchy makes.
- README tightened toward the Omarchy hub pattern: the frugality table
  and the tier-contract details relocated to their documents, the
  quick-start deduplicated, the P5 ledger condensed (the full detail
  lives here, in the CHANGELOG).
- `lab/README.md` rebuilt as the full index of the investigation: the
  five rings + the first OVMF reading, the eight JSON artifacts, and the
  instrument policy (probe scripts are sandbox tools, deliberately
  untracked).
- `findings-2026-09-11.md` renamed to `findings-first-ring.md` — the ring
  nomenclature is now uniform (first → fifth).

**Added**
- `docs/file-layout.md` — how the repo is organized and where everything
  lands once installed (the pattern Omarchy itself uses).
- `CLAUDE.md` — one-line pointer to `AGENTS.md`, no duplication.
- Tags `v0.7.0` and `v0.7.1` pushed at their historical commits.

## 0.7.1 — the honest labels

A real-firmware correction. The deep-dive investigation on actual OVMF
images (lab world, Debian's edk2 package, read-only, zero bytes written)
proved two filesystem-GUID labels wrong and — better — found why: the
synthetic fixture had borrowed the LZMA custom decompress GUID
(`EE4E5898…`) as a variable-store GUID, and the parser inherited the
mistake. Real firmware taught us the truth; the fixture now uses it.

**Fixed**
- `EE4E5898-3914-4259-9D6E-DC7BD79403CF` relabelled: "LZMA custom
  decompress GUID (section signature, not a filesystem)" — it appears
  inside GUID-defined SECTIONS (we used it to pierce OVMF's compressed
  FVMAIN_COMPACT in memory), never as an FV filesystem; removed from
  the variable-store set, so an FV carrying it is no longer scanned
  for variable names.
- `FFF12B8D-7696-4C8B-A985-2747075B4F50` relabelled to what it is:
  "system NV data FV (EFI_SYSTEM_NV_DATA_FV_GUID)" (was "variable
  store (EVSA)").
- The synthetic fixture now uses the real authenticated variable store
  GUID (`AAF32C78…`) — the GUID real 4M images actually carry.
- New test freezes the lesson: an FV carrying the LZMA GUID is
  labelled as LZMA and yields zero variable names. Tests 322 → 323.

**Investigation (the first real firmware the parser has read)**
- `lab/ovmf-findings.md`: on real OVMF the parser reports honestly —
  no descriptor (descriptorless image, expected), 2 outer FVs, and 0
  visible modules because FVMAIN_COMPACT is LZMA-compressed: the
  compression wall vendor images hide behind too. Pierced in-memory
  (stdlib `lzma`, read-only): PEIFV + DXEFV, 115 DXE modules and (on
  the SMM_REQUIRE build) 9 SMM modules, by name; the plain vs secboot
  delta shows Secure Boot arriving together with SMM-hosted variable
  services; a REAL populated variable store yields 22 real variable
  names (and shows the utf-16 heuristic also catches strings inside
  variable DATA — the label holds: names are heuristic, GUIDs are
  identity).

## 0.7.0 — the map of the invisible

One step beyond the runtime frontier. The tool now crosses the edge of
the flash chip — **read-only** — and inventories what lives below: the
"things never seen" where the vol. 4 pathologies sit at the source.

**Added**
- `fw.spi.map` (T0, the fifteenth tool): read-only cartography of the
  SPI flash. Sources, in priority order: `--dump PATH` (offline
  analysis), `FW_SPI_DUMP` (fixture/CI form), else one `flashrom -r`
  live read (root; flashrom reads twice — read + verify — and the
  module writes nothing, ever; the temporary dump is deleted after
  parsing unless `--save-dump` keeps it).
- The parser (stdlib only): the Intel flash descriptor (FLVALSIG,
  FLMAP0/FRBA, the five FLREG regions), firmware volumes (`_FVH`,
  header checksum verified, classified by filesystem GUID), FFS files
  counted by type, DXE and SMM modules with GUIDs and UI names,
  variable-store names (utf-16 heuristic, labelled), the ME region with
  a best-effort version guess (labelled), and the `$BPM`/`$KSH` boot
  manifests — with the honest note that the fused-vs-deactivated
  Boot Guard state is NOT determinable from the image alone.
- `capture --spi-read`: the map joins the photograph when, and only
  when, the human passes the flag. The snapshot carries
  `"spi_read": true`, a `spi_note`, and the section is labelled
  "spi-read (0 bytes written)". The default photograph NEVER reads the
  chip — proven by a structural test.
- `lab/` — the disposable machine (the QEMU half of the replacement
  question): `lab/README.md` (the doctrine: replace in the lab, +0
  octet in the fleet), `lab/ovmf-smoke.sh` (OVMF boots in QEMU,
  headless, boot log captured — the first "replacing the firmware"
  experiment, risk-free), `lab/coreboot-notes.md` (the Volume 5
  doctrine: the sacrificial board, dump-first, external programmer,
  candidate machines, the non-negotiable sequence).
- `docs/spi-map.md` — the module document: the rule, the usage, the
  honesty labels, the September 2026 ruling (replacement = Volume 5 on
  dedicated hardware, never the day-0 machine).
- Tests 302 → 322: a synthetic SPI image built byte by byte in the
  suite (descriptor, FFS2 volume with DXE/SMM files, variable store,
  `$MN2` manifest, `$BPM`/`$KSH`) exercises the whole parser, plus the
  never-by-default guarantee, the MCP-surface exclusion and the CLI
  end to end.

**Changed**
- The contract grows from fourteen to fifteen tools; `fw.spi.map` is
  declared T0 read-only, journaled through the single `_guard` flow,
  and deliberately outside the MCP surface (an SPI read is a declared
  gesture, not an ambient tool — the conformance smoke stays at 12).

**Honesty**
- A failed SPI read (no flashrom, no root, kernel lockdown, timeout)
  answers `"status": "unavailable"` with its reason — a capture keeps
  going, a map never guesses.
- Two parser subtleties caught by the suite before they could lie on a
  real image: the utf-16 UI-name split that ate the last character of
  every ASCII name, and the version regex that truncated 4-digit
  build numbers to 3.

## 0.6.3 — the write-path audit

A deep pass over the code with one question: where could this tool lie,
crash, or write where it must not? Fifteen findings, all closed, each
locked by a test (287 → 302).

**Fixed — the write paths (T1/T2)**
- `undo` validated its targets: the paths it writes come from the
  rollback store in XDG state, so a tampered store could turn the
  two-key undo into an arbitrary-file-write primitive. Every stored
  target is now checked against the sysfs root AND the declared
  attribute patterns (rule 5 applies to the undo path too); refused
  targets are listed, nothing is guessed.
- `undo` aborted on the first failing target, leaving the rest
  unrestored: it now continues and reports per-target errors, exactly
  like the apply path.
- A partial apply (some writes refused) reported status `applied` with
  exit 0: it now reports `partial` (CLI exit 1) with a note pointing at
  `undo` — the machine left half-adjusted is stated, never hidden.
- `update stage --cancel` swallowed a failed persistence and answered
  `cancelled` while the on-disk transaction still said `staged` — the
  human could reboot INTO the flash. It now returns `error` with
  CANCEL NOT PERSISTED.

**Fixed — the audit trail**
- MCP refused/error calls left ZERO journal entries (the CLI journaled
  them): a refused T1 attempt through an agent harness is now recorded
  with its requested value, like its CLI equivalent.
- `journal`/`report` crashed on stray non-object JSONL lines (an
  interleaved fragment): skipped now, never a crash. `journal 0` dumped
  the WHOLE file (`lines[-0:]`): returns empty now.
- The journal append was a buffered text write: a timer run and a
  manual call could interleave half-flushed lines. It is one `os.write`
  on an O_APPEND fd under flock now.
- `kb.update` labelled its data WRITES as tier T0; activate/revert are
  journaled T1 now. The two-key sha256 compare is constant-time
  (`hmac.compare_digest`).

**Fixed — honesty of statuses**
- A failed fwupd check (daemon dead, timeout) was reported as
  "up to date (no updates announced by the daemon)" and cached for
  15 minutes: exit code 1 keeps its nominal meaning, any other failure
  now reads `unavailable`.
- A corrupt rollback store was silently reset to `[]` — the new backup
  destroyed the previous undo history without a word: the bad file is
  moved aside (`*.bad-<ts>`) as evidence, the store restarts fresh.
- `capture` claimed the snapshot was its only artifact while rewriting
  the watch baseline and the update cache: the embedded sections now
  run with persistence off (`record=False`, `persist_cache=False`) — a
  photograph touches nothing, stated in the module contract.

**Fixed — robustness**
- All state files the tool depends on (rollback store, staging
  transaction, watch baseline, KB override, update cache, snapshots,
  rehearsal reports) are written atomically now (temp sibling +
  `os.replace`) via the new `firmware_hal.atomic` module: a crash or a
  full disk can no longer leave a half-written file a later read would
  misinterpret.
- `install.sh --from` cleans its temp dir on EVERY exit path (trap),
  not only on success — no debris, no half-downloaded payloads.
- The bin wrappers resolve the installed library through
  `XDG_DATA_HOME` too — with a non-default data home, install.sh staged
  the lib where the wrappers could not find it (first real session
  would have died on ModuleNotFoundError, again).
- `capture`/`report`/`rehearse` journal a failed invocation instead of
  escaping as a raw traceback; twin sysfs env vars are restored
  in-process after a capture; a stray fd from the rehearsal's curve
  temp file is closed; two stale bin comments fixed.

## 0.6.2 — the photograph, for real

The day-0 protocol's core artifact is `capture` — the photograph of what
the machine really is. This release closes the trap that would have made
that photograph picture the wrong machine, and two frugality debts.

**Added**
- `capture --live`: the day-0 form. Twin assets (fixtures, sysfs tree)
  are ignored and the roots are the real `/sys` — necessary because
  install.sh stages TWIN-1 beside the tool, and the twin-aware default
  would resolve it on the very machine day-0 wants to photograph.
- The twin-aware default is now LOUD: a resolved twin is stated in the
  snapshot (`capture_note`) and in the human render — photographing
  TWIN-1 while believing one photographs the machine is exactly the
  day-0 mistake this tool exists to prevent.
- Every capture section carries its measured cost in `ms`: the
  frugality budget (~0.3 s per one-shot) is a claim, so the photograph
  measures itself — on real hardware this names the slow collector.

**Changed**
- `cve-watch`: the KB file is parsed exactly ONCE per command (it was
  parsed four times — `kb_info`, the drift hashes ×2, the fwupd
  cross-check — and threaded through `cve_kb.collect` too). Enforced by
  a counting test.

**Fixed**
- `capture`: the `cpu_epp` / `hwmon` detail sections are covered by the
  same error discipline as the ten T0 collections — a bad sysfs root is
  recorded in `section_errors`, it can no longer crash the photograph.
- tests 281 → 287: the twin note, the live form, the per-section ms,
  the bogus-root discipline and the single KB parse are all structural.

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
