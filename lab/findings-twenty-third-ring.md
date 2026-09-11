# The twenty-third ring — the churn atlas, the blob authorship, and the speaking ladder

The board still waits, so the ring spent the corpus again: **thirteen
specimens, zero downloads, three fronts that had never been asked.**
Front A diffs every FFS module body along the nine dated ASUS rungs
(the module-body time axis — rings 1-22 measured every OTHER layer,
never this one). Front B classifies every PSP/BIOS-directory blob body
by vendor span across all thirteen specimens (ring 15's grammar, ring
20's one-window mirror extended corpus-wide). Front C decodes the HII
string layer along the ladder and diffs the setup vocabulary at every
frontier (ring 19 counted questions; nobody had read the words).

The three artifacts answer one composite question: **when the vendor
changes something, WHERE does the change land — and does the facade
ever tell us?** The answers: bodies move by the hundreds at every
frontier (front A), the PSP layer's bodies are NOT AMD-universal (front
B — only 3 blob bodies are shared by all four vendors), and the facade
stays wordless through every security wave (front C) — except ONE
option, born exactly at the armor release, stamped by the vendor itself
"NOT FOR PRODUCTION".

## Front A — the churn atlas: bodies move in waves, and the armor's birth certificate is module-exact

The shared walker (`ring23_corpus_walk.py` — the frozen `spi_map` FV/FFS
grammar, validated by the 323-check surface, over ring 22's plane
machinery) admits ~613 FFS modules per specimen across 21 planes. The
frontier table over the nine rungs:

| transition | born | dead | moved |
|---|---|---|---|
| 3604→3802  | **5** | 0 | 201 |
| 3802→3810  | 0 | 0 | **45** |
| 3810→4003  | 0 | 0 | 224 |
| 4003→4202  | 0 | **1** | 85 |
| 4202→4402  | 0 | **1** | 166 |
| 4402→4604  | **2** | 0 | 57 |
| 4604→4631  | 0 | 0 | 238 |
| 4631→4655  | 0 | 0 | 197 |

- **The armor's birth certificate is now module-exact.** The five born
  at 3802 join the ring-20 quorum GUIDs one-to-one: `FlashSmiDxe`,
  `FlashSmiSmm`, `PrepareWhiteListSmm`, `SbRomArmorSmm` + freeform
  `89BE47F4` — the wave-1 score 5/7 decomposed into five FFS files.
  The two born at 4604 are freeform `02076249` and `DXE-helper
  4EB43107` — wave-2's +2, completing 7/7. Ring 18's boundary, measured
  by probe scoring, is now a module roster: 5 files at 3802, 2 more at
  4604, nothing between, nothing after.
- **The legacy SMM retirement is likewise a roster of exactly two
  deaths**: an `smm_driver` dies at 4202 (`827E45A4-…`) and one at
  4402 (`21782819-…`) — ring 18's 2/2 → 1/2 → 0/2 reproduced at file
  granularity, independently, by GUID.
- **The quiet pair is quiet at every granularity**: zero births, zero
  deaths, 45 moved bodies (vs 85-238 for every neighbor). The cert set
  doubled 12→18 at 3810 somewhere outside the FFS bodies — and 45
  modules were rebuilt for it. Quietest frontier of the ladder, still
  not byte-silent.
- **TUF 4645 vs PRIME 4655** — same vendor, same era, different boards:
  613/613 modules shared by GUID, 473 bodies byte-identical, 140 moved,
  zero uniques on either side. One build skeleton, two board tunes.

Honesty: a "moved" body is a whole-FFS-payload hash change — a section
reorder counts; a no-name module (ASUS's blind nameplate, ring 19) is
keyed by GUID only.

## Front B — the blob authorship: the PSP layer is NOT AMD-universal

Ring 22 found 6 ALIB AML bodies shared by all 13 boards and a 46-family
chip whitelist identical across 5 vendors — "AMD's common layer". Front
B asked whether the PSP/BIOS directory bodies below them share that
universality. Answer: **no.** Over 2,900 directory entries admitted by
an independent fletcher32 validator (grammar from ring 15's
`layout_registered`, which itself was transcribed from psptool at
runtime — no memory anywhere):

- **Exactly 3 blob bodies are universal** (identical hash on ASUS, MSI,
  Gigabyte AND ASRock): one 4,096-B body re-entered as `$PSP|0x22` and
  `$PL2|0x22` (the same body shipped twice under two cookies), and one
  163,840-B `$BL2|0x63` body. The platform's PSP layer is otherwise
  vendor-built.
- The largest authorship pattern: **105 keys shared by 12 of 13 —
  everything EXCEPT MSI.** The 2023-frozen board is the PSP-layer
  outlier exactly as it is the GUID-quorum outlier (ring 12) and the
  microcode-era outlier (ring 21): MSI's build lineage diverges at
  every layer measured so far.
- 26 further keys are shared only by `asus-4655` + `gigabyte` — the
  two newest-lineage builds; ASRock joins them one pattern later. The
  PSP bodies follow AGESA generations, not vendor friendships.
- Classes corpus-wide: 355 singletons, 335 vendor-private,
  213 multi-vendor-partial, 103 ASUS-AGESA-keyed, **3 universal**.

Two registered corrections:

1. **The "211 shared PSP blobs" figure is dead metadata.** Under all
   five admissible counting scopes (unique body keys 133 / unique entry
   keys 112 / entry multiset PSP-only 145 / entry multiset all-dirs
   201 / unique body keys all-dirs 186), 211 does not reproduce. The
   ring-18 probe died in a sandbox reset and its counting scope died
   with it — superseded in place, never erased, same doctrine as
   ring 21's rom_sha256 correction. The QUALITATIVE register stands:
   223 entries per rung, 201 identical with multiplicity, the
   (dir,type,size) structure identical — the quiet pair is genuinely
   quiet below the FFS layer too.
2. **The MSI upper window reproduces**: 10 directories above
   0x1000000, matching ring 20's "10 tables" — the double structure is
   now seen by a second instrument. And MSI validates 18/18
   directories, reproducing ring 15's psptool crosscheck with an
   independent fletcher32 implementation.

## Front C — the vocabulary clock: the security waves are wordless

The string layer (ring 7 package discovery + ring 8 UCS2/SCSU decode,
per module, per rung) admits 27 modules / 29 cleanly-closing packages /
~10.5K string ids / ~5K distinct strings per rung — the STRING layer
behind ring 19's 7,975-8,273 questions, magnitudes coherent. Then the
frontier diff:

| transition | new words | what landed |
|---|---|---|
| 3604→3802 | **+7** | **`PSP RPMC Switch`** — "Control RPMC usage. … This option is for test purpose only, NOT FOR PRODUCTION!!!" — plus LCLK min/max frequency controls |
| 3802→3810 | +32 | storage-census templates (Physical Disk 16-31, VIRT 16/17) — capacity, not security |
| 3810→4003 | 0 | the biggest body rebuild (224) — zero words |
| 4003→4202 | 0 | zero words |
| 4202→4402 | +3/−2 | PCIe bifurcation rewording (X8/X4/X4) |
| 4402→4604 | 0 | wave-2 armor — zero words |
| 4604→4631 | +2 | `PCI Express Native Power Management`, `Stability Boost` |
| 4631→4655 | +6/−8 | Q-Fan renaming, GEN1/GEN2 dropped, typography |

Three readings land at once:

- **The facade does not advertise security work.** The legacy-SMM
  retirement (4202), the wave-2 completion (4604) and the largest
  AGESA rebuilds (4003, 4631) land ZERO new words. The one
  security-flavored option the vendor ever exposed — the RPMC
  (Replay-Protected Memory Component) switch — is born exactly at the
  armor release 3802, and the vendor's own help text stamps it "for
  test purpose only, NOT FOR PRODUCTION". The armor wave and its one
  word arrive together; everything else is silent.
- **The body clock and the word clock are disjoint instruments.** At
  3810→4003, 224 modules moved and not one word changed; at every
  frontier, "words changed" modules number 0-5 out of 45-238 movers.
  A rebuild-heavy release ships no new facade; a word-heavy release
  (4655) is feature cosmetics (Q-Fan labels). The two clocks cross-
  confirm the rungs only where BOTH move — 3802, the armor frontier.
- **Day-0 gains a word-level checklist row**: the dumped board's
  string layer should contain `PSP RPMC Switch` (any build ≥ 3802) and
  should NOT contain it at 3604; `Stability Boost` arrives at 4631.

## Consequences for day-0 (16/09)

- Expect the module roster: armor quintet present (5 GUIDs), legacy
  SMM pair absent, total modules ≈ 613 at FFS granularity on a 16-MiB
  ASUS image.
- Expect the vocabulary: ~5K distinct strings, `PSP RPMC Switch`
  present, `Stability Boost` present at ≥4631-lineage builds.
- The corpus is three clocks richer (bodies, PSP authorship, words)
  and two corrections richer (dead 211, roster-exact armor births) —
  all measured with zero downloads and zero bytes written outside the
  artifacts.

## The honesty ledger

- Front A: whole-payload hashing (section reorders count as moves);
  nameplate-blind modules keyed by GUID; plane model admits LZMA only.
- Front B: the 211 register declared dead under five scopes, with the
  numbers shown; fletcher32 validated against ring 15's 18/18 MSI
  crosscheck before any classification ran; address modes 2/3 skipped
  and counted (10/specimen).
- Front C: the size cap suspicion was tested before acceptance —
  widened discovery on the ten biggest modules returns the same 11
  packages (the cap is not binding); ring 8 re-read must close with
  residual 0 or the package is dropped.
