# The twenty-fourth ring — Volume 5 rehearses in software

*Lands after rings 9–23. The Volume 5 decision stands as taken in
"volume 5, the sacrificial board" (b9c9b47): the sacrificial bench is a
second used B450 with a CH341A, and porting our PRIME is developer-grade
— not planned. This ring answers the other half of that volume, the
half that needs no chip: build the replacement firmware, photograph it
next to the vendor image with our own instrument, rehearse the flash
cycle end-to-end at file level, and verify every remembered coreboot
candidate against the release we actually built.*

**Status**: docs-only, surface frozen — 323/323 checks, MCP smoke 12
tools, 0 diff on bin/lib/tests. Zero bytes written to any chip; all
scratch work lives outside the repo. One honest wrinkle: this work was
first committed against a stale local clone as a "ninth ring"; the
fetch revealed the real line (rings 9–23 already pushed), the evidence
commit was preserved (`ninth-ring-local`), and the ring renumbered —
the disque/remote reconciliation is itself part of the ledger.

## Front 24a — build the replacement (coreboot 25.12, QEMU q35)

The release tarball `coreboot-25.12.tar.xz` (sha256
`486a737f089f28e16a9dd73566763ff879149784a2cc0ce8cdf6927af8786c94`)
was built for `emulation/qemu-q35` with the SeaBIOS payload, using the
system toolchain (`CONFIG_ANY_TOOLCHAIN`). Result: `build/coreboot.rom`,
8 MiB (`ROM_SIZE=0x00800000`), sha256
`76a0e9c8c22d22603bd55506a35d52741efcc6a22ba4adf089c32011f8fe17d1`,
CBFS inventory verified by the tree's own cbfstool (14 entries: master
header, romstage, ramstage LZMA, config, revision, build_info, dsdt.aml,
cmos_layout.bin, postcar, SeaBIOS payload, payload_config,
payload_revision, empty slack, bootblock).

The build had to cross three toolchain walls without root, and each fix
is an honest, reusable piece of Volume-5 doctrine:

1. **iasl is mandatory, and its absence is cached.** `toolchain.mk`
   demands either the coreboot toolchain or (`ANY_TOOLCHAIN`) any iasl
   found — but the *xcompile generator* additionally greps iasl's
   output for "ACPI" and, crucially, **the result is cached in
   `build/xcompile`**: a first run without iasl on PATH leaves an
   empty `IASL:=` there, and later PATH fixes are silently ignored
   until the cache is purged. Our iasl (20250404) was extracted from
   the acpica-tools .deb already present in the sandbox — zero
   download.
2. **32-bit libgcc is not optional.** The stages link `-nostdlib` but
   rely on `__udivmoddi4` from libgcc (coreboot wraps only
   `__divdi3/__udivdi3/__moddi3/__umoddi3` via `src/lib/gcc.c`). Debian
   without gcc-multilib has no 32-bit libgcc; `LIBRARY_PATH` alone does
   not fix it because coreboot resolves the archive through
   `-print-libgcc-file-name`.
3. **`-print-libgcc-file-name` lies under `-m32`.** Debian's gcc driver
   reports the 64-bit archive even under `-m32`, and coreboot caches
   that wrong path as `GCC_COMPILER_RT_x86_32` in xcompile. The clean
   fix: a compiler wrapper that answers `-print-libgcc-file-name` with
   the 32-bit `libgcc.a` extracted from `lib32gcc-14-dev` (dpkg -x, no
   root), everything else passed through untouched — no coreboot source
   modified.

**Consequence for the bench day**: the flash-day checklist gains three
lines — iasl on PATH *and* a fresh xcompile; 32-bit libgcc present *and*
the wrapper proven before `make`; never trust a cached xcompile after a
toolchain change.

## Front 24b — the first photograph: vendor vs coreboot, same machine

The repo's own instrument photographed all three images at its
documented offline seam (`omarchy-firmware spi-map --dump <image>`):

| image | size | FVs | outer FFS files | census depth (cross-cited) |
|---|---|---|---|---|
| OVMF_CODE_4M.fd (plain) | 3 653 632 | 2 | 6 | 135 files — 115 DXE, 14 PEI, +core |
| OVMF_CODE_4M.secboot.fd | 3 681 720 | 2 | 6 | 144 files — 113 DXE, 17 PEI, 8 SMM |
| coreboot.rom (q35) | 8 388 608 | **0** | 0 | 14 CBFS entries — 6 stages/payload |

The headline is structural: **the two firmwares do not share a
container**. The vendor world is PI firmware volumes (FFS2, nested and
compressed FVs, an 8-module SMM island on secboot — the same island the
rings 16/18/23 dated and certified); coreboot is a flat named CBFS
world whose entire boot identity is
bootblock→romstage→ramstage→postcar→SeaBIOS-payload. The instrument
reports zero FVs on coreboot *correctly* — and that honest zero is
itself a finding: the day a real coreboot board gets photographed, the
instrument needs a CBFS lens beside the FFS lens (rehearsal form
delivered: the cbfstool parse inside `lab/vol5-qemu-photograph.json`).

Two honesty notes travel with the artifact: the OVMF `.fd` files are
CODE-only halves of a 4 MiB split (the NV varstore lives in
OVMF_VARS_4M.fd, outside the photographed image); no flash descriptor
exists on any image (partial region dumps and a descriptorless QEMU
image) — real-board geometry stays a bench-day question.

## Front 24c — the flash cycle rehearsed before it is needed

The doctrine's non-negotiable sequence was walked end-to-end against
files (the "chip" is a scratch copy; the "programmer" is a copy; every
step sha256-logged in `lab/vol5-cycle-rehearsal.json`):

1. dump-first: read twice, hashes agree, archived on TWO media — pass;
2. identify-before-write: the intended image identified and hashed — pass;
3. write + verify-after-write — pass;
4. **the failed-verify branch**: one flipped byte mid-image — caught by
   verify, protocol applied ("a failed verification is a re-clip, not a
   reboot") — pass;
5. rollback: restored from the second medium, hash equal to the
   original — pass.

**5/5 steps pass.** The rollback path has now succeeded once,
deliberately — at file level. The chip-level rehearsal remains, by
definition, an act of the bench (the second B450, when it exists) —
and it will have this rehearsal as its pre-verified script.

## Front 24d — the candidate matrix, verified against the tree

Every remembered coreboot candidate was re-verified against
`src/mainboard` of the release we just built (the authoritative port
list for 25.12; the web status page 404s today and was not needed).
Three results, all material (`lab/vol5-board-matrix.json`):

- **Discovery — `framework/azalea` is the Framework 13 AMD 7040.** An
  in-tree coreboot port on an **AMD/AGESA** machine: the study's
  PSP lens (built on the TWIN-1's B450-PLUS across rings 11–23)
  transfers directly. **Primary candidate** for the "which machine
  could ever RUN coreboot" question.
- **Two AM4 refutations.** `asus/` holds zero AM4 boards in 25.12
  (confirming the doctrine's "no port" and the bench decision); and
  **the ASRock Rack X470D4U — the research README's "Rack X470D4U +
  coreboot" lane B — is ABSENT from 25.12** (zero hits for x470d4u
  across `src/` and `Documentation/`; `asrock/` holds 21 Intel-era
  boards plus h110m, imb-1222, spc741d8). The two AM4 absences close
  the "coreboot on our audited platform" shortcut: pursuing X470D4U
  means pinning an older coreboot or a fork — a maintenance cost the
  lane decision must own.
- **T440p demoted** (absent from 25.12, same evidence class as the
  X470D4U check — absence in tree is evidence of the release's
  supported set, not of history); System76 confirmed strong (13
  in-tree model dirs, factory lane); x230 confirmed (pre-Boot-Guard,
  maximal maturity — **the school**); bonus lane `asus/h610i-plus-d4`
  proves consumer-ASUS coreboot exists (LGA1700, maturity to verify).

The two questions are now cleanly separated: the **bench** (a second
used B450 — flash experiments on the audited platform, bit-exact
against the ring-16/18/23 registers) and the **coreboot-capable lane**
(a different machine entirely — azalea first, x230 as the school).
Neither touches the guard fleet; +0 octet holds.

## Honesty ledger

- Proven: the build (all three toolchain walls documented and
  reproducible from `scripts/vol5_build_coreboot.sh`); the container
  contrast (instrument + cbfstool outputs, hashes recorded); the cycle
  rehearsal (5/5, failed-verify branch exercised); the tree-level port
  matrix including both AM4 refutations.
- Flagged: "port in tree" is not "port matured" — S3 quality, memory
  training and EC quirks need board-status data at purchase time;
  price/availability deliberately out of scope (the study does not
  shop); QEMU boot of the built image is registered, not performed (no
  QEMU binary without root — the next software lever); the ring-number
  wrinkle of this very ring is registered above, not smoothed over.
- The ledger self-corrects again: the doctrine's candidate table said
  "Framework 13/16, the smoothest modern path" without knowing the
  platform; the tree says the in-tree Framework is the AMD one. The
  research README's lane B said "Rack X470D4U + coreboot"; the tree
  says the port is not in 25.12. Both corrections are the tree's
  answer, not a theory's.

## Consequences for day-0 (16/09) and the bench

- Day-0 protocol unchanged: `capture --live` → `rehearse` →
  `rehearse-diff --latest`, optional `spi-map --save-dump`; the dump
  remains the recovery path AND the control group.
- The bench-day checklist gains the three toolchain lines from 24a and
  the file-level rehearsal script from 24c.
- The instrument's future CBFS lens (24b) is registered as the
  Volume-5 code task that respects the frozen surface (additive, tiers
  intact).
- The purchase decisions now carry evidence: the bench per the Volume-5
  decision; azalea first and x230 as the school for the coreboot lane;
  X470D4U only at the price of pinning history.
