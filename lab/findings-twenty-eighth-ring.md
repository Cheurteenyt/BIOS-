# The Twenty-Eighth Ring — the world-naming stub, and the second world

*Date: 2026-09-12 · Volume 5 lane (software wing) · docs-only, surface frozen*

The ring-27 ledger registered the hook honestly: "the coreboot world is
untouched." Ring 28 touches it — and delivers the study's first
**dual-world boot matrix**: the same FAT disk, carrying the same stub and
the same kernel, boots under **OVMF** and under **coreboot 25.12 with an
EDK2 UefiPayloadPkg built on top of it** — a firmware produced by this
study, carrying a second, independent EFI environment above it.

## Front 28a — FW28, the stub that names its world

FW27's contracts are inherited unchanged: ConOut speech, memory-map
summary, self-PE section consumption (`.cmdline` + `.initrd`), the
LoadFile2 instance on `LINUX_EFI_INITRD_MEDIA_GUID` (size probe must
return `EFI_BUFFER_TOO_SMALL`), LoadImage of `\boot\vmlinuz` with the
CHAR16-widened cmdline. The new contract is identity. All of it is
spec-derived (UEFI 2.10 §4.1.1, §4.6; SMBIOS 3.0 §6.4):

1. `gST->FirmwareVendor` / `FirmwareRevision` are read and printed.
2. **Every** config-table entry is dumped with its GUID and a 5-byte
   content anchor — evidence before verdicts.
3. SMBIOS2/SMBIOS3 entry points are located via their config-table
   GUIDs, the entry-point structure is parsed byte-explicitly
   (`_SM_`/`_SM3_` anchors verified on the wire), and type 0/1 strings
   are walked until the type-127 end marker.
4. The verdict: `coreboot` if the SMBIOS type-0 vendor or type-1
   manufacturer/product says so; `OVMF` if those fields say so; else
   **"unknown world — evidence printed above, no guess made."**

A design note that matters more than it looks: matching `"EDK II"` on
`FirmwareVendor` would have **broken** the instrument. The edk2
UefiPayloadPkg announces `EDK II` in *both* worlds — the same string we
see under Debian's OVMF. The discriminating instrument is SMBIOS type 0,
which each host firmware fills for itself. The world's name lives below
the payload, not in it.

## Front 28b — the matrix

Constants across all six runs: q35, 512 MiB, one disk image
(`fw28-disk.img`, 64 MiB FAT+MBR), one stub (`BOOTX64.EFI`), one kernel
(6.12.94). Only `-bios` changes.

| world | runs | verdict on the wire | chain |
|---|---|---|---|
| Debian OVMF (2025.02-8+deb13u1) | 3/3 | `unknown world — evidence printed above, no guess made` | OK, S5, exit 0 |
| coreboot 25.12 + EDK2 stable202608 | 3/3 | `coreboot world (edk2 payload above it)` | OK, S5, exit 0 |

The OVMF verdict is the honesty contract working *as designed*: Debian's
build masks the upstream identity ("Debian distribution of EDK II"), so
neither anchor fires, and the stub prints its evidence instead of
guessing. The coreboot verdict is the full instrument firing: SMBIOS
type 0 `bios-vendor: "coreboot"`, `bios-version: "25.12-dirty"` — the
table coreboot wrote, handed to the payload through HOBs, rebuilt by
SmbiosDxe, exported through the config table, and finally *named* by our
stub. In both worlds the kernel independently confirms the delivery:
`EFI stub: Loaded initrd from LINUX_EFI_INITRD_MEDIA_GUID device path`,
plus the cmdline the stub carried in its own `.cmdline` section.
`BdsDxe: FSOpen '\EFI\BOOT\BOOTX64.EFI' Success` on the same SATA device
path both worlds use (`Pci(0x1F,0x2)/Sata(0x0,0xFFFF,0x0)`).

## Front 28c — six walls, all named

The resurrection of the coreboot environment after the rings 9–27
instrument loss became its own measured front (full recipe in
`lab/vol5-fw28.json`):

- **28-w1** — the lost snapshot: a tree whose git resolves to a *parent*
  repo makes coreboot's version step die on `git describe` ("No names
  found"). Fixed by restoring the tree's own `.git` backup (describe →
  exactly `25.12`).
- **28-w2** — restoring `.git` re-armed coreboot's submodule gate, which
  then hung fetching modules whose gitdirs are gone. `UPDATED_SUBMODULES=1`
  is coreboot's own documented escape. Lesson: *no-*.git* and
  *restored-*.git* are different build environments.
- **28-w3** — ring 24's libgcc lie, deepened: coreboot selects the
  *prefixed* compiler (`x86_64-linux-gnu-gcc`), so a wrapper named only
  `gcc` is bypassed and the 64-bit archive gets cached anyway. The
  wrapper must exist under both names.
- **28-w4** — the big one. With `VARIABLE_SUPPORT=SMMSTORE` (forced by
  `CONFIG_SMMSTORE_V2=y`), `SmmStoreFvbRuntimeDxe` fails at entry
  (`No memory space descriptor for com buffer found` → `Device Error`),
  FVB never installs, `VariableRuntimeDxe` (depex `FVB AND FTW`) never
  dispatches, and the variable/RTC/monotonic/capsule arch-protocol set is
  missing — `CoreAllEfiServicesAvailable()` returns Not Found; the DEBUG
  build asserts at `DxeMain.c:578`, the RELEASE build crashes (the dump
  resolves to `CpuDxe.dll` only because CpuDxe owns the exception
  handler — its own `fxsave` onto a present-but-RO stack page faults
  first; sub-question registered, not guessed). Reproducible on edk2
  master *and* stable202608, at 512 and 1024 MiB. The principled fix:
  with `-bios`, **QEMU flash behaves as ROM** (coreboot's own log line)
  — the SMMSTORE medium cannot be written; the EMU-variable lane is the
  correct q35-sandbox lane. On a real board with writable flash,
  SMMSTORE remains the bench-day target and this wall is its
  calibration point.
- **28-w5** — the silent-stub trap: after flipping `EDK2_DEBUG=y`,
  `CONFIG_EDK2_SERIAL_SUPPORT` stayed "not set" (olddefconfig preserves
  an explicit negation; it does not re-derive it from a changed
  dependency default) → `TerminalDxe` excluded from DXEFV → ConOut had
  no serial instance → the chain booted *green and mute*. The cmdline,
  initrd and LoadFile2 contracts had all worked. Lesson: never diagnose
  a boot chain through one output channel.
- **28-w6** — the sandbox kills every background process at the
  tool-call boundary (measured with a detached `sleep`; `setsid` does
  not save it). Long builds must run inside one bounded call; edk2's
  `build.py` is incremental, so killed calls still converge.

The edk2 checkout is pinned (`edk2-stable202608`) in `.config` — the
workspace checkout alone is not enough, because coreboot's Makefile
re-fetches and re-checkouts per its own flow.

## What the ring changes

The dual-world contract is no longer a plan: one disk, one stub, one
kernel, two firmware worlds, six green boots, verdicts on the wire. The
day-0 checklist gains a second firmware the real board could run
(*if* the vendor lane ever dies, the coreboot lane is rehearsed in
software end-to-end). And the stub now answers the question every
firmware answers silently: *whose world is this?* — with a verdict that
is honest in exactly the cases where the world refuses to name itself.

## Honesty ledger

- The initramfs markers still print `FW26` — the disk is unchanged since
  ring 26/27; the labels name the marker vintage, not the boot vintage.
- The OVMF-side serial logs are inherited from the previous session;
  coreboot-side runs 2–4 are this session's.
- `AcpiPlatform "start failed: Aborted"` in the coreboot world (tables
  reach the payload via HOBs; AcpiPlatformDxe aborted anyway) — chain
  unaffected, registered as an open observation.
- The stack-RO sub-question of wall 28-w4 is **open**.
- The coreboot world's variable store is EMU (RAM) in this lane; nothing
  persists across resets. On q35 in this sandbox that is the correct
  configuration, and it is labeled as such everywhere it appears.
