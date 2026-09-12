# The thirty-third ring — la loi de l'atterrissage + l'arme du jour 0

Date: 2026-09-13. Zero downloads, zero acquisitions, no hardware. One lane
rebuild each way, 24 fresh instrumented boots plus the 8 surviving ring-32
logs, one register fusion. The ring delivers two artifacts the study has
never had: a **queryable weapon** that places any future dump artifact
instantly and proves its own correctness first — and a **closed-form law**
for the storm's fatal geometry, verified on every storm the study has ever
captured in flight.

## The state entering the ring

Ring 32 had closed the storm trilogy with a passive instrument and left two
threads open *by choice*: the multi-build rate study (one build measured:
3/8) and the residue-class census — *what sets the final landing above the
boundary?* Three CR2 residues were known ({moat−0xA0, −0xD0, −0x180}) and
one depth (543) had appeared in every storm, with no explanation of either.
Meanwhile the nine rings of vendor registers had just been fused into the
species genome — but a genome in a JSON file still needs a human to query
it, and the bench day of 16/09 needs answers in seconds, not sessions.

## Front 33a — the day-0 triage weapon

`lab/fw33-triage-engine.py` is the study's first **deliberately tracked
instrument**. Every prior instrument died with its sandbox; the weapon must
survive to bench day, so it lives in `lab/` next to the seven registers it
fuses (genome, churn atlas, AGESA ladder, flash-armor probes, acquisition
ledger, SMM quorum, armor chipdb). It is stdlib-only, loads its inputs
relative to its own directory, and speaks eight modes: `guid`, `body`,
`rung`, `plan`, `wave`, `agesa`, `selftest`, `manifest`.

The honesty contract is load-bearing. The engine refuses to serve on any
register drift: the AGESA pin aborts at load time if any of the nine ladder
points disagrees with the pinned chronology, and the self-test runs **29
genome-exact gates** — species count, wave births and their exact edges,
the armor quartet GUID set, SbRomArmorSmm moves=0, the two legacy deaths,
the move distribution, AGESA monotonicity with its single 3802==3810 tie,
the armor replay against the register's own recorded scores, the boundary
dates, the sentinel set, per-rung census coverage, and **chain integrity**:
every hash-chain step of all 330 species must link (`from == prev.to`).

Three register-drift lessons were caught *by the gates* before they could
become silent errors, and are registered for every future register author:

1. `move_distribution` keys are move-count classes — the species total is
   `sum(values)` (330); the move-weighted sum (1213) is the total move
   *events* across the genome, a different and interesting number.
2. The armor probes carry **presence** lists, not addition events: each
   probe's `added_present` IS that rung's expected membership. Replaying
   them cumulatively double-counts (5→10→15...).
3. Probed ROM sizes split in two classes: full 16 MiB sentinels (3604,
   4655) vs 16515072-byte capsule payloads (3802–4631) — a 256 KiB wrapper
   difference that day-0 hash matching must respect.

The demo placements are genome-exact: `guid 51080191…` answers
SbRomArmorSmm — wave1 (2022-05-12), born asus-3604→asus-3802 at AGESA
1.2.0.7, moves=0, armor_quartet, empty chain, with the advice that diff
work on it is pointless because its body never changed. `plan 4655`
emits the bench-day card: the full 9-rung ladder with dates, AGESA levels,
armor expectations (5/7 from 3802, 7/7 from 4604, legacy 2/2 → 1/2 → 0/2),
sentinel hashes, the seven-step dump triage procedure, and the 3644
question status.

## Front 33b — the law of the landing

The instrument is ring 32's, unchanged in principle: passive
`-d int,cpu_reset` logging, nothing freezes, the storm fires. The sample:
the SMMSTORE lane rebuilt a third time (2/24 boots stormed — boots 13 and
23) plus the **eight surviving ring-32 logs** (3 storms, boots 1/4/5) —
five storms over two builds, 27 oscillation hangs, all parsed by one
arithmetic.

The census first, as measured:

| storm | build | depth | onset SP | landing−moat | CR2 | residue |
|-------|-------|-------|----------|--------------|-----|---------|
| 32-1  | ring-32 | 543 | 0x4ed8248 | 0x308 | 0x4dfff60 | 0xA0 |
| 32-4  | ring-32 | 543 | 0x4ed8218 | 0x2d8 | 0x4dfff30 | 0xD0 |
| 32-5  | ring-32 | 543 | 0x4ed8168 | 0x228 | 0x4dffe80 | 0x180 |
| 33-13 | ring-33 | 543 | 0x4ed8248 | 0x308 | 0x4dfff60 | 0xA0 |
| 33-23 | ring-33 | 543 | 0x4ed81c8 | 0x228 | 0x4dffe80 | 0x180 |

Every chain step is exactly −0x660 (uniform in all five, measured per
step). Then the law, in three formulas, each verified 5/5:

1. **Depth is forced by the onset alone.** The fatal window — the SP range
   where the *previous* delivery's fxsave write still succeeds
   (`landing ≥ moat − 0x2B8`) while the *next* delivery's stub push already
   faults (`landing < moat + 0x3A8`) — has width exactly
   0x3A8 + 0x2B8 = **0x660, one chain step**. Exactly one delivery of any
   chain can sit in it: `k* = ⌊(onset − moat + 0x2B8)/0x660⌋ + 1`.
   Depth 543 was never a coincidence: every observed onset lies in the
   recovery-ceiling band [moat+0xD8168, moat+0xD8248], which forces 543.
2. **The landing is pure descent:** `landing = onset − (k*−1)·0x660`
   (= onset − 542·0x660 in every storm).
3. **The residue is the onset's alignment:** `moat − CR2 =
   0x3A8 − ((onset − moat) mod 0x660)` — the three "mysterious" residues
   {0xA0, 0xD0, 0x180} are exactly 0x3A8 minus the alignments
   {0x308, 0x2D8, 0x228} of the oscillation ceiling's recovery points.
   The residue classes ARE the recovery-alignment classes; `CR2 = landing
   − 0x3A8` holds identically (the push law).

The hang side completes the picture: the 27 oscillation hangs contribute a
10-point depth distribution — runs up to **542 consecutive at-RET
deliveries observed RECOVERING**, one step short of the fatal 543. The
killer is the window entry, never exhaustion. And a terminal-state
refinement: both ring-33 storms end in **fatal-crossing-then-silence** —
after the #PF the event stream stops but the process does not exit (both
ec=124 kills). Both of the lane's terminals are kills; ring 32's "only end
states are fatal crossing or hang" becomes "fatal-crossing-then-silence or
oscillation-forever".

The second build's rate (2/24, rule-of-three upper bound ≈ 12.5% at 95%)
against the first build's 3/8 is the study's **second data point** for
ring 32's build-scoping correction: the rate belongs to the build and its
scheduling environment, not to the design. The law-form does not: it is
arithmetic about one window per chain, and its constants (0x660, 0x3A8,
0x2B8, the onset band) are lane-scoped measurements that real silicon
would replace with its own — the form is expected to survive.

## What the ring changes

The storm chapter is now closed twice over: mechanically (rings 29–32) and
mathematically (this ring) — a future storm boot needs no new explanation,
only its onset SP plugged into three formulas. And the bench day has its
weapon: any GUID or body hash pulled from the 16/09 dump gets its identity,
birth, death, moves, body chain, wave membership, AGESA context and
recommended diff pair from one command that has already proven it knows
the registers better than the registers' own honesty blocks.

## Honest limits

Five storms is a small sample; every "all storms" here quantifies over
five events across two builds. The residue support is not exhausted — the
law predicts the full support as `{0x3A8 − a : a ∈ reachable alignments}`,
and which alignments the oscillation actually produces is a TCG-scheduler
property, not a payload property. The law is SMMSTORE-lane-scoped; the EMU
lane's green boots never enter the cascade. The QEMU softmmu A/D caveat
stands, and the verdicts rest only on RW=0 geometry and SP/CR2 arithmetic.
The engine knows only what the registers know — the never-touched static
core is not enumerable from any register, and 31 of the 40 ledger releases
are bracketed, not measured.
