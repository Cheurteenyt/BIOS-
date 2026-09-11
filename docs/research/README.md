# Research — the five-volume study (*Beyond the BIOS*)

Everything in this repository descends from a five-volume research study
auditing the Omarchy repository, the AM4 vendor BIOS landscape, and the
founding question "what can an agent do that the vendor BIOS cannot?".

The study exists in **two editions, both archived in full as release assets** —
the repository itself carries no PDF binaries (the same choice Omarchy makes:
the repo is text + code, heavy artifacts live on Releases):

- **English (canonical)** — the [`study-en` release](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-en).
  The edition this repository is written in; updated September 2026 so the
  blueprint chapters report their shipped state (phases P1–P5 delivered,
  281 checks, release `v0.6.0`, the drift canary, the bit-verified installer,
  the day-0 rehearsal of 16/09).
- **French (original voice)** — the [`study-fr` release](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-fr).
  The primary sources, archived unchanged as they were written. Any nuance
  conflict is settled by the French text.

| Volume | English (canonical, on `study-en`) | p. | French (archive, on `study-fr`) | p. |
|---|---|---|---|---|
| 1. Beyond the BIOS | `vol1-beyond-the-bios-en.pdf` | 22 | `vol1-beyond-the-bios.pdf` | 22 |
| 2. The agent and the firmware | `vol2-the-agent-and-the-firmware-en.pdf` | 24 | `vol2-the-agent-and-the-firmware.pdf` | 24 |
| 3. What the BIOS cannot see | `vol3-what-the-bios-cannot-see-en.pdf` | 15 | `vol3-what-the-bios-cannot-see.pdf` | 16 |
| 4. Misconfigured or defective? | `vol4-misconfigured-or-defective-en.pdf` | 18 | `vol4-misconfigured-or-defective.pdf` | 18 |
| 5. The sacrificial board | *(EN edition pending)* | — | `vol5-la-carte-sacrificielle.pdf` | 17 |

## Volume 1 — Beyond the BIOS (firmware study, Omarchy x AM4)

Deep audit of the Omarchy repository (v4.0.0.alpha, 455 commands dissected:
Limine + UKI boot chain, `omarchy-setup-direct-boot` refusing AMI firmware,
`omarchy-update-firmware` = fwupd) against the vendor BIOS landscape for
AM4 boards (ASUS B450/B550 activity, MSI frozen since 2023, Gigabyte,
ASRock) and the CVE timeline (fTPM stutter 2022, LogoFAIL 2023, Sinkclose
CVE-2023-31315, VU#382314 in 2025, CVE-2026-6726/6727 in 2026). Two
structural conclusions: **desktop AM4 boards are absent from the LVFS
catalogue** (BIOS updates = EZ Flash only), and the BIOS keeps exactly four
irreplaceable jobs — platform wake, memory training, trust chain, recovery.
Everything else can move to the OS runtime at zero extra cost. Delivers the
five-module `omarchy-firmware` blueprint (audit / boot / cpu / fans / gpu)
and three strategic trajectories (A: post-BIOS suite — retained; B: ASRock
Rack X470D4U + coreboot; C: AM5 + Dasharo long term).

## Volume 2 — The agent and the firmware

Thesis: **the agent proposes, the HAL disposes, the human decides.** Omarchy
turns out to be built agent-first (AGENTS.md, 7 bundled skills, MCP-ready
harnesses, `# omarchy:*` CLI metadata, the read-only rule of diagnose-crash),
which makes it the ideal host for an agent ↔ firmware bridge. The volume
maps what agents can technically touch (fwupd DBus, efibootmgr, dmidecode,
UEFI variables, hwmon, flashrom — read-first) and erects the **T0-T3 tier
contract** with mechanical locks, the access journal, and the MCP server
shape. Catalogues 8 concrete MCP tools; draws the 3-phase, 8-week roadmap
that this repository implements.

## Volume 3 — What the BIOS cannot see

Answers the founding question: *a CPU overheats because no thermal paste was
applied — the AIO pump spins, everything seems alive. Is that detectable?*
**Yes** — without a daemon, without an embedded model, at ~0.3 s per one-shot
and +0 bytes of SPI flash. The physics: `R_th = (T_die − T_coolant) / P`
(healthy ≈ 0.29 °C/W vs ≈ 0.585 without paste), rise-time to 85 °C (12-20 s
healthy vs 4 s without paste), coolant ΔT for the liquid→air side, and the
power fold-back the BIOS performs silently at Tjmax. Delivers the signature
engine (12 signatures), the bounded active probe, the longitudinal baseline
(what no BIOS remembers), and the measured frugality budget. Phase 2 of
this repo is its direct implementation.

## Volume 4 — Misconfigured or defective?

Generalizes volume 3: thermal paste was one example among dozens — the real
domain is **every component that is misconfigured (`mal réglé`) or defective
(`défectueux`)**. This is exactly where a custom system can outclass the
vendor's official BIOS — and exactly where **critical mistakes become
possible**. The volume builds the four-family grid (misconfigured /
firmware bug / defective / degraded) × repair paths, catalogues 18 named
findings with their measurable evidence, and erects the anti-critical-error
doctrine: three error sources (bad measurement, bad interpretation, bad
action), three barriers, eight rules, and a residual-risk quadrant (grave ×
irreversible) kept empty **by construction** — omniscience in reading,
chastity in writing. See [../security-doctrine.md](../security-doctrine.md)
and [../diagnostics-catalog.md](../diagnostics-catalog.md) for the
repository-facing versions.

## Volume 5 — The sacrificial board (the price of control)

Answers the question the eighteen rings left open: "we can read every AM4
firmware — can we write?" The coreboot tree is fetched from disk and the
answer is measured, not remembered: **zero consumer AM4 boards** in
`src/mainboard` (ASRock/ASUS/MSI/Gigabyte ship Intel boards only; the
remembered "B450M Pro4 port" answers 404 on master), **no Matisse SoC**
in `src/soc/amd` (only APU BGA families + Stoney Ridge), and the ten AMD
boards that do exist are "eval" CRBs — pademelon, the closest, runs a
pre-Zen Merlin Falcon on Stoney Ridge. The port anatomy (family17h.md,
psp_integration.md, amdblobs_license.md) closes the door honestly: the PSP
trains DRAM *before* the first x86 fetch, AGESA v9 ships under NDA, and the
blob licence does not cover extracting vendor images. Porting our PRIME
B450-PLUS = a SoC port **and** a board port — developer-grade, unplanned.
What the study buys instead is the **practical sacrificial bench**: a second
used B450 (~30-70 €) plus a CH341A programmer, with four drills (identical
dump, bit-exact vendor flash, recovery, vendor-update rehearsal) that absorb
the brick risk while the main machine keeps its +0-octet doctrine — and a
day-0 tie-in table (nothing blocking for 16/09, the bench is optional
rehearsal). French edition; EN pending.
