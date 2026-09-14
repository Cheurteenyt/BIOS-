# The forty-fifth ring — the B550 lens layer (2026-09-14)

> Companion to rings one through forty-four. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `fw45-b550-lens.py`
> (TRACKED, new) over the unchanged fw35/fw38/fw39/fw40/fw41/fw43
> machinery. Artifacts: `vendor-b550-lens.json` (the transfer
> calibration) and `vendor-novelty-recon.json` (the 74-vs-60
> reconciliation), both via `scripts/ring45_artifact.py`, one write
> each, assertion-gated. The trigger: ring 44 pre-registered two jobs —
> reconcile the flagged novelty-accounting delta, and un-loud-degrade
> the B550 lens slots. Both are done, and the second one's premise
> did not survive measurement.

## Front A — the measured attribution: nothing ever refused

Ring 44's honesty ledger recorded the seven lens slots as
"loud-degraded (null) — the fw43 proposers are B450-calibrated and L3
refused to guess". Ring 45 ran the proposers on the corrected board's
acquisition and the premise collapses: `fw43-proposal.py propose
b550w2-3644.rom` proposes **7/7 slots, 0 omitted, in 5.2 seconds** —
IFR exact-consumption validity 1.00, Setup uncovered 161 B, share
85.73 %, 203 PSP body hashes, the 3604/3802 comparison sets filling
from the same method. Nothing refused. The ring-44 nulls were simply
the dossier running without `--lenses`; the attribution was
over-cautious, which is the honest failure mode, but still an
attribution — and this campaign measures its attributions when it can.
The correction is registered in both new artifacts without touching
the ring-44 ledger (frozen registers are never rewritten; the pointer
lives in the new ones).

## Front B — the 74-vs-60 reconciliation: a key-naming asymmetry

The flagged delta is fully mechanical, and both numbers were honest
under their own rule. On the SAME novelty result object:

- the **summary rule** (fw41's `total_un`) counts the whitelist axis's
  unregistered names from its local `extra` list: 48 species + 0 certs
  + 4 dsdt + **14 whitelist** + 8 smm + 0 agesa = **74**;
- the **serialized walk** (the ring-44 artifact generator) read only
  the `unregistered` key of each serialized axis — and the whitelist
  axis stores its unregistered count under **`extra`**, not
  `unregistered`: 48 + 0 + 4 + 0 + 8 = **60**.

The dossier's coherence layer already agreed with the summary (74) —
only the walk lagged. fw41 is UNCHANGED: its summary was the full
honest count all along. The 14 rows have names, and they are the
ring's semantic find: **six AUX fan-header strings** (`AUX0 Fan`,
`AUX0 fan PWM-DC`, `AUX1 Fan`, `AUX1 fan PWM-DC`, `AUX2 fan PWM-DC`,
`AUX4 Fan`) and **eight Level strings** (`Level 1`..`Level 8`) — the
WIFI II's fan-control vocabulary, swept into the whitelist axis by the
ring-41 structural extractor's digit-bearing ≤4-token rule on the B550
image. They are real B550 strings and they are NOT chip families: the
extraction carries `missing = 0`, so the 47-family chip whitelist
transfers from the B450 universe **whole, zero new families**. The
B450 3604 probe confirms the 14 are B550-only within the corpus (zero
AUX/Level names in its own extraction). Consequence registered: future
consumers of the serialized novelty axes must read the whitelist
`extra` key — or re-derive; the recon register is the pointer.

## Front C — the transfer calibration: three acquisitions become the basis

What the corrected board actually lacked was its own L2 basis: the 47
rows of `vendor-proposal-calibration.json` say nothing about B550.
Ring 45 makes the three vendor-verified acquisitions the anchor set
(`vendor-b550-lens.json`), re-derived live through the tracked
instruments and cross-checked for consistency. The transfer laws,
all measured and frozen as gates:

- **Release identity**: 3644 and 3645 are EXACTLY identical on all
  five IFR census totals (104 packages / 104 valid / 1,144 pages /
  14,431 questions / 33,158 options) and the whole varstore cross
  (145 varstores, 43,695 B, 6,236 covered, 32 zero-question) —
  "improve system compatibility" touched **zero form grammar**.
- **Validity transfers**: 104/104 exact-consumption packages on both
  WIFI II releases, 105/105 on the sibling — P-13's law holds on B550.
- **The cross is stable across boards where it matters**: share
  85.73 % and Setup uncovered EXACTLY 161 B on all three images; the
  sibling's Setup varstore is one byte smaller (514 vs 515) with one
  fewer question (407 vs 408) and uncovered unchanged — measured,
  registered, not smoothed. The Setup varstore GUID
  (`ec87d643-…`) is the B450 register's own GUID.
- **PSP structure stability**: 14 dirs / 221 blobs / 10 skipped on all
  three, the same `by_magic` {PSP:5, BHD:5, PL2:2, BL2:2} as the B450
  3604 authorship row — the AMD directory layout is one layout.
- **The set deltas order like the whole-ROM differ**: 37 bodies differ
  between releases, 65 between boards — 37 < 65 exactly as
  22.5 % < 32.0 %. The version-number trap law reproduces on the PSP
  axis.
- **The discriminator law**: the IFR quartet CANNOT separate 3644 from
  3645 (release identity); the PSP set can (the 37-body delta). On
  16/09, the PSP hashes alone settle stock-3644 vs flashed-3645.
- **The shared path is one path**: the B450 authorship rows (3604:
  14/223/10, 3802) still reproduce through the same proposer code —
  if B450 ever drifts, B550 proposes nothing (the L2-transfer law).

## Front D — the machine-derived lens-witnessed scoreline

The ring-44 scoreline (4/8/14) was measured WITHOUT lenses. With the
B550 lens values piped through the FROZEN oracle (no hand counting —
`fw35.Oracle.score` on the ring-44 exam findings + the lens values),
the WITH-lenses expectation for a stock 3644 board is:

**6 hit / 1 partial / 10 miss / 9 na** — hits {P-03, P-06, P-08,
**P-13**, **P-16**, P-18}, partial {**P-15**}.

The partial is the ring's last lesson: 161 is outside P-15's frozen
band [126, 158] but inside its registered `widened` [110, 174] — the
register's own semantics, not an estimate; a first manual reading
called it a miss and the oracle corrected the ring. P-12 misses
(14,431 out of [7,900, 8,050]); P-19 misses machine-derived (the
cross-family overlaps are 40 vs 40 — the checker's strict inequality
fails on equality, the B550 direction law the P-19 checker never met);
P-14 stays na (its observed key is the exam's NVRAM variable row, null
on B550 — and the IFR cross's varstore size 515 is a DIFFERENT
quantity; the conflation is pre-empted in the register). Both
scorelines stand: neither is a correction; the register is frozen.

## Front E — what the 16/09 dump means now

The protocol gains its B550 first-class path (all pre-registered in
`vendor-b550-lens.json`):

1. `python3 lab/fw45-b550-lens.py propose dump.rom --out
   proposals.json` — the L2-transfer gate re-derives all 57 anchor
   rows + the 10 shared B450 rows, then proposes; the review table
   marks each slot `== stock-3644 anchor` or `!=` with the anchor
   value beside it.
2. Operator review — corrections beat proposals, always.
3. `python3 lab/fw42-dossier.py dossier dump.rom --lenses
   proposals.json` — the weld consumes them (7/7 proposals land as
   journaled lenses, provenance `lens`, 0 overrides — proven live both
   through the cheap weld proof and the full 3m20 dossier with
   `--lenses`: 31 slots, 20 filled).

The expected reading is now doubly pre-registered: without lenses the
stock scoreline is the measured 4/8/14 with identity `known-clean`
against `b550w2-3644.rom`; with lenses it is 6/1/10/9 with the
P-15 partial. Every deviation is the board's own NVRAM/flash story —
and the PSP set tells flashed-forward-from-stock (delta 37 against
3645, IFR identical) apart from anything else.

## Honesty ledger

- The ring-44 attribution ("L3 refused to guess") is corrected by
  measurement, not edited away: the new registers carry the correction,
  the old ledger stays frozen.
- The B550 anchor set is proposer-derived and cross-checked across
  three vendor-verified images — it is NOT an independent-ring register
  in the B450 sense; the transfer laws plus the shared-path B450
  calibration are what make it a basis. The claim is stated where the
  anchors live.
- The sibling's Setup uncovered staying EXACTLY 161 while the varstore
  shrinks one byte is a coincidence the register declines to smooth.
- The 14 delta rows are classified before being counted: real strings,
  wrong axis; the whitelist genome transfers whole.
- fw43 is untouched (its B450 rows remain its only basis); fw41 is
  untouched (its summary was right); the frozen surface grew zero
  bytes: bin/, lib/, tests/ 0 diff, 323/323 checks, MCP smoke 12 tools.
