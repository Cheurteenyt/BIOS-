# The Third Ring — seven new fronts, zero bytes written (2026-09-11)

> Companion to `findings-first-ring.md` (first ring) and
> `findings-second-ring.md` (second ring). The first ring catalogued the
> species; the second drilled into the objects; the third ring resolved the
> **policy**, the **execution chain**, the **vocabulary**, the **budget** —
> and armed the AMD half of day-0. Read-only throughout; probe scripts live
> in the sandbox (`/home/z/my-project/scripts/`), artifacts here.
>
> Probes: `exec_chain_probe.py`, `policy_locator_probe.py`,
> `facade_probe.py`, `built_vs_shipped_probe.py`,
> `network_amputation_probe.py`, `nvram_budget_probe.py`.
> Artifacts: `lab/ovmf-kill-list.json` (blueprint-grade module lists).

## Front T1 — the firmware's own chain, resolved by position

The second ring resolved the OS-loader chain (Boot0000 → UiApp). This one
resolves the chain that runs before any boot option exists.

**The first instruction of the platform is not a jump — it is a fork.**
The sixteen bytes at `0xFFFFFFF0..0xFFFFFFFF` read
`0F 20 C0 A8 01 74 05 E9 2C FF FF FF E9 11 FF 90`:

```
0xFFFFFFF0  0F 20 C0        mov eax, cr0
0xFFFFFFF3  A8 01           test al, 1          ; CR0.PE
0xFFFFFFF5  74 05           jz  0xFFFFFFFC
0xFFFFFFF7  E9 2C FF FF FF  jmp 0xFFFFFF28      ; 32-bit: already protected
0xFFFFFFFC  E9 11 FF 90     jmp rel16 -> 0xFFFFFF10   ; 16-bit: plain reset
```

**Both branches land inside one file**: the ResetVector FFS (`1BA0062E…`,
type *raw*, 2,872 bytes, the top of the flash, file span
`0x37B4C8-0x37C000`). Execution begins at the very top of the 4 MiB, in a
2,872-byte file that is the only `raw` file in the whole image. The first
question the platform asks itself is *which mode am I in* — and both
answers live in the same two kilobytes.

**The rest of the chain, each hop a file with a GUID, a type, an offset:**

| Hop | File | Type | Offset | Size |
|-----|------|------|--------|------|
| reset entry | ResetVector `1BA0062E…` | raw | 0x37B4C8 | 2,872 B |
| SEC | SecMain `DF1CCEF6…` (3 sections: .text 0x9AC0 / .data 0x1400 / .reloc 0xC0) | SEC-core | 0x348078 | 45,566 B |
| the wall | LZMA GUID-defined section | — | — | 1,569,609 B |
| inflation | → PEIFV + DXEFV | — | — | 16,122,000 B (×10.3) |
| PEI | PeiCore `52C05B14…` | PEI-core | (PEIFV) 0x168 | 28,602 B |
| PEI | 14 PEIMs, last-in-chain DxeIpl `EDADEB9D…` | PEIM | 0x1CE68 | 50,110 B |
| DXE | DxeCore `D6A2CB7F…` | DXE-core | (DXEFV) 0xE0178 | 139,390 B |
| BDS | BdsDxe `6D33944A…` | DXE-driver | 0x17F938 | 86,650 B |
| front-end | UiApp `462CAA21…` | application | 0x194BB8 | 114,414 B |

**FvName proven at the extended header, independently of round two**: the
inner FVs carry their names at ext-header offset `0x60` (note: `0x60 >
HeaderLength 0x48` — the bytes win, there is no hlen bound to respect):
PEIFV = `6938079B-B503-4E3D-9D24-B28337A25806`, DXEFV =
`7CB8BDC9-F8EB-4F34-AAEA-3EE4AF6516A1` — the same GUID Boot0000's device
path pointed at in the second ring. Two rings, two independent positions,
one name. The payload's first bytes (`7C 00 00 19`) are a 0x7C-byte RAW
section that precedes the FVs inside the LZMA stream.

**The code-side budget, closed**: FVMAIN_COMPACT 3,440,640 B + SECFV
212,992 B = 3,653,632 B — every byte of the CODE file accounted for.

## Front T2 — the policy locator: the NX bit is three bytes

Debian ships three OVMF builds of the same version. Round two proved the
census is blind to the third one (strict-NX: 145 vs 145 GUIDs). This probe
hashes every FFS file body per build and intersects by GUID, then diffs
raw blocks — and the answer is almost embarrassingly small.

**plain vs secboot** (two genuinely different builds): 126 GUIDs in both,
120 differ, only 6 identical bodies — different builds differ nearly
everywhere, as expected.

**secboot vs strict-NX** (the policy pair):

- 144 GUIDs in both, **142 byte-identical bodies, 2 differ**:
  `BdsDxe` and `IScsiDxe`. Nothing else. Not DxeCore. Not PcdDxe. Not a
  single PEIM, not a single SMM module — **the PCD database is
  byte-identical**, so the policy is NOT a platform PCD bake.
- The inflated payload (16,122,000 B) differs in **3 bytes total**:
  - `BdsDxe` rel 0x8AB7 (PE-rel 0x89DF, **inside .text**): `0x01 → 0x00`
  - `IScsiDxe` rel 0x171AA-AB (PE-rel 0x17046, **inside .text**):
    `0x66 0x2E → 0x00 0x66`
- Raw outer-image diff: two ranges only — `0x0-0x1000` (the LZMA section
  header region; 3 bytes differ at 0x88/0x8C/0x90) and `0x0A8000-0x195000`
  (the compressed stream tail that a 3-byte input change re-encodes).
- Neither PE has a `.ppcd` section, so this is not a patchable-PCD patch
  site — it is a compiled-in constant/flag inside each module's code.

**Reading**: Debian's "strict-NX" variant is three bytes of policy, carried
by two DXE modules, invisible to the census at every level — GUID list,
file count, phase counts, even the PCD database. Upstream context (web,
front T7): this is the W^X/NX-clean boot chain work (kraxel, Fedora
Changes/Edk2Security) — IScsiDxe is a known NX-unclean module, BdsDxe the
enforcement-adjacent one. **Day-0 consequence, sharpened to a rule**: the
only census-grade detector of a policy delta is a **hash diff against a
known-good reference**. Same module list proves nothing.

## Front T3 — the façade, quantified

"The setup is a facade" (Q1). Measured where it speaks. Method note
(honest): this build embeds the strings as packed utf-16 constants inside
the module PE — **no `.hii` COFF section, no 0x18 FFS section, and the
strings are separated by a single `0x14` byte, not the SIBT-block
form** — so the container format itself stays an open byte-level question
(upstream check); the vocabulary below is read directly from the bytes,
per module, deduped.

| Module | Build | Distinct utf-16 strings | Keyword families |
|--------|-------|------------------------|------------------|
| UiApp `462CAA21…` | plain | **165** | Boot×18, Device×17, Driver×8, Console×5, Network×4, Reset×2 |
| BdsDxe `6D33944A…` | plain | **95** | Boot×14, Device×7, TPM×1, Key×2 |
| Tcg2ConfigDxe `4D9CBEF0…` | plain | **64** | TPM×17, Device×6 |
| SecureBootConfigDxe `F0E6A44F…` | secboot | **99** | Secure×10, Delete×12, Enroll×8, Custom×5, Key×4 |

The façade's own sentences, read from the bytes:

- UiApp: "Configuration changed. Reset to apply it Now.", "Legacy Hard
  Drive", "Non-Block Boot Device", "NO VOLUME LABEL", "Press ENTER to
  reset" — a screen-painter with 165 sentences, every one of them an
  editor of NVRAM state.
- BdsDxe: "Boot Manager Menu", "Default PlatformRecovery", "EFI Internal
  Shell", and — a Debian fingerprint — **"Grub Bootloader"**: the vendor
  customization visible in shipped bytes.
- SecureBootConfigDxe: "Are you sure you want to delete PK? Secure boot
  will be disabled!", "Only Physical Presence User could disable secure
  boot!", "Only supports DER-encoded X509 certificate" — the screens map
  one-to-one onto the keyring operations the second ring parsed (PK/KEK/
  db/dbx, CustomMode, VendorKeysNv).
- Tcg2ConfigDxe: "TCG2 Configuration", "TPM2 Operation", "Current PPI
  Version: 1.2 or 1.3" — the TPM half of the kill-list has its screen.

**Q1's measurable gap, lab edition**: 115 DXE modules exist; the façade
speaks ~423 distinct sentences across 4 modules. Everything else is the
hidden surface the delta measures.

## Front T4 — built vs shipped: the tables do not travel

Scanned the unified 4 MiB flash (the round-two artifact) and the pierced
LZMA payload for ACPI/SMBIOS table signatures.

**The shipped flash: honest zeros across the board** — `DSDT`, `FACP`,
`RSDT`, `XSDT`, `APIC`, `HPET`, `_SB_`, `RSD PTR `, `_SM_`, `SMBIOS`,
`BGRT`, `WAET`: **0 hits in 4,194,304 bytes**. No ACPI table, no SMBIOS
structure ships in the OVMF image.

**The pierced payload: only generator constants.** Every hit inside the
inflated bytes lands inside a module that BUILDS the thing:

- `DSDT`/`FACP`/`RSDT`/`XSDT`/`RSD PTR ` → inside **AcpiTableDxe**
  (`9622E42C…`) and **QemuFwCfgAcpiPlatform** (`17985E6F…`);
- `_SM_` → inside **SmbiosDxe** (`F9D88642…`) and the Shell's smbios
  command (`7C04A583…`);
- `BGRT` → inside **BootGraphicsResourceTableDxe** (`B8E62775…`).

**The category**: beyond shipped/absent there is **RUNTIME-BUILT** — the
firmware ships generators, not tables. Day-0 consequence: the ASUS image
may differ (vendors often ship AML raw in a raw FFS section); the scan
method transfers unchanged, and a hit must then be classified
*table-shipped* vs *generator-string* by which file contains it.

## Front T5 — the network amputation list (blueprint-grade)

From the versioned census, the modules classified by family — the exact
surface our future firmware will NOT ship. Full lists with GUIDs:
`lab/ovmf-kill-list.json`.

- **network (21 modules)**: the whole stack — SnpDxe, MnpDxe, DpcDxe,
  ArpDxe, Dhcp4Dxe/Dhcp6Dxe, Ip4Dxe/Ip6Dxe, Udp4Dxe/Udp6Dxe,
  Mtftp4Dxe/Mtftp6Dxe, TcpDxe, TlsDxe, HttpDxe/HttpUtilitiesDxe/
  HttpBootDxe, DnsDxe, VlanConfigDxe, UefiPxeBcDxe, IScsiDxe.
- **storage (18)**: SCSI/SATA/NVMe/ATA/Fat/Udf/Partition/DiskIo/RamDisk +
  the Virtio family.
- **usb (6)**, **display (6)** for context.

An entire PXE+HTTP+iSCSI boot capability — 21 modules, an unsigned-code
surface — named, GUIDed, and marked *will not ship*.

## Front T6 — the NVRAM budget, and the price of a boot

The journal walked in round two, now priced. Region: store `0x3FFB8`
inside the `0x84000` FV; `278,528` bytes beyond the store (FTW working +
spare).

| Store | live | deleted | used | free |
|-------|------|---------|------|------|
| `OVMF_VARS_4M.fd` (empty) | 0 (0 B) | 0 (0 B) | 0.00 % | 99.99 % |
| `OVMF_VARS_4M.ms.fd` | 21 (9,167 B) | 18 (3,468 B) | 4.82 % | 95.15 % |
| `OVMF_VARS_4M.snakeoil.fd` | 21 (5,547 B) | 18 (3,468 B) | 3.44 % | 96.53 % |

**Superseded records only** (deleted records of names written again):
`ConOut` 1,217 B, `ConIn` 1,182 B, `ErrOut` 650 B, `CustomMode` 166 B,
`BootOrder` 166 B, `VendorKeysNv` 87 B — **3,468 B of journal rewrite per
this boot history**. That is the vendor's own wear. Ours, by doctrine and
by construction: **0 B — 0.00 % of every number in this table**.

## Front T7 — the AMD lens, armed from public sources

The day-0 board (TWIN-1, B450-PLUS) is AMD; the lab world is not. What the
web added to the read-only checklist:

- **One chip, two consumers** (coreboot PSP documentation): "The PSP
  executes its own firmware and **shares the SPI flash storage** that is
  used by the system BIOS." A write-protect decision on our side is also
  a decision about the PSP's and the chipset's bytes — Volume 5 rules
  must account for both consumers of the same silicon.
- **AMD SPI protection exists and is countable**: coreboot issue #4094
  ("AMD SPI lock check") — "up to four memory ranges specified by Rom
  Protect registers can be protected", mirroring Intel's PR0-PR4. Day-0:
  read the Rom Protect registers at the AMD SPI MMIO window (`0xFED80000`
  family) — existence and ranges only, never a write.
- **SMM lock is an MSR** (IOActive's AMD platform security walk): the SMM
  lock lives in SMM HWCR (MSR `0xC0010111`, SMM_LOCK bit 0) — readable
  from Linux via `/dev/cpu/*/msr` where permitted. AMD's own "SMM Lock
  Bypass" advisory is the reminder that even locked SMM has had bypasses;
  ring -2 honesty applies on AMD too.
- **The strict-NX upstream story**: kraxel's "W^X in UEFI firmware and
  the linux boot chain" + Fedora's Edk2Security change — the NX-clean
  boot-chain effort explains why the policy delta lives in exactly the
  modules T2 found. The lab and the upstream finally point at each other.

## What the third ring changes for day-0 (16/09)

1. **Hash-diff is the only policy-grade census** (T2): capture the dump,
   hash every FFS file, compare against the vendor's previous version —
   same names/GUIDs prove nothing about policy.
2. **Classify hits, not just counts** (T4): ACPI/SMBIOS signatures in the
   ASUS image must be labeled *table-shipped* (inside a raw section/file)
   vs *generator-string* (inside a PE) — the position decides.
3. **The façade delta has a method now** (T3): utf-16 census per setup
   module vs setup screenshots; the numbers transfer.
4. **Amputation lists exist** (T5): `lab/ovmf-kill-list.json` is the
   blueprint's first machine-readable kill-list — with GUIDs.
5. **The wear baseline is priceable** (T6): on day-0, the same budget walk
   on the real store tells us what the vendor's own boots cost before we
   ever touch anything.
6. **The AMD half of the walls is a checklist** (T7): Rom Protect
   registers (×4), SMM lock MSR, PSP/chipset as co-consumers of the chip.

## Honesty ledger (third ring)

- The `0x14`-separated packed utf-16 string container (T3) is described,
  not parsed — upstream check pending, flagged.
- `IScsiDxe`'s two-byte change (`0x66 0x2E → 0x00 0x66`) is located and
  recorded; its semantics are interpretation, and interpretation is
  labelled as such (T2).
- The `_SB_` hit inside RamDiskDxe and the `APIC` hit inside
  `E750224E…` are recorded without a name for the latter (GUID-only in
  the census) — day-0/upstream question, flagged.
- Zero bytes written to any SPI image; every probe ends `bytes written: 0`.
