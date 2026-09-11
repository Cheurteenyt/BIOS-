# The seventeenth ring — the mirror was never a mirror

Rings 13 and 14 registered an anomaly and refused to explain it from
memory: the MSI image carries a second, bigger copy of its main
firmware volume (469 vs 453 files, +0x97000 bytes), the bytes at the
mirror position of the primary `$PSP` spell `2PSP` instead, ten PSP
directories validate only in the upper region, and the two NVRAM
stores share every variable name but ship different factory defaults.
This ring measures the whole structure from disk and the root cause
turns out to be an AMD-documented architecture, not a mirror at all.

## Front 1 — the MSI double structure, root-caused

**The image is two 16-MiB SPI windows.** Six top-level FVs, and every
one of them pairs with a twin at exactly +0x1000000 (half the 32-MiB
file): the small FVs at 0x37000/0x1037000, the data FVs at
0xd80000/0x1d80000, the main DXE FVs, the NVRAM anchors at
0x37078/0x1037078, the PSP chains, the combo tables. The half-delta
is derived, not assumed — the paired small FVs vote for it, and the
vote is unanimous.

**The two windows are different builds of the same release.** The
main FVs share 380 GUIDs; 261 of those are byte-identical, 119
changed (84 at constant size, 35 resized). Sixty-nine GUIDs exist
only in the lower window, 85 only in the upper. The AMI core changes
surgically (Setup +195,872 B; Bds, NvramDxe, FlashSmiDxe, SysUuid,
CpuDxe all +~1 KiB; MsiApServiceSmi −1,536 B). Both windows carry
`ComboAM4v2PI 1.2.0.8` raw-verified — same AGESA, different builds.

**The unique names split by CPU family.** The lower window carries
Zen/Zen+ silicon support (Summit, Raven, Pinnacle: `AmdCcxZenRvDxe`,
`AmdCcxZenZpDxe`, `FchTaishanDxe`, `FchSandstoneDxe`,
`CbsSetupDxeRV/ZP`); the upper adds Zen2/Zen3 (Matisse, Renoir,
Cezanne: `AmdCcxZen3Dxe`, `AmdCcxZen3CznDxe`, `SmuV12Dxe`,
`FchShastaDxe`, `CbsSetupDxeSSP/RN`). Each window is a complete,
bootable firmware for a disjoint set of CPU families.

**The combo tables open the routing.** The bytes spelled `2PSP`
because the cookie is the dword 0x50535032 — `PSP2` — the AMD combo
directory from doc #55758, fetched to disk this ring via coreboot's
`combo_directory.h` (the never-from-memory rule, at header-file
granularity). Three tables validate fletcher-32 exactly:

- lower window, PSP2 @0xa7000: 3 entries → `$PSP` @0x178000 (IDs
  0xbc0a0000 and 0xbc0a0100, two IDs sharing one directory) and
  `$PSP` @0xa8000 (ID 0xbc090000) — addresses 0xFF-based absolute;
- upper window, PSP2 @0x10a8000: 3 entries → `$PSP` @0x10d1000,
  0x1301000, 0x1481000 (IDs 0xbc0b0500, 0xbc0c0000, 0xbc0c0140) —
  addresses window-relative;
- upper window, BHD2 @0x10a8800: 2 entries → `$BHD` @0x1461000,
  0x15e1000.

The ring-13 register's 18 valid directories re-assemble without a
remainder: per family, a `$PSP` + `$BHD` + `$PL2`/`$BL2` chain.
Twenty other magic-byte coincidences inside module data were
rejected by count and fletcher and stay in the scratch register.

**Every inherited mystery dissolves.** The "+16 files / +0x97000 B
mirror" is the upper window's larger family coverage, not a clone.
The `2PSP` bytes are the combo cookie at the upper window's fixed
slot. The "ten directories validating only in the upper half" are
the upper families' own directories. The "NVRAM not a clone" is
real: the upper Setup defaults are 1,972 B against 1,428, the
shared 1,428-B prefix differs in 121 bytes (8.5 %, 28 spans) and
the extra 544-B tail is dense data (0x02-heavy IFR defaults), not
padding — each window's firmware ships its own setup database, and
the upper one has 195 KB more of it to configure.

**The builds are the same species ring 16 measured.** Across the 84
shared same-size pairs: 42,441 changed bytes in 3,081 spans —
`HardwareMonitorDiagram` 2 bytes in 1 span, `CpuDxe` 2/2,
`PiSmmCpuDxeSmm` 2/1, `PciBus` 8/4, beside region rewrites
(`Tpm20PlatformDxe` 183 B/94 spans). Two builds of one release,
sharing a codebase, diverging where their families demand it.

## Front 2 — the ring-8 curiosity closes: intentional, not coincidental

Ring 8 left DriverHealthManagerDxe's cross-module hits flagged
"the bytes alone cannot decide". Bytes plus context plus cross-build
stability can. The two DHM formset GUIDs were censused across every
module of three OVMF builds (plain, secboot, strictnx): the carrier
set is identical every time — DriverHealthManagerDxe itself (manager
×2, configure ×3), **BdsDxe** (configure ×1) and **UiApp**
(configure ×1; 462CAA21 resolved from `UiApp.inf` on disk). The
context forensics are decisive: in BdsDxe and UiApp the GUID sits in
code-adjacent rodata right after x86 NOP padding (`66 2e 0f 1f 84`)
— the signature of a compiled GUID constant referenced by code —
and in UiApp it sits next to UiApp's own formset GUID block. String
collisions live in HII string tables and drift between builds; these
constants are stable across all three builds. Verdict: **intentional
runtime formset routing**. The honest limit is registered: the
on-disk edk2 tree (ring 9's fetch) defines the GUID only inside
`DriverHealthManagerVfr.h` and is not the Debian build tree of the
specimens, so the exact include-chain stays open — the byte verdict
does not depend on it.

## The self-correction chain

- The first top-FV census counted zero DXE/SMM modules everywhere:
  the phase filter used hex strings (`"0x7"`) while the ring-15
  register stores phase words (`"DXE"`). The `assert len(main_fvs)
  == 2` refused to pass and the PHASE table was re-read from the
  ring-15 source — nothing hand-waved.
- The first span pass compared the unique-GUID sets — which by
  construction have no pair — and produced 0 rows. The real
  forensics population is the 84 shared same-size pairs; probe 3
  re-ran it correctly.
- Script 2 died on a `data_start` KeyError: `walk_region` rebuilds
  variable records without raw bytes. The recovery was
  `parse_entry` on the recorded entry offset — the grammar layer
  the register was built from.
- The `2PSP` reading was nearly hand-decoded into a fantasy entry
  layout. The fetch of `combo_directory.h` killed the fantasy: the
  header is 32 bytes (cookie, fletcher, count, lookup, 2×u64
  reserved), entries are {id_sel, id, u64 addr} — and the measured
  bytes fit it exactly, fletcher32 `ok` on all three tables.
- psptool's 32-MiB lesson got a sequel: the Blob carries `roms`
  (plural). The singular-attribute probe found nothing and the
  empty result is recorded rather than papered over.

## Honesty ledger

- The combo entry IDs (0xbc09/0x0a/0x0b/0x0c ranges) are measured
  and stable, but no public table maps them to family names; the
  family routing is inferred from the window contents (module
  names) and is flagged as inference, not citation.
- Which window the hardware selects at reset is not measurable from
  the file — that lives in straps and registers. Both windows are
  complete and bootable; each owns the reset vector inside its own
  data FV.
- The two combo address conventions (0xFF-based absolute in the
  lower window, window-relative in the upper) are measured facts;
  their unified semantics are read off the doc-#55758 layout
  diagram, not off silicon.
- Nothing was executed, nothing emulated, nothing written. The MSI
  specimen was read-only all ring.

## Consequences for day-0 (16/09)

- The ASUS PRIME B450-PLUS is a 16-MiB part (as are all our other
  specimens; MSI is the only 32-MiB one) — the dump is expected to
  be single-window. The combo lens (probe 4) joins the day-0 chain
  as an **optional seventh lens**, to run only if the dump is
  32 MiB or shows paired structures.
- The Setup-defaults diff method (shared-prefix drift + extra-tail
  composition) is the proven bridge for ring 14's Q1↔NVRAM plan on
  live silicon.
- The family-split prediction: a dump's unique-module names will
  name its supported CPU families directly — one more
  identity/dating signal that needs no vendor cooperation.
- The mirror question is closed with a reusable lens: paired
  structures at +half-image are combo windows, and "2PSP/2BHD"
  bytes are level-2 directory cookies — the next 32-MiB board is
  already legible.
