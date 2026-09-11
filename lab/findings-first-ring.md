# The Massive Investigation — 2026-09-11

> One campaign, seven fronts, one hour, one rule: **read everywhere, write
> never.** Zero bytes were written to any chip, anywhere, by anything.
> All material is real firmware extracted locally from Debian packages
> (no root, no install) or public documentation; nothing here touches the
> frozen 0.7.1 tool surface.
>
> Companion artifacts: `lab/ovmf-findings.md` (the first real-firmware
> probe, 0.7.1), `lab/ovmf-census.json` (the structured census),
> `docs/open-questions.md` (the map this campaign answers into).

## Front 1 — the multi-species corpus

Ten Debian packages, each a different firmware *species*, extracted
without installing:

| species | material | what it is |
|---------|----------|------------|
| UEFI/PI  | `ovmf` (already probed) | the FV/FFS world our parser was born for |
| legacy BIOS | `seabios` (`bios-256k.bin`, `acpi-dsdt.aml`) | flat code+data, no FVs at all |
| ACPI | `acpi-dsdt.aml` | a REAL compiled DSDT table (OEM `BXPC`) |
| Option ROMs | `ipxe-qemu` (matched `pxe-*`/`efi-*` pairs), `vgabios` | the PCI expansion ROM world |
| embedded | `u-boot-qemu` (x86, arm, arm64, riscv64, mips, ppc) | the same object on six ISAs |
| signed EFI | `shim-signed`, `grub-efi-amd64-signed` | the trust chain, physical |
| tooling | `acpica-tools` (`iasl`) | for the ACPI world |

## Front 2 — how each species presents to a read-only parser

- **SeaBIOS**: `spi-map` reports `ok`, 0 FVs, 0 files — honest. It does
  not hallucinate FVs into a non-UEFI image. The FV world is a UEFI/PI
  world; other species speak other formats, and the parser says so.
- **The DSDT**: a real ACPI table (`DSDT`, 4585 bytes, OEM `BXPC`,
  revision 1) — the firmware's own hardware description language,
  readable at header level without any guesswork.
- **Option ROMs**: every ROM in the corpus closes its checksum and
  parses per the PCI spec (0x55AA, size byte, PCIR, code type).
- **U-Boot**: 2025.01-3 across six ISAs, 0 FVs everywhere — firmware is
  a universal species; FVs are a platform dialect.

### The discovery of the front: ROMs are CHAINS

The `efi-*.rom` files first reported `code=x86, last=False` — wrong,
until the chain was walked. They are **combo ROMs**: two images in one
file, chained through the PCIR structure:

```
efi-e1000.rom (262144 B)
  image#0 @ 0x00000  x86 PC-AT  last=False   (109056 B — exactly a pxe-*.rom)
  image#1 @ 0x1aa00  EFI        last=True    (49152 B)
```

A legacy BIOS loads image#0; a UEFI platform loads image#1; the file
is both. **A signature is not a file — the first image is the first
link of a chain.** Same lesson as the LZMA wall: hidden structure is
the norm, and a census that reads only the first layer counts almost
nothing.

## Front 3 — the trust chain, physical

PE/COFF + Authenticode parsing of the real signed EFI binaries:

| binary | signer (from the PKCS#7 blob) | note |
|--------|-------------------------------|------|
| `shimx64.efi.signed` | Microsoft Corporation UEFI CA 2011 ← Microsoft Corporation Third Party Marketplace Root | timestamp **zeroed** (reproducible build) |
| `grubx64.efi.signed` | Debian Secure Boot Signer 2022 - grub2 ← Debian Secure Boot CA | timestamp 2015-01-01 (canonical epoch) |

What this proves, structurally:

1. **Trust has a body.** "Secure Boot" is a WIN_CERTIFICATE in the PE
   security directory, a pkcs7-signedData blob, certificates with
   names — read, listed, understood. No mystery, no magic.
2. **The hierarchy is visible**: MS Root → MS UEFI CA 2011 → shim →
   (shim's embedded allow-list) → Debian CA → grub. Each arrow is a
   signature over bytes.
3. **SBAT exists as a section** (`.sbat` in both shim and grub): the
   revocation mechanism against vulnerable bootloaders — a kill-list
   at the bootloader level, shipped inside the binary.
4. **Provenance leaks through timestamps**: reproducible-build epochs
   (zeroed / 2015-01-01) vs. vendor BIOSes' real build dates. A
   fingerprint for day-0's dump.
5. **Another wall**: grub's 2.55 MB `mods` section — the module tree,
   compressed (lzma/xz markers). The bootloader hides its own census
   exactly the way firmware images do.

## Front 4 — the full OVMF census (`lab/ovmf-census.json`)

Structured census, both builds, every phase:

- plain: **135 files, 135 unique GUIDs** — 115 DXE + 14 PEI + PEI-core
  + DXE-core + 2 applications + 2 freeform;
- secboot: **144 files** — 113 DXE + 17 PEI + 8 SMM + SMM-core + …;
- PEIMs carry **no UI names** — GUID-only identities (classic PEI);
- five GUIDs hand-identified from public EDK2 knowledge and labelled as
  such (`PeiCore`, `DxeIpl`, `PcdPeim`, `DxeCore`, `ResetVector`);
- the `CpuDxe` duplicate is recorded as `duplicate_guids` — names are
  labels, GUIDs are identity, in writing, in the artifact.

## Front 5 — the runtime mirror is an ENVIRONMENT property (Q8)

Probing this sandbox VM's own firmware surface:

- DMI: **absent** (no /sys/class/dmi/id);
- efivarfs: **absent** (no /sys/firmware/efi);
- ACPI tables: **absent** (no /sys/firmware/acpi);
- /proc/iomem: a single synthetic `System ROM` line;
- /proc/cpuinfo: masked identity (`GenuineIntel Xeon`).

In a containerized VM, the mirror is a porthole with a curtain. This is
the Q8 finding: **the mirror's completeness is a property of the
environment, not of the firmware** — and it is exactly why `capture
--live` provenance-tags every section. On bare-metal TWIN-1 the same
probe will show the full mirror; on day-0, "mirror truncated" will mean
the environment, not a tool failure.

## Front 6 — the AMD/PSP lens, ready for day-0 (TWIN-1 = B450-PLUS)

`scripts/amd_psp_probe.py` (kept outside the repo — investigation
tooling, not surface) scans a dump for the AMD world:

- magics `$PSP` (PSP Directory Table), `$BDIR` (BIOS Directory Table),
  `$PSP2`/`$BDR2`/`$CBIO`/`$CPSP` (generational variants);
- AGESA strings + version-shaped strings near them;
- alignment notes on every hit (a PSP table at a 16 KiB boundary is
  credible; an unaligned hit is a false positive until proven).

Validated honestly: zero hits on OVMF (an Intel-world image — the lens
reports its zero and moves on). Confirmed by web research (Front 7):
coreboot's PSP Integration Guide documents exactly the PSP Directory +
BIOS Directory structure, and the dayzerosec/3mdeb work shows the FET
(Firmware Entry Table) is the pointer chain that locates them. On day-0
this lens runs on `day0-spi.bin` immediately after `spi-map --save-dump`.

## Front 7 — web research: the B450-PLUS kill-list seeds (Q3)

- **No coreboot port**: nothing anywhere suggests an ASUS B450-PLUS
  coreboot port exists; the repo's standing claim survives contact with
  the web. TWIN-1 stays guard fleet, forever.
- **USB BIOS FlashBack exists in the B450 family** (TechPowerUp, ASUS
  docs): "a firmware upgrade or reflash with nothing more than a PSU
  and a USB thumb drive" — a CPU-independent vendor rescue path.
  **Verify the physical button/port on OUR board at day-0** (not
  asserted until seen). Note the discipline: FlashBack writes the chip
  — it is the vendor's own recovery ladder, documented, not ours to
  touch outside Volume 5 rules.
- **ASUS `.CAP` recovery**: ASUS boards boot a recovery path from USB
  with a named `*.CAP` file — the vendor's second rescue mechanism.
- **AMD Platform Secure Boot** (IOActive, 2024): the PSP enforces the
  AMD answer to Boot Guard — fuses again, hardware again. The AMD wall
  has the same shape as the Intel wall: silicon.

## The unified lesson

Every species examined hides its real structure behind a first layer:

| layer that hides | species | what's behind |
|------------------|---------|---------------|
| LZMA GUID-defined section | UEFI/PI (OVMF, vendor images) | PEIFV + DXEFV, the module census |
| PCIR image chain | Option ROMs | x86 AND EFI worlds in one file |
| `mods` section compression | GRUB | the bootloader's module tree |
| WIN_CERTIFICATE / PKCS#7 | signed EFI | the trust chain |
| FET → PSP/BIOS directories | AMD | the PSP world |
| the environment itself | any runtime mirror | truncation by containerization |

The census that counts only what the first layer shows will always be
wrong. Read chains, pierce compression, walk tables, label honestly —
or count almost nothing.

## What this changes for day-0 (16/09)

1. `spi-map` first (as arbitrated), then `amd_psp_probe.py` on the same
   saved dump — expect `$PSP`/`$BDIR`/AGESA hits on the B450-PLUS.
2. Expect **compression** on the vendor image: 0 visible modules means
   "decompress next", never "empty firmware".
3. Expect NVRAM utf-16 artifacts (strings inside variable data) — the
   label already covers it.
4. Physical inspection list: BIOS FlashBack button/port (verify),
   BIOS chip (SOIC8? how many?), UART header — three answers, five
   minutes, no screwdriver.
5. The mirror here is truncated by design; on TWIN-1, `capture --live`
   will show the full runtime mirror — provenance-tagged either way.

## Honesty — what this campaign did NOT establish

- No vendor (ASUS/AMI) B450-PLUS image was available in the corpus;
  every vendor-specific claim above is either structural knowledge,
  public documentation, or explicitly flagged "verify at day-0".
- The PSP lens has not yet seen a real AMD image — day-0 is its first
  real run; its zeros and hits will both be informative.
- Nothing was written anywhere; nothing in the frozen surface changed;
  the fifteen-tool contract and the 323 checks stand untouched.
