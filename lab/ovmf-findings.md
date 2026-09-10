# OVMF findings — the first real firmware the parser has read

> Date: 2026-09-11 (lab world, during the 0.7.0 surface freeze — knowledge
> work only, then an honesty fix published as 0.7.1).
> Material: Debian `ovmf` 2025.02 package, extracted locally — no install,
> no root, no QEMU boot (that waits for the real lab machine).
> Rule held: **zero bytes written, everywhere, by everything.**

## Why OVMF counts as "real"

OVMF is a genuine EDK2 UEFI firmware: real firmware volumes, real FFS
files, real module images, a real variable store — not a synthetic
fixture built byte by byte. It is the closest thing to vendor firmware
that can be picked up with zero risk. The 0.7.0 parser was tested only
against the synthetic image; this was its first contact with the real
world, and the real world corrected it.

## Finding 1 — the parser is honest on a real, descriptorless image

`OVMF_CODE_4M.fd` (3,653,632 bytes):

- descriptor: `present=false`, note "no Intel flash descriptor
  (FLVALSIG) — descriptorless image (coreboot-style) or a partial
  region dump" — **correct**: OVMF images carry no Intel descriptor;
- 2 firmware volumes found, FFS2, header checksums verified:
  `FV @ 0x000000` (0x348000 bytes = FVMAIN_COMPACT, 2 files) and
  `FV @ 0x348000` (0x034000 bytes = SECFV, 4 files);
- `summary: 6 files, 0 DXE, 0 SMM, 0 NVRAM names` — **correct and
  instructive**: see Finding 2.

## Finding 2 — the compression wall (inside the image itself)

FVMAIN_COMPACT contains a GUID-defined section
(`EE4E5898-3914-4259-9D6E-DC7BD79403CF`) whose payload is an LZMA
stream (EDK2 `LzmaCustomDecompressLib`). Everything interesting —
PEIFV and DXEFV with all the modules — lives BEHIND that wall. A naive
scan sees a nearly-empty image; so does a naive analyst.

This is Finding 1's lesson generalised: vendor images compress their
module trees the same way. **The census has to account for compression
or it counts almost nothing.**

Pierced in-memory (stdlib `lzma`, `FORMAT_ALONE`, read-only):

- 1,569,609 compressed bytes → 16,122,000 bytes (×10.3 expansion);
- the decompressed layer holds exactly 2 more FVs:
  - PEIFV: 28 files (PeiCore + 14 PEIMs on the plain build, 17 on the
    secboot build);
  - DXEFV: 120 files (DxeCore + **115 DXE drivers** + 2 applications,
    plain build).

## Finding 3 — the real census (Q6 of the investigation map)

115 named DXE modules on the plain build. The boot chain census is no
longer theoretical; samples by subsystem:

- **core**: DxeCore, PcdDxe, RuntimeDxe, SecurityStubDxe, CpuDxe,
  BdsDxe, DevicePathDxe, HiiDatabase, SetupBrowser, DisplayEngine;
- **display** (Q2 of the map): QemuVideoDxe, QemuRamfbDxe,
  VirtioGpuDxe, GraphicsConsoleDxe, ConPlatformDxe, ConSplitterDxe,
  LogoDxe — pre-OS display IS a driver, swappable, and its absence is
  exactly "no screen";
- **storage**: VirtioBlkDxe, VirtioScsiDxe, VirtioFsDxe, Fat, UdfDxe,
  NvmExpressDxe, AtaAtapiPassThruDxe, ScsiBus, ScsiDisk, DiskIoDxe,
  PartitionDxe;
- **network** (the "who talks before Linux" question): SnpDxe, MnpDxe,
  ArpDxe, Dhcp4Dxe, Ip4Dxe, Udp4Dxe, TcpDxe, TlsDxe, HttpDxe,
  HttpBootDxe, UefiPxeBcDxe, IScsiDxe, DnsDxe, VlanConfigDxe — a FULL
  network stack runs before the kernel;
- **crypto/measurement**: Hash2DxeCrypto, TlsDxe, TcgDxe, Tcg2Dxe,
  Tcg2PlatformDxe, Tcg2ConfigDxe, TdTcg2Dxe, TcgMor, RngDxe;
- **config UI**: HiiDatabase, SetupBrowser, DisplayEngine,
  DriverHealthManagerDxe, PlatformDxe.

## Finding 4 — plain vs secboot delta: what Secure Boot drags in

| only in plain (8) | only in secboot (6) |
|-------------------|---------------------|
| VariableRuntimeDxe, FvbServicesRuntimeDxe, EmuVariableFvbRuntimeDxe, FaultTolerantWriteDxe, VariablePolicyDynamicCommand, tftpDynamicCommand, httpDynamicCommand, LinuxInitrdDynamicShellCommand | SecureBootConfigDxe, PiSmmIpl, SmmAccess2Dxe, SmmControl2Dxe, CpuS3DataDxe, VariableSmmRuntimeDxe |
| — | plus 9 SMM modules: PiSmmCore, PiSmmCpuDxeSmm, VariableSmm, SmmLockBox, FvbServicesSmm, SmmFaultTolerantWriteDxe, VariableSmmRuntimeDxe… |

The lesson (Q7 of the map): on the SMM_REQUIRE build, **variable
services move inside SMM** (ring -2). Enabling one setup-visible
feature (Secure Boot) restructures the privilege topology of the whole
platform. Also: two files in DXEFV share the UI name `CpuDxe`
(`1A1E4886…`, `6490F1C5…`) — **UI names are labels; GUIDs are
identity.**

## Finding 5 — a REAL variable store yields REAL names (Q5 of the map)

`OVMF_VARS_4M.snakeoil.fd` (a populated store, unlike the blank
template): 1 FV classified "variable store", and the utf-16 heuristic
returned **22 real variable names**:

`CustomMode, certdb, VendorKeysNv, MTC, BootOrder, Boot0000, ,UiApp,
Timeout, PlatformLang, Lang, VarErrorFlag, ConIn, ConOut, ErrOut,
Key0000, Key0001, Boot0001, " UEFI QEMU HARDDISK QM00001 ",
MemoryTypeInformation, dbx, KEK, SecureBootEnable`

Two honest caveats, visible in that very list:

- artifacts like `",UiApp"` and `" UEFI QEMU HARDDISK QM00001 "` are
  utf-16 strings found inside variable DATA (boot entry descriptions),
  not variable names — the heuristic is labelled "names by heuristic"
  and this is exactly the fuzziness that label admits;
- `SecureBootEnable`, `KEK`, `dbx`, `CustomMode`, `certdb` — the
  Secure Boot machinery is visible from the store side too.

## Finding 6 — the parser itself was corrected (0.7.1)

The investigation caught a real bug in the frozen surface — caught
BEFORE day-0, exactly as the synthetic-image tests caught three parser
traps before their first real run:

- `EE4E5898…` was mislabelled "system NV data store": it is the **LZMA
  custom decompress GUID**. Root cause: the synthetic fixture had
  borrowed it as a store GUID; the parser inherited the mistake. The
  fixture now uses the real authenticated variable store GUID
  (`AAF32C78…`), the parser labels LZMA honestly, and no longer scans
  an LZMA-GUID FV for variable names;
- `FFF12B8D…` was labelled "variable store (EVSA)": it is
  **EFI_SYSTEM_NV_DATA_FV_GUID**;
- both corrections frozen by a new structural test. 322 → 323 checks,
  all green in both worlds; the fifteen-tool surface is untouched.

## What this changes for day-0 (16/09)

1. Expect the real board's DXE module list to be **partially or fully
   compressed** — 0 visible modules does NOT mean an empty firmware;
   it means the census must decompress (LZMA today, maybe Tiano/EFI
   compressed sections on vendor images) before counting.
2. The NVRAM section may show a mix of variable names and utf-16
   strings from variable data — read the list as "utf-16 strings in
   the store", which is what the label already says.
3. The `descriptor absent` note on the real dump would be a
   **surprise** (real Intel boards carry one) — and surprises are what
   `rehearse-diff --latest` exists for.
