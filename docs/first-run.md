# First run & the 5-day supervised loop — the P4 exit protocol

This is the runbook for the first real week on the target machine
(Ryzen 9 5950X + RTX 3070, ASUS B450/B550, Omarchy). It has two parts:
**Day 0** installs and drills everything in a controlled way, and
**Days 1–5** run the supervised loop whose exit criterion is the P4 one:
*five days of loop without a false positive nor an unconfirmed write.*

Read [AGENTS.md](../AGENTS.md) and [docs/security-doctrine.md](security-doctrine.md)
first if you have not: nothing below will surprise you then. The tone of
this document is deliberate — every step is either a read (free), a
reversible write with its undo typed alongside, or a human decision that
the tooling refuses to take for you.

---

## Step −1 — the dress rehearsal (before the machine, any host)

The whole day-0 surface is executable without the target machine — that
is what TWIN-1, the digital twin, is for (see
[docs/digital-twin.md](digital-twin.md)). Run it once wherever you are:

```bash
omarchy-firmware twin                        # the profile + resolved assets
omarchy-firmware rehearse --backend twin     # 28 probes, expect: green
```

Expect `verdict: green — 28 pass, 0 fail, 0 skip` and a JSON report under
`~/.local/state/omarchy-firmware/rehearse/`. Keep it: on day 0 you run
the same command with `--backend real` and **diff the two reports** —
what changed between the twin and the machine is your list of real
surprises, already named.

Day 0 below remains the authority for the manual gestures (the T1
confirm key, the T2 human layer, the sensor reality check) — the
rehearsal proves the contract, the machine proves the truth.

---

## Day 0 — install, baseline, drills

### 0.1 Install (user-level, nothing root, nothing resident)

```bash
curl -fsSL https://raw.githubusercontent.com/Cheurteenyt/BIOS-/main/install.sh \
  | bash -s -- --from release
```

The installer floats, the payload is pinned: the tagged tarball is fetched
and verified against its published `SHA256SUMS` before anything runs, and
the provenance (tag + digest) is echoed — quote it in the day-0 log.
Development alternative: `git clone https://github.com/Cheurteenyt/BIOS-.git
omarchy-firmware && cd omarchy-firmware && ./install.sh` (floating main).

`install.sh` copies bins to `~/.local/bin`, the self-contained library
and TWIN-1 to `~/.local/share/omarchy-firmware/` (lib + twin), the skill
to `~/.config/omarchy/agents/skills/firmware/`, and the systemd units
**disabled**. It never enables a timer and never touches the ESP or
NVRAM.

Sanity checks:

```bash
omarchy-firmware tiers          # the 15-tool contract prints
omarchy-firmware selftest       # full twin demo, exit 0
omarchy-firmware capture --live # day-0 photograph BEFORE anything else —
                                # the REAL machine: twin assets ignored
omarchy-firmware rehearse       # day-0 drill: 28 probes on THIS machine
omarchy-firmware rehearse-diff --latest   # twin → real: the named surprises
python3 tests/test_suite.py     # 323 checks (run from the clone)
python3 tests/mcp_smoke.py      # needs pip install 'mcp>=1.0,<2'

# OPTIONAL deep probe — one step beyond the runtime frontier (see
# docs/spi-map.md). Reads the flash chip (root, flashrom), writes NOTHING.
# Not part of the day-0 protocol: a declared gesture, run when wanted.
sudo omarchy-firmware spi-map --save-dump day0-spi.bin   # + sha256 it
```

### 0.2 The T0 sweep — the honest baseline

Run the full read sweep once, in this order, and KEEP the outputs (they
are the "before" picture for the whole week):

```bash
omarchy-firmware audit status   --json | tee 01-audit-status.json
omarchy-firmware audit cve      --json | tee 02-audit-cve.json
omarchy-firmware audit cve-watch --json | tee 03-cve-watch.json
omarchy-firmware boot inspect   --json | tee 04-boot.json
omarchy-firmware update check   --json | tee 05-update.json
omarchy-firmware diag quick     --json | tee 06-thermal-passive.json
omarchy-firmware diag storage   --json | tee 07-storage.json
omarchy-firmware diag gpu       --json | tee 08-gpu.json
omarchy-firmware diag ram       --json | tee 09-ram.json
omarchy-firmware diag settings  --json | tee 10-settings.json
```

Expected reality checks (the tools are honest, so should you be):

- `audit status`: board **read from SMBIOS** — never assume it matches
  this repo's fixtures; the BIOS date feeds the CVE reasoning.
- `update check` + `diag gpu`: on desktop AM4 the motherboard is absent
  from LVFS — that is the documented coverage gap, reported as such, not
  an error.
- `diag settings`: anything not observable from the OS lands under
  `needs_bios_check` — it means "look in the UEFI setup screen", never a
  guess.

### 0.3 The active thermal probe (one minute, intentional heat)

```bash
omarchy-firmware diag probe --seconds 30 --json | tee 11-thermal-probe.json
```

The machine heats for half a minute on purpose; the BIOS thermal
protection stays the final guard rail. This is the measurement that
distinguishes a healthy loop (R_th ≈ 0.25–0.35 °C/W on a 5950X with a
decent AIO) from degraded paste or mounting (≈ 0.6 and above, vol. 3).

### 0.4 The T1 drill — reversible writes, proven not promised

Do one full dry-run → apply → verify → undo cycle on the most harmless
target (EPP):

```bash
omarchy-firmware cpu epp set balance_performance --json          # plan only
omarchy-firmware cpu epp set balance_performance --confirm --json # apply + backup
omarchy-firmware diag settings --json                             # verify: the new value shows
omarchy-firmware cpu epp undo --confirm --json                    # restore
omarchy-firmware diag settings --json                             # verify: back to the original
```

Then look at the trace:

```bash
omarchy-firmware journal 12
```

You should see, in order: `dry-run`, `applied`, `rolled-back` — each
with its timestamp. This journal IS the "no unconfirmed write" evidence
for the whole week.

Optional (only if an nct67xx Super I/O is detected by `fans curve show`):
a fan-curve dry-run with the mechanical guard visible — **no
`--confirm` on day 0**. The curve gets its confirm on day 2 at the
earliest, after the loop has observed idle/load transitions.

### 0.5 The T2 drill — staging, a human gesture

First, what the agent may do: prepare the plan.

```bash
# list the GUIDs from update check / fwupdmgr get-devices --json, then:
omarchy-firmware update stage --device <GUID> --json | tee 12-stage-plan.json
omarchy-firmware update rollback --json | tee 13-rollback-inventory.json
```

Expected on this platform:

- for the **motherboard** GUID: refused, with the AM4 LVFS gap and the
  human path (EZ Flash) named — this is the honest answer, not a bug;
- for any LVFS-managed device (an NVMe SSD in the fixtures): a full plan
  with gates, the exact command and the rollback reality;
- `update rollback` always answers with the inventory and states plainly
  that firmware rollback is not a runtime operation on single-BIOS AM4.

**Do not pass `--confirm` on day 0.** Staging exists for the day a
firmware update is actually motivated (a CVE fix, a vendor bug you can
name). When that day comes, the sequence is the human's:

```bash
omarchy-firmware update stage --device <GUID> --reason '<the why>' --confirm
omarchy-firmware update stage --cancel        # only if you change your mind, BEFORE rebooting
```

### 0.6 Wire the agent (MCP)

```bash
pip install mcp                                # or: pacman -S python-mcp
claude mcp add omarchy-firmware -- ~/.local/bin/omarchy-firmware-mcp
```

Then, in the agent, ask the twelve questions the tools answer (audit
status first — the skill enforces it). The agent can read everything,
prepare T1/T2 plans, and apply nothing: T1 confirm and T2 confirm are
typed by the human on the CLI.

### 0.7 Enable the loop (an explicit choice, reversible)

```bash
systemctl --user enable --now omarchy-firmware-doctor.timer   # T0 diag, 15 min
systemctl --user enable --now omarchy-firmware-watch.timer    # CVE watch, weekly
systemctl --user list-timers 'omarchy-firmware*'
```

Cost reminder: the doctor is a one-shot (~0.3 s of CPU per run, zero RAM
between runs, ~0.03 % duty cycle at 15 min). Disable any time with
`systemctl --user disable --now ...` — the loop is a choice, not an
installation artifact.

---

## Days 1–5 — the supervised loop

### The daily gesture (2 minutes)

```bash
omarchy-firmware report --json | tee report-day$N.json
omarchy-firmware journal 40                    # skim the day's trace
```

What the report gives you: calls per day and per tool, statuses
(dry-run / applied / staged / rolled-back / refused / refused-by-design),
errors, KB age, T1 rollback frames, any pending staging transaction.

### What "false positive" means here, concretely

Each day, list the findings the loop raised (`diag quick` summaries in
the journal) and mark each one against reality:

- a finding that names a fault the machine does not have after manual
  verification (e.g. "interface-degraded" but the loop is demonstrably
  healthy) → a false positive: note the date, the finding id, the
  evidence fields, and what the manual check showed;
- an "undetermined" verdict is NOT a false positive by itself — note it
  as an honest result unless its *stated reason* is wrong.

### The two bookkeeping rules

1. **No T1 confirm without its preceding dry-run in the journal the same
   day.** The two-key rule is also a review habit: plan first, apply
   second, verify third, undo offered every time.
2. **OneKB decision point**: when the weekly watch (or you) finds the
   KB stale or a fwupd advisory unknown to it, refresh deliberately:

```bash
omarchy-firmware-cve-update --status
omarchy-firmware-cve-update --file <new-kb.json>        # stage: shows the sha256
omarchy-firmware-cve-update --file <new-kb.json> \
    --confirm --sha256 <the-shown-hash>                 # activate
omarchy-firmware audit cve-watch --json                 # drift names what changed
omarchy-firmware-cve-update --revert                    # if unhappy: one command back
```

### The day-5 checklist (the P4 exit criterion)

| Criterion | Evidence to collect |
|---|---|
| 5 days of loop | `systemctl --user status omarchy-firmware-doctor.timer` + 5 report files |
| no false positive | your day-by-day annotations: every finding verified, none contradicted by reality (or: the ones that were, analyzed) |
| no unconfirmed write | the journal: every `applied`/`staged` entry is preceded by its `dry-run` and followed by a T0 verification; zero `applied` without confirm |
| reversibility demonstrated | at least one full apply → undo cycle (EPP drill), rollback frames visible in the report |
| refusals behave | the board staging refusal, the unknown-GUID refusal, the second-cancel refusal — each journaled with its reason |

If all five lines hold, P4 exits on evidence, not on promise — and the
loop keeps running as the permanent, frugal watch it was designed to be.

### What to send back

After day 5, gather:

```bash
omarchy-firmware report --days 7 --json > p4-week-report.json
omarchy-firmware journal 400 > p4-week-journal.txt
```

…plus your false-positive annotations and anything that felt wrong.
Those three artifacts are the P4 review.
