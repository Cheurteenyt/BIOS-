# The forty-first ring — the unregistered detector (the third reading)

**Date**: 2026-09-13 · **Instrument**: `lab/fw41-novelty.py` (TRACKED,
precedent fw33/35/36/37/38/39/40) · **Register**:
`lab/vendor-novelty-ledger.json` (the ZERO ledger) · **Gates**: 25/25
PASS, tier I live · **Surface**: frozen (323/323, MCP 12 tools, 0 diff
bin/lib/tests)

## 1. The hole

After ring 40 the day-0 chain was zero-seam: identification (33) →
comparison (34) → cartography (36) → walking (37) → exam (38) →
identity (39) → weld (40) → scoring (35). Two machines read the dump —
the ORACLE against 26 frozen predictions (hit/partial/miss/na), the
JUDGE against the nine known rungs (known-release / no-match). Both are
silent about one entire category: phenomena that live OUTSIDE every
register and every prediction envelope. A new SMM body, a ninth AGESA
step nobody predicted, a flash-chip family the armor learned, a DER
body the industry never shipped — none of it has an address in the
current arsenal. The dump would be measured against expectations and
against the known, and the REST would fall between the chairs.

The forty-first ring closes that: the third reading. Every image is
now covered by three exhaustive, mutually independent questions —

    predicted (fw35)  ·  known (fw39)  ·  NOVEL (fw41)

## 2. The instrument

`fw41-novelty.py` — stdlib-only, read-only, imports the neighbours by
path (the fw38/fw40 discipline). Six axes, each a universe plus a live
extraction:

| axis | universe (source) | extraction |
|---|---|---|
| species | 330 register TRANSITION species **∪ live union across the nine rungs = 615** (gate R13 proves register ⊆ union) | fw39 deep walk GUID set |
| certs | vendor-der-inventory per-rung trust sets (4 @3604, frozen 6 from 3810, union 14) | the ring-39 X.509 raw-plane walk |
| dsdt | vendor-acpi checksum-valid variants (union 12; both clock anchors) | the ring-38 checksum-validated ACPI walk |
| agesa | the nine-rung AMD ladder (6b < 7 < 8 < A < B < Ca < E < 12) + the P-02 day-0 envelope + the P-20 floor 1.2.0.12 | fw38 marker-proximity lens |
| whitelist | chipdb 41∪46 = 46 **+ the live extractor deviation** (gate I11) | STRUCTURAL chip-table extractor (§4) |
| smm | LIVE union across the nine rungs = 109 (no register stores SMM GUID sets) | fw39 deep walk, ftypes 0x0A/0x0C/0x0D |

Classes: `known` (inside the universe) / `anticipated` (outside the
universe, inside a registered envelope — the P-02 set {1.2.0.6, 6a, 6b,
6c, 7, 8} or ≥ the P-20 floor **within the same 1.2.0.x line**; a
garbage 9.9.9.99 is unregistered, not anticipated — the monotone claim
is about that line) / `unregistered` (outside everything).
**Contradiction is deliberately not a class** — violating an
expectation is the ORACLE's verdict; fw41 only enumerates the outside.
Every finding is a candidate entry for the zero ledger.

Verdicts: `inside-universe` (all axes clean) / `anticipated-only` /
`novel`. Degradation is LOUD and claim-free: with no corpus, the
species/SMM/whitelist universes cannot be calibrated, the axes report
`degraded` and make ZERO claims (gate I9) — an incomplete universe
never manufactures novelty.

## 3. The zero ledger

`lab/vendor-novelty-ledger.json` starts EMPTY — **by proof**, not by
hope: gates I1/I2 prove zero unregistered on the known rungs 3604 and
4655 (both sha conventions), gate I3 proves novelty is unavoidable on
the foreign stand-in (OVMF: 109 unregistered, species 103/147 outside,
judge agrees no-match). Its `live_calibration` block records what the
instrument measured at freeze time (species universe 615, SMM universe
109, the extractor deviation) while the `universe_snapshot` block
freezes the REGISTER-derived sizes (330/14/12/46) the R-gates re-derive.
At the first event that surprises the registers, entries begin — the
ledger's growth IS the chronicle of the beyond.

## 4. The extractor that beat the register (the ring's discovery)

The chipdb register documents its own extraction method: "NUL-separated
chip-name table after the 'AMD rom armor' banner (16 bytes from banner
start)". Three facts emerged when fw41 tried to reproduce it:

1. **The banner is an ENTRY, not a header**: `AMD rom armor` travels as
   a NUL-terminated 8-aligned name inside the chain itself — and only
   from 3802 (the armor wave's own birth; 3604's table predates the
   banner). A banner-anchored extractor finds nothing on 3604.
2. **The table is structurally recognizable without the banner**:
   NUL-terminated names at 8-byte stride (`SST 25LF040`+5 NUL = 16 B,
   `ATMEL 26DF041/25DF041`+3 = 24 B), chains of ≥8 links; the
   discriminator against POSIX-errno chains and OpenSSL curve chains
   that travel the same way: a chip entry carries a DIGIT in ≤4 space
   tokens.
3. **The structural extractor is STRICTLY MORE FAITHFUL than the
   register**: on every one of the nine rungs it recovers the full
   registered set (missing = 0) PLUS one well-formed chip name the
   original probe dropped — **`STM/Micron/Numonyx 25PF/PX Series`** —
   identical across all nine rungs (gate I11: coverage 9/9, deviation
   stable). The register stays frozen (P-06/P-26 count the REGISTER's
   families — 41/46); the instrument registers the deviation instead,
   with provenance, in the ledger's `live_calibration`.

The same chains explain the register's `n_table_occurrences: 1` vs the
deep walk's 7-9 table copies per image: the original probe searched ONE
plane (`lzma@0xa77084(d0)`), the deep walk sees every copy.

## 5. The AGESA scheme, registered correctly

The ladder's last field is not decimal-with-suffix — it is the AMD
scheme `6b < 7 < 8 < A < B < Ca < E < 12`: digit+letter suffixes stay
within their number (6b after 6, before 7), pure letters are the
letter-major steps, numerals ≥10 come after every letter. `_agesa_key`
encodes exactly this and the register's own nine rungs order monotonically
under it (gate R6). The P-20 floor (1.2.0.12) is PARSED from the
oracle's fields (claim/basis/falsifier — max token = the floor of a
monotone predicate), never hardcoded.

## 6. The gates (25, two-tier)

Tier R (registers, corpus-free): R1 species well-formed 330 · R2
genome rung references parse · R3 cert anchors 4/6/6, union 14 · R4
both DSDT clock anchors · R5 whitelist 41∪46 · R6 ladder 9 + floor
1.2.0.12 + ladder-max == floor · R7 oracle envelopes P-02/P-20/P-23/P-26
· R8 ledger schema + snapshot == live · R9 fw35 26 rows / fw40 31
template keys · R10 SMM census 105/0/1 @3604 · R11 classifier: the
whole P-02 envelope never false-novels, floor safe, garbage caught,
None silent · R12 verdict semantics · R13 register species ⊆ live
union (the parse-form coherence check that would have caught §7's bug
as a gate).

Tier I (live corpus): I1 **3604 inside-universe** (unregistered=0,
no degradation) · I2 **4655 inside-universe** · I3 **OVMF foreign →
novel** (109 unregistered; species 103/147; judge agrees) · I4 **the
needle** — one flipped GUID byte on 3604 yields EXACTLY one
unregistered species and nothing else · I5 certs live 4/12 · I6 DSDT
primary == 27d5e826e111d755 · I7 SMM 106 typed, clean · I8 JSON
roundtrip · I9 degraded axes loud and claim-free · I10 the two
machines agree (judge known-release == detector clean) · I11 the
extractor gate (§4) · I12 TUF sibling robustness (5 unregistered — a
same-vendor sibling is ALMOST inside the universe, and the 5 that are
not are exactly the kind of quiet difference the third reading exists
to name).

## 7. Lessons caught by the gates (before freeze)

- **The 330-species trap**: the first draft used the genome's species
  as the species universe — I1 failed at 285 unregistered on a
  byte-identical known rung. The genome stores the TRANSITION species
  only; the quiet majority (285 of 615) never changes and is therefore
  absent from the register. Universe = register ∪ live union, gate R13
  added so the form-coherence is proven, not assumed.
- **The regex over-collection**: the day-0 envelope initially parsed
  the P-02 PROSE, picking up tokens the structured `expect`/`widened`
  fields already carry; now parsed from the structured fields (gate R7
  prints the exact set).
- **`9.9.9.99` is not anticipated**: the floor comparison originally
  accepted any head; the monotone claim is about the 1.2.0.x line —
  head equality required (gate R11).
- **`set().union(*{set})` unpacks to characters** — the whitelist
  per-rung universe was one character soup away from shipping; R5
  caught it.

## 8. Day-0 usage

    python3 lab/fw41-novelty.py novelty dump.rom            # the third reading
    python3 lab/fw40-merge.py chain dump.rom                 # the first two (oracle + judge)
    python3 lab/fw41-novelty.py ledger                       # the zero ledger

The chain answers predicted/known; the detector answers novel; the
operator merges the three readings into the day-0 report. Any
`unregistered` finding from fw41 is a candidate ledger entry with
provenance (axis, value, class) — appended only at events, never
before.

## 9. Honesty ledger

- The species/SMM universes and the whitelist deviation are LIVE
  corpus-derived: they degrade loudly (no claims) without the corpus
  (gate I9), and their frozen numbers travel in the ledger's
  `live_calibration` block, clearly separated from the register
  snapshot.
- The whitelist extractor is structural, NOT the register's lost
  banner method; it is gate-validated (I11) and found more faithful
  than the register. The register gap is REPORTED, not patched — the
  frozen registers stay frozen.
- PSP remains report-only (the ring-38 honesty ledger stands).
- The known-rung zero-claims (I1/I2) are partially definitional for
  the live-union axes (the union includes the rungs) — the CONTENT
  gates are I3 (foreign → novel), I4 (needle → exactly one), I12
  (sibling → 5); the coverage gates prove the machinery is noise-free.
