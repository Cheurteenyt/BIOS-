# Beyond the BIOS — an agent ↔ firmware bridge for Omarchy

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

## What it does today (5 tools, all T0 = read-only)

| MCP tool | CLI | Answers |
|---|---|---|
| `fw.audit.status` | `omarchy-firmware audit status` | "Where does my firmware stand?" — board, BIOS, socket, boot, fwupd, sensors |
| `fw.audit.cve` | `omarchy-firmware audit cve` | "Am I exposed to LogoFAIL?" — BIOS version vs known AM4 CVEs (fTPM stutter, LogoFAIL, Sinkclose, VU#382314, CVE-2026-6726/6727) |
| `fw.boot.inspect` | `omarchy-firmware boot inspect` | "Is my boot chain healthy?" — efibootmgr, UKI/Limine detection, Snapper snapshots |
| `fw.update.check` | `omarchy-firmware update check` | "Any updates?" — local fwupd state, 15-min cache, no network |
| `fw.diag.thermal` | `omarchy-firmware diag quick` | "Why is it hot?" — pump, paste/mounting (R_th), radiator fan, VRM, 12 V, long-term drift |

Every call — even reads — is appended to an access journal
(`~/.local/state/omarchy-firmware/journal.jsonl`): the agent cannot touch the
firmware side without leaving a dated, replayable trace.

## The one-sentence theses

> **The agent proposes, the HAL disposes, the human decides.**
> **What the BIOS cannot name, the agent names — at zero extra cost.**

The base *structurally* cannot write: there is no write code path in this
package. That is the guarantee, not a temporary limitation.

## Quick start

```bash
./install.sh                                # user-level install (Omarchy / Arch)
omarchy-firmware audit status               # real machine: full inventory
omarchy-firmware diag quick                 # passive thermal check (~1 s)
omarchy-firmware diag probe --seconds 30    # active: time constant (bounded load)
```

Try everything **without any hardware** — 8 pre-recorded thermal scenarios
(5950X physics), 2 complete board fixtures, a 82-check test suite:

```bash
omarchy-firmware diag scenarios             # the list
omarchy-firmware diag quick --scenario no-paste --json
omarchy-firmware selftest                   # full demo
python3 tests/test_suite.py                 # 82 checks, zero dependency
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
omarchy-firmware-mcp           ← typed wrapper: declared tier, structural refusals
   │
omarchy-firmware (CLI)         ← functional reference, # omarchy:* metadata
   │
lib/firmware_hal/              ← T0 collectors + journal + diagnostics + CVE KB
   │
dmidecode · efibootmgr · fwupd · /sys/class/hwmon · snapper
```

One function = one CLI command = one MCP tool. The agent is never a privileged
path: a human types the same thing, a shell script too.

## The tier contract

```
T0  read-only + diagnostics, journaled             ← THIS REPO (P2)
T1  reversible writes (EPP, fan curves)            dry-run, saved profile, rollback
T2  NVRAM/capsule writes (stage, rollback)         human confirmation, tool by tool
T3  physical flash (EZ Flash)                      never the agent: it produces the
                                                   walkthrough, the human executes
```

Project rule: no tool enters the server without its declared tier and its
out-of-scope refusal test. The declared T1/T2 tools answer `REFUSED` with the
exact reason; `fw.flash.write` does not even exist.

## Documentation

| Document | Content |
|---|---|
| [AGENTS.md](AGENTS.md) | how AI agents operate in this repo — read this first |
| [docs/architecture.md](docs/architecture.md) | layers, contract, fixtures, one-implementation-three-consumers |
| [docs/security-doctrine.md](docs/security-doctrine.md) | tiers, error sources, barriers, the 8 rules |
| [docs/diagnostics-catalog.md](docs/diagnostics-catalog.md) | the 18 named hardware findings and their measurable evidence |
| [docs/frugality.md](docs/frugality.md) | the resource budget, L1/L2/L3, why the timer is optional |
| [docs/research/](docs/research/) | the four original study volumes (FR, PDF) + English summaries |

## Roadmap

| Phase | Content | Exit criterion |
|---|---|---|
| P1 | 4 T0 tools + skill + journal | 10 state questions without any write ✓ |
| **P2 — this repo** | + `fw.diag.thermal`: signature engine, probe, baseline, timer | 8 scenarios named one by one, 82 tests, measured frugality ✓ |
| P3 | full T1 HAL: `cpu.epp.set`, `fans.curve.set` | 100 % of writes through the HAL, verified rollback |
| P4 | supervised loop: CVE watch, T2 staging | 5 days of loop without false positive nor unconfirmed write |

## Provenance

Everything here descends from a four-volume study (*Beyond the BIOS*, in
French) auditing the Omarchy repo, the AM4 vendor BIOS landscape, and the
question "what can an agent do that the vendor BIOS cannot?" — see
[docs/research/](docs/research/). The reference test platform is a Ryzen 9
5950X + RTX 3070 on ASUS B450/B550; the board is **never** hardcoded — it is
read from SMBIOS at run time.
