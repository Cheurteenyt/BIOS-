# Research — the four study volumes (*Beyond the BIOS*)

Everything in this repository descends from a four-volume research study
written in **French** — the owner's language. The original PDFs are archived
here unchanged as the project's primary sources; each volume has an English
summary below. The code and documentation are English; the study stays in
its original voice, as any primary source should.

| Volume | PDF | Pages |
|---|---|---|
| 1. Beyond the BIOS | [pdf/vol1-beyond-the-bios.pdf](pdf/vol1-beyond-the-bios.pdf) | 22 |
| 2. The agent and the firmware | [pdf/vol2-the-agent-and-the-firmware.pdf](pdf/vol2-the-agent-and-the-firmware.pdf) | 24 |
| 3. What the BIOS cannot see | [pdf/vol3-what-the-bios-cannot-see.pdf](pdf/vol3-what-the-bios-cannot-see.pdf) | 16 |
| 4. Misconfigured or defective? | [pdf/vol4-misconfigured-or-defective.pdf](pdf/vol4-misconfigured-or-defective.pdf) | 18 |

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
