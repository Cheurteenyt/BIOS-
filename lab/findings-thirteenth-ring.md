# The thirteenth ring — the two lenses (2026-09-11)

> Companion to rings one through twelve. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `ring13_versions.py`,
> `ring13_psp.py`, `ring13_artifact.py` (sandbox; the ring-11/12
> walker imported verbatim — no grammar was rewritten; the PSP type
> tables and fletcher32 are imported at runtime from the psptool 3.6
> package, GPL-3.0, Hardware Security Group Hamburg — transcribed
> from no memory). Artifacts: `vendor-versions.json`,
> `vendor-psp.json` (this repo). The directive: the VERSION-strings
> lens — recover the names ASUS strips — and the PSP lens that rings
> 11-12 counted but never opened.

## Front A — the VERSION-strings lens refutes itself

Ring 12 measured the blindness (ASUS 4655: 600 modules, ONE
USER_INTERFACE section — named share 0.002 — against 384 VERSION
sections) and registered the 0x14 strings as the candidate next
lens. This ring built that lens and let it measure its own
hypothesis.

- **The decode convention is decided by the bytes.** Every 0x14
  section on all five specimens was decoded under BOTH conventions —
  string at +0, string at +2 behind a BuildNumber u16 — and both
  outcomes kept as evidence. The verdict is total: **1,992 sections
  in the five main regions (2,359 across every region of every
  image), 100 % match the PI-spec layout (str@2) only** — zero match
  @0 only, zero ambiguity. The spec holds uniformly across MSI,
  Gigabyte, ASRock and both ASUS releases.
- **The strings are not names.** Across the five main regions the
  0x14 layer carries **eight distinct strings**, seven of which are
  placeholder build numbers (`1.0` ×1,860, `0.0` ×38, `1.1` ×46,
  `2.0`, `7.0`, `0.1`, `000001`). The measured "recovery" from 0.002
  to 0.700 on ASUS is a false recovery — the sections name nothing.
- **The ring-12 candidate is therefore REFUTED by its own
  measurement**, and that is the finding: the ASUS nameplate
  blindness is structural to the packaging, not curable from the
  VERSION layer. The lens that was supposed to recover the names
  proved the names are not there.

One string in the vocabulary is real, and it carries a story — see
the UefiRaid case below.

## Front B — the names recovered anyway: the GUID join

If ASUS strips the names, the other boards kept them — and ring 12's
quorum matrix already showed the living lines share 70-78 % of their
module GUIDs. The names are recoverable by identity:

- A **665-GUID name map** was built from four sources, in registered
  precedence: the ring-9 OVMF curated map (209), the ring-9 manual
  nameplate, and the UI sections of the ASRock, Gigabyte and MSI
  censuses. The conflict rule compares base names only — provenance
  suffixes (`[edk2 master]`, `[census module]`) are not conflicts.
- Result: **two pseudo-conflicts, zero real disagreements**.
  `gUefiShellFileGuid` (OVMF) vs `MinShell` (MSI's UI) is the same
  Shell module named by context; `PcdPeim` with and without its
  source path is a precision difference, not an identity one.
- **ASUS 4655: named share 0.002 → 0.593** (DXE 260/314 = 0.83,
  SMM 91/106 = 0.86); ASUS 3604: 0.002 → 0.591. The 600-row named
  register (`asus_main_modules_named` in the artifact) is the day-0
  table: every module with its GUID, phase, size, version string,
  join name and the source that named it.
- The residual 244 unnamed modules are the vendor-proprietary layer
  (freeform AGESA pieces, AMI-only hubs) — the same residual every
  board shows against the EDK2 core.

**The UefiRaid case** — the one VERSION-string that is real, and the
only one that changed in four years: `C74F06D2` moved from the
placeholder `1.0` (3604, 2022) to `9.3.0.00308` (4655, 2026) — the
exact version ASRock, Gigabyte and MSI already ship, and the same
GUID that their UI sections name `UefiRaid`. The GUID join
identifies the module the version string talks about; the version
string dates the update. ASUS's RAID driver caught up with the
quorum between those two releases.

## Front C — the PSP lens

Rings 11-12 counted `$PSP` magic hits (13 per 16-MiB image) and
registered `$BSP: 0` as an unexplained zero. This ring opened the
tables.

- **The ring-11 zero is closed by source, not by assumption.** The
  verified magic list (imported from psptool 3.6) is `$PSP`/`$PL2`
  for PSP directories and `$BHD`/`$BL2` for BIOS directories —
  `$BSP` exists in no generation this instrument knows, and `$BIO`
  scans zero everywhere too. The ring-11 search was chasing a magic
  recalled from memory; the ring-13 search chased the right two.
- **Every parsed directory validates.** fletcher32 over
  header+body matches the stored checksum on **all 74 directories
  across all five specimens** (18 MSI, 14 each on the four 16-MiB
  images); every entry resolves inside the image; the L2 pointer
  types (0x40/0x49/0x70) are followed one hop. The layout
  constants — 16-byte PSP entries, 24-byte BIOS entries, the four
  address modes — are proven against real vendor silicon, not
  assumed from a spec page.
- **Full agreement with the reference implementation**: 74/74
  directories agree on magic and entry count with psptool after
  joining on file offsets. The join itself was a found lesson: on
  the 32-MiB MSI image, psptool's dict keys are masked address
  labels (`0xd1000`) while `get_address()` carries the true file
  offset (`0x10d1000`) — the same directory, two coordinate
  systems, and the `repr` itself admits it
  (`Directory(address=0x10d1000, ...)`).
- **The PSP layer churns where the packaging stands still.**
  Cross-release, same types present, none added or removed, but 38
  of 75 blob contents changed between ASUS 3604 and 4655 while the
  UEFI VERSION strings went 414/415 stable: PSP_FW_BOOT_LOADER
  (five instances), PSP_FW_TRUSTED_OS, SMU_OFFCHIP_FW and
  SMU_OFF_CHIP_FW_2 (some instances byte-identical across four
  years, others replaced), ABL0-ABL7, SEC_GASKET, DRIVER_ENTRIES,
  TOS_SECURITY_POLICY, DEBUG_UNLOCK all move. A BIOS release is a
  PSP release wearing a mostly-frozen UEFI coat.
- **Constants worth naming**: `PspFtpmHandler` appears in every
  specimen's boot-time trustlets — the fTPM stack is
  vendor-independent AMD code, so the study's fTPM/TPM-stutter
  lineage applies at this layer to all four boards alike. The
  bootloader strings name the key machinery (DRAM encryption keys,
  HMAC keys, NV-storage keys, per-SPI RPMC root keys) — the trust
  surface the UEFI layer never shows.

## The auto-correction chain

- The first probe of 0x14 sections at the top level of the main FV
  returned nothing — VERSION sections live **inside the pierced
  inner FVs**. Probe before parse; the blindness is nested.
- The crosscheck initially compared "main vs main" and flagged MSI
  453 vs 469. The walkers were proven identical side-by-side
  (453=453, zero set difference); the real cause: the
  densest-region pick landed on the MSI **mirror** (@0x1601000,
  469 modules) while the ring-11 baseline is the original
  (@0x59f000, 453). Fixed to region-by-offset comparison — 4/4
  exact — and the mirror asymmetry itself became a finding.
- The GUID-map heuristic required `count("-") == 5` — a GUID has
  **four** dashes. Caught by the map-not-found assertion before
  any number was produced. Even heuristics get the
  never-from-memory treatment now.
- The decode convention initially short-circuited on the first
  matching variant (biasing toward @0); restructured so every
  section carries both candidates as evidence and the ratio
  decides. On this data the outcome was unanimous either way —
  but the method must not depend on that.
- psptool's `get_buffer()` on a Directory returns the whole ROM
  wrapper, not the directory slice — the byte-proof of the join
  came from magic+count+repr instead of a naive buffer diff.
- An `acc` dict missing the `named_union` key died on the first
  inner-FV module — the KeyError was the fix's own smoke test.

## Honesty ledger

- Join names are **identity claims, not semantics**: same GUID,
  same module — vendors may still configure the same module
  differently. The artifact says so on every row.
- VERSION strings are vendor labels; none was verified against
  module behavior. The one informative string (UefiRaid's
  `9.3.0.00308`) is a claim the bytes carry, not a fact about
  behavior.
- The MSI double-structure asymmetry is **registered, not
  explained**: the mirror's big inner FV is 0x97000 bytes longer
  with 16 more files, the halves' PSP directories validate at
  different depths (the mirror of the primary `$PSP` at 0xa8000
  holds no `$PSP` — the bytes there spell `2PSP`), and ten
  directories validate only in the upper half. Root cause not
  chased this ring.
- PSP blobs are fingerprinted (sha256_16, head bytes, embedded
  strings), never executed or emulated.
- The instrument parses what a magic scan plus one L2 hop reaches;
  it does not reconstruct the vendor FET chain — psptool remains
  the authority for FET-level questions, and it agreed 74/74.
- One run per lens, like rings 11-12 — the ring-10 reproducibility
  ritual has not been applied to vendor pipelines yet.

## Consequences for day-0 (16/09)

- **The dump has a name pipeline now.** If the day-0 image is
  ASUS-class packaging (UI-stripped), the GUID join map is built
  and ready: expect ~59 % named immediately, DXE/SMM near 85 %,
  with the residual confined to the vendor-proprietary layer.
- **The PSP tree parses verbatim.** The lens runs on any AM4 image
  without re-derivation: magic scan, fletcher32 validation, 16/24
  byte entries, cross-check against psptool. The dump's PSP layer
  gets the same 74-directory treatment.
- **New decision inputs for the 3644 question**: the UefiRaid
  version string and the PSP blob fingerprints are two more
  per-release fingerprints the dump can be matched against — the
  release identity question now has hardware-grade evidence paths.
