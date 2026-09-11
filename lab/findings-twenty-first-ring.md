# The twenty-first ring — the sixth clock, the hidden map, and the inverse boundary

*Date: 2026-09-12. Constraint unchanged: the board stays untouched; every
probe is read-only, offline, on restored binaries. Three fronts, one probe
each, gates before readings.*

The ring-20 fusion left the dating tree with one soft spot: five clocks on
nine rungs, and the minimal resolving pair `(cert_count, AGESA)` — but every
additional independent clock narrows the day-0 triangulation. The same ring
priced the hidden surface in bytes without drawing it, and left Q8's
shipped-vs-built classification an OVMF-only result. Ring 21 takes all
three:

1. **the microcode clock** — the CPU's own patch set as a sixth dating
   signal, measured on the full nine-rung ladder;
2. **the hidden map** — the never-asked `Setup` offsets as actual ranges,
   per vendor;
3. **the ACPI lens** — what vendor firmware ships as bytes vs builds at
   runtime, plus the DSDT as a seventh clock candidate.

Before any of it: the ladder had to be restored, and the restoration caught
a register defect.

## The restoration, and the dead metadata in the ring-16/18 register

The seven rungs whose binaries the ring-18 probes deleted after scoring
(3802, 3810, 4003, 4202, 4402, 4604, 4631) were re-acquired from the same
official ASUS CDN URLs. Every zip matched its register `zip_sha256` anchor
byte-exact — 7/7. Then every ROM hash check failed — 7/7.

Eight wrapper/offset variants were tested against the registered
`rom_sha256_16` values (full CAP, `raw[2048:]`, trailing-256-KiB trim, and
more): **0/7 hits**. The ring-18 probe scripts themselves were erased by
the earlier sandbox reset, so the computation that produced those values
cannot be reconstructed. The verdict follows the house rule *the disk trumps
the register*: the zip anchors are sound (they verified in the ring-18
session and verify now), the ROM-hash entries are **dead metadata** —
recorded from a byte range or a code path nobody can re-derive. The seven
values are superseded in `vendor-flash-armor.json` under
`ring21_rom_hash_correction` — kept, never erased — and fresh full ROM
sha256s registered in their place.

The restored binaries were then proven to *behave* like the ring-18
specimens before any microcode number was read: the armor census re-run on
all nine rungs reproduces the register exactly (added-present multiset,
core count, legacy count — 9/9 gates PASS).

## Front A — the microcode clock (the sixth clock)

Method: psptool parses each specimen's BIOS directory; entry type `0x66`
is `MICROCODE_PATCH`. Per psptool's own source (the table of record),
the patch header opens with a BCD date packed `0xDDMMYYYY` and a u32
patch level. The lens measures every `0x66` file on twelve specimens:
nine ASUS rungs + MSI/Gigabyte/ASRock.

A first full-run finding was **the bug in my own probe**: `max()` over the
display string `DD/MM/YYYY` ranks `12/06/2018` above `12/05/2024`. The
newest-patch-date column was garbage until the date was parsed as
(Y, M, D). Both the bug and the fix are registered — a string is not a
date.

Results, gates green:

- Every specimen carries **exactly 19 distinct patches** — a structural
  constant (a fixed carrier); the signal is *which* patches occupy the
  slots.
- The newest-patch date is **monotone** along the ladder and moves at five
  of eight adjacent rungs:
  `3604: 2021-07-19 → 3802: 2021-10-14 → 3810: 2021-10-14 → 4003: 2022-03-28
  → 4202: 2022-03-28 → 4402: 2023-07-07 → 4604: 2023-10-07 → 4631: 2024-08-22
  → 4655: 2024-08-22`.
- **The quiet pair 3802|3810 is NOT separated by microcode** — identical
  19-patch sets. The quiet pair survives every state clock except the
  certificate set; the sixth clock agrees with the other five.
- The full patch sets are identical on three more pairs (`4003|4202`,
  `4631|4655`, and — by the set identity — the pair `3802|3810`), and the
  set changes at the same five rungs where the newest date moves.
- The churn is generational: at 4604→4631 ten 2019-era patches leave and
  ten 2024-era patches arrive — the 2024 microcode refresh.
- The resolving-pair computation is re-run with the sixth key included:
  **`(cert_count, AGESA)` remains THE minimal resolving pair**. Microcode
  adds corroboration (and a cheap year-bucket read), not resolution —
  it shares every quiet pair with AGESA.
- Cross-vendor coherence, computed not asserted: MSI 7C02v3G1 (released
  2023-03) carries microcode frozen at 2022-03-28 — the same microcode era
  as ASUS 4003 (released 2023-03-21). Gigabyte F67c (2026-08) and ASRock
  10.41 (2025-04) both freeze at 2024-08-22 — **AMD stopped refreshing the
  AM4 microcode set at the 4631 generation**, and the whole corpus's
  newest patch is the same 2024-08-22 set.

Day-0 value: the microcode scan is a raw directory read (seconds, no
pierce). The newest patch date year-buckets the build; the full set pins
the rung alongside `(cert_count, AGESA)`.

## Front B — the hidden map (the offsets the facade never asks about)

Method: ring-20's front-C machinery imported verbatim (ring-6 grammar,
ring-7 dissection, the ring-19 register gates). The only new code inverts
each covered byte-set into merged `[offset, length)` ranges. The gates
reproduce ring-19's question totals exactly on all five specimens
(7,975 / 8,273 / 8,646 / 6,388 / 6,360 — 5/5 PASS).

The map (`vendor-hidden-map.json`), per vendor, for the classic `Setup`
varstore:

| board | Setup size | never-asked | ranges | largest |
|---|---|---|---|---|
| ASUS 3604 | 456 B | 142 B (31 %) | 27 | 28 B @ +49 |
| ASUS 4655 | 456 B | 142 B (31 %) | 27 | 28 B @ +49 |
| MSI 7C02v3G1 | 1,428 B | 567 B (40 %) | 166 | 135 B @ +904 |
| Gigabyte F67c | 628 B | 247 B (39 %) | 110 | 28 B @ +235 |
| ASRock 10.41 | 677 B | 260 B (38 %) | 71 | 28 B @ +206 |

Two readings:

1. **The ASUS Setup layout is frozen across 4.5 years.** 3604 and 4655
   carry the same 456-byte store, the same 142 never-asked bytes, the same
   27 ranges at the same offsets. The façade's memory did not move once
   between 2022-03 and 2026-08.
2. **The hidden surface is fragmented, not one tail block.** MSI hides the
   most (567 B) and fragments it most (166 ranges interleaved with the
   asked bytes); every vendor keeps a largest contiguous policy block in
   the same size class (28-135 B).

Honesty: this is IFR-side truth — which bytes no question references.
Whether a hidden byte is withheld policy, padding, or written by protocol
at runtime is not decidable from the image alone. The widths keep the
ring-20 approximations (NUMERIC = 1 B — an undercount), so the ranges are
upper bounds on hiding. Knowledge-only: the map prices what a
`setup_var`-style editor *could* address; the zero-write doctrine is
untouched.

## Front C — the ACPI lens (shipped vs built, and the DSDT clock)

Method: Q8's classification ported to the vendor corpus, with a sharper
discriminator than position alone — **an ACPI table checksums itself**
(sum of `length` bytes == 0 mod 256). Position classifies the candidate;
the checksum admits it. The lens scans raw/freeform sections and pierced
LZMA payloads across all twelve specimens, classifying signature words
inside PE bodies as generator vocabulary when they never validate as a
table anywhere.

The first gate was **refuted by the bytes and rewritten**: expecting
`DSDT+FACP+APIC` to ship was the OVMF expectation. The bounded debug probe
scanned the whole 16-MiB 4655 image for `FACP` and found **one occurrence —
garbage inside compressed data** (declared length 3.9 GB). The measured
vendor invariant, 12/12 PASS:

- **What ships**: the AML. `DSDT` and `SSDT` bodies as checksum-valid raw
  sections inside the compressed FV — 27 distinct table bodies on an ASUS
  rung (4 distinct DSDT variants + 23 SSDTs), 29 on MSI/Gigabyte, 18 on
  ASRock. Boards ship *multiple* DSDT bodies — per-configuration AML the
  platform layer picks at runtime.
- **What gets built**: every static table — `FACP`, `APIC`, `MCFG`,
  `HPET`, `IVRS`, `XSDT` — zero bytes shipped anywhere; their signatures
  appear only as generator vocabulary inside the AMI ACPI PE modules.

So the Q8 boundary is **the inverse of OVMF's**: OVMF ships nothing and
builds everything; the vendor ships the AML and builds everything else.
Both sides of the three-class model (shipped / generator / runtime-built)
are now measured.

**The DSDT clock** (main = largest body per rung):

| rungs | DSDT body | size |
|---|---|---|
| 3604 → 4202 | `27d5e826` | 47,184 B |
| 4402 → 4604 | `f23c571b` | 45,043 B (−2,141 B) |
| 4631 → 4655 | `0a4a6f16` | 45,069 B |

Three DSDT generations across the ladder, moving at exactly two rungs —
`4202→4402` and `4604→4631`. Two observations attached: the DSDT *shrank*
at 4402, the same release where the legacy SMM fully retired (ring 18:
0/2 by 4402 — the AML dropping legacy paths is consistent with the SMM
layer dropping legacy handlers); and the *compiler* never moved
(`INTL`, iASL 2014-09-25) while the bodies did — the OEM revision fields
are static, so the body hash is the only honest movement signal. Cross-
vendor: **no table body is byte-identical across all twelve boards** —
every vendor compiles its own AML.

Day-0 value: the dumped board's DSDT hash lands in a three-generation
atlas; a body outside the three is a fourth generation and a finding.

## Consequences for the day-0 checklist

- The decision tree gains two raw-read clocks before the pierce:
  microcode (newest patch date → year-bucket; set → rung corroboration)
  and DSDT (hash → three-generation atlas). Cost order becomes:
  geometry → certs → **microcode** → **DSDT** → AGESA (pierce) → armor →
  PSP. `(cert_count, AGESA)` still resolves all nine rungs alone; the new
  clocks are independent corroboration read in seconds.
- The `Setup` row expects 456 B declared / ~142 B never-asked / 27 ranges
  on this board — the ring-20 row now has an offset-level expectation
  (`vendor-hidden-map.json`).
- The ACPI row: expect DSDT+SSDT shipped (multiple DSDT variants), zero
  FACP/APIC bytes in the image, `INTL` 2014-09-25 creator on every AML
  body. Finding `FACP` bytes in the dump would be a first for the corpus.

## The honesty register

- The ring-16/18 register's seven `rom_sha256_16` values are dead metadata:
  unreproducible from byte-verified zips (8 variants tested, 0/7), probe
  source erased by the sandbox reset. Superseded in place, never erased;
  identity rests on the verified zip anchors. The restored binaries
  reproduce the ring-18 armor census exactly (9/9 gates) before any
  microcode reading.
- My own probe shipped a date bug first (`max()` over `DD/MM/YYYY`);
  caught on the second run when 4655's newest patch contradicted the
  manual enumeration that discovered the lens. Fixed; both registered.
- The ACPI gate imported the OVMF expectation and failed; the debug probe
  refuted it at the byte level (zero FACP in the whole image) before the
  gate was rewritten to the measured invariant. A gate is a hypothesis.
- Microcode family attribution is high-byte clustering only; no CPUID
  cross-reference was performed.
- The hidden map's widths keep the ring-20 undercount approximations;
  ranges are upper bounds on hiding.
- 19 patches per specimen is the carrier constant; the clock is the
  membership, not the count.

## What stays open

- The 16/09 day-0 dump decides Q1's live side (§6 screenshots vs the map)
  and the 3644 H3 question; the checklist above is filled to offset level.
- Whether the multiple shipped DSDT variants are per-board-revision or
  per-configuration is not decidable from the image alone.
- The family-B PSP copies question (ring 20's residue) remains
  image-indeterminable by construction.
