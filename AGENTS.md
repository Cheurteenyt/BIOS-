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
   everything (T0). You may propose actions with evidence and next steps. You
   never execute a write that the current phase does not implement — and the
   current phase (P2) implements none.
3. **Leave the system as you found it.** Reads are journaled, nothing else
   changes. No background daemon, no enabled timers, no side effects outside
   `~/.local/state/omarchy-firmware/`.

## 1. Repo layout (what lives where)

```
bin/                     entry points, one per tool, with # omarchy:* metadata
lib/firmware_hal/        the base: tiers, journal, collectors, diagnostics, CLI, MCP server
agents/skills/firmware/  the skill — conduct rules consumed by harnesses
etc/systemd/user/        one-shot service + timer (NEVER enabled by install)
tests/                   fixtures (2 ASUS boards) + 8 thermal scenarios + test suite
tests/test_suite.py      82 checks, stdlib only — must pass before any push
docs/                    architecture, security doctrine, diagnostics catalog, frugality
docs/research/           the four study volumes the code descends from
```

## 2. The tier contract is frozen

`lib/firmware_hal/tiers.py` declares nine tools with their tier (T0-T3).
Rules that govern any change:

- A new tool enters `TOOL_TIERS` **with its tier** and a refusal test
  (out-of-scope tools must raise `TierRefused`).
- Implemented T0 tools are listed in `IMPLEMENTED_T0`; anything else refused
  with the exact reason, never a silence.
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
python3 tests/test_suite.py        # 82 checks — must print "82/82 tests PASS"
python3 bin/omarchy-firmware selftest
```

- Every scenario in `tests/fixtures/scenarios/` must make the engine name THE
  fault it encodes (`no-paste` → `interface-degraded` + `instant-rise`…), not
  a catch-all list.
- Every declared-but-unimplemented tool must keep its refusal test.
- Before any push: suite green, `selftest` clean, no new dependency.

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
- Remedies are proposed, never applied: paste, dusting, PWM curves, BIOS
  updates are human gestures (T1 hardware / T3 guided walkthrough).
- Report format: **proven** (SMBIOS fields, hwmon readings) / **inferred**
  (CVE statuses, R_th, signatures) / **unknown** (permissions, absent
  sensors). Never assemble confidence out of assumptions.
