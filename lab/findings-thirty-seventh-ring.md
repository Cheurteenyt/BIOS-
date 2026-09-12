# The thirty-seventh ring — the differ, tracked

*2026-09-13 · docs-only · zero bytes written to any firmware object · zero
downloads*

## The hole this ring closes

The ring-34 registers (`ovmf-constellation.json`, `ovmf-nx-pin.json`,
`ovmf-vars-differ.json`) — the identity classes, the module ledgers, the NX
pins, the VARS census — were produced by **session-side scripts the repo
deliberately did not track**: `ring4_lib.py` (the FFS/section/PE walkers) and
`ring9_differ.py` (the three fronts). The lab README says it plainly: *the
repo tracks knowledge, not scratch*. That doctrine left the project's single
most load-bearing capability untracked — the GUID-aligned module differ that
**both** remaining measurement events consume:

- **day-0 (16/09 dump)**: the CAP comparator's §3 layer (module ledger + byte
  pins + store walk) and the identity fingerprints feeding oracle P-18;
- **release-41**: the module ledger is the measurement input for P-20..P-26
  (AGESA monotonicity, armor waves, genome births/deaths, DER count, façade,
  conditional DSDT, whitelist).

Ring 37 promotes that machinery into `lab/fw37-differ.py`, per the
fw33/fw35/fw36 tracked-instrument precedent. The walkers that produced the
registered numbers are now permanent, stdlib-only, read-only, and
self-verifying. **No new JSON artifact is registered**: the ring-34 registers
ARE the artifact, and fw37 reproduces them live — a second copy would be
drift-bait.

## The fidelity contract

The LEDGER pipeline is byte-compatible with the registered numbers, not a
rewriting:

- files start at FV offset + 0x48 (the registered walker's choice; scan mode
  honors each FV's own header length instead — vendor FVs may carry extended
  headers);
- module bodies are hashed **raw** (pad 0xF0 / raw 0x01 skipped) — no
  driver-level decompression, exactly as the constellation was built;
- pins are exact consecutive runs (no gap clustering), first-8-bytes hex;
- the VARS walk keeps the 60-byte auth header derived on live bytes in
  ring-34 debug7 (no PublishSequence field).

## The selftest: 16 gates, tier I live

Tier **R** (always) re-derives every anchor from the persisted registers;
tier **I** (live corpus) re-derives them **with this instrument** and
byte-compares. All 16 PASS with the surviving OVMF corpus present:

| gate | anchor | live result |
|---|---|---|
| R1/I1 | three identity classes `624e06de…/1a462955…/9ee9f238…` | 5 builds → 3 classes, symlink-resolved |
| R2/I2 | module counts 135/144/144 | pierce + walk reproduces exactly |
| R3/I3 | wall ledger 126 common / 6 identical / 120 changed / +777,472 B, only 9/18 | byte-equal, changed-GUID sets equal |
| R4/I4 | strictnx pair 144/142/2/0 | byte-equal |
| R5/I5 | NX pins: BdsDxe 1 B @35487 `01→00`, IScsiDxe 2 B @94610 `66 2E→00 66` | offsets, lengths and hex byte-exact |
| R6/I6 | VARS 0/39/39, states 21 live/17 obsolete/1 replaced | equal |
| R6b | store sha8s `e875a265…/0d12f983…` | equal |
| R7/I7 | key_delta ms\|snakeoil: PK/KEK/db changed, dbx 76 B same-bytes | equal |
| I5b | UI names resolve **without census** | `BdsDxe` / `IScsiDxe` from the image's own UI sections |

Exit semantics follow the house discipline: any gate failure exits 2
(register or corpus drift — fix before diffing).

## What the generalization adds (and the pierce lesson)

1. **Generic pierce**: the registered walker took the *first* LZMA GUID hit;
   fw37 collects **all** LZMA payloads (extended section sizes handled, false
   GUID hits rejected by geometry + decompressor). The lesson of the port:
   the observed OVMF geometry is a **type-0x02 COMPRESSION section carrying
   the LZMA custom-decompress GUID** at sec+4 with a u16 data offset at
   sec+20 — the registered walker never checked the type byte, and a naive
   "GUIDED = 0x17" filter silently rejects the only true hit (found live:
   0 payloads, gate I2 red, fixed before freeze). Both geometries are now
   accepted; the gates hold the line.
2. **Names without census**: UI sections (0x15) are parsed straight from the
   FFS bodies (decode-first-then-cut-at-null), census only as optional
   fallback. Gate I5b proves it on the corpus — the instrument names modules
   on a *vendor* image with zero project state. The named wall ledger makes
   the semantic truth of the rebuild wall legible in one read: plain lacks
   the entire SMM/secureboot stack (`PiSmmIpl`, `SmmLockBox`, `VariableSmm`,
   `SecureBootConfigDxe`, … — the 18), secboot lacks the 9 plain-only
   drivers (`EmuVariableFvbRuntimeDxe`, `VariableRuntimeDxe`, the dynamic
   shell commands, …).
3. **Any-image modes**: `scan/ledger/pin/vars` take arbitrary paths — the
   same command that re-derives ring-34 today runs on the day-0 dump and on
   `release40|release41` without modification.

## Oracle linkage (why this was the recommended ring)

- P-18 (identity = H3, ≥3 independent fingerprints): the fw37 ledger of
  `dump|3644` is the fingerprint generator.
- P-20..P-26 (release-41): the ledger is the measurement input; the pins
  then localize *which bytes* moved inside changed modules.
- P-14..P-17 lenses: `vars` reads the dump's store in first-hour terms
  (records, states, key variables) with the AMI-specific NVAR clock bound
  from ring 36 one call away in fw36.

The day-0 arsenal is now complete end-to-end and every piece self-verifies:
identification (fw33) → comparison (fw34 registers + fw36 cartography) →
walk (fw37) → scoring (fw35). What remains is the event: the 16/09 dump,
then P-01..P-19 close.

## Honesty ledger

- Proven: 16/16 gates (8 R + 8 I, tier I live); byte-exact pin reproduction
  (offsets, lengths, hex); UI-name resolution without census; generic pierce
  reproducing the first-hit pipeline on the corpus (1 payload, 0 notes).
- Registered, not resolved: vendor FVs with extended headers will exercise
  the scan-mode hlen path for the first time on day-0 (the 0x48 ledger path
  is the one the gates prove); Tiano/EFI-compressed (non-LZMA) sections are
  recorded as unpierced, not decompressed — a loud gap, not a silent one.
- Zero bytes written to any firmware object, zero downloads; the sandbox
  scripts (`ring4_lib.py`, `ring9_differ.py`) remain session-side — their
  product is now tracked, which is what the doctrine asks.
