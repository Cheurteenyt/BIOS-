# The tenth ring — the general rehearsal: the pipeline proves itself before the machine (2026-09-11)

> Companion to `ovmf-findings.md` and rings one through nine. Same
> campaign, same rules: read-only, zero bytes written, surface freeze
> untouched. Instruments this ring: `ring10_rehearsal.py` and
> `ring10_diag.py` (sandbox-side orchestrator and classifier — neither
> enters the repo). Artifact: `ovmf-rehearsal.json` (this repo). The
> claim under test is ring 9's closing sentence: *the vendor dump
> arrives into a pipeline that names every GUID, unpacks every
> signature list, and prices every volume — no new code is needed on
> the vendor image, only new inventories.*

## Front A — the general rehearsal (la générale)

Nine rings produced fourteen probe scripts and sixteen artifacts, but
they were never run end to end in one pass — each ring ran its own
front once and moved on. Ring 10 chains all of it, timed, with a
safety net: every artifact is backed up before the chain and restored
afterwards; the only lab file the rehearsal writes is its own record.

- **Run 1: the chain runs clean but is not byte-reproducible.**
  14/14 stages exit 0 in 25.37 s — zero crashes, zero intervention —
  yet three artifacts come back byte-changed (`ovmf-ms-delta.json`,
  `ovmf-scsu-strings.json`, `ovmf-siglist.json`) and the facade
  artifact churns mid-chain before converging. Three artifacts are
  restored from backup. Verdict: PARTIAL — and that is the honest
  result a general exists to produce.
- **The facade converges by design.** Stage 7 rewrites the facade
  without its ring-8 resolution field, stage 8 re-finalizes, stage 11
  (pkg3) re-adds the resolution and the artifact returns byte-identical.
  Mid-chain churn is recorded as data; chain identity is judged at
  chain end. A rewriting stage is not a failing stage.
- **Run 2: REPRODUCIBLE.** After the front-C repairs below, the full
  chain re-runs in 25.35 s, all 14 stages exit 0, all 16 artifacts
  end content-identical, zero restored. Comparison is canonical:
  JSON re-serialized with sorted keys, with one registered noise
  field zeroed (see Front C).

## Front B — classifying the nondeterminism: three natures, two defects, one nature

`ring10_diag.py` re-runs each non-reproducible producer and diffs the
regenerated artifact against the original structurally. The three
cases are three different species:

1. **Ordering instability** (`ovmf-ms-delta.json`): the `changed`
   list was built by iterating a Python `set` — same 120 elements in
   an unstable order. A defect in the instrument, fixed at source:
   the intersection is now sorted before iteration. Semantics never
   changed; the artifact's diff-noise did.
2. **Artifact/producer drift** (`ovmf-scsu-strings.json`): the
   regenerated output carries two `_meta` keys the pushed artifact
   lacks (`decoder_seeding_rule`, `header_layout_observed`) — the
   ring-8 fallback-rule registrations were added to the script after
   the artifact was last written. Not nondeterminism: staleness. The
   regenerated superset is adopted as the baseline.
3. **Measurement noise** (`ovmf-siglist.json`): the scale rehearsal's
   `entries_per_second` is a wall-clock benchmark (426,158 vs
   429,661 across runs — 0.8 %). Irreducible by nature; registered
   in the comparison definition (canonical hash zeroes the field)
   rather than pretending it is stable.

## Front C — the day-0 protocol becomes a repo document

Until this ring the vendor-image reading protocol lived in
conversation memory and lab narratives. It now lives in the repo:
[docs/day0-protocol.md](../docs/day0-protocol.md) — the lab half of
the doctrine, paired with the machine half in `docs/digital-twin.md`.
It fixes, before the machine arrives: the stage order and the
question each stage answers; the five tripwires (empty-string dbx,
nesting rule, unknown-opcode policy, zero-raw-GUID target, category
errors); the vendor-report skeleton; and the honesty line — the
rehearsal proved reproducibility on OVMF, not on vendor silicon.

## Honesty ledger

- The rehearsal's specimen set is the four OVMF code builds; a
  production ASUS image (16 MB map, AMI structs, vendor NVRAM) will
  exercise structures OVMF never shows. The protocol's promise is a
  fixed reading order and fixed rules, not known answers.
- Canonical comparison (sorted keys, one zeroed noise field) is a
  weaker bar than raw byte-identity; the raw-byte view was also
  observed (run 1) and is recorded in the artifact's comparison note.
- The orchestrator and classifier are sandbox scripts; the repo
  receives only the rehearsal record and this narrative — the frozen
  surface is untouched by construction.

## Consequences for day-0 (16/09)

- The claim "only new inventories" is now a measured fact on this
  specimen set: 14 stages, ~25 s, zero intervention, zero drift.
- The first vendor-image runs will time the same chain against the
  real dump; any stage that surprises is a finding registered in the
  same format, not a reason to improvise.
- The scsu drift closure matters beyond tidiness: the artifact and
  its producer are now provably in sync — the rehearsal makes
  artifact staleness a detectable event, not a silent one.

## The ledger self-correction chain, one line per ring

Ring 9 found nothing left to dissolve and paid down names; ring 10
points the instrument at itself and finds the last soft spot —
reproducibility — and closes it with two one-line repairs and one
adoption. The chain now runs clean twice in a row, and the protocol
that runs it is a document, not a memory.
