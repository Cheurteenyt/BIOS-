# The forty-sixth ring — the auto-dossier (2026-09-15)

> Companion to rings one through forty-five. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `fw46-autodossier.py`
> (TRACKED, new) over the unchanged fw35/fw38/fw39/fw40/fw41/fw42/fw43/
> fw45 machinery. Artifact: `vendor-autodossier-register.json` (the
> crown measurement + the PSP set anchors), via
> `scripts/ring46_artifact.py`, one write, assertion-gated. The
> trigger: after ring 45 the day-0 protocol was THREE commands and one
> memory — `fw45 propose` → operator review → `fw42 dossier --lenses`.
> The operator was the only place the stages met, which is the exact
> class of failure the ring-38/40/42 welds exist to eliminate, one
> layer higher. The ring fuses them — and catches, before freezing,
> that the review surface it inherits is blind to the very law it
> exists to carry.

## Front A — the last manual surface was the chain itself

Ring 43 removed the paste; ring 45 gave the corrected board its own
anchors. What remained was the GLUE: the operator ran `fw45 propose
dump.rom --out proposals.json`, read the review table, corrected by
hand into a file, then ran `fw42 dossier dump.rom --lenses` — three
invocations, one mental state, zero machine memory of how the stages
met. `fw46.fused` closes that gap: ONE command that proposes (fw45's
L2-transfer gates run first — every B550 anchor re-derives or the
fusion refuses whole), marks every slot against the stock-3644 anchor,
composes the lenses (the operator's corrections holding L1 precedence,
journaled), and lands the full triptych dossier (fw42 unchanged) —
with the whole provenance chain, proposal → mark → journal → dossier,
in ONE artifact. `--review-only` keeps the cheap review moment for the
operator who wants it; `--lenses corrections.json` keeps the operator
in command — corrections beat proposals, always, and the journal says
which was which.

## Front B — the count-blindness find (the review surface measured
## against its own law)

The ring-45 review marks compare PSP sets by COUNT. But the release
delta 3644→3645 swaps 37 body hashes INSIDE a 203-hash set — both sets
have exactly 203 hashes. Measured live before the crown: on
`b550w2-3645.rom`, every count-level mark reads `== stock-3644 anchor`
(203 vs 203) while the sets differ 37/37. On a flashed-3645 board the
review table would have certified "everything stock" while the board
runs different PSP bodies — hiding the discriminator law the ring-45
register itself proclaims (`psp_discriminates_3644_vs_3645`). The fix
is structural: fw46 anchors the SETS — the 203/194/193 sha256_16
strings captured from the crown run's proposals, registered in
`vendor-autodossier-register.json` — and the same probe on 3645 now
marks `!=` with added 37 / removed 37. The selftest asserts the
lesson BOTH ways on the same proposal (gates I2/I2b): the set mark is
`!=` while the count mark would be `==` — the count anchor is blind
to the discriminator, the set anchor is not. A review surface that
cannot see the law it was built to carry is worse than no review
surface; now it can see.

## Front C — the crown: the derived pre-registration, measured

Ring 45 DERIVED the lens-witnessed scoreline (fw35.Oracle.score on the
ring-44 exam findings + lens values): 6/1/10/9. The crown run of this
ring MEASURES it end-to-end: the full fused dossier on
`b550w2-3644.rom` (pure proposals as lenses, no corrections) in
3m42.8 s — **6 hit {P-03, P-06, P-08, P-13, P-16, P-18} / 1 partial
{P-15} / 10 miss / 9 na**, exactly the derivation. `measured_vs_
derived: agree`. The identity layer reproduces the ring-44 stranger
point WITH lenses: verdict `no-match-h3-eligible`, coupling
`coherent-foreign`, profile `stranger`, unregistered 74 — the
board-dependent facts miss (P-01 32 MiB geometry, P-02 AGESA 1.2.0.12
outside the B450 bracket, P-04/P-05 armor present, P-07 zero legacy
SMM, P-09 DSDT lineage, P-11 six certs, P-12 façade 14,431, P-17 SMM
census 186, P-19 the B550 equality direction), the board-independent
invariants hit, P-15 partial by its registered widened band (161
outside [126,158], inside [110,174] — the register's semantics, again
not an estimate). The weld journaled all 7 lenses with provenance
`lens`, 0 overrides. b550w2-3644.rom has now been read three ways:
4/8/14 without lenses (ring 44), the derivation (ring 45), 6/1/10/9
fused (this ring) — three scorelines, two lens states, no corrections
anywhere.

## Front D — the instrument

`fw46-autodossier.py` (tracked, precedent fw33/35/36/37/38/39/40/41/
42/43/45): modes `fused`, `--review-only`, `selftest`, `manifest`.
Four laws:

- **L1 corrections-beat-proposals** — a `--lenses` key replaces the
  proposal for that slot, journaled `operator_correction`; proposals
  are defaults, never overrides of the operator. Corrections outside
  LENS_ONLY refuse; corrections on judge-owned slots refuse with the
  TRUE violation named (the ring-40 separation is not the operator's
  to lift); a correction on an OMITTED slot lands — that is the
  review moment working.
- **L2 calibration-before-fusion** — fw45's L2-transfer gates run
  first (57 B550 anchor rows + 10 shared B450 rows re-derive before
  anything is proposed, composed, or fused; a broken basis refuses
  the fusion whole).
- **L3 loud degradation** — a slot neither proposed nor corrected is
  ABSENT from the lenses (the weld loud-degrades it, never guesses);
  omissions carry their reasons in the same artifact.
- **L4 zero writes** — read-only on images; exactly ONE write site in
  the source (grep-policed, the pattern assembled so the gate cannot
  match its own check — the ring-43 R9 lesson bitten again and
  banked).

`marks_for` knows three kinds: `set` (registered anchors, added/
removed deltas visible), `count` (the ring-45 fallback, loudly
labelled set-blind), `scalar`; an unknown slot marks `no-anchor` and
is never invented. The Refusal-classes-are-per-module boundary lesson
(ring 42) is honored: downstream loud errors (fw42's Refusal,
fw40's WeldError, anything else) are re-claimed as THIS module's
refusal with their type name attached — never swallowed, never
re-interpreted.

## Front E — the register and the gates

`vendor-autodossier-register.json` (one write, every number asserted
against the live artifacts BEFORE the write, roundtrip-checked after):
the crown measurement (scoreline, sets, stranger point, journal,
3m42.8s), the PSP set anchors (203/194/193 with provenance), the
discriminator 3645 both ways (set != 37/37 while count == 203), the
`measured_vs_derived: agree` cross, the honesty notes, the day-0
usage. The selftest: 38/38 gates — tier R (the laws, the mark/compose
KATs, register well-formedness incl. the both-ways discriminator,
zero-writes police, the acquisition sha16s) and tier I live (propose
on the ref target 7/7 with every mark `==`; the discriminator firing
on 3645 with the count-blindness asserted on the same proposal; live
compose through the REAL weld with a correction landing and 7/7 pure
proposals surviving unchanged; THE CROWN — the full fused dossier
re-run live, scoreline and stranger point confronted to the register;
artifact roundtrip). Two pre-freeze catches: the R3d refusal order
(the message must name the true violation — judge-owned before
outside-LENS_ONLY — or the gate reads the refusal as the wrong law)
and the R4 self-matching pattern (above).

## Front F — the day-0 protocol, now one command

    python3 lab/fw46-autodossier.py fused dump.rom --out dossier.json

propose → marks → compose → dossier → ONE artifact with the whole
chain. `--review-only` for the cheap review moment; `--lenses
corrections.json` when the operator corrects (they win, journaled).
Expected on a stock board: every mark `==`, scoreline 6/1/10/9,
identity no-match-h3-eligible, coupling coherent-foreign, profile
stranger. Any deviation is the board's own NVRAM/flash story — and
the PSP set mark alone tells flashed-forward-from-stock (37/37
against 3645, the IFR quartet identical) apart from anything else.

## Honesty ledger

- The crown artifact's in-run marks are COUNT-level (the register did
  not exist at run time); the register's set-level marks and deltas
  are computed from the SAME measured proposals — no number was
  re-run into existence.
- The crown is the THIRD reading of b550w2-3644.rom (4/8/14 ring 44,
  6/1/10/9 ring 46) — both scorelines stand as registered; the crown
  is a measurement, not a correction.
- The 3645 discriminator is review-only (no dossier was run on 3645):
  the PSP set delta and the IFR quartet are measured at the propose
  layer, which is where the review moment lives; a full dossier-pair
  remains available via fw42 for the post-flash world.
- fw42/fw45/fw40/fw38 are consumed unchanged — 0 diff on the frozen
  surface (bin/lib/tests), 323/323 checks, MCP smoke 12 tools.
- Drift #31 radiated at the checkpoint (the continuation summary
  described ring 35 while the disk stood at ring 45 — ten rings
  ahead; no ghost work; counter reset to zero).
