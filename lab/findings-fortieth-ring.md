# The fortieth ring — la soudure (the weld)

Date: 2026-09-13. Status: **tracked, selftest 34/34 PASS (tier I
live)**, pushed. Precedent: fw33/35/36/37/38/39. The tool surface is
untouched (323 checks, MCP smoke 12, 0 diff on bin/lib/tests).

## 1. The seam this ring closes

The day-0 chain was complete but for ONE hand-seam. Ring 38's own
report said it: *"the operator merges the two drafts before the final
`fw35-oracle.py score`."* A hand-seam in an otherwise machine-checked
chain is exactly where silent errors live: a value pasted into the
wrong slot, a day-0 key leaking into a release-41 verdict, a shallow
exam lens overwriting the judge's deep truth. Every one of those
mistakes manufactures a false oracle verdict — and the whole point of
rings 35–39 is that the verdicts are trustworthy.

Ring 40 makes the seam an instrument: `lab/fw40-merge.py` — the weld,
with four laws, each one a gate:

1. **schema law** — merged documents admit ONLY the fw35 template keys
   (31 unique; the 32-slot key list carries `agesa_level_41` twice,
   shared by P-20/P-25). An unknown key refuses the weld (exit 2).
2. **separation law** — day-0 keys and release-41 keys never mix in
   ONE merged document. A non-None key of the other target refuses the
   weld. The ring-38 leak lesson ("day-0 keys nulled so they cannot
   leak") becomes structural, enforced on the input draft AND on the
   welded output.
3. **precedence law** — identify deep-truth > exam shallow-walk for
   the keys the judge owns; the operator lens fills ONLY the 10 manual
   slots; a lens may override the judge ONLY via an explicit
   `--lens-wins KEY` (journaled as an override record, never silent).
4. **provenance law** — every filled value carries its source
   (`exam | identify | lens`) in the weld report; conflicts and
   overrides are journaled, unfilled slots are listed.

## 2. The precedence law paid for itself on the first live run

Welding the chain on rung 3604 produced **one live conflict**: the
exam shallow walk picked DSDT `20b7e802eb7c0a7a` (a checksum-valid
variant in the raw plane) while the judge's deep truth picked
`27d5e826e111d755` — the REGISTERED dsdt_clock anchor. Without the
weld, pasting the exam value would have scored **P-09 miss on a
byte-identical known release**. The conflict is journaled, the judge
wins, P-09 hits. On 3802 the same conflict fires three times
(DSDT + both armor booleans: the nested-LZMA armor wave is invisible
to the shallow walk — ring 39's fake-H3 lesson, now structural).

## 3. The release-41 map and the whitelist convention trap

The judge maps differently per target. For release-41 the legitimate
deep-truth fills are `trust_cert_distinct_41`, `dsdt_sha16_41`,
`core_armor_41`, `added_present_count_41` — and DELIBERATELY NOT
`chip_whitelist_families_41`: the whitelist count is
convention-DEPENDENT (which registered family set you intersect with),
fw38's exam_pair already parameterizes it by target (the release-41
46-family set), and the judge's day-0 41-convention value would have
corrupted P-26. **Caught live**: the first pair null-model scored
P-26 miss (41) where exam_pair's own convention gives 46 (hit). The
fix is a gate (R13c), and the lesson is registered: deep-truth beats
shallow-walk only where the convention is target-independent.

## 4. The scoreline envelope (the new register)

`lab/vendor-scorelines.json` — the FULL welded chain (no operator
lenses) run on every known rung plus the OVMF floor. Each profile is
the 26-row verdict table the day-0 dump's own scoreline will be read
against:

| stand-in | verdict | hit | partial | miss | na | the misses are |
|---|---|---|---|---|---|---|
| 3604 | known-release | 10 | 1 | 1 | 14 | P-18 (by design) |
| 3802 | known-release | 8 | 1 | 3 | 14 | + P-04, P-05 (armor wave born) |
| 3810 | known-release | 7 | 1 | 4 | 14 | + P-11 (DER set frozen at 6) |
| 4655 | known-release | 4 | 1 | 7 | 14 | + P-02, P-07, P-09 (AGESA/legacy/DSDT gen3) |
| OVMF (floor) | no-match-h3-eligible | 3 | 0 | 6 | 17 | the stranger signature |

**THE MONOTONE DECLINE — 10 → 8 → 7 → 4.** The further a rung sits
from the day-0 expectations (anchored on the 3604-era board state),
the fewer hits it scores, and every decline step is a REGISTERED EVENT
passing in the reverse direction: the armor wave (3802), the cert
freeze (3810), the AGESA/legacy/DSDT crossings (4655). The envelope is
itself a position measurement: the dump's scoreline localizes it on
the chronology before identity is even judged.

**The stranger signature.** On a foreign image the welded chain hits
exactly `{P-04, P-05, P-18}` — the two absence predictions PLUS P-18
itself: the H3 prediction agreeing with the H3 machine. This is
STRONGER than the ring-38 mock invariant (`{P-04, P-05}`, which ran
without the judge). The floor and the ceilings together bracket every
possible day-0 outcome.

**The discriminators.** Between the two bracketing rungs (3604|3802)
exactly two predictions flip: `{P-04, P-05}`. The scoreline alone
cannot separate 3644 from 3604 (P-02's widened set covers both AGESAs)
— that is the layered design working: scoreline = coarse localization,
identify per-rung diff table = fine.

**The release-41 null-model.** `chain_pair` on the adjacent historical
pair 3802→3810 scores 3 hit / 2 miss / 21 na: P-22 hit (zero
births/deaths — genome stability), P-23 hit (certs=6 — the DER
freeze), P-26 hit (whitelist=46 — the chip DB), P-20 miss (AGESA 1.2.0.7
< 1.2.0.12), P-21 miss (added=5, the wave2 completion not yet). A true
release-41 must hit what the historical pair cannot.

## 5. The commands

```
# day-0, ONE command (the whole protocol; then fill the manual lenses):
python3 lab/fw40-merge.py chain dump.rom --out chain.json

# release-41, ONE command:
python3 lab/fw40-merge.py chain-pair release40.rom release41.rom --out chain-pair.json

# the envelope, re-measured any time:
python3 lab/fw40-merge.py ceiling 3604 3802 3810 4655
# or the part-by-part path: merge <draft> <identify> [--lenses m.json] [--score]
```

`chain` runs exam (fw38) + identify (fw39) + weld + score (fw35) in
one pass and prints the verdict, the scoreline, the filled-slot count
and the conflict journal. The manual lenses (IFR façade, varstore
share, PSP hashes) stay manual BY DESIGN — labeled, never invented —
and enter via `--lenses m.json`.

## 6. The selftest (34 gates, two tiers)

Tier R (registers only, always): R1 schema 31 unique/32 slots; R2
separation disjoint 22/9; R3 manual surface covered exactly (10 slots
= JUDGE_FILLS ∪ LENS_ONLY); R4/R5 ownership; R6 all-None → all-26-na
through the weld (fw35 None-guard); R7 leak refusals both targets; R8
schema refusal; R9 lens refusal; R10 precedence (judge beats a wrong
exam value, conflicts journaled); R11 lens-wins override journaled;
R12 provenance completeness; R13 release-41 map inside `*_41` set,
H3-concepts excluded, whitelist convention pinned; R14 release-41 weld
zero day-0 leakage.

Tier I (live corpus): I1 chain@3604 known-release + judge keys
(cert 4 / legacy 2 / whitelist 41 / DSDT anchor); I2 scoreline@3604 ==
register; I3 chain@3802 == register; I4 discriminators == register; I5
OVMF stranger signature == {P-04, P-05, P-18}; I6 chain-pair 3802→3810
welds clean (births=0, deaths=0) and == register.

## 7. Honesty ledger

- The scoreline envelope is a MEASUREMENT on the surviving corpus
  (dated register, re-derived live by the selftest) — evidence, not
  authority; the anchors remain the eleven source registers.
- P-08 scores partial on every rung: the exam module-count convention
  sits inside the band but off the registered 618 point — the ring-39
  constant −4 residual, still report-only in identity, visible again
  here.
- The manual lenses stay manual (10 slots): the weld validates their
  KEYS and journals their provenance, but never invents their VALUES.
- The pair null-model uses the only adjacent pair on disk (3802→3810);
  the 4631→4655 pair would be a better release-41 null-model and can
  be added when the 4631 image lands.
- Summary drift #24 (the session summary described ring 35 + a pending
  recommendation (a) while the disk stood at ring 39, four rings
  ahead) is radiated here per the Task-31 doctrine: the disk is the
  master, no ghost work existed — rings 36–39 landed in parallel
  sessions and were each written off by their own ring.

## 8. What remains

The day-0 protocol is now ZERO hand-seams end to end: identification
(33) → comparison (34) → cartography (36) → walking (37) → examination
(38) → identity (39) → **WELD** (40) → scoring (35). The 16/09 dump
runs `chain`, the operator fills the labeled lenses, `--lenses` re-welds,
the scoreline lands inside the envelope — or outside it, which is what
the falsifiable register is for. Release-41 runs `chain-pair` against
the frozen 4655 anchor. The remaining events are the two the register
was built for: the dump, and the next release.
