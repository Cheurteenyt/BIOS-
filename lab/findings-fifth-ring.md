# The Fifth Ring — three new fronts, zero bytes written (2026-09-11)

> Companion to `findings-2026-09-11.md` (first ring), `findings-second-ring.md`
> (second), `findings-third-ring.md` (third) and `findings-fourth-ring.md`
> (fourth). The fourth ring mapped the gates, the provenance, the texture,
> the supervisor and the keep-set. The fifth ring answers three questions
> the earlier rings left standing: **is enrollment code or data?**, **can
> the facade's interactive grammar be counted?**, and **does OVMF flash
> carry an ACPI ecosystem?** One probe, one run, read-only throughout;
> the artifacts land here.
>
> Probes: `ring5_probe.py` (+ autopsies `ring5_v2_diag{,3,4,5}.py`, kept as
> history). Artifacts: `lab/ovmf-ms-delta.json`,
> `lab/ovmf-ifr-grammar.json`, `lab/ovmf-acpi-footprint.json`.

## Front W1 — enrollment is data, not code

Five Debian builds now exist in the sandbox; the fourth ring had censused
three. The fifth adds `OVMF_CODE_4M.ms.fd` (Microsoft-key enrollment) and
`OVMF_CODE_4M.snakeoil.fd`, hashes every module body, and diffs:

| build | outer sha16 | inner sha16 | outer / inner bytes |
|---|---|---|---|
| plain | `624e06de18b4fa53` | `6d342d0ebd917943` | 3,653,632 / 16,122,000 |
| secboot | `1a46295574430cfb` | `29b041f904f0ed6f` | 3,653,632 / 16,122,000 |
| strictnx | `9ee9f2382e0c6aa9` | `e41322781ff0caf6` | 3,653,632 / 16,122,000 |
| **ms** | **`1a46295574430cfb`** | **`29b041f904f0ed6f`** | 3,653,632 / 16,122,000 |
| **snakeoil** | **`1a46295574430cfb`** | **`29b041f904f0ed6f`** | 3,653,632 / 16,122,000 |

- **`secboot`, `ms` and `snakeoil` are the same image, byte for byte** —
  same outer hash, same pierced payload, **144/144 modules
  byte-identical** (`+0 −0 ~0 =144`).
- `plain ↔ snakeoil` re-derives the fourth ring's named delta through a
  third build, exactly: **18 added** (the 12-module SMM family,
  `SecureBootConfigDxe`, `CpuS3DataDxe`, three unnamed PEIMs), **9
  removed** (the Shell `7C04A583…`, `VariableRuntimeDxe`,
  `FvbServicesRuntimeDxe`, `FaultTolerantWriteDxe`,
  `EmuVariableFvbRuntimeDxe`, the four dynamic shell commands), **120 of
  126 shared bodies rebuilt**, 6 byte-identical. The fourth ring's
  numbers were not an artifact of one pairing; they are the *shape* of
  this edk2 build family.

**The headline: "Secure Boot enabled", "Microsoft keys", "test keys" are
not firmware variants. They are NVRAM variants.** The trust anchors ring 2
walked (`PK` = Debian, `KEK` = Debian + Microsoft Third-Party Marketplace
Root, `db` = Microsoft Root CA 2010 + 3P Marketplace Root, `dbx` = the
canonical empty-buffer SHA-256 `e3b0c442…`) live entirely in the variable
journal; the code that enforces them is one and the same binary. Secure
Boot on this platform treats trust as configuration.

Day-0 translation, three ways:

1. Reading the ASUS keyring is a **variable-space read** (efivarfs or the
   NVRAM walk), never a flash write — it slots straight into the +0-octet
   doctrine.
2. A vendor image with "Windows-signed" vs "custom" enrollment will
   differ in its **journal**, not in its DXE bodies — the diff tool must
   be a variable walker, not a binary differ, when the question is trust.
3. The agent layer can *describe* the keyring and the firmware layer can
   *fence* variable writes without touching a single flash byte: the
   boundary the project wants already exists inside the platform.

## Front W2 — the facade's package layer, and the locked opcode layer

Ring 3 counted the facade's sentences (~423, SIBT 0x14 container) but
never its **interactive grammar**. The fifth ring hunted HII package
lists inside every module's PE image with a self-validating walk: a
candidate is a list only if `u32@+16` equals its total length and the
package chain terminates **exactly** — no external anchor, the walk is
the proof.

**What the walk proves (byte-level):**

- Package lists live **inside PE images**, anchored as
  `PackageListGuid(16) + PackageLength(u32, header included)`.
- The list closes with an **END package, type byte 0xDF, 4-byte empty
  header** — read verbatim as `04 00 00 df` in every validated list.
  Byte-proven.
- Plain carries **five** validated carriers: `LogoDxe` (one list, 12,009
  B — a single 11,981-B type-0x06 package, the logo image) plus the four
  shell dynamic commands (`http`, `tftp`, `VariablePolicy`,
  `LinuxInitrd`; type-0x04 packages of 2,679–8,648 B whose bodies open
  with a 52-byte header, `LanguageName` 0x0001, the literal `en-US\0` at
  body+42, then 0x14-marked UCS-2 blocks — the ring-3 grammar, now seen
  inside a package frame).
- Secboot keeps exactly one true carrier — **`LogoDxe`** — matching the
  fourth ring's `.rsrc` survivor; the shell commands' lists vanish with
  the amputation.

**What the bytes refute:**

- The remembered HII package-type table. Empirically the string-bearing
  packages carry type **0x04** (memory said 0x02) and the logo image
  carries **0x06** (memory said 0x05). Only the END byte (0xDF) survived
  contact with the flash. House lesson re-earned: *memory constants
  lose, bytes win — always.*

**What stays locked (flagged, with bytes recorded):**

- The IFR opcode header. Neither `{Length,Op}` nor `{Op,Length}` validates
  on any real package body; both die mid-stream. The knob count — the
  number of checkboxes, one-ofs and numerics behind the facade — therefore
  stays an open question this ring.
- `UiApp` and `SecureBootConfigDxe` lists never validate at all: a grammar
  element is still missing (padding? package types outside the memory
  table? a sub-header?). Their modules are recorded; their grammar is not.
- The relaxed scan admits a **false-positive cluster**: byte-identical
  1,116/1,117/1,118-B chains of type-0x00 "packages" inside `TlsDxe`,
  `SecurityStubDxe`, `SecureBootConfigDxe` and `VariableSmm` — a shared
  embedded blob (cert-sized) misread as HII. Flagged, unresolved.

Day-0: the **anchor method transfers as-is** to the ASUS image — every
HII list can be located without knowing the grammar. Counting the vendor's
setup knobs needs a spec-fresh grammar pass first; the fifth ring's
autopsy files are the groundwork.

## Front W3 — the ACPI/SMBIOS footprint: templates, not tables

The scanner checks every ACPI signature hit **structurally** (36 ≤ table
length ≤ remaining bytes) and validates every `RSD PTR ` candidate against
its own 20-byte checksum. Run over raw and pierced bytes of all five
builds:

- **Raw (outer) images: zero hits of anything.** The compressed wall hides
  the entire ACPI story.
- Pierced: the only structurally sane candidates in the whole flash are
  **one SSDT (124 B)** and **one BGRT (56 B — exactly the spec size of a
  Boot Graphics Resource Table)**. Everything else is 4-byte ASCII
  collisions with absurd length fields (a "DSDT" of 9,733,135 B, an
  "APIC" of 12,682,511 B) — recorded as false positives.
- The single `RSD PTR ` string found **fails its own checksum** in both
  builds — it is not an RSD PTR.

The carrier lookup turns these near-zero results into the front's real
finding:

| candidate | carrier module | reading |
|---|---|---|
| BGRT, 56 B, spec-sized | **`BootGraphicsResourceTableDxe`** | a real static BGRT template — the module is named after it |
| `RSD PTR ` (checksum fails) + DSDT collisions | **`AcpiTableDxe`** | the runtime builder embeds the signature as a template constant |
| `_SM_` anchor | **`SmbiosDxe`** | same pattern: the anchor string of a runtime-built table |
| SSDT candidate, 124 B | `RamDiskDxe` | flagged candidate; carrier named, semantics unproven |

**OVMF flash ships no finished ACPI ecosystem — it ships the templates
inside the modules that build the tables at runtime** (from QEMU fw_cfg,
or from those templates when fw_cfg is silent). The platform's ACPI is
*code*, not *data*.

Day-0: the same scan on the ASUS dump will be the opposite pole — finished
vendor DSDT/SSDT AML blobs, and the licensing/security tables that are
pure vendor surface: `SLIC`/`MSDM` (Windows licensing), `WPBT` (a
vendor-supplied *executable* the OS may run), `BGRT`, `TPM2`, `WSMT`.
The checksum-validated scanner is the first-pass filter that separates
"template constants inside builder modules" (OVMF-style) from "finished
AML data" (vendor-style) — and that separation is itself a finding about
how the vendor builds.

## The honesty register, after five rings

Closed this ring: **enrollment is data** (byte-proven across three
enrollment variants); the package-list anchor (exact-termination walk);
the END package byte (0xDF); the OVMF ACPI question (templates in builder
modules, no finished tables); the plain↔snakeoil delta shape (third
confirmation of the fourth ring's numbers).

Refuted this ring: the remembered HII package-type table (strings carry
0x04, images 0x06 — bytes recorded; the table in any future probe must be
re-derived from flash, not from memory).

Still flagged, with evidence: the IFR opcode grammar (both plausible
header layouts fail on real bodies; bytes in `lab/ovmf-ifr-grammar.json`);
the `UiApp`/`SecureBootConfigDxe` list validation; the type-0x00 shared
blob (1,116/1,117/1,118 B across `TlsDxe`, `SecurityStubDxe`,
`SecureBootConfigDxe`, `VariableSmm`); the `RamDiskDxe` SSDT candidate;
carried over: Boot0001's 17-byte optional tail, the in-SMM depex anchors
(`C2702B74…`, `F4CCBFB7…`, `4E939DE9…`, `F8775D50…`, `843DC720…`,
`D326D041…`), the LoadFile2 role of `PciBusDxe`.

## Day-0 consequences (16/09)

| Instrument (offline, from the dump) | Feeds |
|---|---|
| enrollment-is-data proof | keyring questions become variable-space reads; flash stays +0 |
| package-list anchor walk | facade inventory on the vendor image, grammar-free |
| checksum-validated ACPI scanner | the vendor ACPI island map; SLIC/MSDM/WPBT hunt; template-vs-finished classification |
| third-confirmed build-delta shape | vendor image diffs must body-hash, not name-count |
| ring-2 NVRAM walk + ring-5 data/code split | the full trust story: journal for anchors, DXE for enforcement |

## Frozen-surface note

No tool added, removed or reshaped: the 15-tool surface and the 12-check
MCP smoke are untouched; the repo gains three JSON artifacts and this
document only. The probe and its autopsies live in the sandbox
(`/home/z/my-project/scripts/`), never in `tools/`. Every number above
came from one probe run over images already in the sandbox; zero bytes
were written to any firmware file, and the 16/09 machine remains a
target, not a workbench.
