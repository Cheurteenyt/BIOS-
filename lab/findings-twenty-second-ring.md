# The twenty-second ring — the eighth clock, the collapsed census, and the frozen whitelist

*Date: 2026-09-12. Constraint unchanged: the board stays untouched; every
probe is read-only, offline, on restored binaries. Three fronts, one probe
each, gates before readings.*

Ring 21 left three measurement gaps registered: the AML atlas hashed only
the largest DSDT body (the SSDTs were counted, never tracked); the trust
material was only *counted* (12 → 18 "certs" at 3810); and the armor's
chip database was a one-line curiosity. Ring 22 takes all three — and the
corpus had to be restored first, again.

## The restoration, again

The sandbox reset wiped the binaries a third time. All 13 specimens were
re-pulled from the same official vendor CDN URLs and gated on the
registers: every zip matched its `zip_sha256` anchor byte-exact (13/13),
every ROM matched its corrected sha256 (12/12 gated + TUF 4645 on its
vendor-certified zip anchor). **Zero new acquisitions** — the corpus is
the registered corpus, re-verified. The restore ledger lives in
`scratch-vendor/restore-ledger-ring22.json` (outside the repo, by the
same convention as ring 20). One repair note: ring 21's restoration
registered `corrected_rom_sha256` values under
`ring21_rom_hash_correction`; this ring's ROM gate verified against those
— 12/12 PASS — closing the loop on the dead-metadata correction.

## Front A — the SSDT clock (the eighth clock)

Method: every checksum-admitted `DSDT`/`SSDT` body across all planes
(raw ROM + pierced LZMA payloads) of all 13 specimens, deduped by body
sha256, containers classified `RAW-SEC` (opens a PI raw section),
`PLANE-START`, or `EMBEDDED`. Admission is ring 21's discriminator
verbatim: signature + declared length in [36, 4 MiB) + `sum(body) & 0xFF
== 0`.

Gate: the main-DSDT atlas reproduces ring 21's `dsdt_clock` exactly —
9/9 rungs PASS (`27d5e826`/47,184 → `f23c571b`/45,043 →
`0a4a6f16`/45,069). Reconciliation: the `RAW-SEC` class per rung is
exactly ring 21's census (4 DSDT variants + 23 SSDTs on ASUS = 27); the
wider net adds 8 `EMBEDDED` bodies — the AMD layer below.

Findings:

1. **The SSDT set is an independent clock with its own frontier.** Three
   SSDT-set generations move at **3604 → 3802** and **3810 → 4003** —
   disjoint from the DSDT's frontiers (4202 → 4402, 4604 → 4631). The
   two AML clocks never move together; the quiet pair 3802|3810 stays
   quiet under both (the sixth independent agreement).
2. **The armor release swapped one AML table**: at 3604 → 3802 exactly
   one SSDT changes — `AOD` (AMD OverDrive) revision 15 → 153. The SMM
   armor release was a platform event down to the AML interface.
3. **The AGESA 1.2.0.8 release rewrote the CPM layer**: 3810 → 4003
   replaces 15 SSDT bodies wholesale — `CPMCMN`, five `CPMDATPX`
   variants, `CPMDF*`, `CPMI2C`, `GPIOAZAL`, plus `AOD` revision 132.
   A generation change, not a patch.
4. **The AMD ALIB layer is common property.** 8 `EMBEDDED` `ALIB`
   bodies per ASUS rung (OEMID `AMD`, TableID `ALIB`, creator `MSFT`);
   74 distinct ALIB bodies corpus-wide; **6 of them are byte-identical
   across all 13 boards**. This refines ring 21's "no table body is
   byte-identical across all twelve boards": true for vendor-compiled
   AML, false at the AMD-shipped layer — vendors ship their own AML but
   all ship AMD's.
5. Cross-vendor AML sharing (deduped vs the ASUS union): TUF 31/35,
   MSI 28/35, ASRock 17/24, **Gigabyte 6/35** — Gigabyte's AML layer is
   the most divergent in the corpus.

## Front B — the DER inventory (the collapsed census)

Method: every parseable X.509 DER certificate in every plane, deduped
by body sha256. Containers classified exactly: `AUTHENTICODE` (the
certificate body appears inside a `WIN_CERTIFICATE`-wrapped PKCS#7
SignedData blob — the PE signature shape), `STANDALONE` (raw trust
material), or `BOTH`.

Gate: ring 19/20 counted certs by a **raw-plane scan** (the fused
clock's own "needs: raw scan, no pierce"). Re-running that census:
**sightings reproduce the register exactly** — 12/12/18/18/18/18/18/18/18
(9/9 PASS), and the cross-vendor zero holds (MSI/Gigabyte/ASRock: 0 raw
trust sightings, 3/3 PASS).

The collapse: those sighting counts are **store copies, not distinct
certificates**. The raw-plane trust material is:

- **4 distinct certs at 3604-3802** (×3 store copies = 12 sightings):
  the ASUS leaf (`CN=ASUSTeK COMPUTER INC.`, Private Organization TW
  23638777), its issuing CA (DigiCert Trusted G4 Code Signing 2021),
  and the 2021 DigiCert timestamp pair;
- **6 distinct certs at 3810-4655** (×3 = 18): two additions — the
  `DigiCert Trusted Root G4` cross-certificate and a re-issued
  timestamp cert.

So ring 19's "12 → 18 certs at 3810" collapses to **4 → 6 distinct
certificates**. And the deeper finding: **the count never changes again,
but the bodies keep rotating** — the timestamp chain re-issues at five
ladder frontiers (2021 → 2022-2 → 2023 → 2024 → 2025 responder), and the
ASUS leaf renews at 4631 (notBefore 2024-05-27, valid to 2027-05-30).
The trust *set* is a better clock than the trust *count*: it moves at
3802, 3810, 4402, 4631, 4655 — more frontiers than any other clock. The
identity of what never moves is equally measured: no PK/KEK material
rotates — the platform keys are static from 3604 through 4655.

Other readings:

- **PRIME 4655 vs TUF 4645: identical 6-cert trust sets** — the second
  ASUS line ships the same factory signing chain.
- The `BOTH`/`AUTHENTICODE` class: 1-3 module-signature certs per board
  (Microsoft UEFI Driver Publisher chains, timestamp responders).
- **Negative serial numbers on vendor-generated certificates** —
  `ASUSTeK MotherBoard SW Key`, `ASUSTeK Notebook SW Key`,
  `MSI SHIP PK`, `GIGABYTE` — an RFC 5280 violation shipped by three
  of the four vendors, registered not graded.
- MSI's NVRAM region carries a pierced-standalone db population
  (Microsoft/Canonical/Debian certs + `MSI SHIP PK`) that no other
  vendor ships outside the compressed region — knowledge-only.

## Front C — the armor's chip database (the whitelist that never learns)

Method: the literal `AMD rom armor` banner (ring 19) anchors
`PrepareWhiteListSmm`; immediately after it a NUL-separated chip-name
table (`SST 25LF040`, `SST 25LF080`, `ATMEL 26DF041/25DF041`, …).
Tokens filtered to chip-like names (printable, ≥1 digit, no printf/GUID
noise — `X-UEFI-AMI`, `%08x-%04x-…`, `en-US` all excluded by
construction), region ends at a 16-NUL run. Cross-check anchor: the
table is additionally located by its first entry, which is how the
non-ASUS builds were read (their armor separates banner from table).

Findings:

1. **3604 carries a 41-chip predecessor table** — the whitelist belongs
   to the AMI flash-update driver and *predates the armor*. The 3604
   specimen has zero armor banners (consistent with ring 18's 0/7) but
   the chip table exists.
2. **The 3802 armor release expanded the whitelist 41 → 46** (+5:
   `Cypress 25FS-S Series`, `Fudan FM25W Series`, `MXIC 77L Series`,
   `XMC 25RH Series`, `XMC 25RU Series` — including two XMC families,
   the SMIC-affiliated flash vendor).
3. **The whitelist is frozen from 3802 through 4655** — 4.5 years,
   nine rungs, zero set changes.
4. **The 46-family set is identical across all five vendors** (ASUS 9
   rungs + TUF + MSI + Gigabyte + ASRock) — the flash armor's chip
   knowledge is AMI-generic infrastructure, cross-confirming ring 20's
   SMM-quorum reading at the data level.
5. Honesty: the whitelist is a *name* census; the armor's per-chip
   command tables (JEDEC IDs, erase/program opcodes) are binary
   structures this probe did not parse. "Never learns" is measured at
   family granularity. Knowledge-only: what a frozen whitelist implies
   about *new* flash chips (post-2022 parts) is an inference, not a
   measurement.

## Consequences for the day-0 checklist

- The decision tree gains the SSDT set as a raw-read corroboration
  clock (after the pierce): the dumped board's 35-body AML atlas must
  land in the registered generations — DSDT main body in
  {`27d5e826`, `f23c571b`, `0a4a6f16`} per the version, SSDT set in the
  three-set atlas, 6 ALIB bodies byte-identical everywhere.
- The trust row sharpens: expect **18 sightings / 6 distinct certs** in
  the raw plane, timestamp chain = the 2025 responder set if the board
  is 4655-era; the leaf validity window (2024-05-27 → 2027-05-30) is
  itself a dating signal readable with any DER tool.
- The armor row gains the chip-table hash: the dumped board's whitelist
  must equal the 46-family set byte-for-byte — a deviation would be a
  corpus first.

## The honesty register

- The SSDT admission is a probabilistic discriminator (checksum) on a
  wide net; the `EMBEDDED` class has no section-boundary proof. The
  ring-21 `RAW-SEC` reconciliation is the guard: the strict class
  reproduces the register exactly.
- Cert roles are container-derived, not intent-derived: a certificate
  shipped raw *could* be something other than trust material; the
  class names describe containers, not purposes.
- The chip-table parser is heuristic (16-NUL stop, chip-like filter);
  both heuristics are registered, and the cross-vendor identity
  (46/46/46/46/46) is the internal consistency check.
- The corpus remains the registered 13 specimens; the restoration
  verified against ring 21's corrected anchors — no anchor was
  re-corrupted by this ring (the ROM gate is the proof).
- psptool was not used this ring; every reading comes from stdlib
  parsing + `cryptography` X.509/PKCS#7 loaders on pierced planes.

## Registers

- `vendor-ssdt-clock.json` — front A: the full AML atlas (13
  specimens), the SSDT movement table with identified movers, the
  generation map, the ALIB layer, cross-vendor sharing.
- `vendor-der-inventory.json` — front B: the three-class cert census,
  the gated sighting counts, the trust movement table, PRIME-vs-TUF,
  the full per-cert inventory.
- `vendor-armor-chipdb.json` — front C: the chip tables per specimen,
  the ladder movement (the single 41 → 46 expansion at 3802), the
  cross-vendor identity.
- Scratch: `scratch-vendor/restore-ledger-ring22.json` + the probes
  (`ring22_restore_corpus.py`, `ring22_pierce.py`,
  `ring22_ssdt_clock.py`, `ring22_der_inventory.py`,
  `ring22_armor_chipdb.py`, `pkcs7_helper.py`).
