# The forty-third ring — les propositions (the last manual surface meets the machine)

Date: 2026-09-14 (session of 2026-09-13/14). Preceding state: ring 42
(`e1b3d29`), the day-0 protocol already welded into one command. This
ring's summary drifts #27 and #28 were radiated at the checkpoint: the
continuation summary described ring 35 plus a pending recommendation
while the disk stood at ring 42 — eight rings ahead, no ghost work.

## The hole

After ring 42 the day-0 protocol is ONE command (`fw42-dossier.py
dossier dump.rom` + labeled lenses) — but seven slots remain LENS_ONLY
in the fw40 weld, and fw40's law is strict: the machine never invents a
lens value. Seven slots means seven manual pastes: seven chances for a
transposed digit, a skipped row, a stale hash — the exact failure class
the ring-38/40/42 welds exist to remove. The seventh ring report itself
named the residue: *the operator pastes them by hand*.

This ring removes the PASTE, not the operator.

    proposal = a machine-drafted value for a manual lens slot, produced
    by a proposer whose method has been CALIBRATED against the frozen
    registers, and which the operator confirms or corrects before the
    weld. A proposal is not a measurement; the slot is still the
    operator's.

The instrument was found on disk as an untracked draft
(`lab/fw43-proposal.py`, laws and modes complete, live gates failing,
calibration register absent) — a parallel session's scaffold. This
session completed it: five grammar discoveries stood between the draft
and the register, each caught by a live gate before anything froze.

## The instrument

`lab/fw43-proposal.py` (TRACKED, fw33/35/36/37/38/39/40/41/42
precedent), stdlib-only over the frozen surface. Two proposers cover
the seven LENS_ONLY slots exactly:

- **PSP proposer** (3 slots: `psp_hashes_3644`, `psp_hashes_3604`,
  `psp_hashes_3802`): the registered layout (vendor-psp.json
  `layout_registered`) — 16 B directories (cookie, fletcher32, count),
  16 B entries, four address modes, one L2 hop; every entry body hashed
  sha256_16, the body-hash SET emitted. The dump's set fills the 3644
  slot (day-0's hypothesis); the on-disk 3604/3802 rungs fill the
  comparison slots with the SAME method — the P-19 checker needs one
  convention, and the calibration rows are the authorship register's
  own counts (14 dirs, 223 bodies, 10 skipped, by_magic 5/2/5/2).
- **IFR proposer** (2 slots) + **varstore cross** (2 slots):
  `ifr_questions_total` / `ifr_valid_fraction` from the ring-6
  exact-consumption walk over the fw39 deep walk (memoized — the
  ring-42 one-walk-per-image weld), and `setup_uncovered_bytes` /
  `varstore_uncovered_share_pct` from the ring-20 coverage cross.

Four laws, each a gate family: **L1 proposal-not-measurement** (the
document's keys are exactly fw40.LENS_ONLY, auto-derived; judge-owned
slots NEVER proposed; fed to the weld the proposals land as ordinary
lenses), **L2 calibration-before-proposal** (a slot is proposed only if
its proposer reproduced every registered row that applies — one
disagreement and the group is BROKEN, refusal exit 2), **L3 loud
degradation** (an image where a proposer cannot run yields an omitted
slot WITH the reason — never a null, never a guess), **L4 zero writes**
(read-only on images; the only files written are the `--out` pair, and
a grep-level gate polices the source itself).

Modes: `propose <image> [--out proposals.json]` (the day-0 proposals +
review table + sidecar report with provenance/omissions),
`verify <rung>` (proposer-vs-register, row by row — the calibration
evidence), `selftest` (two-tier), `manifest`.

## The calibration war — five grammar discoveries

The live gates referee against registers frozen by rings 19 and 20
(vendor-ifr-census.json, vendor-unasked.json). The draft failed them
six ways; each failure was a real grammar fact. In the order they fell:

1. **The names were never in the image.** The big IFR modules (Setup,
   CbsSetupDxeZP/RV/SSP/RN, UefiRaid, AodSetupDxe) carry NO UI sections
   anywhere — not in the raw plane, not in the pierced blobs, not on
   any of the 38 corpus roms (one UI-named FFS per ASUS image, two in
   the deep walk: TlsAuthConfigDxe, Ip4Dxe). Ring 19 had said so all
   along: `vendor-versions.json guid_join` — precedence ovmf-ring9 >
   manual-ring9 > ui-asrock > ui-gigabyte > ui-msi — named the ASUS
   copies by cross-board join. The proposer now sources names from that
   register (`asus_main_modules_named`, 600 rows) as a provenance
   fallback. I2 (Setup module == 3130/241/6001) passed the moment the
   join was wired.

2. **The scope law.** The draft's cross merged varstores by vs_id
   GLOBALLY — 58 varstores found where the register froze 71, and a
   bogus "Setup" row (size 7, 524 beyond, GUID 2e20e180…) where the
   register froze 456/314/368/0. The register's own `top_varstores`
   showed the truth: FOUR same-GUID AmdSetup rows with different sizes
   — each HII package LIST is its own form set with its own vs_id
   space. Scopes became per-package-list. The count still came up one
   short (70): the three byte-identical AodSetupDxe copies share
   PE-relative list offsets, so their scopes collided and one
   AOD_SETUP row collapsed. Fix: census keys and scopes are
   INSTANCE-unique (`i{inst}:…`) — same-name modules merge into one
   census row (the totals count every copy) while every instance keeps
   its own form-set space. 71/71.

3. **The EFI varstore layout is ring-20's, not the modern spec's.**
   One `0x26` def on 4655 parses to garbage under the EDK2 layout
   (vs_id +18 = the GUID's tail, size +22 = 0, name utf-16 = the
   mojibake "捔乧浶噥牡" that decodes to ASCII "GdgNvmeVar" read as
   utf-16). The stream's real fields sit at +2 (vs_id) and +24 (size)
   with the GUID at +4 and an ASCII name at +26 ("TcgNvmeVar", len 37)
   — the ring-20 convention the draft had inherited and this session
   first "corrected" then had to restore. The register is the grammar's
   referee, not the spec table: under ring-20 offsets the store joins
   vs_id 19's two NUMERIC questions and lands size 2 exactly where the
   register froze it. Modern-spec offsets match no registered aggregate.

4. **Straddlers contribute nothing.** A binding that leaves the store
   (`o >= size` or `o + w > size`) counts as `offsets_beyond_size` and
   contributes ZERO to the coverage union — no partial clamp. The
   register's MyRCVirtDisks rows froze 157 where clamp semantics gave
   159 (one w-4 question at the boundary).

5. **The ONE_OF law: the default option's width governs.** The deepest
   divergence took five hypotheses to pin. The ring-20 honesty note
   says "ONE_OF takes its widest option type" — but the register's own
   numbers disagree: widest gives MyRCVirtDisks 159 and MyIfrNVData 143
   where the register froze **157** and **136**; pure width-1 gives
   4131 where 3604 froze 4194. The grammar that reproduces all four
   registered specimens EXACTLY (3604 4194, 4655 4356, Gigabyte 3255,
   ASRock 3452): **a ONE_OF binds the width of its DEFAULT-flagged
   option's type** (flag 0x10, widest when several; fallback widest of
   all attributed options; nothing attributed → 1). Semantically this
   is the honest reading — the store holds the default value, so the
   default's width is what the varstore bytes must house. The note
   described the intent; the register froze the machine. The deviation
   is registered here, the registers stay frozen, and the KAT (R7b)
   pins the law: a NUM16 option flagged 0x10 binds width 2.

Two smaller catches, pre-freeze: the R6/R7 KAT streams were internally
inconsistent with their own gates (the ONE_OF lacked the scope bit its
gate demanded; the option type was 0x02 where the gate name said
NUM16; the binding sat outside the varstore it exercised) — repaired
as `0x8D`/0x01/offset 0x00 before anything froze; and the R9 gate was
self-referential (its grep needles matched the gate's own source) —
the needles are now built split. One spec corner got hardened with its
own gate (R6c): `Length:7 == 0x7F` WITH the scope bit (raw 0xFF) still
opens a scope — the bit lives in byte 1 of both header forms;
corpus-neutral (the exact-consumption totals prove no 0xFF ops in the
corpus streams) but honored.

One deviation registered, register frozen: on the MSI specimen my
cross derives 165 varstores / 41 889 B where the register froze
88 / 26 303 — the ring-20 MSI row was produced under a different scope
method than the other four specimens (its own validation gate gates
question totals only, 8 646 hist). The ASUS/TUF/gigabyte/asrock
specimens reproduce exactly; MSI's row is ring-20's own artifact and
stays as written — the proposer's MSI reading is the more conservative
one, and day-0 does not consume MSI rows.

## The calibration register

`lab/vendor-proposal-calibration.json` (via
`scripts/ring43_artifact.py`, resume-safe one-write): **47 rows, 45
agree, 0 disagree, 2 notes** — status psp/ifr/cross all `calibrated`.
Collected through `fw43.verify()` ITSELF: the same code path the
proposers run is what gets calibrated, so a rerun that disagrees with
the register is a loud L2 refusal, never a silent re-base. The rows:
3604 (psp 5 + ifr 5 + cross 10), 3802 (psp 5 + 2 notes), 4655 (psp 5 +
ifr 5 + cross 10). Every Setup-row field, every census total (7 975 @
3604, 8 273 @ 4655), every PSP count (14/223/10, by_magic 5/2/5/2)
reproduced to the digit.

## The gates — 38, two tiers

Tier R (19, no corpus): R1 the LENS_ONLY contract is auto-derived (7
slots); R1b every slot mapped to a proposer group; R2/R2b judge-owned
and foreign keys refused; R3/R3b/R3c calibration statuses (all-agree →
calibrated, one disagreement → BROKEN, no rows → uncalibrated and L2
refuses); R4/R4b loud degradation on synthetic images (zero dirs, zero
packages — omitted, not guessed); R5/R5b/R5c the fletcher32 PSP KAT
(synthetic directory validates, corrupted checksum rejected, body
hashed from the resolved address); R6/R6b the IFR walk KAT (exact
consumption, truncated stream invalid); R6c the extended-header scope
corner; R7 the scoped walk attributes the option to its ONE_OF; R7b the
cross KAT (default-option NUM16 → width 2, coverage 2/8); R8 the
fraction stays a fraction; R9 the only writes are the --out pair.

Tier I (19, live on the corpus): I1 ×5 the census totals on asus-ref ==
ring-19 register (64/64/779/7975/18222); I2 the Setup module row
(3130/241/6001); I3 ×5 the cross aggregates on asus-ref == ring-20
register (71/26027/4194/83.89/10); I3b the Setup varstore row
(456/314/142/368/0, GUID ec87d643-eba4-4bb5-a1e5-3f3e36b20da9); I4/I5
the PSP counts on 3604 and 3802 == authorship rows; I6 propose emits
only LENS_ONLY keys (7 slots, 0 omitted); I6b/I6c the PSP and IFR
groups propose on the calibrated corpus; I6d every proposal survives
the weld unchanged; I6e the weld journals them as lenses (law L1's
proof through fw40's own machinery).

## Day-0 usage

    python3 lab/fw43-proposal.py propose dump.rom --out proposals.json
    # read the review table; confirm or CORRECT each slot
    python3 lab/fw42-dossier.py dossier dump.rom --lenses proposals.json

`propose` fills all seven manual slots (psp_hashes_3644 from the dump
itself, psp_hashes_3604/3802 from the on-disk rungs, the IFR quartet
from the walk+cross), prints the provenance of each, and writes the
sidecar report (`proposals.json.report.json`) with the calibration
status and the omissions-with-reasons should any slot refuse. The
operator's remaining act is REVIEW: corrections beat proposals, always
— a corrected value passed as `--lenses` outranks the proposal by
fw40's precedence law, and the weld journals it. The judge-owned slots
(matches_known_release, distinct_fingerprints_count,
trust_cert_distinct) are NEVER proposed — fw39 fills those.

Release-41 needs no proposals (the pair path fills its own keys) —
`propose` is the day-0 instrument.

## Honesty ledger

- Summary drifts #27 and #28 radiated at this ring's checkpoint (the
  continuation summary described ring 35 while the disk stood at ring
  42; #21–#26 were already radiated by the Tasks 34–39).
- The instrument arrived as an untracked draft from a parallel session;
  this session completed it and the completion is the ring. The five
  grammar facts above were caught by live gates BEFORE the register
  froze — the draft's "corrections" (modern-spec EFI offsets) were
  themselves reverted when the register ruled.
- The ring-20 honesty note's "widest option type" does not survive its
  own register (finding 5). The note stays as written — registers and
  their notes are frozen artifacts; the deviation lives here.
- The MSI specimen diverges (165/41889 derived vs 88/26303 frozen) —
  registered as a ring-20 scope-method artifact; day-0 consumes no MSI
  rows.
- The proposer inherits the corpus's own conventions: names from the
  ring-19 join (provenance, not invention), widths from the register's
  effective grammar (default-option rule), scopes from the register's
  own row structure. Where the register is silent (MSI), the
  instrument says so loudly instead of guessing.
