# The thirty-second ring — l'instant en vol (the instant, in flight)

Date: 2026-09-13. Zero downloads, zero acquisitions, no hardware. One lane
rebuild, eight instrumented boots, one register fusion. The ring closes the
last open thread of the three-ring storm loop — and corrects two of its
claims — then fuses nine rings of scattered registers into the study's first
species genome.

## The state entering the ring

Ring 31 had caught the storm live under watchpoints and resolved the merge
agent into a flag-decode error — but one residual survived: **the frozen
pre-fatal instant**, declared uncapturable because per-delivery freezing
*defuses* the storm (the observer effect). Every measurement of the fatal
ladder so far had been either post-mortem (ring 29) or taken under an
instrument that stopped the CPU (ring 31b). The lane's own labels carried two
unexamined claims: the storm was "deterministic" (ring 31b) and its CR2 was
"byte-identical" across rings 29/31 (0x4DFFF60). Both were about to meet a
new instrument and a fresh build.

The corpus binaries were gone again (the sandbox reset swept the 13-specimen
storage for the fourth time in the study's history — the sha256 anchors in
the lab registers survive, the bytes do not), so the no-hardware axis ran on
two legs: the living Volume 5 lane for front 32a, the persisted registers for
front 32b.

## Front 32a — the storm caught in flight

**The instrument**: QEMU's `-d int,cpu_reset` per-exception logging. Passive
by construction — nothing stops, nothing single-steps, nothing freezes; the
logger writes one line per exception delivery and gets out of the way. If the
observer effect is about *freezing*, logging should not defuse the storm.
That was the bet; the first boot settled it.

**Boot 1 stormed.** The log holds the entire fatal ladder in flight, and its
geometry is unambiguous:

- **543 consecutive re-deliveries** landed at `0x1f964021` — CpuDxe+0x1021,
  the `ret` of `AsmEnableInterrupts` — before the fatal event. Not the five
  nestings of ring 29's post-mortem, not the 64 deliveries ring 31b counted
  under freezing: 543, in one uninterrupted cascade.
- **Every chained re-delivery descends exactly 0x660** of stack — the step
  ring 29 inferred from five post-mortem frames is now measured per-step, in
  flight, on eleven consecutive tail events.
- The ladder stays **above** the moat the whole way: zero logged deliveries
  below 0x4e00000; the final legal landing sits at 0x4e00308, moat +0x308.
- The fatal event: `v=0e e=0003` at `0x1f970cac` — CpuDxe+0xDCAC, the
  `fxsave (%rdi)` in the exception entry stub — with SP = 0x4dfff60 and
  **CR2 = 0x4dfff60, byte-identical to rings 29 and 31**. The stub's frame
  push from the last legal landing is 0x3A8; the fxsave buffer lands at
  moat − 0xA0. First crossing below the boundary, exactly as the geometry
  demands.

**The mechanism, now visible end to end in flight**: the un-EOI'd
level-triggered HPET cascade (ring 29) re-delivers into a handler that is
still executing; each chained re-delivery consumes exactly 0x660 of stack;
between chains, partial unwinds recover toward the band top (~0x4ed8xxx —
precisely the oscillation band ring 31b watched under freezing); the walk's
fate — fatal crossing or indefinite oscillation — is decided per delivery by
TCG scheduling (ring 30a's race). The three rings' fragments snap into one
picture with nothing left over.

**The sample**: eight boots, 60–90 s each. Three storms (boots 1, 4, 5), five
cascade hangs (boots 2, 3, 6, 7, 8). The rate: 3/8 — honest binomial width,
one build.

**Three corrections, all measured, all registered:**

1. **"Deterministic" was build-scoped, not lane-scoped.** The ring-32 rebuild
   used the exact ring-31 recipe and storms at 3/8, not 100%. Determinism
   belonged to the ring-31 build's binary, not to the SMMSTORE lane.
2. **"Byte-identical CR2" is quantized, not unique.** The three storms'
   crossings land at moat−0xA0, moat−0xD0, moat−0x180 (0x4dfff60, 0x4dfff30,
   0x4dffe80) — a discrete residue set of the walk's final landing above the
   boundary (+0x308, +0x2d8, +0x228), all with the same 543-deep cascade and
   the same 0x3A8 stub push. Rings 29/31 both observed the dominant residue.
   The signature is a small discrete set, not a single constant.
3. **The lane never boots green.** The five "non-storm" boots never completed
   DXE: serial ends at coreboot's `Jumping to boot code`, the stub never
   speaks, and the cascade is still alive at the kill (boot 2: 2,367
   re-deliveries at the RET, longest run 61; boot 3: 4,276 at the RET,
   longest run **513 — and it recovered**). In this lane the cascade never
   fully releases; the only two end states are fatal crossing or indefinite
   oscillation. "Green" here was always a hang that had not yet crossed.

And the residual itself: **closed**. The frozen pre-fatal instant is
uncapturable *by freezing* — but passive logging captures the entire fatal
ladder in flight, storm intact. The observer effect applies to stopping the
CPU, not to watching its exception wire.

The EMU lane was restored afterward (config + ROM backup, the ring-31
recipe); sanity boot: exit 0, CHAIN OK.

## Front 32b — the species genome of the ladder

Nine rings of corpus work left their measurements scattered across a dozen
registers: the churn atlas' frontier events, the armor gates, the quorum's
cross-vendor join, the vocabulary clock's word frontiers. Front 32b fuses
them — zero downloads, pure register surgery (`fw32_genome.py`) — into one
queryable catalog: **330 species**, every GUID ever touched by a frontier
event on the nine-rung ASUS ladder, each with its birth rung, death rung,
move count, body-hash chain, and armor flags (`lab/vendor-genome.json`).

The genome-level reads, all new:

- **SbRomArmorSmm moves=0** — one body across 4.5 years, ring 19's finding
  now exact at genome granularity.
- **The armor quartet is not uniformly frozen**: PrepareWhiteListSmm and
  FlashSmiDxe moved twice since 3802, FlashSmiSmm and the 89BE47F4 freeform
  once, SbRomArmorSmm never.
- **Births are exactly the security waves** — five at 3802, two at 4604,
  zero at every other frontier; **deaths are exactly the two legacy
  smm_driver retirements** (4202, 4402). The ladder's life events are
  security events and nothing else.
- **The churn spine**: 98 species moved exactly five times; 54 chronic
  movers (6+); 26 species moved at *every* one of the eight frontiers — the
  AGESA family, the ladder's engine room.
- **The quiet pair confirmed at genome level**: 3802→3810 is born=0, dead=0,
  moved=45.
- **Day-0 service**: any GUID found in the dump can be placed instantly —
  born when, died when, moved how often, armor-flagged or not. The genome is
  the lookup table the day-0 checklist was missing.

Honesty is registered in the artifact itself: the genome covers only species
*touched* by frontier events (the never-touched static core is not
enumerable from registers — per-rung GUID sets were computed in-session and
not persisted); names join in only at the armor quartet (the 665-entry
GUID-name map body was never persisted, only its size); cross-vendor body
sets survive only as pairwise jaccards and symbolic joins.

## The ring in one sentence

The storm was never caught in flight before because every instrument froze
it — and the first instrument that doesn't freeze shows the fatal ladder
whole (543 × 0x660 into a 0x3A8 stub push across a 0x4e00000 moat), demotes
two "deterministic" claims to build-scoped and quantized, and reveals that
the lane's only alternative to the storm is an endless oscillation that was
never a green boot at all.
