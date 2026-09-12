# The thirtieth ring — the storm and the static moat

> Ring 30 (2026-09-12). Software-only, QEMU, the surviving scratch-ring28
> environment. The three micro-threads left open by ring 29's honesty
> ledger — the storm's trigger window, the AuthcAMDenti buffer's owner
> module, and the writer of the RO entry plus the agent of the merge —
> are closed by measurement. One of ring 29's conclusions does not
> survive the measurement: the merge agent does not exist in the
> vendor-faithful lane. The shadow was a moat all along.

## Front 30a — the storm window, measured as a rate

The vendor-faithful RELEASE+EMU lane (the lane that matters: what the
vendor actually ships) was Monte-Carlo'd on the unchanged ring-29
constants — same q35, 512 MiB, `fw28-disk.img`, FW28 stub, 6.12.94
kernel, same `coreboot.rom` build. Forty fresh boots, each bounded at
60 s, serial-classified by signature.

**Result: 38 green / 2 storm** (runs 5 and 7). This session's rate is
2/40 = 5.0%; pooled with ring 29's 1/6 matrix the estimate is 3/46 ≈
6.5%, with an honest binomial width (Wilson 95% CI ≈ [1.4%, 16.9%] for
this session alone). The storm is real, intermittent, and rare enough
to hide behind any DEBUG-lane matrix smaller than a dozen boots —
ring 28's 3/3 green was exactly such a hiding.

Every storm run carries the byte-identical ring-29 signature: the
RELEASE dump resolves `CpuDxe.dll` (ImageBase `0x1F97F000`) at
RIP `0x1F98CCAC` → RVA `0xDCAC` (the exception-stub `fxsave`), CR2 on
the same boundary-page family (`0x4DFFF70` this session, `0x4DFFF60`
in ring 29), CR3 stable at `0x4801000`. And the green-vs-storm serial
diff shows **no coreboot-stage precursor** — only 1–2 ms jitter in the
BS stage timings. The window lives inside payload DXE dispatch and is
a pure TCG-scheduling race, not a state divergence.

## Front 30b — the ghost caught in the act (and the ghost's non-existence)

Ring 29's post-mortem PD scan named the watchpoint targets: PDE[38] at
`0x4803130` (covering `0x4c00000–0x4dfffff`, the region under the
DxeCore stack boundary) and PDE[39] at `0x4803138` (the stack-top
region, 4-K PT at `0x4c04000`). The method: QEMU gdbstub hardware
watchpoints from reset, armed across every phase — identity mapping
keeps linear==physical with paging off, in the 32-bit builder, and in
DXE alike.

The session caught four writes and then silence:

| Stop | RIP | write | reading |
|---|---|---|---|
| A | `0x803f87` | PDE[38] `0 → 0x4c00000` | the 2-MiB PDE fill loop (`mov %edx,0x4(%rsi); add $8,%esi`), CR3=0, 32-bit pre-paging |
| B | `0x803f8f` | PDE[38] `→ 0x4c00083` | same loop adding flags: P(RW,PS) — the direct map |
| C | `0x80181d` | PDE[39] `→ 0x4c04003` | the 4-K PT fill for the stack-top region (entries `\|3` = P\|RW) |
| D | `0x8042bc` | PDE[38] `0x4c00083 → 0x4c00081` | **the RO writer**: the sub/sbb bounds loop clearing R/W over the protected region |

After Stop D: zero further writes through paging-enable, full DXE,
kernel hand-off, and clean S5. **The merge-back agent does not exist
in the RELEASE+EMU lane.** The tables are static from the moment SEC
finishes; no split, no merge, no runtime page-attribute surgery ever
touches PDE[38].

All three writer sites were then fingerprint-matched by exact byte
window into `coreboot/build/UEFIPAYLOAD.fd` at offsets `vaddr −
0x800000`: every hit lands in the first FFS file (`0xe8–0x51a0`,
type `SECURITY_CORE`) — the payload's SEC module, executing 32-bit,
pre-paging, at `0x800000`. The moat is written by SEC before paging is
ever enabled.

### The revised mechanism: the storm and the static moat

SEC builds the initial identity map with a static protection policy
baked in: the stack-top region above `0x4e00000` is 4-K mapped and
RW; the 2-MiB region below it is a read-only direct map. Green boots
keep the DxeCore stack inside its budget — the deepest observed
descent (ring 29's five nestings) bottoms at `0x4e00308`, still above
the boundary. The un-EOI'd HPET cascade consumes `0x660` bytes per
re-delivery from an initial SP near `0x4e01c88`; the sixth delivery's
exception-stub save-area write lands ~`0xa0` bytes past the boundary —
into the static RO moat — and faults `#PF(0003)`: a write to a
present, read-only page. Pure geometry. Ring 29's "stale RO
translation while the tables merged back" theory is **falsified for
this lane**: there is no merge-back because there is no split; there
is no shadow because the moat is real, static, and exactly where the
fault lands.

A lane-scoped residual is registered honestly: ring 29's SMMSTORE-lane
post-mortem read PDE[38] = `0x4c000e1` — bit arithmetic reads that as
`0x83` (builder RW) plus hardware A and D bits, i.e. an entry that was
*never* RO'd but *was* written through. That lane's table state
genuinely differs from the EMU lane; its merge-agent sub-question
stays open until the SMMSTORE lane is rebuilt (recipe available, cost
registered, not paid this session).

## Front 30c — the AuthcAMDenti buffer's owner, named at three levels

A fresh FV/FFS walker (`fw30_owner_probe.py`, stdlib-only, LZMA-aware,
nested-FV-aware — after fixing the FF-named-pad pitfall that silently
ends naive FFS walks) scanned the built `DXEFV.Fv` (66 files, 65 named
modules) for the vendor-literal fingerprints. The result is a clean
three-way rollup:

- `cmpl $0x756e6547` ("Genu") — **DxeCore**, **CpuDxe**, **HpetTimerDxe**
- the full AMD triple `Auth`+`cAMD`+`enti` as
  `cmpl $imm, -off(%rbp)` stack compares — **CpuDxe** only

Source anchor, found in the tree: `MdePkg/Library/BaseCpuLib/
X86BaseCpuLib.c` → `StandardSignatureIsAuthenticAMD()` —
`AsmCpuid(CPUID_SIGNATURE)` with EBX/ECX/EDX compared against the AMD
constants, which is byte-for-byte the shape of ring 29's preserved
buffer (the register-order anagram of "AuthenticAMD"). The statically
linked copies in DxeCore and HpetTimerDxe are sibling instances of the
same BaseCpuLib; the HpetTimerDxe copy is a delicious irony — the
storm's vector owner carries its own copy of the victim code.

The runtime level completes the naming: the interrupted chain's image
was CpuDxe (the storm IP `CpuDxe+0x1021` is the `ret` of
`AsmEnableInterrupts` inside CpuDxe's copy), and `CpuDxe.inf` links
`CpuLib` + `MtrrLib` — `MtrrLib.c:354` saves and disables interrupts
around the MTRR attribute path, restoring them exactly where the
cascade re-delivers. The owner of the ring-29 buffer is **CpuDxe's
inlined `StandardSignatureIsAuthenticAMD` executing inside its
`SetMemoryAttributes → MtrrSetMemoryAttributeInMsr` path, at the
interrupt-restore boundary of the MTRR sequence** — the exact place
where feature detection, IF re-enable, and the HPET storm intersect.

## Honesty ledger

1. The Monte-Carlo rate carries binomial width (n=40 this session);
   "5–6%" is an estimate, not a constant.
2. The watchpoint session ran a green boot. The moat writes are
   deterministic, and the storm's CR2 geometry matches the static-moat
   model — but the crashing boot's live PDE state in the EMU lane was
   inferred, not re-captured. A storming-boot watchpoint session is a
   registered follow-up (target rate: ~1 storm per 20 boots).
3. The SMMSTORE lane was not rebuilt; the reinterpretation of ring 29's
   `0x4c000e1` post-mortem read is bit arithmetic, not measurement.
4. The instruments (`fw30_owner_probe.py`, `fw30_storm_mc.sh`,
   `fw30_ghost_watch.sh`, `gdb-fw30-ghost.cmds`) are untracked sandbox
   code by house convention; the JSON artifacts and this narrative are
   the durable output.
5. Method note: the FFS walker bug — FF-named pad files are legitimate
   headers, and treating any `Name == FF×16` as free space silently
   ends the walk at the first large pad. Fixed and registered; it is
   exactly the kind of trap that makes two parsers disagree on the
   same image.
