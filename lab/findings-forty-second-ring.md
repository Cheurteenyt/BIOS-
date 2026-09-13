# The forty-second ring — le dossier (the triptych machine, the fourth weld)

**Date**: 2026-09-13 · **Instrument**: `lab/fw42-dossier.py` (TRACKED,
precedent fw33/35/36/37/38/39/40/41) · **Register**:
`lab/vendor-dossier-register.json` (the dossier envelope) · **Gates**:
23/23 PASS, tier I live · **Surface**: frozen (323/323, MCP 12 tools,
0 diff bin/lib/tests)

## 1. The seam

After ring 41 every image was covered by three exhaustive questions —
predicted (fw35) · known (fw39) · NOVEL (fw41) — but the day-0 protocol
still ran as TWO commands plus manual assembly: fw40's `chain` welded
exam+identify+score (readings 1 and 2), while the third reading ran
BESIDE the chain, its JSON landing in a separate output that no
instrument ever confronted with the scoreline. The operator was the
only place where the three readings met — the exact failure class the
ring-38 and ring-40 welds exist to remove. And behind the plumbing hid
a question no machine answered: **do the three readings tell the same
story?** A miss the detector can explain is a different universe from a
miss it cannot even see — and nothing distinguished them.

The forty-second ring closes that seam and answers that question: the
dossier. One command assembles all three readings into ONE document and
adds the layer none of the three has: the coherence verdict.

## 2. The instrument

`fw42-dossier.py` — stdlib-only, read-only, imports the whole chain by
path (the fw38/fw40/fw41 discipline). Modes: `dossier <image>`
(the ONE day-0 command — lenses pass through to the fw40 weld),
`dossier-pair <old> <new>` (the release-41 command), `clean <rung>`
(the live calibration target), `register`, `selftest [--no-live]`,
`manifest`. Four laws, each a gate family:

| law | content | enforcement |
|---|---|---|
| **L1 completeness** | every reading present and provenance-stamped (instrument + ring); a reading that cannot run is a loud refusal, never a silent block | missing image → exit 2 (gate R8); every block carries `instrument`+`ring` |
| **L2 coherence** | every non-hit oracle row is cross-referenced with the detector through the blind-spot map; the identity verdict is coupled to the detector total; contradiction = refusal | the coupling table (gate R3); identity coupling four-branch (gate R4) |
| **L3 calibration** | byte-identity (sha hit) forces the scoreline onto the registered ceiling; the clean profile is the calibration target | ceiling deviation on a known rung → exit 2; gates R12/I1/I4 |
| **L4 separation** | day-0 and release-41 keys never mix (the fw40 law, echoed through the dossier) | poisoned-draft gate R7 |

Two engineering welds make the dossier affordable without touching any
frozen instrument: a process-wide pure memoization of `fw39._deep_inventory`
(abspath-keyed — exam, identify and novelty share ONE deep walk per
image; gates I2/I9 count the walks: 1 per image, 5 for the whole live
tier) and a one-time cache of the register-derived detector universes
(`build_universes` walks all nine rungs — 159.6 s measured; every
subsequent novelty reading costs 17.7 s, a 9× saving measured live).

## 3. The blind-spot map (the ring's first finding)

For each of the 26 registered predictions, the map names the detector
axis that could CONFIRM a miss — or declares the row blind, with the
reason. The measured result is itself a finding:

| strength | count | rows |
|---|---|---|
| `set` — direct evidence (the axis diffs sets) | **14** | P-02, P-04, P-05, P-06, P-07, P-09, P-11, P-17, P-20, P-21, P-22, P-23, P-25, P-26 |
| `co` — co-travel (indirect) | **2** | P-03 (the AGESA prefix travels inside the version token), P-08 (a pure recount is invisible to sets) |
| `blind` — the detector cannot speak | **9** | P-01 (rom size), P-10 (AOD SSDT revisions — the dsdt universe tracks DSDT hashes only), P-12/P-13/P-24 (the IFR façade), P-14/P-15/P-16 (the varstore), P-19 (PSP bodies) |
| `identity` — rides on the judge | **1** | P-18 |

**9 of 26 predictions are invisible to the third reading.** On those
rows a miss can never be confirmed by the detector — the operator lens
(fw38's ten manual slots) is the only witness. The map is validated
against the live oracle register (gate R1: exact coverage of P-01..P-26),
frozen into the register (gate R11: the frozen map equals the instrument
map), and every blind row carries its reason (gate R6). The dossier is
therefore honest about its own limits BY CONSTRUCTION, not by caveat.

## 4. The coherence layer

Coupling classes (every oracle row, through the map): `aligned` (hit),
`na`, `confirmed` (miss/partial AND the detector has unregistered
entries on the same axis — the third reading explains the miss),
`bare` (miss/partial with NO detector entry — lens or measurement
error, or a divergence deeper than the detector names), `blind`
(miss/partial the detector cannot see), `identity` (P-18).

Identity couplings (judge × detector): `known-clean` (known-release +
zero unregistered — the clean profile), `coherent-foreign` (no-match +
unregistered content — the stranger profile), `suspicious` (no-match +
zero unregistered — the judge sees differences the detector cannot
name: check the blind axes), `refused-contradiction` (known-release +
unregistered content — impossible by the fw41 coverage proof I1/I2
unless registers drifted; **exit 2**, not a class to interpret).

Profiles (claim-free, derived — the H3 question is deliberately NOT a
profile; it is the P-18 row and the identity verdict, and the
instrument does not know what the 16/09 image is supposed to be):
`clean` / `stranger` / `suspicious` / `refused`, plus `clean-pair` /
`event-pair` in pair mode. The pair layer adds the strongest class of
all: **brand-new species** — births that even the register universe
cannot claim (birth ∧ unregistered), the beyond-register event the
zero-ledger was built to receive.

## 5. The dossier register (the envelope, measured live)

`lab/vendor-dossier-register.json` — generated live by
`scripts/ring42_artifact.py` (resume-safe: one write per measured
unit), frozen beside the measurements it calibrates.

**The monotone decline extends to the full ladder.** Ring 40 measured
it at four points; the nine clean dossiers measure it everywhere:

| rung | 3604 | 3802 | 3810 | 4003 | 4202 | 4402 | 4604 | 4631 | 4655 |
|---|---|---|---|---|---|---|---|---|---|
| hits | 10 | 8 | 7 | 6 | 5 | 4 | 4 | 4 | 4 |
| partial | 1 | 1 | 1 | 2 | 2 | 1 | 1 | 1 | 1 |
| miss | 1 | 3 | 4 | 4 | 5 | 7 | 7 | 7 | 7 |
| unregistered | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Every rung is the clean profile (identity `known-release`, zero
unregistered, byte-identity ceiling agreeing with
`vendor-scorelines.json` where the four registered ceilings live — gate
R12). The decline is smooth to 4202, then the plateau: from 4402
onward a known release scores exactly 4 hits — P-01 (the rom size),
P-09 (the DSDT generation), P-17 (the SMM census), P-23 (the cert
count) — the four constants of the late chronology. The 16/09 dump's
scoreline now has a nine-point measured context, not four.

The other frozen profiles:

- **foreign_dossier** (OVMF): 3 hit / 6 miss / 17 na, hit-set exactly
  `{P-04, P-05, P-18}` (the stranger signature, re-proven through the
  welded chain), 109 unregistered, `coherent-foreign`, profile
  `stranger`.
- **sibling_dossier** (TUF 4645): no-match at 3 fingerprint diffs, 5
  unregistered, `coherent-foreign`, profile `stranger` — a same-vendor
  sibling is almost inside the universe, and the residue the detector
  names is exactly the kind of silent difference the third reading
  exists for.
- **pair_null_dossier** (3802→3810): 3 hit / 2 miss / 21 na, births 0,
  deaths 0, brand-new species 0, coupling `clean-pair`, profile
  `clean-pair` — the release-41 null model as a dossier: P-22/P-23/P-26
  hit, P-20/P-21 miss, and a TRUE release-41 must hit what the
  historical pair cannot.

## 6. The gates (23, two-tier)

Tier R (registers re-derived, corpus-free): R1 the axis map covers
exactly P-01..P-26 · R2 non-blind axes are fw41 axes, identity is P-18
alone · R3 coupling enum closed under the full verdict sweep · R4 the
four identity-coupling branches, one refusal · R5 profile derivation
closed · R6 every blind row carries its reason (9/26) · R7 the L4
separation echo (the weld refuses the poisoned mixed-key draft) · R8
the L1 refusal on a missing image · R9 the oracle register intact (26
through the chain) · R10 the dossier register exists · R11 the frozen
axis map equals the instrument map · R12 the nine clean dossiers all
clean, ceilings agreeing with the scorelines register · R13 the two
registers agree (zero-ledger empty AND every clean dossier at zero) ·
R14 stranger + sibling + pair-null frozen with measured profiles.

Tier I (live): I1 clean 3604 — profile clean, zero unregistered,
10/1/1/14 == ceiling · I2 ONE deep walk serves exam+identify+novelty on
3604 (walks=1) · I3 clean 4655 — clean, zero unregistered · I4 register
freshness (the live 3604 record equals the frozen record, byte-for-byte
field-for-field) · I5 the OVMF stranger (coherent-foreign, 109
unregistered, profile stranger) · I6 the stranger signature exact
({P-04, P-05, P-18}) · I7 the TUF sibling (no-match at 3 diffs, 5
unregistered, coherent-foreign) · I8 the pair null (clean-pair,
births=0 deaths=0, P-22 hit, 3/2/21) · I9 walk discipline — exactly
five deep walks for five distinct images across the whole live tier.

## 7. Lessons caught live (before freeze)

1. **The tuple convention bites twice.** `fw35.Oracle().score` yields
   `(prediction_dict, verdict, note)` — the first coupling pass
   consumed the dict as the id (TypeError: unhashable), and the row
   builders stored a dict in `id` (StopIteration hunting P-22). Fixed
   once with `_pid()` and applied everywhere. The lesson is the ring-40
   `_n()` lesson again: adapters between instruments must normalize at
   the boundary, not at each use.
2. **The hidden 160 s.** `fw41.novelty(image)` without precomputed
   universes rebuilds `build_universes()` per call — which deep-walks
   all nine rungs (159.6 s measured) — so every dossier silently paid
   three minutes. fw41's own selftest always passes `Uf`; fw42 now
   caches the universes per process (pure: they depend on the registers
   and the corpus, never on the image). The artifact generation fell
   from ~35 min to one ~6-minute pass, measured.
3. **The reaper shapes the tooling.** The sandbox kills background
   processes at the call boundary (registered ring 28) — a 35-minute
   generation cannot survive as a background job. The artifact script
   is therefore resume-safe: one write per measured unit, rerun until
   COMPLETE. Infrastructure constraints became design (the same lesson
   as the ring-10 reproducibility ritual).
4. **P-18 misses on a known release — and must.** The clean dossier of
   3604 shows exactly two non-aligned rows: P-08 partial (bare — the
   registered count-band partial) and P-18 miss (identity coupling).
   The H3 prediction describes a dump that is NOT one of the nine; a
   byte-identical rung falsifies it, exactly as the registered ceiling
   demands (1 miss on every ceiling rung). The coherence layer surfaces
   the semantics instead of hiding them.

## 8. Day-0 usage

The 16/09 protocol collapses to ONE command:

```
python3 lab/fw42-dossier.py dossier dump.rom --out dossier.json
# … fill the ten labeled manual lenses (IFR façade, varstore, PSP …)
python3 lab/fw42-dossier.py dossier dump.rom --lenses manual.json \
        --out dossier.json
```

The dossier prints the three readings, the coupling table (every
non-aligned row with its axis, strength and class), the identity
coupling and the profile. Reading it:

- profile `clean` + matched rung → the dump IS that release (byte
  identity); the scoreline must equal that rung's register record.
- profile `stranger` + `coherent-foreign` → read the coupling table:
  `confirmed` rows are explained by the detector's entries (candidate
  zero-ledger material); `bare` rows need the operator lens or a new
  instrument; `blind` rows are the nine the detector cannot see.
- identity `no-match-h3-eligible` + P-18 hit → the H3 shape: the dump
  triangulates to published-but-unlisted. `suspicious` (judge sees,
  detector silent) → suspect the blind axes first.
- release-41: `dossier-pair old.rom new.rom` — `brand_new_species`
  non-empty is the beyond-register event; its GUIDs seed the zero
  ledger.

## 9. Honesty ledger

- The dossier adds NO new measurements of its own — it is the weld of
  three readings plus their cross-examination; every number it prints
  cites its instrument and ring, and the coherence layer invents
  nothing (couplings are derived, profiles are derived, refusals are
  loud).
- The blind-spot map is the instrument's design, not a measurement —
  it is validated against the registers (R1/R2/R11) and frozen with
  its reasons so a future reader can dispute each row individually.
- The ceilings for five of the nine rungs (4003..4631) live only in
  THIS register; the scorelines register carries four. The two
  registers agree where they overlap (gate R12) — the extension is
  labeled as extension, never as replacement.
- The universes cache is pure by construction (registers + corpus only)
  but its purity is asserted by gate I4 (register freshness) and the
  agreement gates, not by fiat.
- Zero-touch on the frozen surface: bin/, lib/, tests/ unchanged; the
  three frozen instruments consumed (fw38/fw39/fw40) and the one
  extended-by-cache (fw41, via its own public `novelty(image,
  universes)` signature — a parameter it already exposed).
