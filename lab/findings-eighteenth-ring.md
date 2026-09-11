# The eighteenth ring — the wave was never a reaction

Ring 16 bounded the flash-armor chronology with a binary search and
honestly registered the limit: releases 3802/3810/4003 between 3604
(0/7) and 4202 (5/7) were not probed, so the reading said "present
by 4202" — and, pressed into a security narrative, placed the armor
inside the LogoFail year. This ring spends the three withheld
downloads and the correction lands hard: **the core armor predates
the LogoFail disclosure by roughly fourteen months.** What does land
inside the disclosure window is the retirement of the legacy SMM
pair. The same run turns the AGESA lens into a nine-point dated
chronology of the board.

## Front 1 — the three probes, and the boundary becomes exact

The bisect register (16 probes' worth of machinery, `probe()` reused
verbatim) gained three official downloads — 3802 (2022-05-12), 3810
(2022-12-15), 4003 (2023-03-21), each unwrapped, inventoried and
sentinel-tested like its seven predecessors. The register was
written after every probe; partial progress was designed to survive.

**The answer is monotone and clean.** All three measure 5/7 armor
present (the four core SMM modules plus one freeform), legacy SMM
pair 2/2, 623 modules each. The core armor therefore arrives at
**3802 — the release IMMEDIATELY following 3604 in the official
ledger** — and the wave-1 boundary is exact at release granularity:
3604 (2022-03-16, 0/7) → 3802 (2022-05-12, 5/7). No in-between
official build exists to probe. The complete set stays where ring 16
put it: 7/7 first at 4604 (2024-04-08), everything between at 5/7.

The whole 40-release ledger has now been interrogated with seven
downloads plus two free sentinels — and each of the seven paid for
itself.

## Front 2 — the security reading, corrected by measurement

Ring 16 wrote: "the core armor wave brackets the LogoFail disclosure
window (2023); ASUS hardened the flash path inside exactly that
year." With 3802 measured at 2022-05-12, that reading is **wrong by
fourteen months** — the hardening predates the public disclosure and
cannot be a reaction to it.

The correction is itself instructive, and it is registered as a
method lesson, not an embarrassment: **a binary search answers the
question it was asked.** Ring 16 asked "by when present?" and got a
true answer ("by 4202") that was misleading as a "when introduced"
— because the bisect deliberately skipped the three releases whose
only role was to tighten an already-answered bound. The ring-18 fix
is three more probes, not a new theory.

And the measurement gives something back: the **legacy SMM
retirement** — 2/2 present at 4003 (2023-03-21), 1/2 at 4202
(2023-08-02), 0/2 by 4402 (2024-01-08) — lands exactly inside the
LogoFail window. The verified facts now read: old SMM modules added
in 2022, retired in stages across the 2023 disclosure year, armor
completed in 2024. Correlation at year granularity; no day-precise
disclosure date exists in the project's on-disk sources, and the
register says so.

## Front 3 — the AGESA timeline: nine dated rungs on one board

The ring-16 pierced lens (`surfaces()` reused verbatim) scanned the
seven bisect ROMs already on disk — zero new downloads — and the
3604/4655 points cite their existing ring-16 register. The ladder:

| release | date | AGESA (`ComboAM4v2PI`) |
|---|---|---|
| 3604 | 2022-03-16 | 1.2.0.6b |
| 3802 | 2022-05-12 | 1.2.0.7 |
| 3810 | 2022-12-15 | 1.2.0.7 |
| 4003 | 2023-03-21 | 1.2.0.8 |
| 4202 | 2023-08-02 | 1.2.0.A |
| 4402 | 2024-01-08 | 1.2.0.B |
| 4604 | 2024-04-08 | 1.2.0.Ca |
| 4631 | 2025-04-01 | 1.2.0.E |
| 4655 | 2026-08-27 | 1.2.0.12 |

Monotone, and it cross-checks the two ring-16 verdicts it reuses.
The third dating signal is now a scale, not a pair of points: a dump
trapped between two rungs is dated between their releases without
reading any version string. The ladder's own limit is registered —
3802 and 3810 share 1.2.0.7, so the AGESA rung pairs with the PSP
and NVRAM lenses for identity, never alone.

## Honesty ledger

- The wave-1 introduction is exact at OFFICIAL-release granularity;
  an OEM/factory image between 3604 and 3802 remains formally
  possible and would be invisible to any ledger-based probe.
- The LogoFail correlation is stated at year granularity only.
- 3802/3810/4003 carry no vendor sha256 in the ledger; provenance
  rests on the official CDN URL plus the zip sha256 recorded at
  download time in the register.
- The ring-16 security reading was wrong and is corrected here; the
  wrong reading is preserved in the correction itself, not erased.

## Registers

- `vendor-flash-armor.json` — nine probes, exact boundaries, the
  corrected reading and the sampling-bias lesson.
- `vendor-agesa.json` — the six-specimen cross-vendor verdicts plus
  the nine-point PRIME timeline (`timeline`).
- Scratch: `ring16-armor-bisect.json`, `ring18-agesa-timeline.json`.
