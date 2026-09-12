# The twenty-ninth ring — the RELEASE lane, the interrupt storm, and the vestigial abort

> The world-naming stub of ring 28 answered *whose world is this*. The
> twenty-ninth ring asks the question every vendor answers with a
> shipping binary and never with a word: *what does the world look like
> when it is built the way the vendor builds it?* The lab lane was
> DEBUG; the vendor lane is RELEASE. Between the two sat two open
> threads of ring 28's honesty ledger — the wall 28-w4 stack-RO
> sub-question, and the AcpiPlatform abort — and, as the measurement
> would show, the DEBUG numbers were partly kind fiction. All three
> fronts close measured. Zero bytes were written outside the artifacts.

## Front 29b — the stack-RO sub-question, arbitrated live (gdb + `-d int`)

Ring 28 registered, in one breath of honesty: *the RELEASE build
crashes, the dump resolves to CpuDxe.dll only because CpuDxe owns the
exception handler, its own `fxsave` onto a present-but-RO stack page
faults first; sub-question registered, not guessed.* The twenty-ninth
ring spent its deepest probe on that sentence.

**The lane.** The failing configuration is exactly the one wall 28-w4
mapped: `CONFIG_SMMSTORE_V2=y` in coreboot forces
`-D VARIABLE_SUPPORT=SMMSTORE` into the EDK2 payload
(`payloads/external/edk2/Makefile:75`), the SmmStoreFvbRuntimeDxe
cannot open its medium under `-bios` (QEMU flash is ROM — the
principled EMU-variable lane exists precisely because of this), the
variable/RTC/monotonic/capsule arch protocols never install, and
`CoreAllEfiServicesAvailable()` returns Not Found. In DEBUG that path
asserts at `DxeMain.c:578`. In RELEASE the assert compiles away and the
boot continues into the void.

**The wire.** One bounded boot, `-d int,cpu_reset` on, 512 MiB, q35.
The interrupt log holds **1806 events of vector 0x40 and exactly one
`v=0e`**. The tail of the series is the whole story:

```
1801: v=40 IP=...1f964021 SP=...4e01c88
1802: v=40 IP=...1f964021 SP=...4e01628   (-0x660)
1803: v=40 IP=...1f964021 SP=...4e00fc8   (-0x660)
1804: v=40 IP=...1f964021 SP=...4e00968   (-0x660)
1805: v=40 IP=...1f964021 SP=...4e00308   (-0x660)
1806: v=0e e=0003 IP=...1f970cac SP=...4dfff60 CR2=...4dfff60
```

Five deliveries of the same vector at the *same instruction pointer*,
each leaving the stack pointer exactly **0x660 bytes lower**, then a
page fault whose error code **e=0003** — supervisor *write* to a
*present* page — and whose CR2 equals the stack pointer itself. The
stack walked down in equal steps and died on the page at the
0x4e00000 boundary.

**The two instructions.** The RELEASE CpuDxe.dll disassembles cleanly
(GCC5 ELF, RVAs = runtime offsets against the dump's ImageBase):

- `RVA 0xDCAC = fxsave (%rdi)` — the fault site. This is *inside* the
  exception/interrupt entry stub of `CpuExceptionHandlerLib`: the asm
  carves its CPU-save context out of the stack (`sub rsp`, no memory
  writes), then the **first real write** — the `fxsave` of the FP
  state, 512 bytes starting at the carved address — lands 0xa0 bytes
  inside the boundary page. CR2 = that address, exactly. Ring 28's
  guess was right *in the letter*: the fxsave is the faulting
  instruction.
- `RVA 0x1021 = ret` of `AsmEnableInterrupts` (`sti; xor eax,eax;
  ret`) — the instruction the ticks kept interrupting. Not a handler,
  not a stub: the tail of *EnableInterrupts itself*.

**The live page tables (gdb, attached post-crash).** CR3 unchanged
(0x4801000); CR0 = 0x80010011 (**WP=1** — supervisor writes respect
RO). The page-directory entry covering the fault region reads
`0x4c000e1` — a **2-MiB, present, read-write** direct map. A
supervisor write to that region cannot fault with e=0003 *under this
table*. The conclusion is the ring's sharpest edge: **the RO
translation that faulted existed in the TLB while the memory tables
had already been merged back to a 2-MiB direct map.** The machinery
that splits and merges (the payload entry's `ToSplitPageTable` splits
around the stack; image protection applies `EFI_MEMORY_RP`/RO+X per
region — PDE[37] = `0x4a00081`, a 2-MiB **RO+X** image region, visible
in the same walk) moved under a running system whose TLB kept the old
truth. The "present-but-RO stack page" of ring 28 was a *translation
shadow*, not a wall.

**The preserved frames.** The original stack above 0x4e00000 survived
untouched: repeated interrupted contexts at the EnableInterrupts `ret`,
and — at level zero, under the nested frames — the caller's frame
holding a 12-byte buffer reading `Auth`+`cAMD`+`enti`, followed by
`cmpl $0x756e6547, -0x34(%rbp)` — "Genu". The buffer is the CPUID
vendor string assembled in **EBX, ECX, EDX order** — the register-order
anagram of `AuthenticAMD` — inside CPU feature-detection code that
spins with interrupts re-enabled. The tick magnet that started the
cascade.

**The vector, named.** 0x40 is not a coincidence and not an SMI: the
payload's `EFI_TIMER_ARCH` is **`PcAtChipsetPkg/HpetTimerDxe`** (the
FV roster proves it — `OvmfPkg/LocalApicTimerDxe` is *not* built into
UefiPayloadPkg; only SioBusDxe survives from OvmfPkg). HpetTimerDxe
registers `TimerInterruptHandler` on **`PcdHpetLocalApicVector` =
0x40** (`PcAtChipsetPkg.dec:59`) and routes the timer IRQ
**level-triggered** through the IOAPIC
(`IoApicConfigureInterrupt(..., TRUE, ...)`). Green boots show the same
vector absorbed normally — the classic tick-magnet poll loop, one
increment of RAX per delivery at a fixed IP. The storm is the same
delivery *without* the EOI completing: a level line still asserted is
re-delivered immediately at the IRET-restored RIP, the handler's full
0x660 frame stacks again, and five nestings later the stub's fxsave
falls through the floor. `HEAP_GUARD_NONSTOP_MODE` is FALSE by PCD
default, so CpuDxe's #PF handler does not dance — it dumps
(`DumpCpuContext`, the RELEASE register block on the serial wire) and
`CpuDeadLoop()`s, measured as a `pause; jmp` spin at CpuDxe+0x1328.

**Verdict.** Ring 28-w4's sub-question closes **measured, and rewritten**:
the crash is an **un-EOI'd level-triggered HPET interrupt cascade**
(vector 0x40) descending the DxeCore stack in 0x660 steps to the
0x4e00000 boundary, with the fatal write being the exception stub's
`fxsave` against a **stale RO translation** of a region the tables had
already merged back to 2-MiB RW. Not a guard page. A storm, and a
shadow.

## Front 29a — the vendor-faithful matrix (RELEASE)

The vendor ships RELEASE firmware; ring 28's 3+3 matrix ran a DEBUG
payload. Front 29a rebuilds the coreboot+EDK2 world with
`CONFIG_EDK2_RELEASE=y` (EMU variable lane kept, `EDK2_SERIAL_SUPPORT=y`
kept — wall 28-w5's lesson), same disk, same FW28 stub, same 6.12.94
kernel.

Six boots: **5/6 green** — exit 0, `[world] VERDICT: coreboot world
(edk2 payload above it)` on the wire, `FW26 CHAIN OK`, clean S5 —
**and one crash**, run 2, before the stub ever printed: the RELEASE
dump resolving CpuDxe at **the same +0xDCAC fxsave site** (ImageBase
arithmetic on the dump line). The storm of front 29b is not a
property of the SMMSTORE lane; it is a property of the *lane's
interrupt wiring*, firing intermittently whenever a delivery lands in
the un-EOI'd window during dispatch. Ring 28's DEBUG 3/3 was partly
kind fiction: slower, serialized, masked.

Two quiet victories ride along:

- **The stub is RELEASE-grade.** The FW28 world-naming block —
  FirmwareVendor, config tables, SMBIOS type 0/1 walk, the honest
  verdict — prints with *zero* DEBUG infrastructure. The chain's
  entire speech was always its own.
- Wall 28-w2 re-measured: the submodule gate re-arms on every fresh
  `make` (first invocation hung past the bounded window),
  `UPDATED_SUBMODULES=1` stays a standing recipe item, not a one-shot
  fix.

## Front 29c — the AcpiPlatform abort, source-led

Ring 28's ledger: *`AcpiPlatform "start failed: Aborted"` in the
coreboot world — chain unaffected, registered as an open observation.*
The source closes it in three lines:

1. The driver is `MdeModulePkg/Universal/Acpi/AcpiPlatformDxe`
   (UefiPayloadPkg.fdf:345) — the OVMF-heritage installer that reads
   ACPI tables from an **FV storage file**
   (`PcdAcpiTableStorageFile`) via `EFI_FIRMWARE_VOLUME2`.
2. `LocateFvInstanceWithTables` walks every FV handle hunting for that
   file; UefiPayloadPkg's DXEFV carries none — the tables arrive from
   coreboot **via HOBs**, consumed by AcpiTableDxe. The loop
   exhausts, returns `EFI_NOT_FOUND`, and line 191 converts it to
   `EFI_ABORTED` — the entry fails, DxeCore prints
   `Error: Image at ... start failed: Aborted` (a DEBUG-only line:
   the RELEASE lane swallows it silently).
3. The real table flow never needed this driver: coreboot → HOBs →
   payload entry → AcpiTableDxe → kernel, measured complete every
   boot (ACPI PM S0–S5, clean S5).

**Verdict: benign-by-design — a vestigial OVMF-ism.** The DEBUG lane
simply spoke a truth the RELEASE lane swallows. Day-0 consequence: the
same message class, ever seen on real hardware, carries the same
meaning — an optional FV-table installer failing while HOB-fed tables
do the work.

## Consequences for day-0 (16/09)

- The lab lane is now vendor-faithful: RELEASE payload, green 5/6,
  failure classes named. The checklist rows written against DEBUG
  numbers survive unchanged, now with an error bar.
- Bench-day SMMSTORE calibration gains its software half: under
  `-bios` (ROM flash) the SMMSTORE lane dies not by a static wall but
  by interrupt cascade into the stack floor — the calibration point
  has a mechanism, not just a symptom.
- The stack-RO micro-threads that stay open: the writer of the RO 4-K
  translation and the agent of the 2-MiB merge (measured around, not
  yet named), and the storm's exact trigger window (TCG timing vs the
  HPET period). Both are registered in `docs/open-questions.md`.

## The honesty ledger

- Storm sample: 1 crash in 6 RELEASE+EMU boots plus the deterministic
  SMMSTORE-lane reproduction; no probability claim.
- The run-2 crash has no `-d int` capture (instrumentation followed
  the first crash); the signature evidence is the dump's fxsave IP and
  ImageBase arithmetic.
- The `AuthcAMDenti` buffer is measured in the preserved stack; its
  owner module is named by function class (CPU feature detection,
  `cmpl "Genu"`), not by file — the RELEASE layout has no driver-name
  prints.
- The early 1800 v=40 deliveries of the deterministic run were
  absorbed normally; only the final six cascade.
- The OVMF-side logs are untouched ring-26/27/28 evidence; every new
  measurement is coreboot-lane.
- Scripts: `fw29b_gdb_probe{,2,3}.sh`, `fw29a_lvt_probe.sh` live in
  the session instrument directory, untracked by doctrine; the JSON
  artifact carries the full recipe.
