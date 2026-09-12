# The twenty-sixth ring — the chain speaks, and the chain is timed

Date: 2026-09-12 · Mode: software-only (the bench day stays deferred) ·
Specimens: the ring-24 coreboot.rom (unchanged), Debian OVMF plain 4M, a
64 MiB disk built from nothing.

## What was asked

« On va continuer à investiguer massivement… reverse engineering extrêmement
compliqué ou code ultra complexe, mathématiques, optimisation meilleur que
constructeur. Je te laisse choisir. » The vendor-RE axis is saturated at the
software level (rings 19-23 took it module-exact, blob-exact, word-exact);
the remaining questions there are hardware-gated. The open frontier that
serves « un meilleur bios » is the one Volume 5 left green but mute: a
firmware built in this study that boots to "No bootable device". This ring
gives it an OS, then measures it against the vendor-native world on
identical ground.

## What stands

### Front 26a — a bootable disk manufactured from nothing, root-less

No `losetup`, no `mount`, no root anywhere: debs extracted (syslinux 6.04
from bullseye — it is GONE from bookworm/trixie; dosfstools, mtools,
busybox-static, libdevmapper for grub tools, and the signed trixie kernel
`linux-image-6.12.94+deb13-amd64` resolved from the metapackage's Depends).

- **The initramfs is a byte-by-byte cpio-newc writer** (`vol26_initramfs.py`):
  header fields as ASCII hex, 4-byte paddings, the `/dev/console` char device
  5:1 encoded in rdevmajor/rdevminor, and a hand-written `/init` that mounts
  proc/sys, prints the evidence markers, and powers off — `poweroff -f` is
  what makes QEMU exit.
- **The UKI is hand-built with objcopy** (the Omarchy boot model — the study
  itself showed Omarchy boots Limine+UKI): vmlinuz + `.cmdline` + `.initrd`
  sections → `\EFI\BOOT\BOOTX64.EFI`.

The disk itself took three layouts and left a diagnostic trail worth
keeping (kept, not erased — see the factory scripts v1/v2/v3):

1. **MBR + syslinux + dosfstools-4.2 FAT32 @1 MiB** → syslinux 6.04:
   `invalid media signature`. Hand-verified the BPB first (512 B/S, 32
   reserved, 55AA — the FS is valid); syslinux's `-o`/`-t` semantics fought
   back twice. Registered.
2. **MBR + GRUB embedded by hand** (`boot.img` @LBA0 with the partition
   table preserved through it, `core.img` (diskboot + lzma core) in the
   1 MiB gap, blocklist patched straight from the grub sources' offsets:
   `boot.img+0x5c` kernel_sector, `core.img+0x1f4` blocklist start,
   `+0x1fc` length — the Debian defaults already matched the layout, which
   the embed script verifies before writing). GRUB 2.12 came up on serial
   after the early-config lesson (`terminal_input serial` — without it the
   shell waits for a VGA keyboard that doesn't exist under `-display none`),
   then declared the same FS **`unknown filesystem`**. Two independent
   2019/2025-era tools rejecting a mountable filesystem = the failure class
   is **« FAT behind a hand-written MBR partition »**, not the FAT flavor.
   The decisive probe: a **superfloppy FAT16 at LBA 0 attached as `-hdb`**
   mounts from the same GRUB, and `cat` works file-level.
3. **The superfloppy is the answer**: FAT16 over the whole file, no
   partition table, syslinux installed INTO the FAT boot sector (the
   USB-stick path), OVMF's FatDxe mounts it raw. Sector 0 reads
   `OEM SYSLINUX`, 55AA.

### Front 26b — the chain, end to end, on both worlds

- **coreboot → SeaBIOS → syslinux → Linux → userspace**: `Booting from
  Hard Disk… / Booting from 0000:7c00` → `Linux version 6.12.94` →
  `=== FW26 firmware=bios ===` → `=== FW26 CHAIN OK ===` → `reboot: Power
  down`. 3/3 runs green.
- **OVMF → QemuKernelLoaderFsDxe → BdsDxe → kernel EFI stub → same kernel**:
  `EFI stub: Loaded initrd from LINUX_EFI_INITRD_MEDIA_GUID device path` →
  `=== FW26 firmware=uefi ===` → `=== FW26 CHAIN OK ===` → power down. 3/3.
- The **kernel self-qualifies its firmware mode** (`/sys/firmware/efi`
  present or absent): the chain tells us which firmware booted it. No
  trust, just evidence.

### Front 26c — the first A/B of the study (math, quantified)

Same machine (q35), same TCG, 512 MiB, same kernel, same initramfs, same
cmdline, 3 runs per side, medians (seconds, wall clock):

| boundary | coreboot + SeaBIOS + syslinux | OVMF | Δ |
|---|---|---|---|
| first serial byte | 0.039 (bootblock, log level 7) | 3.047 (the EFI stub line) | — |
| **kernel start** | **4.573** | **3.460** | +1.11 s |
| **userspace (CHAIN OK)** | **7.485** | **6.462** | +1.02 s |
| kernel stage (kernel→userspace) | 2.91 | 3.00 | ≈ equal |

Reading: the kernel stage is INVARIANT (same kernel, same TCG) — the whole
Δ is the firmware stage. OVMF's is largely invisible on serial (RELEASE
build logs to 0x402), so its ≤3.0 s is an upper bound; coreboot's is fully
on the wire and names itself (`bootblock starting`, `BS:` timeline). This
is the study's first **measured** firmware A/B — « optimisation meilleur
que constructeur » stops being a slogan and becomes a table, with its
honest limits written next to it (TCG ≠ silicon; OVMF = the vendor-native
proxy, not the ASUS AMI BIOS).

## The UKI open thread (registered, not hidden)

The hand-built UKI on the disk loads and STARTS under OVMF
(`BdsDxe: starting Boot0001`, no failure status) with a lesson chain
attached: VMA 0 sections → `Unsupported`; ukify-style `.initrd@0x3000000` →
`Out of Resources` (objcopy recomputes SizeOfImage — the firmware is asked
for ~49 MiB contiguous on a 128 MiB VM); tight VMAs computed from the
kernel's own SizeOfImage (`0xbf5000`/`0xbf6000`) → loads, starts,
then silence. `earlyprintk` debugging is next session's first front.
The fw_cfg path carried the A/B meanwhile.

## Honesty ledger

- TCG absolute times are NOT hardware times; only the A/B claims anything.
- OVMF plain is the vendor-native PI/FFS2 proxy — the ASUS AMI BIOS cannot
  run in QEMU.
- Loaders are asymmetric BY CONSTRUCTION (each firmware boots with its
  native machinery); the comparable metrics are the wall-clock boundaries
  on identical kernel/initramfs/VM.
- The specimen coreboot.rom is byte-identical to ring 24/25's (no rebuild);
  OVMF code was checksummed per run.
- All debug fights are kept in the factory scripts as registered history:
  syslinux offset semantics, GRUB early-config serial input, grub-bios-setup
  host-fs refusal, libdevmapper, the mtools PATH dependency of syslinux
  image-mode, the QEMU image write-lock, the `-m 512` kernel init_size wall.

## Day-0 consequences

None by design — no hardware touched. The Volume 5 software wing now
carries: build (ring 24), read both worlds (rings 24-25), boot (ring 25),
**boot to a real OS with evidence markers (ring 26)**, flash-cycle
rehearsal 5/5 (ring 24). The bench day only adds the physical: SOIC8 clip,
`--flash-name`, real rollback.
