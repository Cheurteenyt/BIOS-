# Beyond the BIOS — an agent ↔ firmware bridge for Omarchy

> **Read-only firmware & hardware intelligence layer for Omarchy.** Audits BIOS,
> boot chain and AM4 CVEs, and names physical faults the BIOS can't see: dead
> AIO pump, missing thermal paste, hot VRM, sagging 12 V rail. 5 MCP tools, all
> read-only — *the agent explains, the firmware protects.*

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

## What it does today (11 tools: 9 T0 read-only + 2 T1 reversible writes)

| MCP tool | CLI | Tier | Answers |
|---|---|---|---|
| `fw.audit.status` | `omarchy-firmware audit status` | T0 | "Where does my firmware stand?" — board, BIOS, socket, boot, fwupd, sensors |
| `fw.audit.cve` | `omarchy-firmware audit cve` | T0 | "Am I exposed to LogoFAIL?" — BIOS version vs known AM4 CVEs (fTPM stutter, LogoFAIL, Sinkclose, VU#382314, CVE-2026-6726/6727) |
| `fw.boot.inspect` | `omarchy-firmware boot inspect` | T0 | "Is my boot chain healthy?" — efibootmgr, UKI/Limine detection, Snapper snapshots |
| `fw.update.check` | `omarchy-firmware update check` | T0 | "Any updates?" — local fwupd state, 15-min cache, no network |
| `fw.diag.thermal` | `omarchy-firmware diag quick` | T0 | "Why is it hot?" — pump, paste/mounting (R_th), radiator fan, VRM, 12 V, long-term drift |
| `fw.diag.storage` | `omarchy-firmware diag storage` | T0 | "Is my disk lying to me?" — NVMe media errors/spare/wear, SATA reallocated/pending/CRC, PCIe links |
| `fw.diag.gpu` | `omarchy-firmware diag gpu` | T0 | "Is my GPU sick or just capped?" — Xid history, thermal slowdown, BAR1 (ReBAR), link width |
| `fw.diag.ram` | `omarchy-firmware diag ram` | T0 | "Is my memory at the speed I paid for?" — rated vs configured (XMP/EXPO/DOCP), EDAC errors |
| `fw.diag.settings` | `omarchy-firmware diag settings` | T0 | "What is mis-adjusted?" — Secure Boot, SVM/VT-x, IOMMU, EPP, fan mode, TPM; the invisible listed honestly |
| `cpu.epp.set` | `omarchy-firmware cpu epp set VALUE` | T1 | "Fix the efficiency hint" — every CPU, **dry-run by default**, `--confirm` applies, backup + undo |
| `fans.curve.set` | `omarchy-firmware fans curve set --file F` | T1 | "Replace the Q-Fan curve" — nct67xx hardware curve, mechanical guard (last point = 255), **dry-run by default**, undo |

Every call — even reads — is appended to an access journal
(`~/.local/state/omarchy-firmware/journal.jsonl`): the agent cannot touch the
firmware side without leaving a dated, replayable trace.

## The one-sentence theses

> **The agent proposes, the HAL disposes, the human decides.**
> **What the BIOS cannot name, the agent names — at zero extra cost.**

Reads are free and unlimited (T0, journaled). The only two writes this
package can ever do are T1: **reversible, dry-run by default, backed up
before applied, rolled back on demand** — and mechanically incapable of
capping cooling (a fan curve that does not end at full speed is refused
before any write). Everything else (NVRAM, flashing) has no call path.

## Quick start

```bash
./install.sh                                # user-level install (Omarchy / Arch)
omarchy-firmware audit status               # real machine: full inventory
omarchy-firmware diag quick                 # passive thermal check (~1 s)
omarchy-firmware diag storage --json        # disks + PCIe links (vol. 4)
omarchy-firmware diag gpu                   # Xid, BAR1, thermal slowdown
omarchy-firmware diag ram                   # XMP/EXPO evidence, EDAC
omarchy-firmware diag settings              # SVM, IOMMU, EPP, fan mode
omarchy-firmware cpu epp set balance_performance   # T1 DRY-RUN (plan only)
omarchy-firmware cpu epp set balance_performance --confirm  # apply + backup
omarchy-firmware fans curve set --file curve.json   # T1 DRY-RUN
```

Try everything **without any hardware** — 8 pre-recorded thermal scenarios
(5950X physics), 3 board fixture sets (issues + clean), a 177-check test
suite, and an MCP conformance smoke:

```bash
omarchy-firmware diag scenarios             # the list
omarchy-firmware diag quick --scenario no-paste --json
omarchy-firmware selftest                   # full demo
python3 tests/test_suite.py                 # 177 checks, zero dependency
python3 tests/mcp_smoke.py                  # MCP handshake + T1 dry-run proof
```

Wire an agent (MCP):

```bash
pip install mcp                             # or: pacman -S python-mcp
claude mcp add omarchy-firmware -- ~/.local/bin/omarchy-firmware-mcp
```

## Frugality is a hard constraint, measured

The firmware must never become heavier than the stock BIOS. It isn't:

| Budget item | Cost |
|---|---|
| One-shot diagnostic (passive) | ~0.3 s CPU, no resident process |
| RAM between runs | 0 (the doctor is a one-shot) |
| Optional systemd timer (15 min) | ~0.03 % duty cycle |
| SPI flash added | **+0 bytes** |
| LLM | never resident — called only when L2 says "attention" or "critical" |

No daemon, no embedded model, no framework. Stdlib-only for the CLI;
`mcp` is an optional dependency.

## Architecture in one glance

```
13 agent harnesses             ← unchanged
   │  MCP stdio
omarchy-firmware-mcp           ← typed wrapper: declared tier, structural refusals,
                                 T1 dry-run by default (confirm = second key)
   │
omarchy-firmware (CLI)         ← functional reference, # omarchy:* metadata
   │
lib/firmware_hal/              ← T0 collectors + T1 actions + journal + CVE KB
   │
dmidecode · efibootmgr · fwupd · smartctl · lspci · nvidia-smi · hwmon · snapper
```

One function = one CLI command = one MCP tool. The agent is never a privileged
path: a human types the same thing, a shell script too.

## The tier contract

```
T0  read-only + diagnostics, journaled             ← THIS REPO (9 tools)
T1  reversible writes (EPP, fan curves)            ← THIS REPO (2 tools):
                                                   dry-run default, confirm key,
                                                   backup store, undo
T2  NVRAM/capsule writes (stage, rollback)         declared, refused — Phase 4
T3  physical flash (EZ Flash)                      never the agent: it produces the
                                                   walkthrough, the human executes
```

Project rule: no tool enters the server without its declared tier and its
out-of-scope refusal test. The declared T2 tools answer `REFUSED` with the
exact reason; `fw.flash.write` does not even exist.

## Documentation

| Document | Content |
|---|---|
| [AGENTS.md](AGENTS.md) | how AI agents operate in this repo — read this first |
| [docs/architecture.md](docs/architecture.md) | layers, contract, fixtures, one-implementation-three-consumers |
| [docs/security-doctrine.md](docs/security-doctrine.md) | tiers, error sources, barriers, the 8 rules |
| [docs/t1-write-layer.md](docs/t1-write-layer.md) | the two-key rule, rollback store, mechanical curve guards |
| [docs/diagnostics-catalog.md](docs/diagnostics-catalog.md) | the named hardware findings and their measurable evidence |
| [docs/frugality.md](docs/frugality.md) | the resource budget, L1/L2/L3, why the timer is optional |
| [docs/research/](docs/research/) | the four original study volumes (FR, PDF) + English summaries |

CI runs the full contract suite (Python 3.11/3.13) and the MCP conformance
smoke on every push — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Roadmap

| Phase | Content | Exit criterion |
|---|---|---|
| P1 | 4 T0 tools + skill + journal | 10 state questions without any write ✓ |
| P2 | + `fw.diag.thermal`: signature engine, probe, baseline, timer | 8 scenarios named one by one, measured frugality ✓ |
| **P3 — this repo** | + storage/GPU/RAM/settings T0 diagnostics + the T1 HAL (`cpu.epp.set`, `fans.curve.set`) | 177 checks, MCP 11-tool conformance, verified rollback, mechanical curve guards ✓ |
| P4 | supervised loop: CVE watch, T2 staging | 5 days of loop without false positive nor unconfirmed write |

## Provenance

Everything here descends from a four-volume study (*Beyond the BIOS*, in
French) auditing the Omarchy repo, the AM4 vendor BIOS landscape, and the
question "what can an agent do that the vendor BIOS cannot?" — see
[docs/research/](docs/research/). The reference test platform is a Ryzen 9
5950X + RTX 3070 on ASUS B450/B550; the board is **never** hardcoded — it is
read from SMBIOS at run time.
