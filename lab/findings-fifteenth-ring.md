# The fifteenth ring — what an update changes, and the chain that holds (2026-09-11)

> Companion to rings one through fourteen. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `ring15_release_delta.py`
> and `ring15_day0_chain.py` (sandbox), `ring15_artifact.py` — the
> first-contact machinery (ring 11-12), the proven walker (ring 4)
> and the OVMF LZMA piercing pattern imported verbatim; no grammar was
> rewritten. Artifacts: `vendor-release-delta.json`,
> `vendor-day0-chain.json` (this repo). The directive: continue the
> massive investigation — and the ring answered the question the
> 16/09 day actually depends on: what does a BIOS update *do* to a
> board, and does our pipeline hold when the vendor lenses run as one
> chain.

## Front 1 — the release-delta lens: 3604 vs 4655, file by file

Two official releases of the same board, PRIME B450-PLUS, 4.5 years
apart (2022-03-16 and 2026-08-27, both pinned from the ASUS API
ledger in ring 12). Every FFS file on both sides, outer and pierced
inner volumes alike, fingerprinted by the sha256 of its *body* —
sections, not header bits, which churn with size/state without
content. The GUID sets join at 616 files (285 + 322 + 7 added + 2
removed). The verdict:

**46.3 % of the module set is byte-identical across four and a half
years.** A BIOS update is not a rewrite; it is a targeted transplant
into a mostly frozen body.

The changed 322 cluster exactly where a vendor must rebuild per AGESA
generation: `AmdApcb*` (the PCB — AMD Platform Customization Blob —
default-parameter images shrink by a few hundred bytes each, the
tuning changed), `AmdCcx*` (core/complex topology: `AmdCcxZen3Dxe`
grows 71,958 → 85,942 B — the Zen 3 support story measured in bytes),
`AmdCpm*` (the common platform module), and the SMM shadows that
mirror them. 201 of the 322 are DXE, 65 SMM — the launch surface
changes far more than the ring-0 surface.

The seven *added* modules are the front's headline. Between 2022 and
2026 ASUS shipped in: **`PrepareWhiteListSmm`, `SbRomArmorSmm`,
`FlashSmiSmm`, `FlashSmiDxe`** — a whitelist gate and ROM armor for
the flash path, SMM side and DXE side. The vendor built flash-attack
hardening into the same window the industry needed it (LogoFail is
2023+). Two SMM modules were removed; their GUIDs carry no name in
the 532-GUID join and are recorded as-is. One raw blob
(`1DF36FF9-…`) changes by exactly **one byte** at 80,232 B — body
hash sees what size comparison never could.

Cross-check earned mid-lens: the NVRAM store file
(`CEF5B9A3-476D-497F-9FDC-E98143E0422C` — the anchor ring 14 walked)
changes content at an identical 130,952 B. The factory defaults
moved between releases; the delta lens re-derived the ring-14
finding from the other direction, unprompted.

## Front 2 — the second generale: the vendor chain, REPRODUCIBLE

Ring 10 rehearsed the 14-stage OVMF pipeline. The vendor lenses were
built one per ring and re-run pairwise (ring 14 retired the
"one-run-per-lens" caveat). What no ring had done is the CHAIN: all
six vendor lenses, in protocol order — unwrap → census → versions →
PSP → NVAR → depex — two full runs, every register byte-compared,
judged exactly the ring-10 way.

First verdict: COMPLETE-NOT-IDENTICAL. The ritual caught one
nondeterminism event, and it is a fossil from a previous ring:
`mirror_census_delta.phases_delta` in the versions instrument built
its dict from a `set()` union — key order leaked from Python set
iteration, the *same species* ring 10 found in `ring5_probe.py`. The
fix is the same one word, `sorted()`, at the source. Second verdict:
**REPRODUCIBLE — 6 stages × 2 runs, all registers byte-identical,
~8 s per chain.**

The ring-10 lesson is now institutional: it is not something that
happened once; it is what happens every time a new instrument meets
the ritual. The day-0 protocol gains its vendor table: six lenses,
fixed order, chain identity judged at the end — the shape 16/09
actually runs, plus the live-delta stages a factory image cannot
exercise (live variables minus the factory register).

## Honesty ledger

- Names in the delta come from a 532-GUID join (ASRock's 382
  UI-named modules, MSI, Gigabyte, the ring-9 OVMF map) — not from
  the ASUS ROMs' own voice, which the packaging lens proved is one
  UI section wide. 269 of 322 changed modules carry a name; 53
  remain GUID-only, recorded as GUIDs, not invented names.
- Body-hash identity deliberately ignores FFS header/state bits. A
  module changing only its header would be called unchanged; never
  observed in this delta, not proven impossible.
- Two releases measured. No claim covers the 37 intermediate
  releases; the API ledger lists them and the method extends, but
  they were not downloaded.
- AGESA level strings were not recovered (the scan finds
  "AGESA Driver" only — the level lives inside APCB blobs, a lens
  for a future ring or for the dump).
- The chain's six stages are the vendor-applicable subset of the
  OVMF table; IFR facade stages (OVMF-only instruments) are out of
  scope here and remain proven on the OVMF side by ring 10.
- ring13_versions.py was edited (one `sorted()`); its scratch
  register changes bytes but no published lab artifact changes
  content — `vendor-versions.json` carries no phases_delta table
  (verified before commit).

## Consequences for day-0 (16/09)

- **The update question is pre-answered for our board**: the dump's
  3644-vs-4655 delta can be measured the same way, and the answer
  will name which subsystems differ — with this ring's 3604→4655
  table as the reference vocabulary.
- **The vendor chain is rehearsed**: six lenses, ~8 s, zero drift.
  The dump joins the chain as a seventh specimen in the first hour.
- **The added-modules list is the security-relevant delta**: if the
  dump runs an older release, the flash-armor modules
  (`SbRomArmorSmm`, `FlashSmiSmm`, `PrepareWhiteListSmm`) may be
  absent — that absence, proven by the same body-hash method, is
  itself a day-0 finding.
- **The factory NVRAM register now has a second dimension**: the
  defaults moved 3604→4655 at constant size, so matching the dump's
  Setup blob against both sides dates the image independently of
  version strings.
