# Security doctrine — omniscience in reading, chastity in writing

Giving an agent eyes on the firmware multiplies what it can do — including
what it can do **wrong**. This doctrine, distilled from volumes 2 and 4 of
the study, is how the project stays on the right side of that line. It is
implemented in code, not in intentions.

## The risk tiers

| Tier | Nature | Guard rails | Status |
|---|---|---|---|
| **T0** | reads + deterministic diagnostics + watch | journaled, read-only by construction | **implemented (10 tools)** |
| **T1** | reversible writes (EPP, fan curves) | dry-run default · confirm key · backup store · undo · mechanical curve guards · journal | **implemented (2 tools)** — see [t1-write-layer.md](t1-write-layer.md) |
| **T2** | firmware transaction (staging, rollback) | **human-only CLI**: dry-run plan by default, `--confirm` typed by the human · motivation (`--reason`) mandatory · transaction record + cancel until reboot · rollback refused by design | **implemented, outside the MCP surface (P4)** — see [t1-write-layer.md](t1-write-layer.md) |
| **T3** | physical flash (EZ Flash) | **never the agent.** It produces a dated, checksummed walkthrough; the human executes | forever human |

Structural facts of this repo (tested, not promised):

- `fw.flash.write` and `fw.nvram.raw.write` are in `FORBIDDEN_FOREVER` — no
  call path exists, not even a refusal: the tool does not exist.
- The T2 tools are not in the MCP surface at all: `fw.update.stage` refuses
  there with the exact human CLI path; `fw.rollback` is a refusal-by-design
  that answers with the rollback inventory instead of pretending. Staging
  applies at the NEXT reboot (by fwupd itself — this base never reboots),
  carries a mandatory `--reason`, and is cancellable until that reboot.
- The KB updater obeys the two-key rule on DATA: stage shows the sha256,
  `--confirm --sha256` activates, a mismatch is refused (supply-chain
  guard), `--revert` restores. A knowledge base that changed silently
  would poison every inference built on it.
- The two T1 writes enforce the two-key rule in code: without the explicit
  confirm flag they are dry-runs that touch nothing; a write always
  backs up first; undo restores. A fan curve that does not end at full
  speed is refused before any write — cooling can never be capped.
- Writing to efivarfs, reordering efibootmgr entries, disabling Secure Boot,
  flashing via `flashrom` — none of these paths exists in the base, and the
  skill instructs agents to never improvise them via shell.

## The three error sources, and the three barriers

Volume 4 formalizes where a false or harmful conclusion can come from, and
what stops it:

| Error source | Example | Barrier |
|---|---|---|
| **bad measurement** | coarse Super I/O ADC (± 3 %) reading 11.4 V on a healthy PSU | confidence levels · cross-checks (multimeter advice) · thresholds owned as orders of magnitude |
| **bad interpretation** | a high R_th blamed on paste when the pump is dying | named findings with evidence · anti-double-diagnosis · "undetermined" instead of a guess |
| **bad action** | an agent "helpfully" reordering boot entries, or staging a BIOS flash "to be safe" | T1: two keys (dry-run default + confirm), backup, undo · T2: human-only CLI, mandatory `--reason`, cancel until reboot · T3: nonexistent |

The residual risk quadrant — an action that is both **grave and
irreversible** — is kept empty **by construction**: nothing in the T1 set
(EPP, fan curves) is irreversible; staging is reversible until the human
reboots and the human is the one who reboots; firmware rollback does not
exist as a runtime operation here (refused by design, with an inventory);
and everything irreversible (flash) is outside the agent's reach forever.

## The 8 rules

1. Every tool declares its tier before it exists in the server.
2. Every read is journaled — accountability starts at read time.
3. Every finding carries evidence, hypothesis, next steps, confidence.
4. Unknown means unknown: a missing sensor is a report, never a guess.
5. Remedies are proposed, never applied by the agent.
6. The active probe is bounded (10-120 s), deliberate, announced — the BIOS
   thermal protection remains the final guard rail.
7. Escalation follows the tiers: passive first, active with human agreement,
   writes only where the HAL implements them, flash never.
8. When in doubt, stop and ask the human. "Undetermined" is a valid output.

## What this protects against, concretely

- **The misdiagnosed machine.** A wrong "it's the paste" that makes the user
  repaste for nothing — mitigated by named signatures with quantified
  evidence and confidence levels, and by the anti-double-diagnosis rules.
- **The overzealous agent.** An LLM that decides to "fix" the boot order or
  disable Secure Boot — structurally impossible from this base, and
  explicitly forbidden to improvisation by the skill.
- **The silent mutation.** A write nobody knows happened — future writes
  journal their dry-run, their saved profile and their rollback path.
- **The fishing expedition.** Undisclosed firmware reads by an agent — every
  read lands in a user-owned JSONL journal, inspectable with
  `omarchy-firmware journal`.

## Threat model notes

- The journal lives in the user's XDG state dir, like the rest; nothing runs
  as root; the MCP server is one user process on stdio (no listening port).
- Network touches are explicit human requests only: `--refresh` (LVFS
  metadata) and the KB updater `--from URL`. Nothing polls, nothing
  auto-refreshes; the weekly watch timer reads local state only.
- Fixture mode is for tests and demos — the journal marks fixture calls so a
  demo can never be mistaken for a real machine's history; fixture-mode
  staging without `FW_FWUPD_BIN` refuses to execute anything.
