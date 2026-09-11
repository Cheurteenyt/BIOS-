# The eleventh ring — the instrument meets real vendor silicon (2026-09-11)

> Companion to `ovmf-findings.md` and rings one through ten. Same
> campaign, same rules: read-only over downloaded vendor images, zero
> bytes written anywhere but the lab record. Instruments this ring:
> `ring11_vendor_firstcontact.py`, `ring11_census.py`,
> `ring11_crossprobe.py`, `ring11_depex.py` (sandbox). Artifact:
> `vendor-specimens.json` (this repo). The directive: extend the
> investigation to other motherboard models and their latest updates.

## Front A — acquisition: the two ends of the update cliff

The vendor landscape (docs/vendor-bios-heritage.md) named four AMI
Aptio AM4 vendors; the ring pins the latest BIOS of one board per
vendor and acquires what the network allows.

- **MSI B450 TOMAHAWK MAX 7C02v3G1** (2023-03-09, AGESA ComboAm4v2PI
  1.2.0.8, 32 MB) — downloaded from the vendor CDN. This is the
  *frozen* end: the support cliff of March 2023, in bytes.
- **Gigabyte B450 AORUS PRO F67c** (2026-08-18, AGESA ComboV2 1.2.0.12,
  16 MB) — downloaded from the vendor CDN. This is the *living* end:
  released three weeks before day-0, fixing CVE-2026-6726/6727 (AMD
  TPM reference code).
- **ASRock B450 Steel Legend 10.41 Beta** (2025-04-18, AGESA 1.2.0.E)
  — version pinned by search; the file itself answers **HTTP 403**
  from this network (WAF). Registered, not bypassed.
- **ASUS B450-PLUS GAMING 3644** — the reference board; its latest
  measured BIOS (Aug 2026) is the study's value, and the specimen
  that matters is the day-0 dump itself.
- Vendor HTML support pages (MSI, ASRock, ASUS helpdesk) are
  bot-walled; the CDNs behind them mostly are not. The working route
  was: search → support page rendered server-side → direct CDN URL.

## Front B — first contact: the nesting rule bites its own registry

Flash maps first, always with the ring-8 rule: `_FVH` candidates are
guilty until validated (zero vector, known filesystem GUID, container
fit).

- MSI: 18 raw candidates; Gigabyte: 6. **Every one was rejected** —
  and the rule was right about the specimens and wrong about the
  reason: the FS-GUID registry lookup was case-sensitive while
  `spi_map._guid` returns uppercase. After the one-line fix, the true
  maps emerge: MSI carries six top-level FVs (main 7.75 MB at
  0x59f000, plus a mirrored second-half structure at +16 MB — the
  dual-BIOS image wastes nothing twice), Gigabyte four (main 4.94 MB
  at 0x94f000), each with nested FVs flagged and never walked
  top-level. The garbage candidates (impossible lengths like 2.7
  trillion MB) die on the fit check, exactly as designed.
- The lesson is registered in the honesty ledger: **the rule is only
  as good as its registry** — the validator's failure mode was a
  lookup bug, not a specimen property. It bit on ring 11 so it cannot
  bite on day-0.
- The FTYPE table had also been written from memory and was wrong
  from 0x0A on; the error was caught by cross-checking
  `ovmf_census.py` before any number was read. Copied verbatim since.

## Front C — the census: the OVMF grammar crosses to vendor silicon

The pierced-census result is the ring's headline:

- **The AMI Aptio main FVs open with the OVMF pattern**: a handful of
  fv_image files (5 per main FV) whose GUID_DEFINED sections carry
  the EDK2 LZMA GUID; `FORMAT_ALONE` decompression yields the inner
  FVs — 4 pierced per specimen, the big one holding 402 (MSI) and
  444 (Gigabyte) files.
- **MSI: 453 modules — 264 DXE, 86 SMM, one DXE-core, one SMM-core,
  one application.** **Gigabyte: 498 — 309 DXE, 112 SMM, one PEI.**
  Named via UI sections: 77.5 % and 84.7 %. The names are the AMI
  standard inventory (CsmDxe, SnpDxe, TcpDxe, HttpDxe, …).
- **AGESA verified by bytes where the bytes allow**: MSI carries the
  literal string `ComboAM4v2PI 1.2.0.8` — the vendor page's claim,
  byte-proven. Gigabyte's image holds the board-version string
  `8A16BG04F67c` but no ASCII AGESA — the claim rests on the vendor
  page and is registered as such. Uneven evidence is still evidence
  when it is labelled.
- `dbxDefault`: zero hits on both. SecureBoot strings: 5 (MSI) /
  1 (GB) — the trust store lives in the NVRAM region, walked at file
  level only this ring.

## Front D — the same bones, measured: 275 shared GUIDs, one hub to rule both

- **Cross-vendor identity: 275 module GUIDs shared of 453/498 —
  jaccard 0.549.** The heritage doc's "same bones and same blind
  spots" becomes a number: 55 % shared identity on the DXE/SMM layer;
  the differences are board-specific drivers and vendor option
  software.
- **The dispatch layer reads 100 %**: 228/228 DEPEX sections
  postfix-parsed on MSI, 278/278 on Gigabyte, zero failures — the
  ring-8 grammar, applied verbatim. Opcode shapes match OVMF's
  family: PUSH/AND dominate, TRUE rare, OR rarer, no FALSE, no
  BEFORE/AFTER.
- **PcdProtocol rules both boards**: fan-in 202 (MSI) and 270
  (Gigabyte), against OVMF's 56. Three more top hubs are
  AMI-proprietary and stay GUID-only — no .dec name is claimed
  without a source.

## Honesty ledger

- Two specimens, not four: ASRock is WAF-blocked, ASUS deferred to
  the day-0 dump. The spectrum claim (frozen vs living) rests on the
  two ends actually acquired.
- The DEPEX lens counts parses and fan-in; the full DAG walk
  (ring-8-style transitive structure) was not run on vendor images
  this ring.
- PSP directories were counted ($PSP: 26/13) but not parsed; the
  $BSP BIOS-directory signature has zero hits and no conclusion is
  drawn from that absence.
- The nesting-rule case bug and the from-memory FTYPE table are
  registered in full — both were caught by the discipline, neither
  by luck.

## Consequences for day-0 (16/09)

- The dump arrives to an instrument with two vendor precedents: the
  flash-map method, the pierce, the census, and the dispatch lens
  have all now run on real AMI silicon.
- The vendor report gains a cross-vendor page: OVMF builds vs MSI vs
  Gigabyte as a standing comparison — the ASUS dump slots in as the
  third column.
- The trust-store lens (empty-string dbx tripwire first) applies to
  the dump's NVRAM region unchanged.

## The ledger self-correction chain, one line per ring

Ring 10 proved the instrument reproduces itself; ring 11 proves it
travels — and pays two tolls on the way (a case-sensitive registry,
a from-memory table), both registered. The grammar holds; the maps
differ; the ledger keeps the difference visible.
