# AGENTS.md — how AI agents operate in this repository

This repo is built agent-first, in the spirit of the Omarchy conventions
(`CLAUDE.md` → `@AGENTS.md`, skills, `# omarchy:*` CLI metadata). If you are
an AI agent (claude, codex, opencode, or any MCP harness) working **in this
codebase** or **through its tools**, this file is your contract. Read it
before your first commit and before your first `fw.*` call.

## 0. The three laws

1. **Work from evidence.** Never reason from a guessed platform. The board is
   read from SMBIOS (dmidecode) at run time; hardware state comes from hwmon,
   efibootmgr, fwupd. "Undetermined" is an honest verdict; an invented
   conclusion is a defect.
2. **The agent proposes, the HAL disposes, the human decides.** You may read
   everything (T0). You may propose actions with evidence and next steps.
   The current phase (P5) implements exactly two T1 writes — `cpu.epp.set`
   and `fans.curve.set` — both **dry-run by default**: without an explicit
   confirm flag (`--confirm` / `confirm: true`) they return the plan and
   write nothing. Only request `confirm` after the human has seen the plan.
   The T2 layer is **human-only on the CLI**: you may prepare a staging plan
   (`update stage --device GUID`, dry-run) but `--confirm` is typed by the
   human, and `fw.rollback` is a refusal-by-design. Flashing (T3) has no
   call path at all.
3. **Leave the system as you found it.** Reads are journaled, nothing else
   changes. No background daemon, no enabled timers, no side effects outside
   `~/.local/state/omarchy-firmware/`.

## 1. Repo layout (what lives where)

```
bin/                     entry points, one per tool, with # omarchy:* metadata
lib/firmware_hal/        the base: tiers, journal, collectors, diagnostics,
                         T1 actions, T2 staging, KB watch/updater, twin
                         (TWIN-1 + rehearsal), CLI, MCP server
agents/skills/firmware/  the skill — conduct rules consumed by harnesses
etc/systemd/user/        one-shot services + timers (NEVER enabled by install)
tests/                   fixtures (3 board sets: issues + clean) + twin-sysfs
                         + 12 thermal scenarios + test suite + MCP smoke
tests/test_suite.py      287 checks, stdlib only — must pass before any push
tests/mcp_smoke.py       MCP conformance: handshake, 12 tools, T1 dry-run
docs/                    architecture, security doctrine, write layers (T1+T2),
                         diagnostics catalog, digital twin, vendor BIOS
                         heritage, frugality, first-run protocol
docs/research/           the four study volumes the code descends from
.github/workflows/ci.yml the CI: contract suite (py 3.11/3.13) + MCP smoke
```

## 2. The tier contract is frozen

`lib/firmware_hal/tiers.py` declares fourteen tools with their tier (T0-T3).
Rules that govern any change:

- A new tool enters `TOOL_TIERS` **with its tier** and a refusal test
  (out-of-scope tools must raise `TierRefused`).
- Implemented T0 tools are listed in `IMPLEMENTED_T0`; implemented T1 tools
  in `IMPLEMENTED_T1`. Anything else is refused with the exact reason,
  never a silence. T2 refusals carry their `T2_HINTS` pointer (the human
  CLI path) — keep them true when the CLI moves.
- T1 code lives in `lib/firmware_hal/actions.py` and obeys the two-key
  rule: dry-run default, explicit `confirm` to write, backup before write,
  undo through the rollback store. See [docs/t1-write-layer.md].
- T2 code lives in `lib/firmware_hal/stage.py` (staging gates, transaction
  record, cancel) and `rollback.py` (refusal-by-design + inventory). T2 is
  NEVER added to the MCP surface: the agent prepares, the human applies.
  The KB updater (`kb_update.py`) applies the same two-key rule to DATA:
  stage, then `--confirm --sha256` with the shown hash.
- `FORBIDDEN_FOREVER` (`fw.flash.write`, `fw.nvram.raw.write`) has no call
  path, not even an elegant refusal. Do not add one.
- Writing to efivarfs, reordering efibootmgr entries, disabling Secure Boot,
  or running `flashrom` in write mode are prohibited to agents even via
  direct shell commands. If a task seems to need one, stop and ask a human.

## 3. Code conventions

- **One function = one CLI command = one MCP tool.** The CLI is the single
  functional reference; the MCP server is a typed wrapper around it. If you
  add a capability, wire it through `cli.py` `_guard` (which journals) —
  never around it.
- **Stdlib only** for `lib/` and `tests/`. `mcp` stays an optional import
  (lazy, with a clean error message).
- **Fixtures over hardware.** Any collector must accept `--fixture-dir` /
  `FW_FIXTURE_DIR` and run on `tests/fixtures/`. Any diagnostic must run on
  bundled scenarios. Tests never require real hardware.
- **Journal everything.** Every T0 call appends to the access journal
  (`journal.record`), including failures.
- **Honesty in output.** Errors are reported per-section, tolerating missing
  pieces; unknown means unknown; inference is labelled as inference.

## 4. Testing discipline

```bash
python3 tests/test_suite.py        # 287 checks — must print "287/287 tests PASS"
python3 tests/mcp_smoke.py         # MCP conformance (needs the optional mcp pkg)
python3 bin/omarchy-firmware selftest
omarchy-firmware rehearse --backend twin   # 28 probes — must print "green"
```

Day-0 instruments (CLI-only, the 12-tool MCP surface is frozen):
`rehearse-diff --latest` grades the twin → real debrief (clean/review,
surprises named and classified) and `capture` photographs the machine
(read-only, provenance-tagged).

- Every scenario in `tests/fixtures/scenarios/` must make the engine name THE
  fault it encodes (`no-paste` → `interface-degraded` + `instant-rise`…), not
  a catch-all list. Same discipline for the storage/GPU/RAM fixtures: the
  fixture set encodes the faults, the clean set must produce zero findings.
- Every declared-but-unimplemented tool must keep its refusal test — including
  the T2 refusals naming their human path.
- Every T1 behavior must be tested on a temp sysfs tree (`FW_SYSFS_CPU`,
  `FW_SYSFS_HWMON`): dry-run writes nothing, confirm writes + backs up,
  undo restores, mechanical guards refuse.
- Every T2 staging behavior must be tested with `FW_FWUPD_BIN` pointing at a
  fake fwupdmgr: gates, refusal without reason, staged transaction, cancel,
  and the fwupd-failure path. Fixture mode without `FW_FWUPD_BIN` refuses to
  execute anything.
- CI (`.github/workflows/ci.yml`) runs the suite on Python 3.11 and 3.13
  plus the MCP smoke on every push — a red CI is a broken contract.
- The dress rehearsal (`rehearse`, 28 probes) must stay **green on TWIN-1**:
  it is the executable form of this whole discipline. Its no-write
  guarantee is enforced by a scan — the human-confirm flag may appear only
  in `stage-confirm-refused`, where refusal IS the expected outcome. If you
  add a probe, add its counterpart assertion, and keep ids stable (reports
  are diffed across machines).
- Before any push: suite green, smoke green (where `mcp` is installed),
  `selftest` clean, no new dependency.

## 5. Commits and PRs

- Small, single-purpose commits; imperative subject (`Add S12 trend
  signature`, not `misc`).
- Any behavior change to tool output must update `tests/test_suite.py` in the
  same commit.
- Documentation lives next to code: a new tool without its README table row,
  its SKILL.md mention and its docs update is an incomplete commit.

## 6. When running the tools on a real machine

- Prefer `--json` output and cite the evidence fields verbatim
  (`r_th`, `delta`, `pump_rpm`, `power_fold_x`).
- The active probe (`diag probe`) deliberately loads half the cores for a
  bounded time (10-120 s). Ask the human first; warn that the machine will
  heat for a minute; the BIOS thermal protection remains the final guard.
- Remedies are proposed, never applied unilaterally: paste, dusting, BIOS
  updates are human gestures. The two T1 writes exist because they are
  reversible; even then: dry-run first, show the plan, ask, then `--confirm`.
  For staging, prepare the plan (`update stage --device GUID`) and hand the
  `--confirm` command to the human with the reason spelled out.
- After any T1 write, verify the result with the matching T0 read
  (`diag settings` for EPP, `fans curve show` for curves) and offer the undo
  before leaving.
- Report format: **proven** (SMBIOS fields, hwmon readings) / **inferred**
  (CVE statuses, R_th, signatures) / **unknown** (permissions, absent
  sensors). Never assemble confidence out of assumptions.
