# The thirty-eighth ring — « l'examen blanc » (the conductor + the dress rehearsal)

Date: 2026-09-13 · Instrument: `lab/fw38-exam.py` (tracked, fw33/fw35/fw36/fw37
precedent) · Mode: docs-only, read-only, stdlib-only · Surface frozen: 323
checks, MCP smoke 12 tools, 0 diff on bin/lib/tests.

## 1. The gap this ring closes

Ring 37 completed the day-0 arsenal: identification (33), comparison (34),
cartography (36), walking (37), scoring (35). But the arsenal was FRAGMENTED —
five instruments, five command surfaces, human interpretation between each, and
a fill-in template whose 31 fields mostly required reading outputs by hand. The
day-0 was a choreography. Ring 38 makes it ONE command, and — the part that did
not exist anywhere — rehearses the whole exam against a stand-in corpus BEFORE
the board exists, with a discrimination invariant asserted: **on a non-target
image, the oracle may hit only the absence-predictions; any band/presence hit
on the wrong board is an over-broad oracle and the mock fails loudly.**

## 2. The instrument

`fw38-exam.py` imports the tracked instruments as modules (fw36 atlas, fw37
load/pierce/inventory/vars/ledger, fw35 oracle) and fuses eight registers
(vendor-agesa, -flash-armor, -genome, -acpi, -psp, -armor-chipdb, -lifecycles,
-oracle). Modes:

- `exam <image> [--out f.json] [--no-geometry]` — the full measurable chain:
  rom census → pierce → inventory → vars → AGESA ladder → armor names/GUIDs →
  SMM census → ACPI walk → PSP scan → whitelist match → findings draft →
  fw35 score. Auto-fills **12 of the 20 day-0 fields**; the 10 manual lenses
  stay null and are LABELED in the output (`manual_lenses`), never invented.
- `exam-pair <old> <new>` — the release-41 lens: extractors on both images +
  the fw37 ledger at GUID truth → auto-fills **7 of the 8 release-41 fields**
  (agesa_level_41, core_armor_41, added_present_count_41, births_41, deaths_41,
  dsdt_sha16_41, chip_whitelist_families_41; DER and IFR stay manual). The
  draft carries ONLY the `_41` keys — day-0 keys of the old image must not
  leak into release-41 verdicts (a real bug caught before first run).
- `mock` — the examen blanc (below).
- `selftest` — two-tier, 20 gates (fw36/fw37 discipline): tier R re-derives
  every anchor from the registers (always); tier I runs the full chain LIVE
  on the surviving OVMF corpus (loud skip when absent).
- `manifest`.

Auto-filled day-0 fields: rom_bytes, agesa_level, agesa_string,
armor_quartet_present, sbrom_armorsmm_present, chip_whitelist_families,
legacy_smm_count, module_count, dsdt_sha16, aod_ssdt_revision,
setup_varstore_size, smm_census_total. Manual (labeled): trust_cert_distinct,
ifr_questions_total, ifr_valid_fraction, setup_uncovered_bytes,
varstore_uncovered_share_pct, matches_known_release,
distinct_fingerprints_count, psp_hashes_{3644,3604,3802}.

## 3. The discoveries (caught live by the gates before they could lie)

1. **OVMF has NO static DSDT.** The Debian OVMF builds carry
   `QemuFwCfgAcpiPlatform` — ACPI tables are generated AT RUNTIME via fw_cfg,
   so no checksum-valid DSDT exists in the flash. The lens honestly reports
   `dsdt = None` with the structural cause named in the inventory
   (`acpi_modules: [AcpiTableDxe, QemuFwCfgAcpiPlatform]`).
2. **The ring-36 footprint register's DSDT "hit" was a FALSE POSITIVE.** The
   register itself documented its weakness ("sigs validated by length-field
   plausibility"): its DSDT @2259668 carried length 9,733,135 — absurd — and
   its RSDP failed the 20-byte checksum. The new checksum-validated walk
   refuses ALL FOUR DSDT sig hits in the pierced payload and reports every
   refusal with its reason. A real static SSDT @1871944 (124 B) DOES validate —
   the small table the register saw was real. Ring-36's heuristic is thereby
   SUPERSEDED, and the correction is auditable, not silent.
3. **Genome transition labels carry the vendor prefix** — `dead_at` is
   `"asus-4003->asus-4202"`, not `"4202"`. A naive split("->")[-1] == "4202"
   silently matched NOTHING (gate R4 caught it; the legacy-SMM lens was dead
   until fixed: the two legacy species are 21782819… and 827E45A4…).
4. **The template has 32 observed-key slots for 31 unique fields** — P-20 and
   P-25 share `agesa_level_41` (gate R1; a dupe is expected, not drift).
5. **The wall re-derives through the conductor**: exam-pair plain↔secboot
   yields births 18 / deaths 9 / byte_delta +777,472 — the registered ring-34
   numbers, re-derived at genome level by a chain that never read them.

## 4. The examen blanc: the profile

`mock` runs exam(plain) + exam(secboot) + exam-pair(plain↔secboot) and scores
all three drafts through the real fw35 oracle. The profile on the stand-in:

| target | hit | partial | miss | na | hits |
|---|---|---|---|---|---|
| day0-3644 (on OVMF) | 2 | 0 | 5 | 19 | P-04, P-05 |
| release-41 (pair on OVMF) | 0 | 0 | 3 | 23 | — |

- Day-0 hits are EXACTLY the absence-predictions (armor quartet absent,
  SbRomArmorSmm absent) — trivially true on any non-AMI image, by design.
  Day-0 misses: P-01 (3,653,632 B ≠ 16 MiB), P-06 (0 families), P-07
  (0 legacy SMM), P-08 (135 modules), P-17 (0 SMM census). Everything AGESA/
  PSP/IFR/DSDT/Setup-shaped scores `na` — structural absence, honestly.
- Release-41 misses: P-21 (core 0 ≠ 4), P-22 (18 births / 9 deaths ≠ 0), P-26
  (0 families ≠ 46).
- **The invariant holds: the oracle discriminates the board.** Had the armor
  NAME strings been searched with a loose matcher, or the census counted by
  "module name contains SMM", OVMF could have manufactured false hits — it
  did not.

Seven assertions are checked and reported in every mock run:
absence-only day-0 hits, empty release-41 hits, P-01 miss, P-09 never hits,
dsdt-honest-None (with refusals > 0), wall 18/9, score roundtrip 26/26.

## 5. The 20 gates

| tier | gate | what it re-derives |
|---|---|---|
| R1 | template 31 unique keys, conductor fields covered | fw35 template shape (32 slots, shared keys expected) |
| R2 | quartet = 4 named, SbRomArmorSmm in | watchlist naming rule (FlashSmiDxe/FlashSmiSmm/PrepareWhiteListSmm/SbRomArmorSmm) |
| R3 | wave1 births = 5, prefixes in watchlist | genome wave1_births ∩ added_watchlist |
| R4 | legacy dead species = 2 | the ->4202/->4402 retirements (vendor-prefixed labels) |
| R5 | acpi anchor = oracle P-09 expect | `27d5e826e111d755` agrees across registers |
| R6 | AGESA ladder ≥ 9 rungs, 3644 = 1.2.0.6b | the timeline |
| R7 | chipdb 41 @3604, a 46-family set exists | the whitelist law |
| R8 | SMM census 3604 = 105/0/1 | the lifecycles convention |
| R9 | PSP layout documents 16 B header + 16 B entry | the registered parse convention |
| R10 | oracle chain selftest passes | fw35 36/36 invoked through the chain |
| R11 | census buckets resolve | fw37 FILE_TYPES 0x0A/0x0C/0x0D |
| I1 | exam(plain) completes | 3,653,632 B / 135 modules live |
| I2 | ACPI walk honest + deterministic | dsdt None, ring-36 false positive rejected, 4 refusals |
| I2b | runtime-ACPI marker present | QemuFwCfgAcpiPlatform in inventory |
| I3 | P-01 miss on OVMF | 4M ≠ 16M |
| I4 | P-09 never hits | na is the honest OVMF verdict |
| I5 | day-0 hits ⊆ {P-04, P-05} | THE discrimination invariant |
| I6 | pair wall 18/9 | genome-level re-derivation |
| I7 | release-41 hits = ∅ | second discrimination face |
| I8 | score roundtrip both drafts | 26 rows each |

Result: **20/20 PASS, tier I live** (3.9 s wall, tier R only when the corpus
is absent).

## 6. Day-0 usage (the one command)

```
python3 lab/fw38-exam.py exam dump.rom --out findings-draft.json   # §1-§4 lenses + draft + draft score
python3 lab/fw38-exam.py exam-pair release40.rom release41.rom     # the P-20..P-26 lens
python3 lab/fw35-oracle.py score findings-draft.json               # after the manual lenses are filled
```

The draft score is EXPLICITLY a draft: 10 manual lenses remain null (na) until
the §1-§3 tables are filled by hand. The exam output carries every fingerprint
the manual lenses need (module names/GUIDs/sha8, DSDT/SSDT candidates with
checksum verdicts, PSP candidates with region sha16 for fw33 `body` matching,
the setup varstore size).

## 7. Honesty ledger

- PSP remains REPORT-ONLY: header fields, entry types, region sha16 — the
  fletcher32 verdict and entry-hash matching stay with the human + psptool
  cross-check (the registered convention), because no PSP specimen bytes
  exist on this disk to validate a stdlib reimplementation against.
- The whitelist lens counts REGISTERED families present (41-set/46-set); a
  board carrying unregistered families under-reports — the honesty note
  travels in the output.
- AGESA with multiple version-like tokens stays null in the draft (the human
  picks); single-token cases auto-fill.
- The mock is a rehearsal against OVMF, not a proof about the ASUS board;
  it proves the CHAIN (no crashes, no false hits, wall agreement) and the
  ORACLE's discrimination — nothing more.
- Drift #22 (this session's summary described ring 35 while the disk stood at
  ring 37) is radiated here per the Task-31 doctrine: the disk is the master,
  no ghost work existed — parallel sessions had landed rings 36-37 (d95fdd7).

## 8. What remains

The 16/09 dump fills the 10 manual lenses, scores P-01..P-19, and settles
question_3644 (P-18's H3 + P-19's PSP direction). Release-41 scores
P-20..P-26 through the same exam-pair command. Both events now run on
rehearsed rails: identification → comparison → cartography → walking →
**examination** → scoring.
