# Architecture — one implementation, three consumers

This document explains how the base is put together and why each seam sits
where it sits. It condenses volume 2 of the study (the agent and the
firmware) into repo-level engineering terms.

## The five layers

```
┌────────────────────────────────────────────────────────────┐
│ L5  agents (13 harnesses)                                  │
│     claude · codex · opencode · fireworks · …              │
├────────────────────────────────────────────────────────────┤
│ L4  MCP server (mcp_server.py)                             │
│     typed tools · declared tiers · stdio JSON-RPC          │
├────────────────────────────────────────────────────────────┤
│ L3  CLI (cli.py + bin/)                                    │
│     functional reference · # omarchy:* metadata · --json   │
├────────────────────────────────────────────────────────────┤
│ L2  HAL (lib/firmware_hal/)                                │
│     collectors · journal · diagnostics engine · CVE KB     │
├────────────────────────────────────────────────────────────┤
│ L1  system (read-only)                                     │
│     dmidecode · efibootmgr · fwupdmgr · snapper · hwmon    │
└────────────────────────────────────────────────────────────┘
```

Layer L1 is never reached other than by reading. The kernel layer of
volume 2 (fig. 6.1) — efivarfs, NVRAM, SPI flash — has no code path here at
all. That absence is the security model (see
[security-doctrine.md](security-doctrine.md)).

## The seams

### One function = one CLI command = one MCP tool

Every capability is implemented once, in `lib/firmware_hal/`, exposed twice:
as a CLI subcommand (the human/reference surface) and as an MCP tool (the
agent surface, a JSON dump of the same dict). There is no agent-only code
path: a human typing `omarchy-firmware audit status` and an agent calling
`fw.audit.status` execute the same function through the same `_guard` flow.

`_guard` is the single pipeline for T0: check the tier → execute → journal
the call (ok or error) → emit (human or `--json`). T1 calls go through
`_guard_t1`: same journaling, but the status carries the two-key outcome
(`dry-run` / `applied` / `rolled-back` / `refused`). Anything that bypasses
the guards would bypass journaling; code review and tests both enforce that
nothing does.

### Fixtures over hardware

Every collector accepts a fixture directory; when present, expected tool
output is read from disk instead of executed (`system.py`). Three board
fixture sets (ASUS TUF B450-PLUS GAMING "issues" — BIOS 3644/2026 — with
every P3 fault encoded; the same board "clean" — zero findings expected;
ASUS ROG STRIX B550-F, BIOS 3001/2023) plus eight pre-recorded thermal
scenarios (5950X + 240 mm AIO physics) make the whole base — including the
CVE reasoning, the diagnostic engine and the T1 dry-run plans — fully
exercisable on any machine:

- development without hardware;
- CI without hardware;
- acceptance without hardware (`FW_FIXTURE_DIR`, `FW_DIAG_SCENARIO`);
- reproducible demo (`selftest`, `diag scenarios`).

The T1 layer has its own injection point: `FW_SYSFS_CPU` and
`FW_SYSFS_HWMON` redirect the write targets to a temp sysfs tree, so the
two-key rule, the backups, the undo and the mechanical guards are all tested
without touching a real machine. The board is never hardcoded. The fixtures
exist precisely so nothing needs to be.

### The access journal

`journal.py` appends one JSONL line per call to
`$XDG_STATE_HOME/omarchy-firmware/journal.jsonl`: timestamp, tool, tier,
argv, status, fixture flag, one-line summary. Reads are journaled like
writes would be — the journal is the first brick of accountability, and the
substrate of the future T1/T2 confirmation gates (an action can only be
confirmed against a dated trail of what was seen).

### The CVE knowledge base

`data/cve_am4.json` encodes the timeline of volume 1, chapter 5: fTPM
stutter (2022), LogoFAIL (2023), Sinkclose CVE-2023-31315 (2024),
VU#382314 / CVE-2025-14302+ (2025), CVE-2026-6726/6727 (2026). Each entry
carries an optional `fixed_from_bios_date`; the tool compares the SMBIOS
BIOS date and produces a **status + rationale** pair where the rationale is
always displayed. Date-based inference, owned as such.

### The diagnostics engine

`diagnostics.py` normalizes all hwmon chips into one canonical sample
(`tctl`, `ambient`, `coolant`, `vrm`, `power_w`, `fans`, `volts`, `phase`)
and applies twelve deterministic signatures (S1-S12):

| # | Signature | Fault named |
|---|---|---|
| S1 | pump RPM ≈ 0 under heat | `pump-dead` |
| S2 | fan head at 0 RPM | `fan-zero-rpm` |
| S3 | coolant − ambient ≥ 15 °C | `coolant-hot` |
| S4 | R_th ≥ 0.42-0.55 °C/W (steady state) | `interface-degraded` |
| S5 | idle ΔT ≥ 25 °C (weak signal) | `interface-degraded` (low confidence) |
| S6 | 85 °C reached < 8 s under load | `instant-rise` |
| S7 | sustained slope ≥ 0.5 °C/s near Tjmax | `runaway` |
| S8 | plateau ≥ Tjmax with measured power fold-back | `thermal-protection-active` |
| S9 | VRM ≥ 89 °C | `vrm-hot` |
| S10 | +12 V rail < 11.40 V | `v12-low` |
| S11 | generic sensor ≥ 85 °C | `hot-sensor` |
| S12 | R_th or ΔT drift ≥ 25 % over ≥ 7 days | `gradual-degradation` |

Steady-state values (R_th, medians) are computed on the last 60 % of the
load window — the definition of a thermal resistance, not the ramp.
Anti-double-diagnosis: a dead pump explains the resistance, so
`interface-degraded` is suppressed when the pump is dead. Every finding
carries: id, severity, title, quantified evidence, hypothesis, next steps,
confidence (high/medium/low).

Three consumption modes: passive `quick` (~1 s), active `probe` (controlled
load on half the cores, 10-120 s, 1 Hz sampling, bounded and self-terminating),
and the optional longitudinal timer. The baseline (`baseline.json`, XDG
state) keeps 200 entries of dated measurements — the thermal memory the BIOS
does not have, and the substrate of S12.

## The P4 seams — watch, staging, report

Phase 4 adds three seams without touching the existing ones:

- **cve_watch.py** sits on top of `cve_kb` (freshness, drift baseline in
  XDG state) and `fwupd` (advisory cross-check). It reads only; the KB
  override precedence lives in `cve_kb.load_kb()` — XDG override first,
  packaged fallback, corrupt override never crashes a tool.
- **stage.py / rollback.py** are the T2 layer: they reuse `fwupd`'s
  device/update parsing, add the gate engine and the transaction record,
  and are reachable from the CLI only. The fwupdmgr binary is injectable
  (`FW_FWUPD_BIN`) so tests stay hermetic; fixture mode without the
  injection refuses to execute anything.
- **report.py** reads the journal as a view (no self-journaling) — the
  one-implementation-three-consumers rule does not extend to it: a
  report has no MCP tool by design, the CLI is the single consumer.

## Versioning and compatibility

- `firmware_hal.__version__` tracks the package; `PHASE` names the current
  scope in one phrase (`P4 — supervised loop: CVE watch + human-gated T2
  staging`).
- Tool output dicts are the API: renaming a key is a breaking change and
  must land together with `tests/test_suite.py` updates.
- Tested on Python 3.11+ (CI runs the suite on 3.11 and 3.13); no compiled
  dependency; runs anywhere dmidecode, efibootmgr and hwmon exist — and
  reports honestly where they do not.
