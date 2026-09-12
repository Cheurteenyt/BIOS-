# The thirty-sixth ring — la cartographie du delta

> The ring-34 differ says WHICH modules change; this ring maps WHERE and
> HOW in the raw image — and finds that the raw image lies by three hundred
> thousand to one.

## What was built

Two artifacts and one tracked instrument (the fw33/fw35 precedent),
zero downloads, zero hardware — the OVMF corpus survived the sandbox this
time and paid for it:

- `lab/fw36-atlas.py` — stdlib-only, two-tier selftest (14/14 PASS, tier I
  live): tier R re-derives every anchor from the ring-34 registers; tier I
  re-derives them LIVE on the surviving corpus and is loudly SKIPPED when
  it is absent. Modes: `atlas` (multi-scale entropy fingerprint, raw
  `_FVH` scan with checksum validation, 0xFF slack, NVAR census), `delta`
  (byte-run cartography: gap-clustering at 64 B, structural classes from
  window-entropy pairs, 64 KiB density map), `vars`, `manifest`.
- `lab/ovmf-geometry.json` — the first OVMF-side geometry (the
  vendor-geometry counterpart): FVMAIN_COMPACT 0x0-0x348000 + SECFV
  0x348000-0x37C000 on every CODE build, checksum-valid; VARS_4M a single
  NVRAM FV; plain 52.02 % erased / 43.05 % packed, secboot 48.43/44.84 —
  the rebuild wall is INVISIBLE to layout (same size, same FVs) and
  visible only to bodies.
- `lab/ovmf-delta-map.json` — three raw cartographies under the ring-34
  module ledgers, each cross-cited.

## The discovery: the compression lies, by 322,734 to one

The register's NX truth is 3 semantic bytes (BdsDxe 1 + IScsiDxe 2, in
decompressed module bodies). The RAW whole-image diff of the same two
builds is **968,203 bytes in exactly 2 runs** — an amplification of
**322,734×**. The anatomy is precise:

1. run @0x88, **9 bytes** — FV-container metadata (including a `dc→cd`
   nibble-swap class delta);
2. run @0xa8409, **968,194 bytes** — the LZMA stream tail re-encoded from
   the first compressed semantic change, ending exactly where the
   compressed section ends (identical padding resumes beyond).

The lesson for day-0 is structural, not incidental: **a raw byte diff of
compressed firmware measures the container, not the content.** Any
semantic change inside FVMAIN_COMPACT rewrites the tail of the LZMA
stream; the ratio between raw and semantic deltas is a property of the
stream position, not of the change. The CAP comparator keeps its order:
identity classes → module ledger (semantic) → byte pins (semantic,
decompressed) — and the raw cartography's job is to LOCATE container
change, never to count it.

## The uncompressed window: SECFV tells the truth

The wall's raw map (plain↔secboot: **1,657,607 bytes in 26 runs**,
28/56 blocks changed) decomposes into exactly two regimes:

- @0x5af7, 1,634,053 bytes — the LZMA tail carrying the whole semantic
  wall (120 changed modules + 18 SMM births + 9 removals);
- **~23 KB inside SECFV (0x348000-0x37C000), UNCOMPRESSED and therefore
  raw-visible**: the 22,104-byte SEC-core body run @0x34be5c plus ~20
  small pointer runs shifted by −9/−16 bytes — relocation deltas of two
  compilations of the same SEC source with slightly different layouts.

**Any rebuild changes SECFV; no decompression is needed to see it.** A
raw-cartography hit inside SECFV is a build-difference signal that day-0
can read in seconds, before any module walk.

## The stores and the clocks

- VARS ms↔snakeoil: PK/KEK/db differ as **ONE contiguous raw run of
  7,309 bytes** (the auth-key block); dbx byte-identical (ring 34) holds
  — absent from the map. The 39-record stores differ in one slab.
- VARS plain: 100 % erased at 64 KiB, the store header alone breaking the
  0xFF tail at 0x42fe0 — the blank-store shape.
- **The NVAR clock is AMI-specific**: NVAR magic census = 0 on every
  OVMF image (auth-variable store, GUID AAF32C78); the 18–19 counts in
  vendor-geometry.json are AMI-build artifacts. Registered as a boundary
  on a first-hour read before day-0 tries it on the vendor dump.

## The second verse of the identity class

`OVMF_CODE_4M.ms.fd` and `OVMF_CODE_4M.snakeoil.fd` are **symlinks** to
`OVMF_CODE_4M.secboot.fd` (23-byte links, Debian packaging). The ring-34
class `1a462955` {secboot, snakeoil, ms} is one file under three names —
proven at filesystem level, one depth below the hash coincidence. The
enrollment-is-data doctrine (ring 5) gains its mechanism: the package
never compiled three CODE images.

## Honesty ledger

- Proven: 14/14 selftest gates (tier R + tier I live); the amplification
  anatomy (2 runs, positions, window classes); the SECFV decomposition;
  the single-slab VARS delta; the symlink topology.
- Registered, not resolved: the exact sub-FV structures at 0x19xxxx where
  the NX big run ends (identical-padding boundary); the reason the two
  builds' SEC layouts differ by 9/16-byte pointer steps (compiler phase
  ordering — a rebuild-wall mechanism, not a policy delta).
- Skipped loudly when the corpus is absent: the six tier-I gates (the
  instrument refuses to pretend).
- Zero bytes written to any firmware object, zero downloads.
