---
name: firmware
description: >
  Audit and diagnostics of this machine's firmware/BIOS and hardware via
  the omarchy-firmware base (Phase 4: full read-only diagnostics, two
  reversible writes, the CVE watch, and the human-gated T2 staging).
  Use whenever a question touches the BIOS, UEFI,
  NVRAM, the boot chain, fwupd, firmware CVEs, temperatures, disks, GPU,
  memory speed, BIOS settings, or a suspected hardware fault. Triggers:
  BIOS, UEFI, firmware, NVRAM, efibootmgr, boot entries, boot order, ESP,
  Limine, UKI, Secure Boot, fTPM, TPM, AGESA, LogoFAIL, Sinkclose,
  firmware CVE, fwupd, LVFS, dmidecode, SMBIOS, CPU running hot,
  overheating, throttling, temperature, thermal paste, AIO pump, fan,
  VRM, dust, thermal diagnostics, NVMe, SMART, reallocated sectors, Xid,
  GPU, XMP, EXPO, DOCP, RAM speed, Resizable BAR, SVM, VT-x, IOMMU, EPP,
  fan curve, "where does my BIOS stand", "am I exposed", "why is it
  running hot", "is my disk dying", BIOS update. Writes are limited to
  two T1 reversible actions (dry-run by default); T2 staging is prepared
  by the agent but applied only by the human: see the Scope section.
---

# Firmware Skill (Phase 4 — full T0 diagnostics + T1 writes + the supervised loop)

Work from evidence. The goal is an honest picture of the firmware AND the
hardware, not a plausible story. Ten tools are T0: pure reads, journaled
in `~/.local/state/omarchy-firmware/journal.jsonl`. Two tools are T1:
reversible writes, **dry-run by default** — they never touch anything
without an explicit confirm flag, and they back up before they write.
The T2 staging layer exists on the CLI alone: the agent prepares the
plan, the human types `--confirm`. If a question requires anything
else, it is out of scope — see Scope and Tiers.

## The twelve tools (first call first)

| Tool | CLI | Tier | What it answers |
|---|---|---|---|
| `fw.audit.status` | `omarchy-firmware audit status --json` | T0 | "Where does my firmware stand?" — board, BIOS, boot, fwupd, sensors |
| `fw.audit.cve` | `omarchy-firmware audit cve --json` | T0 | "Am I exposed to LogoFAIL?" — AM4 version/CVE cross-check |
| `fw.boot.inspect` | `omarchy-firmware boot inspect --json` | T0 | "Is my boot chain healthy?" — efibootmgr, UKI/Limine, snapshots |
| `fw.update.check` | `omarchy-firmware update check --json` | T0 | "Are there updates?" — local fwupd state, 15-min cache |
| `fw.cve.watch` | `omarchy-firmware audit cve-watch --json` | T0 | "Is the CVE timeline current?" — KB freshness, drift since last watch, fwupd advisory candidates |
| `fw.diag.thermal` | `omarchy-firmware diag quick --json` | T0 | "Why is it running hot?" — signatures: pump, paste/mounting (R_th), fan, VRM, 12 V, trend |
| `fw.diag.storage` | `omarchy-firmware diag storage --json` | T0 | "Is my disk lying to me?" — NVMe media/spare/wear, SATA reallocated/pending, PCIe links |
| `fw.diag.gpu` | `omarchy-firmware diag gpu --json` | T0 | "Is my GPU sick or capped?" — Xid history, thermal slowdown, BAR1, link width |
| `fw.diag.ram` | `omarchy-firmware diag ram --json` | T0 | "Is my RAM at the paid speed?" — rated vs configured (XMP/EXPO/DOCP), EDAC |
| `fw.diag.settings` | `omarchy-firmware diag settings --json` | T0 | "What is mis-adjusted?" — Secure Boot, SVM/VT-x, IOMMU, EPP, fan mode |
| `cpu.epp.set` | `omarchy-firmware cpu epp set VALUE` | T1 | efficiency hint of every CPU — dry-run default, `--confirm` + undo |
| `fans.curve.set` | `omarchy-firmware fans curve set --file F` | T1 | nct67xx hardware curve — dry-run default, mechanical guard, undo |

**Rule 1 — the agent proposes, the HAL disposes, the human decides.**
T1 writes: dry-run first, SHOW the plan to the human, get an explicit
agreement, only then confirm. A write is always followed by a T0
verification read and the undo offer.

**Rule 2 — audit first.** `fw.audit.status` is always the first call.
Never reason from a guessed board: the platform is read from SMBIOS
(dmidecode), not from a model's memory.

**Rule 3 — ask for --json.** The CLI is the reference; the agent consumes
the machine output. The journal records both usages identically.

**Rule 4 — the diagnostic says what it names, nothing more.** Every
finding carries its quantified evidence, its hypothesis, its next steps
and its confidence (high / medium / low). Cite the evidence, never
summarize it into a bare "it's the paste". An "undetermined" verdict is an
honest result, not a failure: say why (missing sensors, insufficient
load) and propose `diag probe`.

## Thermal diagnostics (vol. 3, ch. 3) — conduct

1. **Passive first**: `fw.diag.thermal` (3 reads, ~1 s). It names
   everything nameable without disturbing the machine: pump at 0,
   stopped fan head, VRM > 89 °C, low 12 V rail, hot coolant, degraded
   R_th if a power counter exists.
2. **Active next, with human agreement**: `omarchy-firmware diag probe
   --seconds 30`. It deliberately loads half the cores and measures the
   time constant — this is what catches missing paste when no coolant
   sensor exposes the loop temperature. Warn them: the machine will heat
   up for a minute, it is intended and bounded (the BIOS thermal
   protection remains the final guard rail).
3. **Reason from the evidence**: take the finding's `evidence` fields
   (R_th, coolant/ambient delta, rpm, power fold-back). Tell apart the
   three families the BIOS confuses: broken die→liquid (paste/mounting,
   high R_th), broken liquid→air (fan/flow, hot coolant with healthy
   R_th), broken circulation (dead pump, everything else spins for
   nothing).
4. **Propose, never apply**: redoing a joint, retuning a PWM curve,
   dusting — the human does it. The agent prepares the walkthrough and
   will re-measure afterwards (`diag probe` compares to the baseline).

## Scope and Tiers

| Tier | Status | Meaning |
|---|---|---|
| T0 | **implemented (10 tools)** | read-only + diagnostics + watch, journaled |
| T1 | **implemented (2 tools)** | reversible writes: dry-run default, explicit confirm, backup + undo, mechanical guards |
| T2 | **implemented, human-only CLI** | firmware transaction: `update stage` (dry-run plan by default, `--confirm --reason` typed by the human, `--cancel` until reboot) and `update rollback` (refused by design, prints the inventory) — NEVER in the MCP surface |
| T3 | **never** | physical flash, EZ Flash: the human executes, the agent prepares the dated, verified walkthrough |

## T1 conduct (the only two writes in existence here)

1. `cpu epp set VALUE` — plan first (dry-run output), cite the diff
   (current -> proposed, all CPUs), ask, then `--confirm` / `confirm:
   true`. Verify with `diag settings` and offer `cpu epp undo`.
2. `fans curve set --file curve.json` — validate the curve BEFORE
   proposing: 2-7 points, temps ascending, last point pwm=255 at <= 90 °C
   (the guard refuses anything else — cooling can never be capped).
   Dry-run, show `plan_writes`, ask, confirm. Verify with
   `fans curve show` and offer `fans curve undo`.
3. Anything else — efivarfs, boot entries, Secure Boot, NVRAM, flash —
   stays forbidden: no path exists, do not improvise one through direct
   shell commands.

## T2 conduct (staging: the agent prepares, the human applies)

1. When a firmware update becomes advisable (a CVE fix, a vendor bug you
   can name), run the dry-run plan first: `omarchy-firmware update stage
   --device GUID --json`. Read the gates aloud: exact device, candidate
   version, power, rollback reality.
2. Refusals are answers: a motherboard outside LVFS means the update
   goes through EZ Flash (T3) — produce the walkthrough, stop there.
3. Hand the human the exact confirm command WITH the reason spelled out:
   `update stage --device GUID --reason '<the why>' --confirm`. Never
   type `--confirm` yourself through any shell path: T2 confirm is a
   human gesture by contract.
4. Remind them: `update stage --cancel` works until they reboot, and the
   firmware is flashed by fwupd at the next reboot — the tool never
   reboots. After the flash, `update rollback` shows where the rollback
   surfaces stand (it will honestly tell you firmware rollback does not
   exist at runtime on this platform).
5. If the weekly watch reports the KB stale or unknown fwupd advisories:
   stage the KB update (`omarchy-firmware-cve-update --file ...`) and let
   the human confirm with the shown sha256 — data follows the two-key
   rule too.

Absolute prohibitions for the agent, even if another path seems to exist:
writing to efivarfs, deleting/reordering efibootmgr entries, running
`flashrom` in write mode, disabling Secure Boot, modifying NVRAM boot
variables. None of these paths exists in the base; do not improvise one
through direct shell commands.

## Privilege rules (inherited from the omarchy skill)

The T0 tools run as the user; dmidecode/efibootmgr may require sudo
depending on the machine. With a terminal: `sudo`. Without a terminal
(background process): `pkexec`. Do not wrap a command that already
handles elevation. T1 writes touch sysfs files owned by root; run them
with `sudo` in a terminal, and never inside an unattended loop.

## Honesty about limits (vol. 1, ch. 4 and vol. 3, ch. 6)

- Desktop AM4 motherboards are **absent from the LVFS catalogue**:
  `fw.update.check` with no removable device to update is the normal
  result, not a failure. The BIOS update then goes through EZ Flash — a
  T3 operation: produce the walkthrough (file, checksum, target version,
  restore point), let the human execute.
- CVE statuses are **date inferences** ("probably fixed", "potentially
  exposed"), not attestations. Always cite the rationale provided by the
  tool; never say "fixed" bare.
- Thermally, without a coolant sensor or a power counter, R_th **does
  not exist**: the fold-back signatures (time constant, plateau, idle
  ΔT) carry lower confidence and the active mode then becomes mandatory
  to name a failing paste. The 12 V rail reading via the Super I/O ADC
  is coarse (± 3 %): a low signal invites a multimeter, it does not
  condemn a PSU.
- What the tool cannot read (Secure Boot without permissions, undeclared
  socket, pump without a dedicated label), it says so: do not fill the
  gaps with confidence.

## Diagnosing an fTPM suspicion (worked example)

1. `fw.audit.status --json` — note BIOS version/date, socket.
2. `fw.audit.cve --json` — check the `ftpm-stutter-2022` line.
3. Correlate symptoms (periodic one-second stutters, frozen I/O) with
   the BIOS date: if < 2022-06, the "potentially exposed" inference is
   documented.
4. Propose: BIOS update (guided T3) or discrete TPM switch — proposal
   only, no action.

## Diagnosing "my CPU runs too hot" (worked example, vol. 3)

1. `fw.audit.status --json` — sensors actually present (k10temp,
   Super I/O, possible coolant).
2. `fw.diag.thermal --json` — read verdict, measurements, findings.
3. Depending on the finding: `diag probe --seconds 30` with human
   agreement for the time constant, then cross-interpretation (pump /
   dead head / interface / airflow).
4. Report: the quantified evidence, the hypothesis, THE most likely next
   step — and remind what the BIOS did silently (fold-back at Tjmax)
   was not a diagnosis but a survival.

## Reporting

A firmware report separates: what is **proven** (SMBIOS fields,
efibootmgr entries, HSI levels, hwmon readings), what is **inferred**
(CVE statuses, thermal signatures, R_th), and what is **unknown**
(permissions, absent hardware, missing sensors). Never assemble
confidence out of assumptions.
