# The digital twin — TWIN-1 and the dress rehearsal

> **Sept. 16 must be a replay day, not a discovery day.**
> Everything that can be rehearsed without the machine must be rehearsed
> before the machine.

The target machine (Ryzen 9 5950X, RTX 3070, ASUS B450-PLUS) is not
available for the first real session until September 16. Waiting idle
would mean discovering the tool's day-0 behaviour *on* the day — the
worst possible time to learn that an exit code surprises you or that an
installed binary cannot find its library. Phase 5 closes that gap: the
test fixtures are promoted to a first-class, installable machine profile —
**TWIN-1, the rehearsal machine** — and one command, `rehearse`, walks
the entire behavioural contract against it.

The twin is a fixture directory, not a daemon: idle when unused, +0 bytes
on any SPI flash, and never more resource-hungry than the stock BIOS.

## The profile

| Field | Value |
|---|---|
| Name | TWIN-1 |
| Story | rehearsal machine for the first real session — the vol. 1–4 reference build |
| Board | ASUS B450-PLUS GAMING (BIOS 3644, AGESA 1.2.0.12) |
| CPU | AMD Ryzen 9 5950X (16C/32T, AM4) |
| GPU | NVIDIA RTX 3070 (GSP-capable) |
| Storage | Samsung 980 PRO 1TB (NVMe) + SATA disk |
| Cooling | AIO 240 (pump + radiator fans) + chassis fans (nct6798) |
| Boot | Limine + UKI chain (Omarchy) |

`omarchy-firmware twin` prints this profile **and** where its assets
actually resolved from — so there is never a doubt about which machine
you are talking to.

## The assets

Resolution order (first match wins):

1. `$FW_TWIN_DIR` — explicit override (tests, CI, a second twin);
2. the installed twin — `~/.local/share/omarchy-firmware/twin`, staged by
   `install.sh`;
3. the repository layout — `tests/fixtures/` (development).

Three asset families:

- **Board fixture sets** — `b450-plus` (the reference, with its planted
  issues), `b450-plus-clean` (the same board without issues), `b550-f-old`
  (a frozen-support second board). Each carries the full collection set:
  dmidecode, efibootmgr, fwupd (devices/security/updates/history), sensors,
  SMART, lspci, nvidia-smi, dmesg.
- **12 thermal scenarios** — pre-recorded 5950X physics covering the whole
  signature surface S1–S12: dead pump, missing paste, dead radiator fan,
  case-fan masking, runaway slope, heatwave, hot NVMe, undetermined…
- **A sysfs tree** — a minimal `/sys` (EPP on two cpus, an nct6798 with
  three curve slots) so the T1 dry-run path exercises a *real plan* on any
  host, deterministically.

## The dress rehearsal

```
omarchy-firmware rehearse --backend twin    # against TWIN-1 (no hardware)
omarchy-firmware rehearse                   # against THIS machine (day-0)
```

28 behavioural probes, one verdict (`green` / `red`), one diffable JSON
report (`~/.local/state/omarchy-firmware/rehearse/rehearsal-*.json`,
schema `omarchy-firmware/rehearsal@1`, the last 10 kept):

| Family | Probes | Asserts |
|---|---|---|
| Contract | `contract-tiers` | the 14-tool contract displays, T2 declared |
| T0 collections | `audit-status`, `audit-cve`, `audit-cve-watch`, `boot-inspect`, `update-check` | exit 0, JSON shapes, board/chain content on the twin |
| T2 gates | `stage-plan-nvme`, `stage-board-refused`, `stage-confirm-refused`, `rollback-inventory` | dry-run plan with six gates, the AM4 gap refused with the EZ Flash path named, the motivation gate cannot be waived, rollback stays a refusal-by-design |
| Diagnostics | `diag-scenarios`, `diag-pump-dead`, `diag-no-paste`, `diag-heatwave`, `diag-undetermined`, `diag-storage/gpu/ram/settings`, `diag-live` | each scenario names THE fault and nothing else; sensorless hosts degrade honestly |
| T1 gates | `t1-epp-gate`, `t1-epp-dryrun-plan`, `t1-epp-undo-gate`, `t1-fans-gate`, `t1-fans-show` | without the human gesture: **refused (exit 2) or dry-run (exit 0) — never applied**; the twin plan carries the full diff and the backing file is untouched |
| MCP | `mcp-surface` | two contract outcomes: full stdio session (initialize, tools/list == the exact 12 contract tools, one T0 call answers) where the `mcp` SDK is installed, or the server's clean SDK-refusal (exit 1, pin named) where it is not |
| Bookkeeping | `journal-integrity`, `report-digest` | every probe left a trace; the digest answers |

Backend rule: structural expectations hold on **both** backends; content
expectations (the B450-PLUS name, the named faults) are twin-only and are
reported as an honest `skip` on real hardware. The four scenario probes
are the deliberate exception — scenario mode is deterministic, so they
must also pass on the real machine.

**The no-write guarantee is enforced by construction, and by test.** No
probe ever performs a write gesture; the only appearance of the
human-confirm flag in the whole probe set is `stage-confirm-refused`,
whose expected outcome *is* the refusal. The test suite scans
`build_probes()` and fails if that invariant ever drifts.

## Honesty — what the twin cannot prove

The twin replays recorded collections and sensor series. It proves the
*behavioural contract* (exit codes, refusals, dry-run plans, journal
lines, MCP surface). It cannot prove:

- real sensor names and their mapping (`/sys/class/hwmon` differs per board);
- real EPP presence and granularity;
- a live fwupd D-Bus and real LVFS metadata;
- ADC noise and real physics (the ±3 % sensor honesty still applies).

These are exactly what the day-0 drill measures. That division of labour
is the point: **the twin proves the tool, the machine proves the truth.**

## The P5 protocol

1. **Now (before the machine):** `install.sh`, then
   `omarchy-firmware rehearse --backend twin` → expect `green`, 28/28.
2. **Day 0 (Sept. 16, on the machine):** `omarchy-firmware capture` —
   the photograph: one read-only snapshot of what this machine really
   is (the ten T0 collections + per-cpu EPP + per-chip hwmon, every
   section provenance-tagged). Keep the file: it is the ground truth
   the twin approximates, the before/after for future BIOS updates,
   and the raw material for the twin's next revision.
3. Then `omarchy-firmware rehearse` (default backend = real).
   Structural probes must pass again; content probes now measure the
   actual machine. Twin-only probes report their skip honestly; the
   manual drills of `docs/first-run.md` cover the rest.
4. **Debrief:** `omarchy-firmware rehearse-diff --latest` — the twin →
   real comparison by stable probe id, zero paths. `!!` rows are named
   day-0 findings (investigate); `~` rows are the expected content
   harvest (real facts vs twin facts); `--` rows are twin-only drills
   covered live. What the diff names is precisely the list of machine
   surprises worth writing down — and the twin's next revision
   (TWIN-1.1, fed by the capture).

## The install fix the rehearsal class of tooling exists to catch

Before P5, `install.sh` copied the bins but never the library: the first
real session would have died on `ModuleNotFoundError` the moment
`~/.local/bin/omarchy-firmware` was invoked — a bug invisible from the
repository checkout, discovered the worst possible way. install.sh now
stages a self-contained layout:

```
~/.local/bin/omarchy-firmware…            the bins (resolve lib as fallback)
~/.local/share/omarchy-firmware/lib/      firmware_hal + CVE data
~/.local/share/omarchy-firmware/twin/     TWIN-1: boards, scenarios, sysfs
```

and the rehearsal was run against that installed layout, outside the
repository, to prove it: 28/28 green from `~/.local/bin` alone. This is
the class of bug the rehearsal exists to kill: anything that dies in
rehearsal never gets to die on the day.
