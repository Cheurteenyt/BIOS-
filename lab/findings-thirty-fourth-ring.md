# The thirty-fourth ring — the differ, re-derived

*A stale clone, a collision with history, and a fresh instrument walked
over ground already measured — and agreed with it. The reconciliation is
the finding; the confirmations are its proof.*

## The reconciliation (the honest wrinkle, second verse)

This ring was first committed against a **stale local clone** (still at
the eighth ring) as a "ninth ring" — complete with artifacts, a findings
file, and a Volume 5 software preparation. The fetch then revealed what
the remote already knew: rings 9–33 exist, and the twenty-fourth ring
lived this exact wrinkle before ("first committed against a stale local
clone as a ninth ring; the fetch revealed the real line"). The evidence
commit is preserved as tag `thirty-fourth-ring-local`; the ring is
renumbered; the redundant Volume 5 preparation (a readiness ledger and a
runbook the rehearsal state of rings 24–26 had already surpassed — the
flash cycle was already rehearsed 5/5 at file level, coreboot 25.12
already boots a real OS under QEMU) is **dropped from the tree** and
survives only in the evidence tag. The disk has priority — but the disk
is the repository, not one clone of it.

## What the fresh differ is

One stdlib-only probe (`ring9_differ.py`, sandbox-side per doctrine)
fusing four capabilities into one pass: whole-image sha256 identity
classes → GUID-aligned module ledgers per pair → run-clustered byte pins
for same-size module deltas → an auth-variable-store walk. Its outputs
are three JSON artifacts (`ovmf-constellation.json`, `ovmf-nx-pin.json`,
`ovmf-vars-differ.json`), renumbered and cross-cited against the prior
rings they re-measure. The value proposition for day-0 is exactly this
fusion: the vendor CAP comparison needs all four granularities in one
run, ordered as one pipeline.

## The re-derivations (all four agree with the ledger)

**Ring 4's rebuild wall, confirmed exactly.** plain↔secboot: 126 common
modules, **6 byte-identical, 120 changed**, +18/−9 uniques —
`ovmf-build-delta.json`'s numbers, reproduced from scratch by a
different walker. The wall holds: enabling secure boot recompiles the
platform.

**Ring 5's enrollment-is-data, extended to whole images.** The three
sha256 identity classes are `624e06de` (plain), `1a462955`
(**secboot == snakeoil == ms**, byte-identical images), `9ee9f238`
(strictnx). The CODE carries no key material — not per-module
(ring 5's 144/144) but at the level of the whole flashable object.

**Ring 3's three bytes, re-derived blind.** strictnx vs secboot: 144
common, 142 identical, 2 changed, zero size delta — `BdsDxe` `0x01→0x00`
(one byte, inside .text) and `IScsiDxe` `66 2E → 00 66` (two bytes: the
same alignment-NOP re-encoded one prefix earlier). Ring 3's offsets
(0x8AB7 / 0x171AA-AB) and this probe's runs (`@35487` / `@94610`)
locate the same bytes from different base conventions; the reading
added here is the assembler's: a one-byte policy change leaving a
two-byte NOP-padding fingerprint behind.

**Ring 2's VARS walk, confirmed with sharper state resolution.** Both
populated stores: 39 records, 21 live, 18 not-live — ring 2's census
exactly. The decomposition goes one byte deeper: 17 records at `0x3C`
(deleted-after-transition) and 1 at `0x3D` (replaced), and the replaced
one is **BootOrder — whose newest record has no live successor in the
store**. Ring 2 read 18 deleted; the differ's histogram splits the class
and registers the BootOrder anomaly as an open observation (a packaging
snapshot taken mid-cleanup, or a successor that never shipped in this
region). Also made explicit here: the 60-byte auth record header —
StartId/State/Attr + a 28-byte auth zone + NameSize/DataSize/GUID —
carries **no PublishSequence field**, derived on live bytes (debug4–7
persisted), and `dbx` is **byte-identical between the ms and snakeoil
stores** (76 B — the same single empty-string SHA-256 revocation,
`e3b0c442…`, already visible in ring 2's keyring, here stated as the
cross-image invariant it is).

## Consequences for day-0 (16/09)

1. **The differ pipeline is the CAP comparator**: identity classes first
   (is the "update" even a different build?), module ledger second
   (rebuild wall expected — vendor deltas will be ledgers, not patches),
   byte pins third (reserved for same-size pairs, where they shine —
   ring 16's lesson on the vendor ladder, here proven on OVMF too),
   var-walk last (the vendor NVRAM census before anything overwrites it).
2. **The state-byte decomposition joins the day-0 NVRAM protocol**: count
   `0x3C` and `0x3D` separately; a replaced-without-successor record is
   a snapshot-timing signal, not noise.
3. **The confirmation discipline works**: four prior rings' claims,
   one fresh instrument, four agreements — and the corpus passed. The
   standing rule survives: *every claim byte-derived, every instrument
   re-derivable*.

## Honesty ledger

- Proven: the four re-derivations above (artifact + prior artifact,
  numbers agreeing to the digit).
- New: the identity classes at image granularity; the `0x3C`/`0x3D`
  split and the BootOrder nuance; the dbx cross-image invariance as an
  explicit statement; the fused differ pipeline itself.
- Registered, not resolved: the exact EDK2 semantics behind BootOrder's
  `0x3D` newest record; the offset-base convention difference between
  ring 3's rel addresses and this probe's FFS-body runs.
- Dropped: the Volume 5 preparation files of the evidence commit
  (redundant with rings 24–26's rehearsal state — the tree stays true).
- Zero bytes written anywhere; the probe scripts and four debug scripts
  stay sandbox-side per the tracked-knowledge rule.
