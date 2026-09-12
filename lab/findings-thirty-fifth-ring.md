# The thirty-fifth ring — l'oracle du jour 0

> *Sept. 16 must be a replay day, not a discovery day* — the digital-twin
> doctrine already said it. This ring makes it literal: the dump now has
> expected answers, registered three days before the machine, each with its
> own falsifier, scored mechanically.

## What was built

Two artifacts, zero downloads, zero hardware, every number re-derived from
the persisted registers at load time:

- `lab/vendor-oracle.json` — the prediction register: **26 falsifiable
  predictions** across two targets. `day0-3644` (19 predictions): the
  physical board dump of 16/09, which also resolves `question_3644`
  (the ledger's H3 — published-but-unlisted — is the registered outcome).
  `release-41` (7 predictions): the next PRIME B450-PLUS release after
  4655, whenever it lands.
- `lab/fw35-oracle.py` — the scorer, stdlib-only, tracked in lab/ (the
  fw33 precedent): five modes (`list`, `show`, `template`, `score`,
  `manifest`) behind a **36-gate selftest** that re-derives every basis
  number from its source register (armor, AGESA, genome, DER, IFR, unasked,
  chipdb, lifecycles, SSDT clock, TUF ledger) and refuses loudly on any
  drift. 36/36 PASS.

## The register (why these twenty-six)

Every prediction is anchored on the target board's OWN measured values,
never on corpus-wide ranges — the ring's first lesson was catching exactly
this transplant error: the 84–90 % never-asked share is a five-vendor band,
but the ASUS board itself measures **83.89 %**, so P-16 registers
[83.0, 86.0], not the corpus band. The high-confidence set (P-01, 03, 04,
05, 07, 09, 11, 13, 17, 20, 23, 26) rides laws the genome and the clocks
established at probe granularity: the 16 MiB part, the ComboAM4v2PI prefix,
the wave-1 boundary (armor absent before 3802), the two legacy SMM modules
that die at 4202/4402, the first DSDT generation `27d5e826e111d755` (held
3604→4202), the frozen 4-cert band until 3810, the 46-family chip whitelist
frozen since 3802, AGESA monotonicity. The medium set prices the neighbor
hypothesis: 3644 sits between the 2022/03/16 and 2022/05/12 rungs, so its
AGESA should be 1.2.0.6b/6c/7 (point 1.2.0.6c), its module count within
tens of 618, its facade near 7,975 questions, its PSP hashes closer to 3604's
than to 3802's (P-19 — the directional identity test), and its identity
verdict should land on H3 with ≥ 3 independent fingerprint differences
(P-18 — the registered resolution of `question_3644`).

The release-41 half converts the genome laws into foresight: no third armor
wave in a routine release (P-21), zero births/deaths outside wave events
(P-22), the DSDT generation moves only if the AGESA moves (P-25, the
conditional that scores `na` the moment its precondition dissolves), the
facade never shrinks (P-24).

## Scoring semantics

`hit` = inside the registered band / equal to the registered value /
predicate true. `partial` = inside the widened band only — direction right,
magnitude off. `miss` = outside both — the register is falsified on that
point. `na` = a predicate's precondition dissolved. The protocol is
mechanical: `fw35-oracle.py score <findings.json>` where the findings file
maps prediction ids to observed values; `template` emits the fill-in sheet.
The honesty rule is baked into the output: every partial and miss requires
a written cause in the next ring report. The register is frozen at commit —
predictions are never edited after registration.

A synthetic demo run (19 hit / 0 partial / 0 miss / 7 na) exercised every
code path including the four verdict classes; it is session-side, clearly
labeled DEMO, and is not a measurement. The selftest smoke (G13) proves one
of each verdict through the same machinery.

## What day-0 looks like now

The 16/09 session fills the template alongside the dump (the §1–§3 lenses
of the day-0 report produce exactly the observed values the register wants),
then `score` prints the exam result. The dump is no longer a discovery
session on an open map — it is a **measurement against twenty-six
registered expectations**, where each miss is as valuable as each hit: a
miss localizes precisely which law failed to extend, which is the fastest
route to a new ring.

## Honesty ledger

- Proven: the register derivable from eleven persisted registers with zero
  new bytes; 36/36 selftest gates; the four-verdict scorer end to end.
- Registered, not resolved: the actual outcomes — all 26 remain open until
  the dump (P-01..P-19) or release #41 (P-20..P-26).
- The self-imposed rule that produced one correction during the ring: bands
  anchored on corpus ranges rather than board values are transplant errors
  (P-16 was re-anchored 84–90 → 83.0–86.0 before the register froze — the
  only edit, made pre-freeze, documented here).
- Zero bytes written to any firmware object, zero downloads; the demo
  findings file stays session-side per the tracked-knowledge rule.
