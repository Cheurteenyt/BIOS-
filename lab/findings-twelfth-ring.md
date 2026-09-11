# The twelfth ring — the quorum (2026-09-11)

> Companion to rings one through eleven. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `ring12_unwrap.py`,
> `ring12_quorum.py`, `ring12_diag_asus.py`, `ring12_artifact.py`
> (sandbox; the ring-11 probes imported verbatim — no grammar was
> rewritten). Artifacts: `vendor-acquisition.json`,
> `vendor-quorum.json` (this repo). The directive: find a way past the
> blocked files, make sure every specimen is the latest official
> version, keep investigating in parallel.

## Front A — the blocked files find their way

- **ASRock is in.** Ring 11 recorded `download.asrock.com` answering
  403 to everything. The way through was not a different door but a
  different front door manner: the same URL answers **200** to a full
  browser header set (Chrome UA + Accept + Accept-Language + Referer)
  where the ring-11 attempt used a bare user agent. The Incapsula WAF
  gates on header-set completeness, not on the URL. Delivered:
  11,493,759 bytes — matching the official listing's 10.96 MB —
  containing one raw 16 MiB ROM (`B45STL_10.41`,
  sha256_16 `d94afae9eecd64ca`).
- **ASUS is in.** The hand-built `dlcdnets` paths of ring 11 answered
  404 (240-byte stubs). The way through: the vendor's **official
  GetPDBIOS API** answers 200 from this network and returns the
  canonical per-release CDN URL — including a `?model=` query
  parameter no hand-built path carried. Both targets landed: the
  latest official **4655** (2026-08-27) and the **3604** (2022-03-16)
  reference.
- The lesson is now a method: **when a vendor file is blocked, the
  block is a shape, not a wall** — header-set completeness (ASRock),
  canonical naming (ASUS), or the CDN-behind-the-page route (MSI,
  Gigabyte, ring 11). Each defeat is registered with its shape.

## Front B — the latest-official ledger, and the 3644 question

Every specimen is now pinned as the vendor's head of line, verified
the same day from the vendor's own channel:

- **ASUS PRIME B450-PLUS**: the API ledger holds **39 entries**,
  0318 (2018-06-22) through **4655 (2026-08-27)** — released fifteen
  days before this ring. No 3644 in it. The series jumps 3604
  (2022-03-16) to 3802 (2022-05-12); the TUF B450-PLUS GAMING ledger
  shows no 3644 either (latest 4645, 2026-02-02).
- **The ring-11 acquisition entry was wrong and is corrected** (in
  `vendor-specimens.json`, visibly, not silently): it claimed
  "3644, AGESA 1.2.0.12, Aug 2026" — date and AGESA actually match
  the **Gigabyte F67c** release (2026-08-18, ComboV2 1.2.0.12):
  cross-contamination in the study notes. Three hypotheses stand:
  a misread of 3604 (most economical), a different board than
  recorded, or a non-stock BIOS. **The 16/09 dump decides** — the
  ROM's own strings name what is truly on the chip.
- **MSI**: 7C02v3G1 (Beta, 2023-03-09) confirmed as the head of the
  v1 list — the cliff is real. The successor **B450 TOMAHAWK MAX II**
  continues (7C02vHG5, 2026-08-21): registered, deliberately not
  acquired, so the quorum matrix stays one board per vendor.
- **Gigabyte**: F67c confirmed (checksum AAC6 on the official page).
- **ASRock**: 10.41 Beta confirmed — with the vendor's own warning
  ("ASRock do NOT recommend updating this BIOS") attached in the
  ledger; pinned and acquired anyway as the honest head of the line.

## Front C — the CAP wrapper, measured

The ASUS `.CAP` is a **2,048-byte wrapper before the 16 MiB ROM**
(16,779,264 = 2,048 + 16,777,216). Measured, not assumed: the first
nesting-rule-valid FV sits at 0x40800 in the CAP and 0x40000 in the
sliced ROM — the delta equals the wrapper exactly, for both 4655 and
3604. The wrapper head carries no ASCII signature. Day-0 consequence:
the SPI dump is compared against the **sliced** ROM, never against
the CAP.

## Front D — the quorum

First contact with the two new specimens through the ring-11
instruments, imported verbatim:

- **ASRock 10.41 Beta**: 3 top-level FVs (main 0x94f000 — the same
  offset class as Gigabyte's main), **633 modules, 382 named
  (60.3 %)**, DEPEX **253/253** postfix-parsed, zero failures.
- **ASUS 4655**: 4 top-level FVs (main 0x9c0000), **600 modules, 1
  named in the main region**, DEPEX **286/286**, zero failures.
- **The packaging lens**: the ASUS DXE layer (a 545-file inner FV)
  carries **384 VERSION sections (0x14) and ONE USER_INTERFACE
  section (0x15)**. ASUS replaces the nameplate with version
  sections — the OVMF-derived lens goes structurally blind there.
  Registered, not forced; the VERSION-section strings are the
  candidate next lens.
- **The quorum matrix** (module-GUID identity, densest region per
  board): the three living lines cluster — ASRock|Gigabyte 0.775,
  ASRock|ASUS 0.758, ASUS|Gigabyte 0.704 — while MSI, the frozen
  2023 cliff, is the outlier (0.535–0.576 against all three). Each
  board shares **41–43 GUIDs with the OVMF reference set**
  (jaccard ~0.08): the EDK2 common core survives every packaging.
- The dispatch hubs repeat across silicon: PcdProtocol (13A3F0F6)
  fan-in 245 (ASRock) and 278 (ASUS) — vendor fan-in runs four to
  five times OVMF's 56, as ring 11 measured on MSI/Gigabyte.

## The self-correction chain

Four bites, all caught before any number was published: (1) Python's
`Path.stem` ate `B45STL_10.41`'s `.41` as a suffix — the extracted
ROM was renamed and the unwrap script fixed; (2) the unwrap assumed a
valid FV within 64 KiB of the wrapper — the first real FV lives at
0x40000, so the proof switched to the whole-blob delta method; (3)
the OVMF reference extractor read the wrong key (`phase` where the
OVMF census uses `type`) — its first run produced a false "0 shared"
row against every board, caught because 13A3F0F6 (PcdProtocol) is an
OVMF-named GUID that demonstrably recurs in vendor DEPEX hubs;
(4) the corrected matrix reproduces ring 11's MSI|Gigabyte 0.549
exactly — the lens cross-validates against its own past.

## Honesty ledger

- One run per new specimen, not rehearsed (OVMF's ring-10
  reproducibility ritual not yet applied to vendor pipelines).
- AGESA claims are unverified for ASRock (1.2.0.E) and ASUS 4655 —
  literal AGESA hits exist, no full version string in bytes. MSI
  1.2.0.8 remains the only byte-verified AGESA.
- GUID identity is identity, not semantics; the OVMF reference set
  (153 GUIDs from 2 builds) is a different scale, so vendor-OVMF
  jaccard rows are not comparable to vendor-vendor rows.
- The quorum lens is the densest region per board — a definition,
  applied identically to all rows.

## Consequences for day-0 (16/09)

- The 3604 and 4655 ROMs are unwrapped and waiting as comparison
  targets; the CAP-slicing rule is fixed.
- The 3644 question resolves from the dump's own strings.
- If the dump is ASUS-class packaging, expect the nameplate lens to
  come back near-empty and the VERSION-section strings to become the
  name source — the lens knows its own blindness now.
