# The sixth ring — the IFR grammar, spec-fresh (2026-09-11)

> Companion to `ovmf-findings.md` (the first OVMF reading), `findings-first-ring.md`
> (first ring) through `findings-fifth-ring.md` (fifth ring).
> One campaign, born from the repo audit itself: ring 5's locked question
> ("the opcode layer") dissolved the moment the grammar was re-derived from
> the EDK2 spec headers instead of memory. Read-only, zero bytes written,
> surface freeze untouched. Instruments: `ring6_ifr_probe.py` (sandbox),
> artifact `ovmf-ifr-census.json` (this repo).

## Front S1 — why ring 5 locked: two wrongs, both now named

Ring 5 hunted IFR opcodes inside **string** packages and matched `{len,op}`
and `{op,len}` pairs against real bodies — both failed, and the question was
flagged locked. The spec-fresh read (EDK2 `UefiInternalFormRepresentation.h`,
pulled from tianocore/edk2 master, opcode values parsed from the header file —
zero memory-encoded constants in the probe) names both mistakes:

1. **Wrong package type.** The spec says `EFI_HII_PACKAGE_FORMS = 0x02` and
   `EFI_HII_PACKAGE_STRINGS = 0x04`. Ring 5 walked the 0x04 carriers
   (http/tftp/VariablePolicy/LinuxInitrd strings, "en-US" at body+42) and
   called the type table "refuted by the bytes". The bytes were right — but
   they were **strings** packages, as the spec says. The honest ledger gets a
   self-correction: ring 5's refutation was itself the error. The 0x06
   package in LogoDxe is `EFI_HII_PACKAGE_IMAGES` per spec (the logo) — ring
   5's reading stands, now with the right name. And **BdsDxe carries zero
   forms**: its 95 strings (ring 3) are data consumed by UiApp's forms —
   which is why no opcode stream was ever found in it.
2. **Wrong grammar.** `EFI_IFR_OP_HEADER { OpCode:8; Length:7; Scope:1 }` —
   the top bit of the second byte is the **scope flag**, not length. Any
   naive 2-byte match on scoped opcodes was doomed. The probe walks
   `{op, len = b1 & 0x7F}` and treats `b1 == 0x7F` as the extended-header
   candidate (4-byte header, u16 length) — recorded, though **no real
   package needed it** on these builds (0 extended headers in 21 packages).

## Front S2 — the validation that cannot lie: exact consumption

The strongest possible proof replaces the anchor hunt: **an opcode walk is
accepted only if it consumes its forms-package body EXACTLY** (residual 0).
A random dword in `.rdata` has ~zero chance of a full IFR stream closing on
the boundary. Result: **21/21 form packages across three builds close
exactly** (18 plain, 21 secboot, 21 snakeoil — secboot and snakeoil
byte-identical, again, at the IFR level this time).

Secondary result, honestly flagged: the **package-list headers of the IFR
carriers still do not close** under the spec walk (GUID + total, packages
4-byte-aligned relative to the list start, END 0xDF last) — the same five
small carriers validate (ring 5's strings porteurs), the big ones (UiApp,
SecureBootConfigDxe, Tcg2ConfigDxe…) still refuse the anchor even with
alignment padding accounted for. The census no longer needs the list
closure; the question stays open, registered, not guessed.

## Front S3 — the facade, counted in questions (not sentences)

Ring 3 priced the facade at ~423 strings. Those were sentences. The real
interactive price — the questions the setup actually asks — is now counted
per module (form packages, pages = FORM opcodes, questions = ops whose spec
struct embeds `EFI_IFR_QUESTION_HEADER`, options = ONE_OF_OPTION):

| Module | pkgs | bytes | pages | questions | options |
|---|---:|---:|---:|---:|---:|
| SecureBootConfigDxe (secboot builds) | 3 | 2 704 | 21 | 62 | 9 |
| UiApp | 5 | 2 464 | 29 | 33 | 0 |
| IScsiDxe | 1 | 1 336 | 5 | 36 | 10 |
| Tcg2ConfigDxe | 1 | 1 070 | 1 | 19 | 17 |
| TlsAuthConfigDxe | 2 | 703 | 8 | 14 | 0 |
| RamDiskDxe | 2 | 568 | 5 | 13 | 2 |
| Ip6Dxe | 1 | 606 | 3 | 11 | 2 |
| Ip4Dxe | 1 | 312 | 1 | 7 | 0 |
| VlanConfigDxe | 1 | 265 | 2 | 5 | 0 |
| HttpBootDxe | 1 | 184 | 1 | 3 | 2 |
| PlatformDxe | 1 | 174 | 1 | 3 | 0 |
| DriverHealthManagerDxe | 2 | 260 | 2 | 2 | 0 |
| **plain build total** | 18 | 7 942 | 58 | **146** | 33 |
| **secboot build total** | 21 | 10 646 | 79 | **208** | 42 |

Readings that matter:

- **The whole OVMF facade is ~2.6 KB of IFR per question family** — the
  12 modules together carry ~10 KB of forms. The "monstrous" BIOS setup is,
  structurally, a folder of tiny scripts.
- **SecureBootConfigDxe is the single biggest form carrier** (62 questions,
  2 704 bytes, 21 pages) — and it exists ONLY in the secboot builds. Combined
  with ring 5 (`secboot == ms == snakeoil` byte-identical, enrollment is
  NVRAM data), the sixth ring adds the last brick: **the entire Secure Boot
  UI is 62 questions; the trust itself is zero code**. Amputating Secure
  Boot costs 62 questions of facade, not one byte of trust.
- **UiApp's 33 questions in 29 pages** — the browser is wide, not deep:
  mostly REF navigation over sub-forms; the questions concentrate in the
  network stack (IScsiDxe 36 + Tcg2ConfigDxe 19 + Ip6/Ip4/Vlan 23).
- Cross-build: secboot − plain = SecureBootConfigDxe (+3 pkgs, +21 pages,
  +62 questions, +9 options), every other module identical — the ring-5
  delta shape, confirmed at the finest grain yet.

## Day-0 consequences

- The probe is **vendor-ready as-is**: pierce → FFS walk → PE32 → forms
  packages → exact-consumption walk. On the ASUS dump (16/09), the same run
  counts the vendor's setup questions per module — the number OVMF says is
  146 (plain) now gets its vendor counterpart. The "count the buttons of the
  ASUS setup" backlog item has its instrument.
- String counts (ring 3) + question counts (ring 6) together give the full
  facade price: sentences + questions per module, comparable vendor vs OVMF.
- Question-class op set was derived from the spec header (18 structs
  embedding `EFI_IFR_QUESTION_HEADER` → 10 distinct opcodes: ONE_OF 0x05,
  CHECKBOX 0x06, NUMERIC 0x07, PASSWORD 0x08, ACTION 0x0C, REF 0x0F,
  DATE 0x1A, TIME 0x1B, STRING 0x1C, ORDERED_LIST 0x23). REF-heavy formsets
  (UiApp) inflate "questions" — day-0 reporting should also print the
  per-op histogram (it is in the artifact).

## Honesty ledger

- The list-header closure of IFR carriers remains locked (S2). The census
  does not depend on it. No interpretation offered; bytes registered.
- No extended (0x7F) headers appeared in any real package — the 4-byte
  header path is untested against reality, flagged as such.
- Options counted = ONE_OF_OPTION only; ORDERED_LIST option buffers not
  expanded (registered, not hidden).
- UiApp may carry more formsets than the 5 found if some live outside the
  walked FFS file types (0x07/0x08/0x09) — the walk covered all DXE/SMM/app
  files; PEI modules never carry HII. Residual risk: negligible, flagged.
- The "0x14 separator" of ring 3 is now explainable as the SIBT block
  grammar inside STRINGS packages (ring 5's 0x04 carriers) — the two rings'
  observations close on each other; full SIBT decoding remains open.
