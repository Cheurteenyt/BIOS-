# The forty-seventh ring — the pair witness (2026-09-15)

> Companion to rings one through forty-six. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `fw47-pairmarks.py`
> (TRACKED, new) composed over the unchanged fw35/fw37/fw38/fw39/fw40/
> fw41/fw42/fw43/fw45/fw46 machinery — on top, never instead. Artifact:
> `vendor-pairmarks-register.json` (the crown measurements + the
> corrected pair taxonomy + the pre-registration ledger), via
> `scripts/ring47_register.py`, one write, assertion-gated, roundtrip-
> checked. The trigger: ring 46 measured the count-blindness inside the
> day-0 fused chain and healed it there — but the release-41 machinery,
> fw42's `dossier_pair` (the command the board meets AFTER a flash),
> still reads the pair through module species only. This ring anchors
> the pair coherence to the SETS, and catches the founder of the flaw:
> the frozen pair-null model itself.

## Front A — the pair layer was blind to the law the registers carry

Ring 46's find, one layer wider. The `dossier_pair` coherence derives
its class from species births/deaths: GUIDs present in one image and
absent from the other. But the measured release event 3644→3645 —
"un meilleur bios", "Improve system compatibility", published 2026-09-14
— births ZERO species and kills ZERO species. It swaps 37 PSP body
hashes INSIDE a 203-hash set, changes 18 modules at near-constant size
(−992 B total module-size drift against 7,544,486 B of run-level
difference, 22.5% of the image), and its fw42 profile reads
**clean-pair — the NULL profile** — on the exact pair the ring-45/46
registers proclaim to be THE discriminator event. The post-flash world
would have run a coherence layer certified blind by its own register.
`fw47-pairmarks.py` closes it with four laws: **L1** set-truth-over-
count (pair marks read the PSP sets; counts are emitted only as the
labeled blindness witness, never as a mark); **L2** anchors-before-
marks (a registered pair — release 3644↔3645, board 3644↔nw-3644 —
must reproduce its registered delta from `vendor-b550-lens.json
psp_set_deltas` live or refuse; unknown pairs claim no anchor, never
invented); **L3** corrected-taxonomy (`clean-pair` now REQUIRES set
delta == 0; content swapped inside stable containers is a new class,
**swap-event**; frozen registers are read, never rewritten —
contradictions are recorded as named corrections); **L4** zero writes
(the only write site is the `--out` document, grep-policed with the
ring-43 assembled-pattern lesson).

## Front B — the crown: the release pair through the corrected
## coherence

Measured end-to-end in 206 s (`cohere b550w2-3644.rom
b550w2-3645.rom`): PSP set **!= with added 37 / removed 37**
(anchor-checked against the lens register, both directions), count
witness **==** (203 vs 203 — the ring-46 lesson live at pair level),
species **0 births / 0 deaths** (PR-1 hit), ledger **18 modules
changed, byte_delta −992 B**, fw42 profile **clean-pair**, corrected
profile **swap-event**, and the **CORRECTION NAMED** in the same
document — never smoothed. fw42's side readings on the new image
reproduce the known world: identity `no-match-h3-eligible` (3645 is
not a B450 rung), novelty `unregistered_total` **75** — one MORE than
the 74 measured on 3644 in ring 44, a real release observation,
recorded in the register's honesty block. The board pair (same version
number, sibling board) measured next: PSP **65/65** (anchor-checked),
count **==**, species **0 births / 4 deaths**, 108 modules changed
(−13,008 B), corrected class **registered-births**. Read together, the
two crowns give the version-number trap its pair-level signature: the
RELEASE pair kills zero species and swaps content (swap-event); the
BOARD pair kills four species (registered-births). A version string
never identifies an image — and now the pair layer can SEE the
difference structurally.

## Front C — the null3802 verdict: the founder of the flaw was itself
## count-blind

The ring-42 pair-null (3802→3810, the B450 "routine historical pair"
frozen as `clean-pair`) re-read through the set lens: PSP set **!=
with added 17 / removed 17** inside 193-hash sets (count **==** —
no anchor claimed, the B450 corpus carries no registered sets, L2
honest), species 0/0 (the frozen row reproduces — refusing loud was
the alternative and did not fire), **34 modules changed, −86,264 B**.
Verdict: **corrected**. The frozen clean-pair was set-blind: the class
corrects to swap-event, the correction lives in
`vendor-pairmarks-register.json`, the frozen register is never
rewritten. The ring-46 lesson did not merely propagate forward — it
reached back and corrected the null model every later pair was judged
against. A routine AGESA bump was never "clean"; it was a 17-hash
content swap that the species lens could not see.

## The pre-registration ledger (frozen before the crown ran)

Eight predictions registered in the instrument's gates before
measurement: PR-1 (release 0/0 species) HIT; PR-2 (37/37 lens
reproduction) HIT; PR-3 (count witness ==) HIT; PR-4 (corrected
swap-event, correction named) HIT; PR-5 (65/65 lens reproduction) HIT;
**PR-6 (board 0/0 species) REFUTED — measured 0/4**; PR-7 (null
births/deaths reproduce the frozen row) HIT; PR-8 (null PSP delta
unknown, verdict by measurement) RESOLVED — 17/17, corrected. The
PR-6 refutation is kept visible in the gate names and the register:
the same-version sibling kills four species, and the measurement wins
pre-freeze (the ring-45 precedent, applied before the commit).

## Day-1 usage (the post-flash world, pre-registered)

`fw46 fused dump.rom` remains the WHOLE day-0 command. The morning
after a flash, the pair world is now witnessed too:
`fw47-pairmarks.py marks dump.rom b550w2-3645.rom` reads the
set-level truth of what the flash changed (a flashed-3645 board is a
swap-event vs stock-3644: 37/37, zero births, zero deaths — any
deviation from THOSE marks is the board's own NVRAM/flash story);
`fw47-pairmarks.py cohere b550w2-3644.rom b550w2-3645.rom` lands the
full corrected pair dossier with the release-41 event named.
`fw47-pairmarks.py null3802` re-derives the null verdict any time the
foundation needs re-checking.

## The honesty ledger

- The byte_delta values (−992 / −13,008 / −86,264 B) are MODULE-SIZE
  deltas from the fw37 ledger; the 22.5% / 7,544,486 B figure is the
  ring-44 differ's run-level ruler. Different rulers, both recorded,
  neither silently substituted for the other.
- The B450 null pair claims NO anchor: no registered B450 PSP sets
  exist, so the 17/17 is a measurement, not a reproduction — and the
  register says so.
- fw42 is FROZEN and untouched: the corrected taxonomy composes on
  top (the fw46 pattern). The frozen `clean-pair` rows keep their
  places in their registers; the corrections live here, named,
  with provenance.
- The selftest's first run scored 29/32: one test-data bug (R2b, the
  "identical sets" KAT was not identical), and the PR-6 refutation
  (I7/I7b) — which is not an instrument bug but the ring's finding
  arriving through the gates, recorded and corrected pre-freeze.
