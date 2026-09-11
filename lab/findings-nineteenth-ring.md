# The nineteenth ring — the anatomy of the vendor line

The board cannot be touched until the 16/09 dump, so this ring
spends what the study already owns: **thirteen specimens, ~200 MiB of
vendor firmware already on disk, zero new acquisitions.** Seven
fronts run the old instruments on the whole corpus for the first
time — PE provenance, raw geometry, trust material, the PSP blob
layer, the SMM armor's anatomy, a real security patch, and the
vendor setup facade. The corpus answers with four dating signals,
one cross-confirmed platform event, and an inverted reading of what
vendor trust material is.

## Front 1 — PE provenance: the factory is cleaner than EDK2, until you meet the fossils

The ring-4 lens (same `pe_sections`, every surface pierced) read all
13 specimens: **5,707 PE modules, every one x86-64** (subsystems:
5,472 boot-service drivers, 233 runtime, 2 applications), **zero PDB
paths**, and exactly **four nonzero timestamps in the entire corpus**
— all four belong to two MSI modules, `GraphicsAlgorithmEx`
(2014-09-18) and `GetFileFromFFS` (2012-11-08), mirrored across both
SPI windows. Two fossil blobs, untouched for a decade, leak the build
dates of a compiler run from the MSI archive of 2012-2014; the ring-17
double-structure pairing is confirmed at PE-header granularity.

The inversion is the finding: OVMF arms a few modules NX_COMPAT
(10/133 plain, 19/142 secboot); **vendor silicon arms zero of 5,707.**
On AMI-Aptio the PE flag is not the enforcement channel — the
ring-4 lesson (policy is PCD-driven, census-invisible) holds for the
whole vendor line.

## Front 2 — the geometry: the dump's anatomy, priced in bytes

Sixty-four-KiB entropy windows over the raw images (the day-0 eye
view): the ten ASUS 16-MiB images keep one skeleton — **~6 MiB of
top-level FV (41-42 % of the image), 56-60 % compressed payload,
18-19 % erased, ~1.05-1.09 MiB top 0xFF slack.** The packed share
creeps up the ladder (55.9 % at 3604 → 60.3 % at 4604) and dips at
4655 — the only geometry-level sign of aging. The NVAR-magic count
grows 18 → 19 at 4631. The 32-MiB MSI double structure reads 63.7 %
FV and **34 % erased** — half-empty by design (ring 17). Day-0's raw
read should look exactly like these; anything else is an anomaly
flag before parsing starts.

## Front 3 — trust material: zero signature lists, and the signing story only ASUS tells

The signature-list lens (ring-9 machinery, type-GUID located across
every pierced surface) returns **zero EFI_SIGNATURE_LIST structures
in all 13 images.** The factory does not ship assembled key stores;
the material lives as **raw Authenticode DER chains**, and only one
vendor tells a story with it:

- **ASUS ships 12 certificates at 3604, 18 from 3810 onward** —
  DigiCert roots, the G4 Code Signing 2021 CA1, timestamping chains,
  and a leaf reading *Private Organization TW 23638777, Beitou Dist.,
  Taipei* — ASUS itself. MSI, Gigabyte and ASRock ship none in-image.
- The cert set **doubles 12 → 18 at 3810 (2022-12)** — the same year
  the armor wave-1 lands — and the timestamp chain walks its own
  calendar: **2021 (3604) → 2022-2 → 2023 (4402/4604) → 2024 (4631)
  → 2025 responder (4655/4645)**. A fourth dating signal, independent
  of AGESA and of the armor.
- The DER chains sit in raw areas outside every walked FFS module —
  container territory, not named modules; attribution is by subject
  string, no signature was cryptographically verified (registered).

## Front 4 — the PSP chronology: 3802 cross-confirmed as a platform event

Ring-13 machinery over the nine dated PRIME rungs, every entry
fingerprinted per blob type (50 types, fletcher-validated dirs): the
churn per transition reads **42/50 types moving at 3604 → 3802, then
7/50 at 3802 → 3810, then 28-43/50 for every later transition.**

The 3802 event is now cross-confirmed from an independent layer: the
same release that introduces the SMM armor also rebuilds the PSP
stack — bootloader, ABL0/ABL6, APCB(+copy), AMD_PUBLIC_KEY,
TOS_SECURITY_POLICY, DRTM_TA all move at once. And the quiet release
is equally clear: **3810 shares AGESA 1.2.0.7 AND a near-frozen PSP
layer** — a maintenance release, confirming the rung rule that 3802
and 3810 must be paired with other lenses to be told apart.

## Front 5 — the armor, opened

The seven armor modules stopped being GUID counts and became bytes:

- **`SbRomArmorSmm` is ONE body across all 8 rungs it inhabits**
  (3802-4655, byte-identical for 4.5 years) — the core guard never
  changed.
- **`PrepareWhiteListSmm` (17.5 KB) carries the literal string
  `AMD rom armor`** plus an SPI flash chip database — ADESTO
  AT25SF641/AT25SL128A, AMIC 25L, ATMEL 26DF/25DF families, ~50
  vendor/chip strings — a chip-aware guard running in SMM, evolved
  in 3 bodies.
- `FlashSmiSmm` (5.7 KB) and `FlashSmiDxe` (9.8 → 11.3 KB) churn in
  2-3 bodies; the completing pair (`4EB43107`, freeform `02076249`)
  appears only at 4604+ (present_at = 3 rungs), consistent with the
  ring-18 7/7 boundary.
- The SMM census moves 106 → 109 at 3802 (+ the armor), then settles
  at 107 as the legacy pair retires (21782819: 1 body, gone at 4402;
  827E45A4: 3 bodies, gone at 4202).

## Front 6 — the CVE patch lens: a security patch is a platform rebuild

The Gigabyte pair **F65 (2026-04) → F67c (2026-08)** — the update
carrying the CVE-2026-6726/6727 fixes — was diffed with the ring-15
machinery (after the sandbox's old "f65 zip" proved a 196-byte 404
page; re-fetched from the official CDN at the listing's canonical
URL, board id `8a16bg04`).

**18.1 % of the GUID set survives; 410 of 503 modules change,
107 of them SMM, plus GbtCrbSmbios added and AmiDeviceGuardApi
removed — in four months.** The patch also rides an AGESA bump
(1.2.0.B → 1.2.0.12), and the ladder lesson sharpens: Gigabyte
shipped 1.2.0.B — an ASUS-2024-01 level — in April 2026. The
ring-15 surgical story (AcpiTableDxe's 9 bytes) is the exception;
**the rule is that a vendor security update is a platform rebuild in
which the fix is not isolable at FFS granularity.** Body-hash churn
includes rebuild noise; the reading is about release philosophy, not
410 semantic fixes.

## Front 7 — the vendor facade, quantified

The ring-6 grammar ported to six vendor-representative specimens —
**100 % of form packages validate by exact consumption.** The
vendor facades carry **6,360-8,646 questions across 732-1,104
pages** (OVMF plain: 146/58): MSI 8,646/1,104 (Setup alone 4,222
questions over 516 pages), ASUS 3604 7,975/779 growing to 8,273 at
4655, ASRock 6,360, Gigabyte 6,388. AMD's CBS modules dominate every
board (CbsSetupDxeZP/RV/SSP per CPU family, 513-1,178 questions).

And the hidden surface inverts again: **SUPPRESS_IF / GRAYOUT_IF /
DISABLE_IF count ~zero across 46,000+ questions** (the corpus holds
exactly one SUPPRESS_IF, on F67c). OVMF hid 64/202 questions behind
conditions; the vendor facade is flat. On these boards, hiding is
variable-level (the unexposed `Setup` fields ring 14 measured), not
question-level — Q1's denominator is now per-vendor and the "hidden
surface" lives in what the facade never asks about.

## Consequences for day-0 (16/09)

- The dump should match the front-2 geometry (FV share, packed
  share, slack); deviations are pre-parse anomalies.
- The armor checklist gains an anatomy row: `SbRomArmorSmm`
  byte-identical since 3802, `PrepareWhiteListSmm` with the chip DB —
  both expected, sizes known.
- The ASUS cert set (18 DERs, timestamp chain) is a fifth
  first-hour fingerprint for the dump, independent of AGESA/armor.
- The facade numbers (7,975 → 8,273 questions on this board) give
  the day-0 IFR census its expected magnitude; 100 % validity
  expected.
- The PSP churn table (42/50 at 3802, ~30/50 typical) sets the
  expected churn magnitude when the dump joins the chain as the
  seventh specimen.

## Honesty ledger

- "Changed" at body-hash granularity includes rebuild noise; both
  delta readings (ring 15 surgical, ring 19 wholesale) are release
  philosophy, not semantics counts.
- The signer attribution reads DER subject strings; no signature
  verification was performed, and the cert-bearing areas are raw
  containers, not named modules.
- Zero signature lists in-image does not prove the other vendors
  sign nothing — it proves their trust material is not shipped as
  assembled lists (or not shipped at all).
- The facade counts are opcode-level, not visible-widget counts; a
  "question" is a question-class opcode.
- Entropy classes are 64 KiB-window heuristics; windows mix
  categories.
- F65's release date (2026-04) comes from the vendor page's date
  column as recorded at acquisition time, not from the image.
- MSI/Gigabyte/ASRock cert-zeros rest on one specimen per vendor.

## Registers

- `vendor-pe-trust.json` — fronts 1 + 3: PE provenance, the MSI
  fossils, the NX inversion, the DER trust material and its ASUS
  chronology.
- `vendor-geometry.json` — front 2: the entropy atlas, the priced
  dump anatomy.
- `vendor-lifecycles.json` — fronts 4 + 5 + 6: the PSP churn table,
  the armor anatomy, the CVE patch lens.
- `vendor-ifr-census.json` — front 7: the vendor facade in
  questions, per module.
- Scratch: `ring19/ring19-{pe-provenance,entropy-atlas,secureboot-
  posture,der-certs,psp-chronology,smm-anatomy,patch-lens,ifr-census}.json`.
