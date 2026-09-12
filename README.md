# Beyond the BIOS — an agent ↔ firmware bridge for Omarchy

[![ci](https://github.com/Cheurteenyt/BIOS-/actions/workflows/ci.yml/badge.svg)](https://github.com/Cheurteenyt/BIOS-/actions/workflows/ci.yml)

> **Read-only firmware & hardware intelligence layer for Omarchy.** Audits BIOS,
> boot chain and AM4 CVEs, and names physical faults the BIOS can't see: dead
> AIO pump, missing thermal paste, hot VRM, sagging 12 V rail. 12 MCP tools
> (10 read-only + 2 reversible) — *the agent explains, the firmware protects.*

**omarchy-firmware** is a read-only firmware and hardware intelligence layer for
[Omarchy](https://github.com/basecamp/omarchy) (Arch Linux) machines. It lets AI
agents — claude, codex, opencode, any MCP-compatible harness — audit the BIOS,
reason about firmware CVEs, inspect the boot chain, and **name physical faults
the BIOS cannot see**: a dead AIO pump, missing thermal paste, a stopped
radiator fan, a hot VRM, a sagging 12 V rail, months-long cooling degradation.

The founding question of this project: *your CPU overheats because no one ever
applied thermal paste — the pump spins, the fans spin, the BIOS throttles at
Tjmax and says nothing. Can that be detected?*

**Yes.** Measured on the reference platform (Ryzen 9 5950X + 240 mm AIO on an
ASUS B450-PLUS):

```
R_th = (T_die - T_coolant) / P_package     (°C/W, steady state)

healthy paste/mounting  →  R_th ≈ 0.29  ·  reaches 85 °C in 12-20 s
missing paste           →  R_th ≈ 0.585 ·  reaches 85 °C in 4 s   →  named
dead pump               →  Tctl explodes, everything else spins   →  named
radiator fan dead       →  coolant hot, R_th healthy              →  named
```

The BIOS watches Tctl, throttles, then shuts down — without ever saying why.
This base correlates the very same sensors and **says the fault's name**.

## What it does today (12 tools: 10 T0 read-only + 2 T1 reversible writes + the human-only T2 layer)

| MCP tool | CLI | Tier | Answers |
|---|---|---|---|
| `fw.audit.status` | `omarchy-firmware audit status` | T0 | "Where does my firmware stand?" — board, BIOS, socket, boot, fwupd, sensors |
| `fw.audit.cve` | `omarchy-firmware audit cve` | T0 | "Am I exposed to LogoFAIL?" — BIOS version vs known AM4 CVEs (fTPM stutter, LogoFAIL, Sinkclose, VU#382314, CVE-2026-6726/6727) |
| `fw.boot.inspect` | `omarchy-firmware boot inspect` | T0 | "Is my boot chain healthy?" — efibootmgr, UKI/Limine detection, Snapper snapshots |
| `fw.update.check` | `omarchy-firmware update check` | T0 | "Any updates?" — local fwupd state, 15-min cache, no network |
| `fw.cve.watch` | `omarchy-firmware audit cve-watch` | T0 | "Is the CVE timeline current?" — KB freshness, drift since last watch, fwupd advisory correlation (P4) |
| `fw.diag.thermal` | `omarchy-firmware diag quick` | T0 | "Why is it hot?" — pump, paste/mounting (R_th), radiator fan, VRM, 12 V, long-term drift |
| `fw.diag.storage` | `omarchy-firmware diag storage` | T0 | "Is my disk lying to me?" — NVMe media errors/spare/wear, SATA reallocated/pending/CRC, PCIe links |
| `fw.diag.gpu` | `omarchy-firmware diag gpu` | T0 | "Is my GPU sick or just capped?" — Xid history, thermal slowdown, BAR1 (ReBAR), link width |
| `fw.diag.ram` | `omarchy-firmware diag ram` | T0 | "Is my memory at the speed I paid for?" — rated vs configured (XMP/EXPO/DOCP), EDAC errors |
| `fw.diag.settings` | `omarchy-firmware diag settings` | T0 | "What is mis-adjusted?" — Secure Boot, SVM/VT-x, IOMMU, EPP, fan mode, TPM; the invisible listed honestly |
| `cpu.epp.set` | `omarchy-firmware cpu epp set VALUE` | T1 | "Fix the efficiency hint" — every CPU, **dry-run by default**, `--confirm` applies, backup + undo |
| `fans.curve.set` | `omarchy-firmware fans curve set --file F` | T1 | "Replace the Q-Fan curve" — nct67xx hardware curve, mechanical guard (last point = 255), **dry-run by default**, undo |

Two more tools exist **outside the MCP surface, on the CLI alone** (P4):

| CLI | Tier | What it does |
|---|---|---|
| `omarchy-firmware update stage --device GUID` | T2 | **Human-only**: dry-run plan (gates, exact command, rollback reality) by default; `--confirm --reason '...'` stages a fwupd update — the firmware is flashed by fwupd at the NEXT reboot, which this tool never triggers. `--cancel` revokes before reboot |
| `omarchy-firmware update rollback` | T2 | **Refused by design**: firmware rollback does not exist as a runtime operation on single-BIOS AM4 — the tool answers with the honest inventory (T1 store, pending transaction, fwupd history, FlashBack) |

Every call — even reads — is appended to an access journal
(`~/.local/state/omarchy-firmware/journal.jsonl`): the agent cannot touch the
firmware side without leaving a dated, replayable trace.

## The one-sentence theses

> **The agent proposes, the HAL disposes, the human decides.**
> **What the BIOS cannot name, the agent names — at zero extra cost.**

Reads are free and unlimited (T0, journaled). The only two writes this package
can ever do are T1 — reversible, dry-run by default, backed up before applied,
mechanically incapable of capping cooling. T2 staging is a human CLI gesture;
flashing (T3) has no call path. The full contract: [docs/security-doctrine.md](docs/security-doctrine.md).

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/Cheurteenyt/BIOS-/main/install.sh \
  | bash -s -- --from release               # user-level install, bit-verified payload
omarchy-firmware twin                       # meet TWIN-1, the rehearsal machine
omarchy-firmware rehearse --backend twin    # the WHOLE contract, no hardware
omarchy-firmware rehearse-diff --latest     # day-0 debrief: the named surprises
omarchy-firmware capture                    # day-0 photograph: T0 snapshot
omarchy-firmware audit status               # real machine: full inventory
omarchy-firmware diag quick                 # passive thermal check (~1 s)
omarchy-firmware diag storage --json        # disks + PCIe links (vol. 4)
omarchy-firmware diag gpu                   # Xid, BAR1, thermal slowdown
omarchy-firmware diag ram                   # XMP/EXPO evidence, EDAC
omarchy-firmware diag settings              # SVM, IOMMU, EPP, fan mode
omarchy-firmware cpu epp set balance_performance   # T1 DRY-RUN (plan only)
omarchy-firmware cpu epp set balance_performance --confirm  # apply + backup
omarchy-firmware fans curve set --file curve.json   # T1 DRY-RUN
omarchy-firmware audit cve-watch           # KB freshness + advisory drift (P4)
omarchy-firmware update stage --device GUID  # T2 DRY-RUN plan (human-only layer)
omarchy-firmware report                    # the supervised-loop digest (P4)
```

The installer floats, the payload is pinned: whatever `--from release` (or
`--from v0.6.0`; `--from main` is the floating development path) installs
was verified against its published `SHA256SUMS` **before** anything ran —
the provenance (tag + digest) is echoed, and worth quoting in the day-0
log. From a checkout or an extracted tarball, plain `./install.sh` still
installs that tree.

Try everything **without any hardware** — TWIN-1, the digital twin of the
target machine: 12 pre-recorded thermal scenarios (5950X physics), 3 board
fixture sets (issues + clean), a sysfs tree for deterministic T1 dry-runs,
a 323-check test suite, and an MCP conformance smoke:

```bash
omarchy-firmware diag scenarios             # the scenario list
omarchy-firmware diag quick --scenario no-paste --json
omarchy-firmware selftest                   # full demo on the twin
python3 tests/test_suite.py                 # 323 checks, zero dependency
python3 tests/mcp_smoke.py                  # MCP handshake + T1 dry-run proof
```

Below the runtime frontier there is one more map — the flash chip itself.
`fw.spi.map` (0.7.0, "the map of the invisible") reads a dump or the chip
(flashrom `-r`, root) and inventories firmware volumes, DXE and SMM
modules, variable-store names, the ME/PSP region and the boot manifests.
**It reads and never writes** (+0 octet enforced at the byte level), it
never runs by default (`capture --spi-read` or the standalone command),
and it is deliberately outside the MCP surface — an SPI read is a
declared gesture, not an ambient tool. See [docs/spi-map.md](docs/spi-map.md).

Wire an agent (MCP):

```bash
pip install mcp                             # or: pacman -S python-mcp
claude mcp add omarchy-firmware -- ~/.local/bin/omarchy-firmware-mcp
```

## Frugality is a hard constraint, measured

The firmware intelligence must never become heavier than the stock BIOS it
answers: a one-shot diagnostic is ~0.3 s CPU, RAM between runs is 0 (no
daemon — the doctor is a one-shot a timer *may* wake), the optional 15-min
timer costs ~0.03 % duty cycle, the LLM is never resident, and SPI flash
added is **+0 bytes**. Stdlib-only for the CLI; `mcp` is an optional
dependency. The full budget and its L1/L2/L3 reasoning:
[docs/frugality.md](docs/frugality.md).

## Architecture in one glance

```
13 agent harnesses             ← unchanged
   │  MCP stdio
omarchy-firmware-mcp           ← typed wrapper: declared tier, structural refusals,
                                 T1 dry-run by default (confirm = second key),
                                 T2 NOT in the surface (human-only CLI)
   │
omarchy-firmware (CLI)         ← functional reference, # omarchy:* metadata
   │
lib/firmware_hal/              ← T0 collectors + T1 actions + T2 staging + journal + CVE KB
   │
dmidecode · efibootmgr · fwupd · smartctl · lspci · nvidia-smi · hwmon · snapper
```

One function = one CLI command = one MCP tool. The agent is never a privileged
path: a human types the same thing, a shell script too. Layers, fixtures and
the one-implementation-three-consumers contract: [docs/architecture.md](docs/architecture.md)
· how the repo maps to disk and to the installed system: [docs/file-layout.md](docs/file-layout.md).

## The tier contract

```
T0  read-only + diagnostics + watch, journaled     ← THIS REPO (10 tools)
T1  reversible writes (EPP, fan curves)            ← THIS REPO (2 tools):
                                                   dry-run default, confirm key,
                                                   backup store, undo
T2  firmware transaction (stage, rollback)         human-only CLI (P4): stage =
                                                   dry-run plan + --confirm by the
                                                   human; rollback = refused by design
T3  physical flash (EZ Flash)                      never the agent: it produces the
                                                   walkthrough, the human executes
```

Project rule: no tool enters the server without its declared tier and its
out-of-scope refusal test. The T2 tools refuse the MCP surface with the exact
human path; `fw.flash.write` does not even exist.

## Documentation

| Document | Content |
|---|---|
| [AGENTS.md](AGENTS.md) | how AI agents operate in this repo — read this first |
| [docs/first-run.md](docs/first-run.md) | the day-1 runbook + the 5-day supervised loop protocol (P4 exit criterion) |
| [docs/digital-twin.md](docs/digital-twin.md) | TWIN-1, the rehearsal machine: profile, assets, honesty, and the dress-rehearsal protocol (P5) |
| [docs/architecture.md](docs/architecture.md) | layers, contract, fixtures, one-implementation-three-consumers |
| [docs/security-doctrine.md](docs/security-doctrine.md) | tiers, error sources, barriers, the 8 rules |
| [docs/t1-write-layer.md](docs/t1-write-layer.md) | the two-key rule, rollback store, mechanical curve guards, the human-gated T2 staging |
| [docs/diagnostics-catalog.md](docs/diagnostics-catalog.md) | the named hardware findings and their measurable evidence |
| [docs/vendor-bios-heritage.md](docs/vendor-bios-heritage.md) | what ASUS/MSI/Gigabyte/ASRock actually shipped, what we keep, what we answer — the vendor-facing coherence audit |
| [docs/frugality.md](docs/frugality.md) | the resource budget, L1/L2/L3, why the timer is optional |
| [docs/file-layout.md](docs/file-layout.md) | how the repo is organized and where everything lands once installed |
| [docs/packaging.md](docs/packaging.md) | lever D: the Arch-native delivery shape (PKGBUILD) beside the day-0 user-space default |
| [docs/day0-protocol.md](docs/day0-protocol.md) | reading a vendor image: the lab pipeline stage order, the five tripwires, the report skeleton — the lab half of the day-0 doctrine |
| [docs/day0-report-2026-09-16.md](docs/day0-report-2026-09-16.md) | the pre-filled day-0 report: empty tables (identity triangulation, delta, armor checklist, chain run, combo lens) and the fill-in procedures, ready for the live dump |
| [lab/README.md](lab/README.md) | the disposable machine: the twenty-eight investigation rings, their JSON evidence, the doctrine |
| [docs/research/](docs/research/) | the five-volume study *Beyond the BIOS*: per-volume summaries + the FR/EN editions (PDF release assets) |

CI runs the full contract suite (Python 3.11/3.13) and the MCP conformance
smoke on every push — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Roadmap

| Phase | Content | Exit criterion |
|---|---|---|
| P1 | 4 T0 tools + skill + journal | 10 state questions without any write ✓ |
| P2 | + `fw.diag.thermal`: signature engine, probe, baseline, timer | 8 scenarios named one by one, measured frugality ✓ |
| P3 | + storage/GPU/RAM/settings T0 diagnostics + the T1 HAL (`cpu.epp.set`, `fans.curve.set`) | 177 checks, MCP 11-tool conformance, verified rollback, mechanical curve guards ✓ |
| P4 | + the supervised loop: `fw.cve.watch` (KB freshness, drift, fwupd advisories), the human-gated T2 staging (`update stage`, `update rollback`), the loop report, the weekly watch timer | code complete: 246 checks, 12 scenarios, MCP 12-tool conformance · the 5-day criterion itself is measured on the real machine — see [docs/first-run.md](docs/first-run.md) |
| **P5 — this repo** | + the digital twin and the dress rehearsal: TWIN-1 as an installable machine profile, `rehearse` (28 behavioural probes, one verdict), `rehearse-diff --latest` (the day-0 debrief), `capture --live` (the read-only day-0 photograph), `spi-map` (0.7.0 — the cartography of the flash chip, 0 bytes written, outside the MCP surface), the installed-layout fix, the hardened distribution (checksum-verified installer, SDK pin + drift canary, pinned runners, the write-path audit), `lab/` (QEMU/OVMF now, the sacrificial coreboot board as study Volume 5), 0.7.1 ("the honest labels") | 323 checks, rehearsal green on TWIN-1 on py3.12/3.13, installed-binary rehearsal green outside the repo, `install.sh --from release` roundtrip verified · day-0 behaviour proven before the machine — see [docs/digital-twin.md](docs/digital-twin.md); the full ledger: [CHANGELOG.md](CHANGELOG.md) |

## Provenance

Everything here descends from a five-volume study auditing the Omarchy repo,
the AM4 vendor BIOS landscape, and the question "what can an agent do that
the vendor BIOS cannot?" — see [docs/research/](docs/research/). The full
series (79 pages) is archived as **release assets**, not in-repo binaries:
the **English edition** (canonical, updated September 2026 so the blueprint
chapters report their shipped state) on the
[study-en release](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-en),
the **French originals** (the primary voice, archived unchanged) on the
[study-fr release](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-fr):
*Beyond the BIOS* (22 p.) · *The Agent and the Firmware* (24 p.) · *What the
BIOS Cannot See* (15 p.) · *Misconfigured or Faulty* (18 p.). The reference
test platform is a Ryzen 9 5950X + RTX 3070 on ASUS B450/B550; the board is
**never** hardcoded — it is read from SMBIOS at run time.
