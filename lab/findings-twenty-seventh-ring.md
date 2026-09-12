# The twenty-seventh ring — the silence decomposed, and our own stub speaks

Date: 2026-09-12 · Mode: software-only (the bench day stays deferred) ·
Specimens: the ring-26 FAT16 superfloppy (evolved — see honesty), the
ring-24 coreboot.rom (untouched), Debian OVMF plain 4M, and — new in this
ring — **an EFI loader written by the study**.

## What was asked

The disk says the next front: « earlyprintk debugging is next session's
first front » — the hand-built UKI loads and starts under OVMF
(`BdsDxe: starting Boot0001`, no failure status) and stays silent. The
user's standing order: ingenuity, ultra-complex, "ce qui n'existe pas".
This ring answers the open thread by decomposing it into three measured
root causes — none of which is earlyprintk — and then builds the thing
that did not exist: **FW27, the study's own EFI stub**, which boots the
full chain end to end and talks at every stage, where the vendor firmware
refuses to speak at all.

## What stands

### Front 27a — the silence has three layers, all measured

**RC1 — the UKI sections are inert.** The x86 kernel EFI stub never reads
its own `.cmdline`/`.initrd` PE sections (v6.12 `x86-stub.c`: cmdline =
`efi_convert_cmdline(LoadOptions)`; initrd = LoadFile2 device path or
cmdline `initrd=`). Those sections are systemd-stub's food, and no
systemd-stub is in the image. Control arm C: the pristine kernel speaks
and panics **with the whole 1 MiB initramfs still embedded in its own PE**
— the stub never consumed it. The ring-26 objcopy recipe was mechanically
perfect and architecturally moot.

**RC2 — the decompression knife-edge.** `efi_decompress_kernel()` asks
`efi_random_alloc()` for `ALIGN(max(output_len, kernel_total_size),
MIN_KERNEL_ALIGN)` of conventional pages; on failure the status stays
`EFI_OUT_OF_RESOURCES` and x86-stub.c:1000 prints the **misleading**
"Failed to decompress kernel" — no decompressor ever ran. The fw_cfg RAM
floor is measured (single-run ladder): 128 MiB FAIL, 192 MiB OK → the
allocation is somewhere in (~55, ~120] MiB. At 512 MiB the disk path sits
on the knife's edge: 5/5 stub-fails with the UKI's 13.2 MiB pre-loaded,
then arm C speaks the moment the pristine kernel is exec'd without that
pre-load. The kernel source names no constraint we could not confirm; the
Debian System.map is a `-dbg` pointer stub, so the ladder IS the
measurement.

**RC3 — empty LoadOptions = mute boot.** When the allocation succeeds and
no LoadOptions exist (the auto-boot path), the kernel runs with no
`console=` and panics or waits invisibly — the ring-26 "silence" as
experienced. The earlyprintk front closes with its true answer: earlyprintk
was never reachable; delivering the cmdline is the whole game.

The probes that got us there are themselves registered: `bcfg optional
data` rejected by this OVMF shell (Invalid argument — kept in
`vol27_bcfg_probe.py`); the debugcon on 0x402 mute (RELEASE build) — the
vendor voice does not exist, so we built one.

### Front 27b — FW27: the study's own EFI stub

~260 lines of C on gnu-efi 3.0.18 (extracted root-less from trixie per the
house playbook; its headers lack LoadFile2 — we defined it from UEFI 2.10
§13.6). OVMF auto-boots it as `\EFI\BOOT\BOOTX64.EFI` and it:

1. **speaks** on ConOut — the observability the vendor refuses;
2. dumps a **memory-map summary** (112 descriptors, conventional 462 MiB,
   biggest region 419 MiB) — the measurement the mute firmware withheld;
3. walks **its own PE section table** and consumes `.cmdline` (81 B) and
   `.initrd` (1,063,434 B) — the ring-26 sections finally read, by our code;
4. installs **EFI_LOAD_FILE2_PROTOCOL** on the LINUX_EFI_INITRD_MEDIA_GUID
   device path — implementing the 6.12 consumer's exact contract (the size
   probe must return `EFI_BUFFER_TOO_SMALL`, not `EFI_SUCCESS` — a
   spec-vs-consumer divergence now registered);
5. `LoadImage`s the pristine `\boot\vmlinuz` from the same FAT volume via a
   device path built from the volume's own, hands the kernel its cmdline as
   CHAR16-widened LoadOptions (the v1 CHAR8 attempt reached the kernel as
   UTF-16 mojibake — silent boot — caught and kept as history), and
   `StartImage`s;
6. if the kernel ever returns, **prints the status** — the vendor never
   tells you why.

The chain, 3/3 green at 512 MiB, no shell, no boot-entry variables, no
fw_cfg: OVMF → FatDxe → **FW27-stub** → kernel stub (initrd served by OUR
protocol — the kernel's own line `Loaded initrd from
LINUX_EFI_INITRD_MEDIA_GUID device path` is the consumption proof) →
busybox → `FW26 firmware=uefi` → `FW26 CHAIN OK` → clean S5 power-down.
The stub is 1.1 MiB where the UKI was 13.2 — the knife-edge load
disappears with it.

## Honesty ledger

- The disk evolved in this ring (`BOOTX64.NOB` = the ring-26 UKI, preserved;
  `BOOTX64.EFI` = FW27; NvVars churn). The ring-26 artifact's disk sha256
  describes the disk before these changes; every transformation is a
  persisted mtools command in the session scripts.
- The coreboot world is untouched: same specimen, same syslinux chain, no
  new coreboot claim.
- TCG absolute times are not hardware times; ring 27 adds no timing claim.
- The fw_cfg floor is a single-run ladder, not a median — a bound, not a
  tight one. The disk-path 512 MiB outcome is non-deterministic (both the
  stub-fail and the silent-success were observed) — the matrix records both.
- FW27 v1's CHAR16 bug is kept in the source comments and the first W-run
  trail, per house rules for debug fights.

## Day-0 consequences

None by design — no hardware touched. Volume 5's software wing now also
owns **a loader**: build (24), read both worlds (24-25), boot (25), boot
to a real OS with markers (26), flash-cycle rehearsal (24), and now
**our own EFI stub with full serial observability (27)**. On the bench
day, if the vendor firmware stays silent about a failure, the same
instrument pattern applies: our code, on the wire, naming what happens.
