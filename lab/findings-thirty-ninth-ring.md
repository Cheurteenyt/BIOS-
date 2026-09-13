# The thirty-ninth ring — « le moteur d'identité » (the identity engine, the H3 machine)

Date: 2026-09-13 · Instrument: `lab/fw39-identity.py` (tracked,
fw33/fw35/fw36/fw37/fw38 precedent) + register `lab/vendor-identity-matrix.json`
· Mode: docs-only, read-only, stdlib-only · Surface frozen: 323 checks, MCP
smoke 12 tools, 0 diff on bin/lib/tests.

## 1. The gap this ring closes

Ring 38 rehearsed the exam and proved the oracle DISCRIMINATES. But the
question the 16/09 dump will actually pose had no instrument: **is this
image one of the nine known PRIME B450-PLUS releases, or is it a
published-but-unlisted build** — the H3 hypothesis, P-18's registered
identity adjudication (≥3 independent fingerprint differences)?
Ring 37's `ledger` produces fingerprints; nothing JUDGED them. Ring 39
builds the judge: eight fingerprint axes, each grounded in its own
register, every convention measured live on the surviving corpus before
freezing, a 36-pair separation matrix calibrating the P-18 threshold,
and a verdict semantics wired straight into `fw35`'s `ck_identity_h3`.

## 2. The instrument

`fw39-identity.py` imports fw36/fw37/fw35/fw38 and fuses NINE registers
(vendor-agesa, -flash-armor, -genome, -acpi, -armor-chipdb,
-lifecycles, -der-inventory + the probes ladder). Modes: `lens`
(the trust-cert census alone), `fingerprint` (the observed half of
every axis), `anchors` (the registered half), `identify` (the verdict),
`matrix` (the 36-pair separation calibration), `selftest` (two-tier,
54 gates, tier I live), `manifest`.

Axes scored (each = one independent identity feature):

| axis | byte side | register anchor |
|---|---|---|
| rom_sha | sha256[:16] FULL + BODY (rom[0x40000:]) — BOTH always computed | probe sha16 per its registered rom_bytes convention |
| agesa_level | top near-marker token (fw38 lens) | vendor-agesa timeline |
| dsdt_sha16_set | ALL checksum-valid DSDTs across ALL deep blobs | vendor-acpi shipped variants |
| smm_census | the 3-bucket dict (SMM/SMM-DXE/SMM-core) | vendor-lifecycles per rung |
| trust_certs | raw-plane DER census (NEW lens, below) | vendor-der-inventory trust sets |
| armor_core | the 4 `armor_quartet` species GUIDs | genome flag + probe core_armor |
| armor_added | the 7 watchlist-prefix GUIDs | probe added_present ladder |
| genome_profile | (wave1, wave2, legacy) species present | genome born/death labels |

Report-only (measured, never scored — each for a named reason):
module_count (three-way semantics mismatch + constant −4 residual),
whitelist_str (string pool may be rung-invariant), genome_full_set,
PSP (ring-38 honesty ledger stands).

## 3. The discoveries (every one caught live, before it could lie)

1. **The sha16 conventions are NOT uniform — and both are derivable.**
   3604/4655 (the two ring-12 sentinels, acquired as stripped .rom) hash
   the FULL 16,777,216 bytes; 3802..4631 (downloaded as CAP, stripped at
   `cap_wrapper_first_fv` 0x40800 = 0x40000 in rom coordinates) hash the
   16,515,072-byte BODY. The engine computes BOTH forms from any dump
   and matches each anchor under ITS convention — verified 9/9 rungs.
2. **The trust-cert lens was BORN this ring.** The ring-22 register's
   trust sets are re-derivable from bytes alone: scan the RAW plane for
   X.509 structures (`30 82` … tbs/sigAlg/BITSTRING walk — short-form
   DER lengths included; the first validator died on exactly that),
   sha256[:16] them. On 3604: 12 sightings / 4 distinct / each cert
   exactly ×3 (PK/KEK/db) — set EQUALITY with the register. Validated
   10/10 specimens (nine rungs + TUF) and cross-vendor (MSI/Gigabyte/
   ASRock factory stores: 0 sightings — the ring-22 gate re-derived).
3. **The armor wave hides behind a nested LZMA pierce.** The shallow
   fw37 walk (payloads of level-1 pierce only) sees 583 files @4202 and
   misses EXACTLY the armor species: `89BE47F4-80CE-4B87-ABD1-…` lives
   in the raw-plane FV @0x980000 and inside a NESTED guided LZMA section
   the level-1 pierce never reaches (its only shallow trace is an HII
   string reference, not a file). Left unfixed, the bias would have
   INFLATED a day-0 dump's diff count by sha + armor + wave1 = 3
   artificial axes on a mere repack — a manufactured H3. The lens
   pierces recursively (depth cap 3, 22 blobs) and walks every FV of
   every level with fw37's iter_files semantics verbatim; fw37 itself
   stays untouched.
4. **The quartet is countable by GUID, not by name.** The armor files
   carry no UI names (AMI strips them); the genome register carries the
   `armor_quartet` flag and the `names` lists (391626DB =
   PrepareWhiteListSmm, 51080191 = SbRomArmorSmm, 6C289241 = FlashSmiSmm,
   755877A6 = FlashSmiDxe). Name-based counting reads 0 everywhere;
   GUID-based counting reads 0/4/4/4/4/4/4/4/4 — exactly the probe law.
5. **DSDTs ship as FOUR checksum-valid variants per rung** (occ 1+2+1+1);
   the occ-2 variant IS the dsdt_clock anchor (27d5e826e111d755 @3604,
   0a4a6f162cad3e51 @4655). The set axis unions all variants — self-diffs
   drop to 0 once the walk collects across ALL deep blobs instead of the
   level-1 payloads only.
6. **The P-18 threshold is calibrated — and it is STRICTER than reality
   requires.** The 36-pair anchor matrix: floor_full = 2, floor_semantic
   = 1 (3802↔3810 differ by ONE semantic axis — the trust certs — and
   3810↔4003 by one: AGESA). No two known rungs EVER separate by ≥3
   semantic axes; a dump clearing 3 against EVERY rung is more distinct
   than any pair in the whole chronology. The frozen P-18 semantics
   (hit ≥3 / partial = 2 / miss otherwise) stand, now with a measured
   context instead of an arbitrary number.
7. **module_count: the three-way mismatch is real and CONSTANT.** Live
   deep walk 604/609/609/609/608/607/609/609/609 vs genome
   608/613/613/613/612/611/613/613/613 — a constant −4 across ALL nine
   rungs. A counting-convention artifact, not identity signal — the axis
   stays report-only, and the constant gap is itself registered.

## 4. The live verdict table (this ring's measurement)

| image | verdict | nearest | diffs |
|---|---|---|---|
| 3604 | known-release | self | 0 |
| 3802 | known-release | self | 0 |
| 3810 | known-release | self | 0 |
| 4003 | known-release | self | 0 |
| 4202 | known-release | self | 0 |
| 4402 | known-release | self | 0 |
| 4604 | known-release | self | 0 |
| 4631 | known-release | self | 0 |
| 4655 | known-release | self | 0 |
| TUF B450-PLUS GAMING 4645 | no-match-h3-eligible | 4655 | 3 |
| OVMF (raw-plane lens) | no-match-below-floor | — | — |

The discrimination is complete: same board different release = 0 diffs;
different board same vendor = 3; and every self-identification is 0 on
the SEMANTIC axes too (the sha-hit no longer hides anything — gate
I5b/I2d pin this). ~2.4 s per image, all-in.

## 5. The 54 gates

Tier R (registers, always): R1 genome presence-deltas == transition
born/dead for all eight rungs; R2 profile anchors; R3 cert anchors
(4@3604, 6@3810+); R4 AGESA ladder monotone; R5 DSDT anchors 9/9;
R6 SMM census anchor; R7 probe ladder (distinct shas, core 0→4, added
0/5×5/7×3); R8 sha conventions from rom_bytes; R9 chipdb law 41/46;
R10 the fw35 36-gate selftest through the chain; R11 module_count
report-only. Tier I (live corpus): I1 trust lens @3604 (12/4/×3/set);
I2+I2b/c/d @3810 (set 6, armor (4,5), sbrom GUID present, self semantic
diffs 0); I3 TUF trust set == register (6, 3 shared with PRIME);
I4a–i the 3604 fingerprint against every anchor (sha, AGESA, SMM, certs,
armor, profile, DSDT 4 variants, whitelist 41, legacy 2); I5/I5b
self-match + semantic-zero; I6 matrix 36 pairs, floors 2/1; I7 TUF
no-match; I8 OVMF no-match; I9 the fw35 roundtrip (self-match → P-18
miss; no-match/3 → hit).

Result: **54/54 PASS, tier I live**.

## 6. Day-0 usage (two commands)

```
python3 lab/fw38-exam.py exam dump.rom --out findings-draft.json   # the conductor
python3 lab/fw39-identity.py identify dump.rom                     # the judge
```

The identify output fills the exam draft's `matches_known_release`,
`distinct_fingerprints_count` (P-18), `trust_cert_distinct` (P-11), and
carries deep-truth overrides for the armor/legacy lenses
(`armor_quartet_present`, `sbrom_armorsmm_present`, `legacy_smm_count`,
`chip_whitelist_families`, `dsdt_primary`) — the operator merges the two
drafts before the final `fw35-oracle.py score`. H3 verdicts: `known-
release` (byte-identity), `no-match-h3-eligible` (count ≥ 3 — the P-18
hit shape), `no-match-below-floor` (count 1–2 — a repack or neighbour).

## 7. Honesty ledger

- module_count stays report-only: fw37 shallow 580, probes 618, genome
  608, deep walk 604 @3604 — four counting conventions, the constant −4
  residual documented but not explained away.
- PSP remains report-only (ring-38 ledger): candidates are listed, the
  fletcher32/entry-hash verdicts stay with the human + psptool.
- The whitelist STRING pool is measured but not scored (may be
  rung-invariant); the scored whitelist field counts the registered
  day-0 41-family set found.
- The live verdict table is THIS ring's measurement on the surviving
  corpus — evidence, not authority; the anchor column IS the registers.
- The 240-byte `asus_b450plus_3644.zip` ghost on disk is the H3 question
  itself, preserved: the release that could not be downloaded is the one
  the 16/09 dump will either match or refute.
- Summary drift #23 (this session's summary described ring 35 + a
  pending recommendation while the disk stood at ring 38) is radiated
  here per the Task-31 doctrine: the disk is the master, no ghost work
  existed — rings 36–38 had landed in parallel sessions.

## 8. What remains

The 16/09 dump now faces a chain where EVERY stage is rehearsed on the
target board's own silicon family: identification (33), comparison (34),
cartography (36), walking (37), examination (38), IDENTITY (39), scoring
(35). Release-41 runs the same rails via exam-pair + identify (its
anchors enter the same matrix when it ships). The H3 question — the only
registered question whose answer no download can preempt — is now
measured by a machine that proved it can recognize every known release
and refuse every foreign one.
