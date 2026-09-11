# The twentieth ring — the clocks, the quorum, the unasked bytes, and the rebuild

The board still cannot be touched, so the ring went massive on four
fronts at once: a synthesis that fuses the five dating signals the
study has measured since ring 13, a cross-vendor read of ring -2 that
answers whether ASUS's flash armor is an ASUS thing at all, the
variable-level completion of the Q1 hidden-surface question, and the
deepest read of the MSI double structure yet. One preparation was
required first: the sandbox reset had wiped the specimen binaries, so
the corpus was **restored** (not re-acquired) — five files re-pulled
from the vendors' own CDNs, every zip and every ROM sha256-verified
byte-exact against the ring-11/12 acquisition register before any
probe ran. The ASUS CDN rejects a plain client fingerprint (403); it
answers a full browser header set with `Referer: asus.com` — the
ring-12 lesson, extended.

## Front A — the five clocks, fused: the cert set is the missing coordinate

Rings 13-19 measured five independent dating signals on the nine dated
PRIME B450-PLUS rungs — AGESA (software build), the DER cert set
(signing calendar), the SMM armor (security waves), the PSP blobs
(platform stack), and the image geometry (raw shape). The fusion probe
(`ring20_clocks.py`, zero downloads, artifacts only) builds one table
and prices each clock's discriminating power:

- **The 3802|3810 pair — the quiet-release pair that shares AGESA
  1.2.0.7, shares the 5/7 armor score, and shares 211 PSP blobs — is
  separated by exactly ONE state clock: the certificate set, 12 DERs
  at 3802 vs 18 at 3810.** The cert clock is not a fifth signal; it is
  the missing coordinate.
- The minimal resolving pairs are computed, not asserted:
  `(cert_count, AGESA)` pins all nine rungs uniquely — as do
  `(AGESA, geometry)` and `(certs, geometry)`, but geometry is the
  noisiest clock (64-KiB window heuristics), so the doctrine pair is
  cert count + AGESA. `(armor, AGESA)` fails on the quiet pair;
  `(armor, certs)` fails on 3810|4003.
- The day-0 decision tree is now ordered by cost: geometry first
  (seconds, raw read, anomaly flag), certs second (raw scan, no
  pierce), AGESA third (pins the rung), armor and PSP as
  confirmation. No clock is decisive alone.

## Front B — the SMM quorum: the armor is AMI-generic, not ASUS-made

The five restored specimens walked with the frozen lib's `_scan_fvs`
plus the ring-4 walkers verbatim (LZMA pierced with the stdlib), SMM
membership by PI file type — validated against the ring-19 register
BEFORE any cross-vendor number was read (both ASUS gates reproduce
106/0/1 and 105/0/1 exactly):

- **The four named armor modules ship under the SAME GUIDs on MSI
  (2023), Gigabyte (2026) and ASRock (2025): `SbRomArmorSmm`
  (51080191…), `PrepareWhiteListSmm` (391626DB…), `FlashSmiSmm`
  (6C289241…), `FlashSmiDxe` (755877A6…).** The ASUS flash armor is an
  AMI-Aptio platform deliverable. ASUS's own copies are GUID-found
  only — the nameplate blindness (ring 12) hides their names.
- **`SbRomArmorSmm` has three distinct bodies across four vendors —
  and MSI and ASRock ship a byte-identical body.** The other three
  armor modules build one body per vendor. Identity is AMI-generic;
  bodies are vendor builds.
- MSI's frozen cliff is visible in ring -2: it still carries
  legacy-SMM-827E45A4, which ASUS retired at 4202 (2023-08) — two
  months AFTER MSI's last release. The retirement calendar holds
  across vendors.
- 83 SMM GUIDs sit in all five specimens — the AMD family stacks
  (AmdCcx*/AmdFabric*/AmdApcb*/AodSmm*), the FCH stacks, AMI plumbing
  — and each vendor overlaps OVMF's SMM reference set by exactly 4
  GUIDs (the EDK2-heritage core).
- SMM jaccard ASUS 3604|4655 = 0.954 (104/107 shared): the armor
  arrival plus the legacy retirement is the whole intra-vendor delta.

A method note that almost cost a correction: MSI's two SPI windows
double-count every GUID; the first spine computation (per-occurrence
counting) fabricated an all-5 armor spine — which would have
contradicted ring 18's 3604 = 0/7. The variants probe (one GUID per
armor module, no family variants) refuted the artifact before
publication; all set math dedupes per specimen. The ring-11
case-sensitivity lesson also bit again (uppercase canonical GUIDs vs a
lowercase LZMA constant — zero LZMA sections pierced until caught).

## Front C — the unasked bytes: Q1's hidden surface, priced per vendor

Ring 19 proved hiding is variable-level (~zero IFR conditions across
46,000+ questions). The completion: for every varstore the facade
declares, how many bytes are ever referenced by a question's
(varstore_id, offset, width)? The ring-6 grammar and ring-7
dissection were imported verbatim; **the gate reproduces the ring-19
question totals EXACTLY on all five specimens** (7,975 / 8,273 /
8,646 / 6,388 / 6,360) before any coverage number was read:

- **84-90 % of varstore bytes are never referenced by any question**
  (ASUS 3604: 83.9 %, 4655: 83.4 %, MSI: 85.3 %, Gigabyte: 87.1 %,
  ASRock: 90.4 %).
- The `Setup` blob itself — the classic `setup_var` target — carries
  142-567 never-asked bytes per board (ASUS 456 B size / 142 B
  unasked; MSI 1,428 / 567; Gigabyte 628 / 247; ASRock 677 / 260).
  The IFR-side sizes cross-validate ring 14's NVRAM-side blob sizes
  exactly (MSI 1,428, Gigabyte 628) — the Q1↔Q5 bridge lands on
  vendor silicon from both ends.
- 10-28 zero-question varstores per board: memory the facade declares
  and never reads from the UI.

Honesty: widths default to 1 byte (ONE_OF takes its widest option
type; STRING counts one utf-16 char; NUMERIC width needs the raw
flags byte the dissection did not retain — an undercount, so the
uncovered shares are UPPER bounds on hiding).

## Front D — the MSI mirror at the PSP layer: a parallel build, not a copy

The full-ROM psptool parse yields 18 directories — all in the LOWER
16-MiB window; its FET walk misses the upper window (the two FET
warnings). Slicing the upper 16 MiB as a standalone image parses it —
**the upper window's PSP layer, read for the first time in the study**
(10 tables vs the lower's 8 standalone):

- The 10 full-ROM "extra" tables sit at lower-window offsets that
  mirror the upper's ten (+0x1000000, same magics, same entry counts,
  same entry sizes) — the combo architecture carries both chip
  families in both windows.
- **But the tables are NOT byte-copies: 0/10 table-identical** (the
  copies relocate entry addresses), and at the blob level the pairing
  is decisive: **72 of 76 paired (magic, type, subprogram) keys
  changed at identical sizes; 4 identical (incl. the 4,096-B type-0x22
  policy table); 33 family-A blob types exist only in the lower
  window; 0 upper-only.**
- The PSP layer measures **3.7 % byte-stability across the windows**
  vs the FFS layer's majority-identical (ring 17: 261/380 shared
  GUIDs identical). Ring 13's cross-release churn lesson extends
  WITHIN one release: the mirror is a parallel build — same table
  skeleton, rebuilt bodies.

## Consequences for day-0 (16/09)

- The §1.5 fingerprints gain the five-clock decision tree: geometry
  (seconds) → cert count + timestamp year (the missing coordinate) →
  AGESA (pins the rung) → armor + PSP confirm. The 3802-vs-3810
  ambiguity — the one pair AGESA cannot split — is resolved by the
  DER count alone.
- The armor checklist (§3.1) generalizes: the four core armor modules
  are AMI-generic, so a NON-ASUS dump (or a same-vendor other-board
  dump) should be checked for the same GUIDs, not just ASUS rungs.
- §1's Setup-blob row gets expected unasked bytes (~142-567 B per
  board family) — the dump's NVRAM + facade join now has a number to
  land on.
- If the dump ever lands on an MSI-class dual-family image, the PSP
  layer must be read per window — the upper window is NOT a copy.

## Honesty ledger

- The fusion inherits every honesty line of its five sources; nothing
  in front A was re-measured. The resolving-pair computation treats
  clocks as categorical; finer lenses could split what clocks cannot.
- Body identity (front B) is sha256 of the whole FFS file body, not
  of PE text; rebuild noise inside one section flips the hash without
  a semantic change.
- Armor presence cross-vendor is identity-level (GUID + body bytes);
  whether the other vendors' SPI-protection POLICY matches ASUS's is
  a runtime question the image cannot answer.
- The corpus is four latest-official specimens + one ASUS reference
  rung; an older MSI release could predate the armor entirely (the
  2023-03 cliff sits INSIDE the armor era).
- Width heuristics (front C) make uncovered shares upper bounds.
- The PSP family reading (front D) inherits ring 17's
  lower=Zen/Zen+ / upper=Zen2/Zen3; this probe adds pairing
  granularity, not family naming. psptool's newer API differs from
  the ring-13 notes; its on-disk source (magics, entry layout,
  address modes) was the table source this time.
- The restoration re-pulled five already-registered files and
  verified both zip and ROM hashes against the register; nothing
  outside the register was downloaded. The register's own 13-specimen
  count is unchanged.

## Registers

- `vendor-clocks.json` — front A: the fused five-clock table, the
  pair-discrimination matrix, the minimal resolving pairs, the day-0
  decision tree.
- `vendor-smm-quorum.json` — front B: per-specimen SMM censuses
  (gated on ring 19), the pairwise SMM jaccard, the 83-GUID spine,
  the armor GUID presence matrix and body identity, the OVMF overlap.
- `vendor-unasked.json` — front C: per-specimen varstore coverage
  (gated on ring 19's exact totals), the Setup rows, the
  zero-question varstores.
- `vendor-psp-mirror.json` — front D: the upper window's first parse,
  the table-mirror check, the blob classification (4/72/33/0) and the
  byte-stability share.
- Scratch: `scratch-vendor/` (restored corpus + restore ledger +
  debug probes `ring20_debug_*.py`).
