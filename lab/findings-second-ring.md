# The Second Ring — seven new fronts, zero bytes written (2026-09-11)

> Companion to `findings-first-ring.md` (the first ring: species census, ROM
> chains, trust chain, PSP lens). This campaign drilled **into** the objects
> the first ring had only catalogued: the variable store byte by byte, the
> boot option grammar, the dependency web, the security GUID carriers, and
> the third build Debian ships. Read-only throughout — the probe scripts live
> in the sandbox (`/home/z/my-project/scripts/`), the artifacts here.
>
> Probes: `nvram_anatomy.py`, `boot_chain_probe.py`, `depex_probe.py`,
> `pe_xref_probe.py`. Artifacts: `lab/ovmf-keyring.json` (byte-level walk of
> three real stores).

## Front N1 — the NVRAM is a journal, not a dictionary

Walking `OVMF_VARS_4M.{fd,ms.fd,snakeoil.fd}` (the three real variants Debian
ships — empty, Microsoft-keyed, snake-oil-keyed) with a hand-rolled
authenticated-variable walker produced the densest single page of the
campaign.

**Store geometry (real bytes).** One FV per image (`0x84000`), FileSystemGuid
`FFF12B8D` (system NV data FV), header `0x48`; then a
`VARIABLE_STORE_HEADER` with signature `AAF32C78` (the **authenticated**
variable store), size `0x3FFB8`, format `0x5A` (formatted), state `0xFE`
(healthy). Past the store, at `0x40000`, the FTW working space — all `0xFF`
in the shipped images: the fault-tolerant reclaim machinery has never fired
yet. The spare block fills the rest of the FV.

**All three variants use the authenticated store — even the empty one, even
the non-secboot pairing.** Time-based authenticated variable headers
(60 bytes: StartId `0x55AA`, state, attributes, monotonic count, 16-byte
timestamp, pubkey index, name/data sizes, namespace GUID) are the edk2
*default*, not a Secure Boot consequence. Q7 gains a nuance: the expensive
variable machinery predates the Secure Boot switch; what Secure Boot moves
into SMM is the *service*, not the *format*.

**The state machine, read on real records.** 39 headers per populated store:
21 live (`0x3F`), 18 deleted (`0x3D` / `0x3C`), 0 aborted (`0x7F`). Deletion
is a **state-byte flip** — the record stays until FTW reclaim — so a real
store is a journal of everything that ever happened to it. The journal
reads like boot history:

- `ConIn`/`ConOut`/`ErrOut` rewritten five to six times each (34 → 107 →
  243 → … bytes, settling at 146/195/146) — console enumeration retried
  across early boots before the config stabilized;
- `BootOrder` deleted **twice** and absent from the live set — see front N2;
- `CustomMode` flipped three times, `VendorKeysNv` deleted and re-added —
  the fingerprint of a key-enrollment operation;
- `MemoryTypeInformation` (NV|BS, 48 bytes) — the reboot-presets-memory
  variable, a kill-list-adjacent curiosity.

Space audit: of 262,044 recordable bytes, live data is 9,167 (ms) / 5,547
(snake-oil) against 3,468 of deleted garbage — about 1.3% churn in a fresh
image, with the structure (not the ratio) being the lesson.

**The keyring, parsed.** `EFI_SIGNATURE_LIST` walking of PK/KEK/db/dbx with a
mini-DER extractor (subjects pulled from the X509 blobs):

| Store | PK | KEK | db | dbx |
|-------|----|-----|----|-----|
| `.ms` | Debian UEFI Secure Boot (961 B) | Debian + MS Third-Party Marketplace Root (2) | MS Root CA 2010 + MS Third-Party Marketplace Root (2) | 1 SHA-256 |
| `.snakeoil` | SnakeOil Test Key (987 B) | SnakeOil (1) | SnakeOil (1) | 1 SHA-256 |

- Signature types read from the bytes: X509 = `A5C059A1-94E4-4AA7-87B5-
  AB155C2BF072`, SHA-256 = `C1C41626-504C-4092-ACA9-41F936934328`.
- **The pre-provisioned `dbx` is `e3b0c442…` — the SHA-256 of the empty
  string.** A revocation entry that revokes nothing: a placeholder so the
  forbidden-database variable exists. LogoFAIL-class revocations replace
  exactly this content on real machines.
- `certdb` (namespace `D9BEE56E…`) is a 4-byte internal integrity record of
  the auth-variable driver — **not** a signature list; not parsed, honestly.
- Namespaces discovered live: `SecureBootEnable` `F0A30BC7…`, `CustomMode`
  `C076EC0C…`, `VendorKeysNv` `9073E4E0…`, `VarErrorFlag` `04B37FE8…`.

**EVSA: closed empirically.** A byte scan for the `EVSA` marker across all
three stores: absent. The edk2 authenticated store is not EVSA; the 0.7.1
label correction is confirmed against reality, and the taxonomy is clean.

**Feeds:** Q3 (kill-list rows for PK/KEK/db/dbx/SecureBootEnable/CustomMode),
Q5 (the journal anatomy — names AND states AND history), Q7 (auth format
default).

## Front N2 — the boot chain, resolved by position, not by memory

Decoding `EFI_LOAD_OPTION` entries with a device-path walker that labels
nodes **by structure and by byte-proven GUID position** (two remembered
subtype constants turned out wrong when confronted with the bytes — the
walker now trusts shapes, not recall):

- `Boot0000 "UiApp"` (attrs `0x109` = ACTIVE | CATEGORY_APP):
  `Media(7CB8BDC9-…)` → proven = **the DXEFV FvName** (it sits exactly at the
  FV extended-header position, a bare 20-byte GUID+size block inside the
  first pad file) → then `Media(462CAA21-…)` → proven = **the UiApp FFS
  file** (a type-0x09 APPLICATION, 114,478 bytes, live in DXEFV). The setup
  UI is an application inside the DXE volume, launched like an OS.
- `Boot0001 "UEFI QEMU HARDDISK QM00001"` (attrs `0x1`): `ACPI(PNP0A03)` →
  `PCI(1f.2)` → a 10-byte SATA-shaped node (`HBA=0, PM=0xFFFF, LUN=0`) →
  End. Optional data = one 16-byte GUID, unidentified (honest). No HD node,
  no file path: the actual `\EFI\BOOT\BOOTX64.EFI` resolution happens at
  boot time via SimpleFileSystem enumeration.
- **`BootOrder` is deleted in the shipped store.** The candidates live
  (`Boot0000`, `Boot0001`), the order does not — BDS reconstructs the
  sequence at every boot. The store carries candidates; the runtime carries
  policy.
- **Console channels, from the firmware's own NVRAM**: `ConIn` = keyboard
  (`PNP0303`) + serial; `ConOut`/`ErrOut` = `PNP0501` UART node with an
  `EFI_UART_DEVICE_PATH`-shaped payload decoding to **115200 8N1**. The
  never-dying channel is not doctrine here — it is a first-class console in
  the shipped variable store (Q2 evidence, byte-level).
- `OsIndicationsSupported` is absent from flash — constructed at runtime,
  never stored.

**The unified 4 MiB image.** Assembling VARS + CODE (secboot) and re-running
the frozen `spi-map` on the whole flash — the QEMU-shaped rehearsal of
day-0's dump:

```
FV @ 0x000000  len=0x0084000  [VARS] system NV data FV   (22 NVRAM names)
FV @ 0x084000  len=0x0348000  [CODE] FVMAIN_COMPACT (FFS2, 2 files → LZMA)
FV @ 0x3CC000  len=0x0034000  [CODE] SECFV (FFS2, 4 files)
```

`spi-map` reports honestly on a whole-flash image: 3 FVs, compressed main
volume, 22 NVRAM names, no hallucinated modules. The tool is ready for the
real dump's shape.

**Feeds:** Q2 (serial console in NVRAM), Q6 (chain resolved to file level).

## Front N3 — the dependency web: what the platform waits for

Parsing DEPEX sections (DXE `0x13`, PEI `0x1B`, SMM `0x1C`) across both
builds:

- Coverage: plain = 78 DXE depex for 115 DXE files (**37 drivers with no
  depex at all — the spine by absence**, dispatched in FV order); secboot =
  76 DXE + 17 PEI + 8 SMM. Explicit `TRUE,END` spine: only three files
  (PcdPeim, one unnamed PEIM, DevicePathDxe).
- **Zero BEFORE/AFTER constraints** in OVMF — ordering is emergent from
  dependencies, never legislated. (Vendor images may differ; day-0 check.)
- The most-waited-for protocols (PUSH counts):
  `PcdProtocol` 56/62, `DevicePathUtilities` 50/54, **`VariableArch` +
  `VariableWriteArch` 28/29** — nearly every driver waits for the variable
  service: *the write gate sits on the platform's critical path*. Then
  CpuIo, Metronome, Reset, HiiDatabase, BdsArch, CpuArch.
- Every SMM servant declares a gate (8 SMM depex in secboot); `PiSmmCore`
  needs none — the core is above the gate vocabulary.

**Feeds:** Q1 (what loads before anything can be asked), Q4/Q7 (the
variable service as chokepoint).

## Front N4 — the security x-ray, and a build that hides nothing

Scanning every module's PE body for the byte patterns of security-critical
GUIDs (variable namespaces, arch protocols) in both builds, then diffing
the **third build** (`secboot.strictnx`) against secboot:

- **GlobalVariable carriers**: 24 (plain) vs 22 (secboot). The secboot build
  gains `SecureBootConfigDxe`, `SecurityStubDxe`, `VariableSmm`,
  `VariableSmmRuntimeDxe` — and **amputates the UEFI Shell**
  (`7C04A583-…`) plus `LinuxInitrdDynamicShellCommand`,
  `httpDynamicCommand`, `tftpDynamicCommand`. Enabling Secure Boot in this
  platform does not just move variables into SMM — it removes an
  unsigned-code execution surface from the image entirely.
- The security namespaces (`db`/`dbx`, `SecureBootEnable`, `CustomMode`,
  `VendorKeysNv`, `certdb`) are carried by exactly `SecureBootConfigDxe`
  and the variable service — one UI module, one enforcement module, per
  namespace. `VarErrorFlag` moves from `VariableRuntimeDxe` (plain) into
  `VariableSmm` (secboot): even the error flag went to ring -2.
- **strictNX: 145 GUIDs vs 145 GUIDs, zero delta.** Strict-NX is a **policy
  bit**, not a module delta — a class of hardening that leaves no census
  trace. Day-0 consequence: census says what is present; PCDs and policy
  say what is enforced. Both must be read.

**Feeds:** Q4 (who holds which wall), Q7 (the SMM migration made concrete),
Q1 (the setup façade's enforcement side).

## Front N5 — the measurement and capsule lens (documentation front)

- TPM support is present **in both builds** by module names: `TcgDxe`,
  `Tcg2Dxe`, `Tcg2PlatformDxe`, `Tcg2ConfigDxe`, `TdTcg2Dxe`, `TcgMor`;
  the secboot build adds `TcgMorLockSmm` — even the MemoryOverwriteRequest
  lock moves into ring -2 with Secure Boot.
- Honest negative: a remembered Tcg2 *protocol* GUID matched zero bytes in
  both builds and was dropped from the probe. TPM presence is proven by
  names; the protocol GUID gets a registry lookup on day-0, not a guess.
- The measurement channel is the agent's read-only truth probe: PCRs 0–7
  (firmware measurements) readable at `/sys/class/tpm/tpm0/pcr-sha256/N`,
  the event log at `/sys/kernel/security/tpm0/binary_bios_measurements`
  (root). "What booted" without writing anything.
- Capsule path: `CapsuleRuntimeDxe` in both builds; the update gate the
  doctrine never touches. Its NVRAM side (`OsIndications` bit
  `FILE_CAPSULE_UPDATE`) is runtime-constructed, not stored.

## Front N6 — EVSA: closed empirically

`EVSA` marker absent from all three real stores — the edk2 authenticated
variable store is not EVSA. The 0.7.1 label correction (which stopped
calling `FFF12B8D` an "EVSA store") is confirmed against the actual bytes.
One label, three images, zero doubt left.

## Front N7 — the Linux-side contract (what the agent reads)

The runtime mirror of everything front N1 byte-mapped, for the day-0
agent on bare metal:

- `efivarfs` (`/sys/firmware/efi/efivars`): entries are `Name-GUID`, each
  file prefixed by a u32 attributes word — the same attribute bits read
  from the store (NV|BS|RT = 0x7; TimeBasedAuth = 0x20 marks the keyring).
  **Reading is zero-write by construction.**
- The NVRAM journal (front N1) is what makes the write path safe to
  understand and safe to refuse: TimeBasedAuth variables (PK/KEK/db/dbx)
  require signed sets — the keyring parsed here is exactly what makes an
  unsigned SetVariable fail. The agent explains this; it never exercises
  it.
- This sandbox has no efivarfs (the mirror is an environment property,
  first ring); on TWIN-1 bare metal the mirror opens and `capture --live`
  tags provenance in both worlds.

## What this changes for day-0 (16/09)

The dump checklist gains five read-only instruments, all proven on real
firmware this campaign:

1. **NVRAM journal walk** (front N1 walker): states, attributes, deleted
   archaeology, keyring subjects — offline from `day0-spi.bin`.
2. **Boot option decode** (front N2): vendor `Boot####` device paths
   resolved by position; expect FvFile boot managers and USB/SATA/NVMe
   chains.
3. **Depex census** (front N3): who waits for whom; expect non-zero
   BEFORE/AFTER on vendor images.
4. **Security x-ray** (front N4): GlobalVariable and security-namespace
   carriers — the enforcement map in one pass.
5. **Policy-vs-census discipline** (strictNX lesson): module presence ≠
   policy enforcement; read both or claim nothing.

Discipline unchanged: zero bytes written to any firmware; the only scratch
artifact is the unified image reassembled from already-read bytes inside
the sandbox; repo artifacts are documents and one JSON. Surface frozen:
15 tools, 323 checks, MCP smoke 12 — all re-verified after the campaign.
