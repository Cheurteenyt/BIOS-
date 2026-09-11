# The Fourth Ring — seven new fronts, zero bytes written (2026-09-11)

> Companion to `findings-first-ring.md` (first ring), `findings-second-ring.md`
> (second ring) and `findings-third-ring.md` (third ring). The first ring
> catalogued the species, the second drilled into the objects, the third
> resolved the policy and closed the execution chain. The fourth ring maps
> the **gates**, the **provenance**, the **texture**, the **supervisor**
> (SMM), the **kernel lane**, the **keep-set** — and closes most of the
> honesty ledger left open by three rings. Read-only throughout; probe
> scripts live in the sandbox (`/home/z/my-project/scripts/`), artifacts
> here.
>
> Probes: `gate_xray_probe.py`, `pe_provenance_probe.py`,
> `entropy_atlas_probe.py`, `smm_anatomy_probe.py`, `honesty_ledger_probe.py`,
> `kernel_lane_probe.py`, `read_path_probe.py` (+ shared `ring4_lib.py`).
> Artifacts: `lab/ovmf-build-delta.json`, `lab/ovmf-pe-provenance.json`.

## Front U1 — the gates x-ray and the named build delta

Four platform gates decide what a UEFI machine can do: variable services
(everything persists through them), the Security/Security2 stubs (image-load
verification), the HII database (the setup facade), and the device-path
utilities (every boot target is one). The probe scans every module body for
the 16-byte protocol GUID constants of each gate and cross-references the
depex web (a PUSH is an explicit wait).

| Gate (secboot build) | body holders | depex waiters | note |
|---|---|---|---|
| VariableArch | 31 | 29 | DxeCore among holders |
| VariableWriteArch | 33 | 29 | the critical-path service (ring 2) |
| SecurityArch | 23 | 20 | the entire network stack waits on it |
| Security2Arch | **3** | 0 | DxeCore + SecurityStubDxe + **PiSmmCore** |
| HiiDatabase | 21 | 11 | LogoDxe waits on it |
| HiiConfigRouting | 23 | 21 | |
| HiiString | 20 | 10 | |
| HiiConfigAccess | 14 | 0 | the setup-screen producers |
| DevicePathUtilities | **112** | **54** | the most universal gate |
| SimpleFileSystem | 11 | 0 | |
| BlockIo | 14 | 0 | |
| LoadFile2 | 3 | 0 | DxeCore, PciBusDxe, QemuKernelLoaderFsDxe |
| RngProtocol | **0** | 0 | honest zero — see below |
| Tcg2Protocol | 10 | 4 | byte-proven GUID (Front U5d) |
| RuntimeArch | 23 | 21 | |
| SmmVariableWrite | 2 | 1 | VariableSmm pair only |

**Security2Arch is a near-choke-point**: three holders, and the third is
PiSmmCore — the SMM supervisor itself sits in the image-verification
triangle. **DevicePathUtilities is the platform's true commons** (112 of
142 modules embed it). **RngProtocol is an honest zero**: no module embeds
the constant, even searched by 4-byte prefix — OVMF takes entropy at
library level (RDRAND), never through a protocol. There is no RNG surface
to audit on this build; the day-0 question becomes *what the vendor build
does* — an ASUS image with an RngProtocol producer would be a difference
that matters.

The named plain↔secboot delta (inner FVs; whole-image hashes were Front
T2's): **126 GUIDs in both, 18 added, 9 removed, 6 byte-identical bodies.**

- Added: `SecureBootConfigDxe` (716,382 B), 12 SMM-family modules
  (`VariableSmm` 868,498 B, `PiSmmCpuDxeSmm` 82,074 B, `PiSmmCore` 41,026 B
  type 0x0D, `PiSmmIpl`, `FvbServicesSmm`, `SmmLockBox`,
  `SmmFaultTolerantWriteDxe`, `CpuHotplugSmm`, `CpuIo2Smm`, `SmmAccess2Dxe`,
  `SmmControl2Dxe`, `TcgMorLockSmm`), `VariableSmmRuntimeDxe` 24,726 B,
  `CpuS3DataDxe`, and three unnamed PEIMs (SMM reload helpers).
- Removed: **the UEFI Shell** `7C04A583…` (894,422 B, the largest single
  file in the plain build), `VariableRuntimeDxe` 41,086 B (replaced by the
  893 KB SMM pair), `FvbServicesRuntimeDxe` → `FvbServicesSmm`,
  `FaultTolerantWriteDxe` → `SmmFaultTolerantWriteDxe`,
  `EmuVariableFvbRuntimeDxe`, and the four dynamic shell commands
  (`VariablePolicy`, `http` 38,534 B, `tftp` 30,278 B, `LinuxInitrd`
  20,878 B).
- The headline: **`SecurityStubDxe` 13,942 → 825,334 B (×59)**. Secure
  Boot does not arrive as a flag — it arrives as an 811 KB payload of
  PKCS7/certificate machinery welded into the security stub. "Secure Boot
  enabled" means "a second, bigger verifier now owns image load."

Artifact: `lab/ovmf-build-delta.json`.

## Front U2 — the PE provenance x-ray (all three builds)

Every module is a PE image; the header is a passport. All 133/142/142
parseable modules across the three builds, plus honest counts of the
non-PE (raw/section-less files):

- **Timestamps: all `0x0`** — Debian's reproducible build zeroes
  `TimeDateStamp` everywhere. The build leaks no dates.
- **CodeView/PDB paths: none.** The RSDS lens returns zero — binaries are
  stripped. On Debian the provenance lens finds nothing; the same lens on
  the ASUS dump is therefore *differential*: any path or timestamp found
  there is vendor information Debian chose not to leak.
- Subsystems: plain = 121 BS-drivers + 10 RT-drivers + 2 applications
  (UiApp + Shell); secboot = 131 + 10 + 1 (Shell amputated).
- **DYNAMIC_BASE (PE ASLR): 0 modules.** OVMF executes
  position-dependent; relocation tables exist (`.reloc` in 118/124
  modules) but no image chooses a random base.
- **The NX flag (`DllCharacteristics 0x100`) is the runtime+SMM badge.**
  Plain: exactly the 10 runtime modules. Secboot: those 7 that survive +
  12 SMM-family modules = 19. The DXE drivers carry no flag — consistent
  with Front T2's finding that the DXE NX policy lives in three compiled
  bytes of BdsDxe/IScsiDxe `.text`, not in headers. And the NX pair's
  headers are **byte-identical between secboot and strict-nx** — the
  policy leaves no passport trace. Header-level read = phase-aware read.
- `.rsrc` sections: plain has 5 (`LogoDxe` + the four dynamic shell
  commands); secboot keeps exactly one — **`LogoDxe`, the LogoFAIL-class
  image-parser surface that survives every amputation**.

Artifact: `lab/ovmf-pe-provenance.json`.

## Front U3 — the entropy atlas of the unified 4 MiB flash

Census counts what is named; hash-diff sees what changed. Texture is the
third sense: a 4 KiB Shannon window (2 KiB step) over the unified image
(snake-oil VARS + secboot CODE = 4,194,304 B, exactly what a chip
programmer reads):

| Class | Bytes | Share |
|---|---|---|
| void (≈0.00, erased 0xFF) | 2,469,888 | **58.9 %** |
| near-random (≥7.6, the LZMA wall) | 1,654,784 | 39.5 % |
| dense (6.0–7.6) | 38,912 | 0.9 % |
| structured (2.5–6.0) | 18,432 | 0.4 % |
| sparse (<2.5) | 10,240 | 0.2 % |

- The compressed payload is one near-random run `0x084000–0x218000`
  (mean 7.95 B/B; densest window 7.966 at 0x161800).
- **Behind the wall sits a 1,783,300-byte pure-0xFF void**
  (`0x2189FC–0x3CC4E0`) — 43 % of the entire 4 MiB is empty flash the
  compressed payload never grows into. FVMAIN_COMPACT reserves room for
  firmware that is twice as big as what ships. On day-0, the same void in
  the ASUS dump is the vendor's growth reserve — and the place where an
  update will write.
- A second void: 164,408 B at `0x3D7290` (SECFV tail).
- The NVRAM half is void from `0x2800` — the entire variable journal,
  39 records and all its archaeology, fits in the first 10 KB of a
  256 KB store (ring 2's budget, now seen as texture).

Day-0 translation: run this walk on `day0-spi.bin` first. Texture tells
you where to aim the FFS walker and the LZMA piercer before any name is
resolved — and classifies vendor regions (compressed? keystore? padding?)
without knowing their names.

## Front U4 — the SMM anatomy of the secboot build

The complete supervisor inventory, by name, type, depex, and size:

| Module | Type | Size | depex anchor |
|---|---|---|---|
| VariableSmm | 0x0A | 868,498 B | Pcd + in-SMM anchors |
| PiSmmCpuDxeSmm | 0x0A | 82,074 B | |
| PiSmmCore | 0x0D | 41,026 B | **no depex** |
| SmmFaultTolerantWriteDxe | 0x0A | 24,786 B | + RuntimeArch, FTW gate |
| VariableSmmRuntimeDxe | 0x07 | 24,726 B | pushes **SmmVariableWrite** |
| PiSmmIpl | 0x07 | 24,718 B | pushes an extra 843DC720… gate |
| SmmControl2Dxe | 0x07 | 20,638 B | TRUE + two SMM gates |
| FvbServicesSmm | 0x0A | 20,634 B | |
| SmmLockBox | 0x0A | 20,626 B | |
| CpuHotplugSmm | 0x0A | 16,570 B | |
| CpuIo2Smm | 0x0A | 16,490 B | |
| TcgMorLockSmm | 0x0A | 12,474 B | |
| SmmAccess2Dxe | 0x07 | 2,674 B | |

- **Total SMM-hosted: 1,175,934 B of 6,576,614 module bytes = 17.9 %.**
- `VariableSmm` alone is 868 KB — the single biggest module in the build.
  Secure Boot's variable services are not just SMM-hosted; they ARE the
  SMM payload. The platform's supervisor exists, in this build, to guard
  the keyring.
- Every in-SMM handler depex-pushes two recurring un-named anchors
  (`C2702B74…`, `F4CCBFB7…`) — the in-SMM services spine. The
  SMM↔runtime bridge constant is **`DA1B0D11-D1A7-46C4-9DC9-F3714875C6EB`**,
  shared by *exactly* `VariableSmm` and `VariableSmmRuntimeDxe`
  (byte-proven; memory name retired — see the ledger).
- AM4 translation: expect an order of magnitude more SMM on the ASUS
  image (AGESA SMM drivers, vendor setup callbacks); MSR `0xC0010111`
  bit 0 (SMM_LOCK) is the register-side cross-check (Front T7).

## Front U5 — the honesty ledger: four flags, three closed

**(a) The 0x14 container — CLOSED.** The facade vocabulary is a chain of
**`EFI_HII_SIBT_STRINGS_UCS2` blocks** (HII string-package inline blocks,
block type 0x14) packed into `.data`: a 0x14 marker opens a block of
NUL-terminated UCS-2 strings, each block terminated by an empty string.
Structural proof on UiApp's 30,144-byte `.data`: **128/145 sentences are
immediately preceded by a 0x14 marker; 126/145 by the NUL-pair + 0x14
pattern** (the remainder are continuation strings inside open blocks —
exactly the SIBT grammar). Ring 3's "~423 sentences" were strings inside
these blocks; the facade's container is now a named, spec-shaped object.

**(b) GUID E750224E-… — CLOSED.** `E750224E-7BCE-40AF-B5BB-47E3611EB5C2` is
**TdxDxe** — the Intel TDX guest-support module, census-named in both
builds. On an AMD AM4 machine it is dead weight riding in the image: a
fresh, GUID-precise amputation candidate (recorded in the kill-list
spirit, frozen like everything else).

**(c) Boot0001's optional tail — MEASURED, semantics still flagged.** The
auth-variable walk had to be rebuilt byte-first: the header is **60
bytes, not 64** (`PubKeyIndex` is UINT32), the first record sits at
`0x64`, and the re-proven walk counts **39/39 records in both populated
stores** — matching ring 2 exactly. Boot0001: 110 B load option, state
0x3F, attr 0x1, device path 32 B, **optional tail 17 B**
(`004eac0881119f594d850ee21a522c59b2`). Hypotheses tested: ESP
partition-type GUID — refuted; LBA/size u64 pair — implausible. The tail
stays flagged, now with its exact bytes on the record.

**(d) The Tcg2 protocol GUID — CLOSED.** The byte-proven constant is
**`607F766C-7455-42BE-930B-E4D76DB2720F`** (embedded in Tcg2Dxe,
depex-confirmed via TcgMor/TcgMorLockSmm). Ten holders across the
measurement stack. The ring-2 memory constant (`…9306-E3E0B3D9F32B`)
is retired: zero matches even by 4-byte prefix. The house lesson holds:
*memory constants lose, bytes win — always.*

## Front U6 — the direct-kernel lane (firmware side)

Omarchy's doctrine boots a Linux UKI as a UEFI image. OVMF ships the
QEMU-only shortcut for that lane: `QemuKernelLoaderFsDxe`, present in
BOTH builds (plain 11,514 B / secboot 11,066 B, 5 depex pushes) — the
fw_cfg `-kernel/-initrd/-cmdline` files exposed as a SimpleFileSystem
for BDS. Its served file names are constructed at runtime (zero plain
ASCII hits — honest note).

- `LINUX-INITRD-MEDIA` (`5568E427…`): **zero references in either
  build.** The initrd hand-back protocol is OS-side; the firmware never
  embeds the constant.
- LoadFile2 references: DxeCore, PciBusDxe, QemuKernelLoaderFsDxe — plus
  (plain only) `LinuxInitrdDynamicShellCommand` and the Shell.
- **Verdict:** the secboot amputation of the shell-side initrd command
  removes nothing the UKI lane needs. On real AM4 the lane needs: a
  block path + Fat to read the ESP, and DxeCore's LoadImage on a PE32+
  payload. The loader (Limine/systemd-stub) serves its own initrd.
  `QemuKernelLoaderFsDxe` is a virtual-machine shortcut, not part of any
  real-machine blueprint.

## Front U7 — the read-path anatomy: the keep-set

The kill-list (Front T5) says what can be removed. This front writes the
positive counterpart: the chain a machine NEEDS to open `\EFI\…` on a
disk — PCI host bridge → PCI bus → SATA/NVMe/virtio pass-through → block
→ partition → FAT → SimpleFileSystem:

| Module (secboot) | Size | depex | BlkIo | SFS |
|---|---|---|---|---|
| PciBusDxe | 41,858 | TRUE-spine | 0 | 0 |
| ScsiDisk | 30,466 | TRUE-spine | 1 | 0 |
| AtaAtapiPassThruDxe | 26,582 | TRUE-spine | 0 | 0 |
| NvmExpressDxe | 26,570 | TRUE-spine | 1 | 0 |
| **Fat** | 24,694 | TRUE-spine | **1** | **1** |
| PciHostBridgeDxe | 17,574 | 8 pushes | 0 | 0 |
| PartitionDxe | 13,578 | TRUE-spine | 1 | 0 |
| AtaBusDxe | 12,866 | TRUE-spine | 1 | 0 |
| ScsiBus | 7,422 | TRUE-spine | 0 | 0 |
| DiskIoDxe | 7,234 | TRUE-spine | 1 | 0 |
| VirtioBlkDxe | 5,642 | TRUE-spine | 1 | 0 |
| SataController | 4,686 | TRUE-spine | 0 | 0 |
| VirtioPciDeviceDxe | 4,118 | TRUE-spine | 0 | 0 |

- Chain total: **223,290 B (secboot) / 226,426 B (plain)** — the
  entire ability to boot from disk costs less than half a percent of the
  inflated payload, and eleven of its thirteen modules are TRUE-spine
  (no depex: dispatched immediately).
- `Fat` is the only module that both produces and consumes across the
  block/file boundary — the single socket where firmware touches the
  ESP we never write.
- **The doctrine collision: 11 of these 13 modules ARE the kill-list's
  "storage family (18)".** Amputating that family as JSON'd would
  amputate the boot path itself. The kill-list must carry a keep-set
  carve-out: `ScsiDisk, AtaAtapiPassThruDxe, NvmExpressDxe, Fat,
  PartitionDxe, AtaBusDxe, ScsiBus, DiskIoDxe, VirtioBlkDxe,
  SataController, VirtioPciDeviceDxe` — ≈215 KB that no amputation may
  touch. (The disk-less blueprint variant is the only exception, and it
  is a different machine.)

## The honesty register, after four rings

Closed this ring: the 0x14 container (SIBT), E750224E (TdxDxe), the Tcg2
protocol GUID (byte-proven), the BdsDxe/IScsiDxe header question
(header-identical), the RNG question (honest zero), the SMM bridge GUID
(DA1B0D11, byte-proven). Corrected: the ring-2 depex table labelled
`B7DFB4E1-052F-449F-87BE-9818FC91B733` as "HiiDatabase" — it is
**RuntimeArch** (pushed 21× alongside the arch family; 23 body holders
including DxeCore); true HiiDatabase is `EF9FC172…` (pushed 14×). The
ring-2 probe file stays as history; this ring's probes carry the
correction.

Still flagged, with evidence: Boot0001's 17-byte optional tail
(bytes recorded); the in-SMM depex anchors `C2702B74…`, `F4CCBFB7…`,
`4E939DE9…`, `F8775D50…`, `843DC720…`, `D326D041…` (byte-proven, names
not resolved from memory — registry check on day-0); the LoadFile2 role
of `PciBusDxe` (constant present, semantics unproven).

## Day-0 consequences (16/09)

| Instrument (offline, from the dump) | Feeds |
|---|---|
| entropy atlas walk on `day0-spi.bin` | target selection before naming |
| PE header x-ray (stamps, NX badge, PDB) | vendor provenance differential |
| gates x-ray (holders/waiters per gate) | choke-point map of the vendor image |
| SMM inventory + byte share | supervisor inflation vs the 17.9 % reference |
| keep-set check before any kill-list talk | boot-path survival |
| corrected GUID table (Tcg2, RuntimeArch, DA1B0D11) | registry cross-checks |

The protocol is unchanged: `capture --live` → `rehearse` →
`rehearse-diff --latest`, optionally
`sudo omarchy-firmware spi-map --save-dump day0-spi.bin` + sha256.
Read-only everywhere; the machine is never the workbench.
