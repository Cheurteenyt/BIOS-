# The forty-eighth ring — the full-axis pair witness (2026-09-15)

> Companion to rings one through forty-seven. Same campaign, same
> rules: read-only over downloaded vendor images, zero bytes written
> anywhere but the lab record. Instruments this ring:
> `fw48-pairaxes.py` (TRACKED, new) composing on the unchanged
> fw37/38/39/41/43/45/47 machinery. Artifact:
> `vendor-pairaxes-register.json` (this repo, via
> `scripts/ring48_register.py`), one write, assertion-gated,
> roundtrip-checked. The trigger: the ring-47 pair witness reads the
> PSP axis only — the release's other content axes were pair-blind,
> and the 16/09 dump deserves the whole axis map, not one axis of it.

## Front A — the axis map, measured on three pairs

fw48 extends the set lens from the PSP axis to the five non-PSP
content axes of the novelty walk — the DER trust set (`certs`), the
checksum-valid DSDT variants (`dsdt`), the extracted whitelist
including the fan vocabulary (`whitelist`), the SMM-typed GUID set
(`smm`), and the AGESA level set (`agesa`) — and derives each pair's
SIGNATURE from the full evidence {axis deltas, species births/deaths}.
Three pairs measured (66 s / 65 s / 39 s):

- **The release pair (3644 → 3645)**: psp +37/−37 (the lens anchor,
  reproduced), **certs +1/−1 — one DER certificate rotated
  (`2da09da7f4131f9f` → `4aa03fa22cd75c84`) inside a stable count of
  6** — the count witness reads `==` while the set reads `!=`, the
  ring-46 blindness class caught on a NEW axis at pair level — and
  dsdt, whitelist, smm, agesa all exactly `==`. Container 0/0 (18
  modules, −992 B, reproduced). Signature: **multi-axis-swap**.
- **The board pair (3644 ↔ nw-3644, same version number)**: psp
  +65/−65, **dsdt +4/−4 — the sibling carries FOUR entirely
  different DSDT variants, zero overlap, at a stable count of 4**
  (the WIFI II's own set, primary `bdd18b8af25e0c7a`, is
  WIFI-II-exclusive) — again count `==` with set `!=` — while certs,
  whitelist, smm, agesa all exactly `==`. Container 0/4 (108 modules,
  −13,008 B, reproduced). Signature: **registered-births**.
- **The B450 null pair (3802 → 3810), exploratory re-read**: psp
  +17/−17 (fw47's correction, reproduced), **certs +1/−3 — the trust
  store rebuilt from 4 certs to 6: one certificate left the old set,
  three entered the new** — with dsdt, whitelist (47 = 47), smm
  (109 = 109), agesa all `==`. Signature: **multi-axis-swap**; fw47's
  corrected verdict reproduces.

## Front B — the orthogonality law (the ring's product)

The three rows align into one law: **certs is a RELEASE marker; dsdt
is a BOARD marker.** A release touches the trust store and not the
ACPI lineage — on BOTH families (the B550 release rotates one cert
and keeps all four DSDT variants; the B450 3810 rebuilds the trust
store 4→6 and keeps its DSDT set). A board change touches the ACPI
lineage and not the trust store — the same-version sibling swaps all
four DSDT variants and keeps the six certs verbatim (ring 44's
"transfers verbatim", now pair-level). The whitelist (61 = 47 chip
names + 14 fan strings on B550, 47 on B450), the SMM GUID set and
the AGESA level moved on NO measured pair. And the corpus's oldest
cert observation — "the DER count freezes at 6 from 3810" — is now
pair-explained: **3810 is the release that brings the trust store to
6**, one out, three in.

Both event axes hid behind stable counts: the cert rotation (6 vs 6)
and the DSDT replacement (4 vs 4) would have read `==` to every
count-level mark. The campaign's first ASYMMETRIC set deltas are the
certs rows (+1/−1 on 3644→3645, +1/−3 on 3802→3810) — the fw47
orientation (added = old-only, removed = new-only) is inherited
verbatim and now documented in the register, because it finally
mattered.

## Front C — the pre-registration ledger: 5 hit / 3 refuted, all visible

Eight PRs were frozen in the gate names and in `PRE_REG` before any
measurement. **PR-1 hit** (release dsdt == 0 — the P-25 analog: AGESA
unchanged, ACPI untouched), **PR-3 hit** (release whitelist == 0),
**PR-4 hit** (release smm == 0 — the law corollary: species 0/0
implies every GUID subset stable), **PR-5 hit** (release agesa == 0),
**PR-6 hit** (board dsdt != 0 — the version-number trap reaches the
DSDT axis). Three refutations, kept visible pre-freeze (the ring-45/47
precedent), and each is more informative refuted:

- **PR-2 refuted** — "release certs == 0": the release rotates one
  certificate. The sharpened security reading: "improve system
  compatibility" quietly changed the trust store, under a stable
  count, with zero species events, zero form grammar and a 22.5 %
  byte delta that the class histogram had filed as packed→code
  repack. Only the set lens saw it.
- **PR-7 refuted** — "board whitelist != 0": the sibling's whitelist
  is IDENTICAL, fan vocabulary included — the 14 AUX/Level strings
  are B550-generation vocabulary, not WIFI-II-specific (the B450
  probe had already bounded them to B550; the board pair now bounds
  them to the generation, not the SKU).
- **PR-8 refuted** — "release signature == psp-localized-swap": the
  cert swap widens the event to multi-axis-swap. The PSP-localized
  class remains defined (the taxonomy keeps it) but no measured pair
  instantiates it — the honest state of the world.

First selftest 30/32: two TEST bugs (the R2 gate asserted the wrong
side of the inherited orientation — `["h1"]` is old-only, not
`["h4"]` — and R9 compared JSON lists to live tuples), the
measurement itself never in doubt (the R9 detail printed reg == live
numerically). Final: **32/32** with the crown register live.

## Front D — what the 16/09 dump gains

The dump law, pre-registered in the crown: **the cert set alone
discriminates stock-3644 from flashed-3645** (the rotation items are
in the register — if the dump's trust set carries
`4aa03fa22cd75c84` where stock carries `2da09da7f4131f9f`, the board
is flashed forward), **alongside the PSP set and count-blind-proof**
— and **the DSDT set alone certifies the board identity** (the
WIFI II's four variants, primary `bdd18b8af25e0c7a`, are
SKU-exclusive). Day-0 additions:

- `fw48 axes dump.rom` — the cheap per-image reading (counts +
  items + meta, per axis).
- `fw48 marks dump.rom b550w2-3645.rom` — the full-axis flash story:
  psp 37/37 AND the cert rotation are the expected swap marks; any
  OTHER axis moving is the board's own NVRAM/flash story.
- `fw48 marks dump.rom b550w2-3644.rom` — the stock story: every
  content axis expected `==` (the dump's NVRAM does not reach these
  sets); any `!=` is a lead, not a verdict.

## Honesty ledger

- PR-2, PR-7, PR-8 are refuted by measurement and stay visible in
  the register; no claim was edited to fit the data.
- The crown anchors are FIRST-MEASUREMENT anchors (this ring's own
  crown run, anchor-checked by the selftest's live re-derivation);
  the basis is stated where the anchors live (the register's L2
  row), and the null3802 axes row is exploratory — it anchors
  nothing until a later ring pre-registers it.
- The added/removed orientation is fw47's, inherited verbatim and
  now written down — it was orientation-irrelevant while every delta
  was symmetric, and it matters from the certs rows onward.
- The cert items are hash-level evidence: the rotation is measured;
  the CERTIFICATE'S subject and purpose are NOT extracted at this
  layer — no claim is made beyond the swap.
- fw47/fw45/fw42/fw41/fw38/fw39/fw37 are consumed unchanged — 0 diff
  on the frozen surface (bin/, lib/, tests/), 323/323 checks, MCP
  smoke 12 tools, fw35 36/36, fw42 23/23, fw46 38/38, fw47 32/32.
