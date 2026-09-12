# The Thirty-First Ring — the storm, caught live

*2026-09-12 — software-only (QEMU), the vendor-faithful lane and the deterministic lane*

Ring 30 closed ring 29's micro-threads and left two residuals in the honesty
register: the storming boot's live PDE state had been *inferred*, never
captured; and the SMMSTORE lane's post-mortem read (PDE[38]=0x4c000e1) kept a
merge-agent sub-question open "until rebuilt". This ring caught the storm
live — and in doing so discovered that the paradox ring 29 left behind was
never a mystery at all. It was a flag-decode error.

## Front 31a — the storming boot, watched

The instrument: every boot runs under the QEMU gdbstub with hardware
watchpoints on PDE[38]@0x4803130 (covers 0x4c00000-0x4dfffff, the moat) and
PDE[39]@0x4803138 (covers 0x4e00000-0x4ffffff, the DxeCore stack region)
armed from reset. 22 boots in the RELEASE+EMU lane (the ring-30
vendor-faithful build): 20 green, **2 storms caught** (hunt6, hunt7) — a
rate consistent with ring 30's unwatched 2/40 and pooled 3/46.

The storms' moat-write sequences are **byte-identical to the green boots**:
stop A the 2-MiB fill (`0x803f87`), stop B PDE38=`0x4c00083` (RW), stop C
the 4-K PT fill (`0x80181d`, PDE39=`0x4c04003`), stop D the RO-clear pass
(`0x8042bc`, PDE38=`0x4c00081`) — then nothing. The carve does not differ
on the lane that dies. The fatal dumps differ only in nesting depth:
RIP `0x1F98CCAC` / CR2 `0x4DFFEC0` and RIP `0x1F98CBD7` / CR2 `0x4DFFFF8`
— CR2 always just below the `0x4e00000` boundary, inside the moat.

A wall was named on the way: in both storm sessions the `continue` after
stop D was rejected with *"Cannot execute this command while the target is
running"* — the QEMU gdbstub watchpoint desync. The repeated-continue
instrument (catch script, then three parallel catchers on ports
1234/1235/1236 with per-catcher disk copies) ran clean on 12 more boots.

## Front 31b — the deterministic lane

Ring 29 recorded that the RELEASE+SMMSTORE_V2 lane storms *deterministically*
— the perfect catch. The lane was rebuilt (`CONFIG_SMMSTORE_V2=y` → payload
`-D VARIABLE_SUPPORT=SMMSTORE`, the mapping re-verified in
`payloads/external/edk2/Makefile`; DXEFV census confirms
`SmmStoreFvbRuntimeDxe` + `VariableRuntimeDxe`), with the ring-30 EMU state
backed up first and **restored** at session end (sanity boot green).

The reproduction is byte-identical to ring 29: fatal #PF at RIP
`0x1F970CAC`, CR2=`0x4DFFF60`, e=0003, CR3=`0x4801000`. Three frozen
sessions then dissected it:

1. **Watchpoints** (stops A-D): identical to the EMU lane. The SEC carve is
   universal.
2. **The fxsave breakpoint** (hw breakpoint on the fatal site `0x1F970CAC`,
   executed on every nested delivery): HIT1 shows PDE38=`0x4c000e1`,
   PDE39=`0x4c04023`, RSP=`0x4ed8560` — the stack still *above* the
   boundary.
3. **64 deliveries observed** (watchpoints kept armed): the cascade
   oscillates in the `0x4ed7xxx`-`0x4ed8xxx` band and the ring-29 **0x660
   nesting step is visible live** (HIT11→13: `0x4ed8320` → `0x4ed81f0` →
   `0x4ed7b90`). PDE38 stays `0x4c000e1` and PDE39 stays `0x4c04023` for
   the whole cascade. No fatal crossing occurs under per-delivery
   freezing — **the observer effect is real**: each freeze delays the next
   interrupt arrival, the handler unwinds between deliveries, and the
   compounding nesting that crosses the boundary never builds while
   watched.

## The verdict — and the correction of ring 29

**The decode.** `0x4c000e1` = `0b1110_0001` = Present + Accessed + Dirty +
PS(2-MiB). **R/W = 0.** The post-mortem PDE that launched the merge-agent
hunt was *still read-only*. Ring 29's "2-MiB, PRESENT, R/W=1" text and the
"tables had been merged back" / TLB-shadow theory built on it were a
flag-decode error. The #PF e=0003 — supervisor write to a present RO page —
is fully consistent with the static tables. No shadow translation ever
existed.

**The agent.** Watchpoints armed from reset in three regimes (EMU green,
EMU storming, SMMSTORE deterministic) caught every instruction-store to
these PDEs: exactly the four SEC writes, then nothing, ever. The only
post-carve deltas are walk-time flag updates — PDE38 +A+D, PDE39 +A — set
by the page walker host-side in TCG, invisible to guest-instruction
watchpoints (the named blind spot: a watchpoint proves the *absence of
software writes*, not the absence of flag deltas). **The merge agent does
not exist, in any lane.** Ring 30's verdict, extended.

**The storm is geometry.** SEC carves a 2-MiB RO moat below the stack
region; the un-EOI'd HPET cascade nests 0x660 per re-delivery; the fatal
delivery is the one whose compounded nesting pushes the exception-entry
`fxsave` target below `0x4e00000` into the moat. That is the whole story.

## Instrument walls (named, for the next session)

- gdbstub watchpoint desync after stop D in storming sessions (transcript
  cut, guest runs on, hangs under gdb — no triple-fault reset while
  attached).
- Conditional breakpoints on the QEMU gdbstub desync systematically (3/4);
  unconditional breakpoints are stable (3/3). Use unconditional +
  post-hoc filtering.
- The frozen pre-fatal instant is not capturable by per-delivery freezing
  (observer effect) — it remains the ring's one registered residual.
- Walk-time A/D updates are invisible to instruction watchpoints; the D
  bit on a faulting write is a QEMU softmmu behavior (real silicon does
  not set D on a faulting access) — the verdict rests on RW=0 everywhere,
  which is decode-robust.

## Consequences

- `docs/open-questions.md`: the two ring-30 follow-ups are CLOSED
  (storming-boot watchpoint session — done, with the desync/observer
  boundary recorded; SMMSTORE merge-agent sub-question — closed as *absent
  everywhere*, with ring 29's decode corrected).
- Ring 29's narrative in `lab/vol5-fw29.json` is a historical record and
  stays untouched; this ring's JSON is the correction of record.
- The lane is restored: the scratch environment stands at the ring-30
  RELEASE+EMU state, sanity-booted green (exit 0, CHAIN OK).
