# The forty-fourth ring — the corrected board (2026-09-14)

> Companion to rings one through forty-three. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `fw36-atlas.py` (the
> cartography differ, promoted ring 36), `fw42-dossier.py` (the
> triptych, ring 42) — both run as-is, unchanged, against a target
> they were never calibrated for. Artifact: `vendor-ledger-b550w2.json`
> (this repo, via `scripts/ring44_artifact.py`). The trigger: the
> founder corrected the board identity before the 16/09 dump — and the
> whole question_3644 mystery collapsed under acquisition, not
> speculation.

## Front A — the founder's correction resolves question_3644 by acquisition

The registered founder's brief (rings 12–14) said: the physical board
reports BIOS 3644, ASUS B450-PLUS class. Every B450 ledger in reach was
searched then — PRIME B450-PLUS (39 entries), TUF B450-PLUS GAMING
(33), TUF B450M-PLUS GAMING (33) — and 3644 was in none, so H3
(published-but-unlisted) stayed open and P-18 was frozen as its
machine-readable form. The founder now corrects: the board is a
**TUF GAMING B550-PLUS WIFI II** (the API's own CAP name `TG550PW2.CAP`
confirms the SKU). The B550 family was never checked, because the
family was never declared. Three minutes of the ring-12 recipe
(GetPDBIOS, `website=global&cpu=AM4`) answer everything:

- **WIFI II ledger: 17 entries, 0303 (2021/10/21) → 3645 (2026/09/14,
  TODAY) — 3644 IS THERE, dated 2026/08/27, 16.28 MB.**
- TUF GAMING B550-PLUS (non-WIFI): 34 entries, 0242 (2020/05/20) →
  3645 (2026/09/14) — 3644 there too, same day.
- TUF GAMING B550-PLUS (WI-FI v1): 24 entries, head 3636 (2026/01/27)
  — **3644 absent**: the version space is genuinely per-board, and the
  v1 line had already gone quiet before the 1.2.0.12 wave.

Verdicts, by the ring-12 frame: **H2 (board-model variant) PROVEN** —
3644 lives in another ASUS product's ledger, and always did. **H3
(published-but-unlisted) REFUTED in the literal frame** — 3644 is
published and listed, for the correct board. And yet the machine-H3
class (no-match against the B450 corpus) is independently CONFIRMED by
fw39 on the acquired image: both hypotheses were right at their own
level — one about the vendor's catalogue, one about our corpus's
blindness. The register's honesty also gets a rehabilitation: the
ring-12 "contaminated" metadata (Aug 2026, AGESA 1.2.0.12) matches the
WIFI II 3644 release description EXACTLY ("Update AGESA version to
ComboV2 PI 1.2.0.12. Mitigate fTPM vulnerabilities CVE-2026-6726,
CVE-2026-6727"). The founder's brief was right about version, date and
AGESA — wrong only about the family. The acquisition trail records
everything: zip sha256s, CAP bytes, ROM sha256_16 — three new
vendor-verified specimens, the CAP wrapper proof reproducing on the
B550 geometry (below).

## Front B — the CAP convention doubles, and P-01's miss is structural

The B450 corpus CAPs carry a 0x800 header (rom = cap[0x800:], 16 MiB
exact, registered ring 12). The B550 WIFI II CAP is 33,558,528 bytes =
32 MiB + 4096: it carries **TWO 0x800 header blocks** whose flash-block
descriptors differ (the second half re-states the map with 0x0800-
sized blocks where the first uses 0x1000), so **rom = cap[0x1000:]**,
32 MiB exact — verified by all ten `_FVH` checksums validating on the
0x1000 split (and identically on the 0x800-shifted view; the split is
decided by size and the header block structure, the FV map cannot
discriminate because it is the same FVs). The corpus's first oracle
prediction, P-01 (rom_bytes = 16777216), misses on the corrected board
**by a factor of two — the geometry itself doubles**. The convention
table (B450 0x800/16 MiB, B550 0x1000/32 MiB) is registered in
`vendor-ledger-b550w2.json` for every future fetch.

## Front C — the triptych on the real target: a measured stranger point

`fw42-dossier.py dossier b550w2-3644.rom --target day0` ran unchanged.
The scoreline against the frozen 26-prediction register:
**4 hit / 0 partial / 8 miss / 14 na**, profile **stranger**, identity
coupling **coherent-foreign**, identity verdict **no-match-h3-eligible**
(3 independent fingerprint diffs). The decomposition is the ring's
product — it splits cleanly along board-dependence:

- **The 4 hits are exactly the board-independent invariants**: P-03
  (the AGESA family prefix ComboAM4v2PI — the AM4 line is one family
  across chipsets), P-06 (exactly 41 chip whitelist families — the
  same whitelist generation the B450 corpus carries), P-08 (module
  count 616, inside the [600,640] band, point 618 — the same AMI
  module scale), and **P-18 (identity = H3) machine-confirmed** — the
  dump-matches-no-known-rung prediction held even though the reason
  changed: not an unlisted release, but a corrected board.
- **The 8 misses are exactly the board-dependent facts**: P-01 (32 MiB
  vs 16 MiB), P-02 (AGESA 1.2.0.12, outside the {6b, 6c, 7} B450-time
  bracket — the desc's claim, machine-extracted from the ROM:
  `agesa_level 1.2.0.12`, `agesa_string ComboAM4v2PI`), P-04 and P-05
  (the armor quartet AND SbRomArmorSmm are PRESENT — the B550 line's
  armor wave schedule differs entirely from the B450 wave-1 boundary
  at 3802), P-07 (0 legacy SMM modules, not 2), P-09 (DSDT anchor
  `bdd18b8af25e0c7a` — a lineage the corpus's 12-entry DSDT universe
  has never seen), P-11 (6 distinct DER certs, not 4 — the B550 sits
  at the corpus's 3810 freeze level), P-17 (SMM census 186 vs the
  106–109 band — a much larger SMM population).
- The weld's three conflicts (armor quartet, SbRomArmorSmm, DSDT
  variant) all resolve "judge wins (deep truth)" — the nested-LZMA
  shallow-walk lesson from ring 40 reproduces verbatim on a board the
  judge was never calibrated for. The precedence law is
  board-independent, measured.
- The IFR lens quartet (façade, validity, varstore size/share) and the
  PSP hash sets came back **loud-degraded (null)** — the fw43
  proposers are B450-calibrated and L3 refused to guess. The honesty
  laws held on first contact with the corrected target.

The novelty reading names the stranger precisely: 644 species
observed, **596 known to the B450 universe (92.5% genome transfer
across the chipset divide)**, 48 unregistered; 8 of 112 SMM entries
unregistered (92.9% transfer); 4 of 4 DSDT variants unregistered (the
board's own lineage); **certs 0 unregistered — the 6-certificate DER
set transfers verbatim**; AGESA and whitelist fully inside their
universes. One accounting discrepancy is registered, not smoothed:
the novelty summary reports `unregistered_total = 74` while the
per-axis walk sums 60 — a coherence-vs-novelty counting delta of 14
to reconcile in ring 45; both numbers are machine-derived and
registered as-is.

## Front D — what "un meilleur bios" means, byte-level (3644 → 3645)

The WIFI II's head-of-line **3645 released TODAY (2026/09/14,
"Improve system compatibility")** was acquired beside 3644 — the
concrete flash-target question answered by the ring-36 cartography
differ, unchanged: same size (32 MiB = 32 MiB), **53 change runs,
7,544,486 bytes differing (22.5% of the ROM), 133 of 512 64-KiB
blocks touched**. The class histogram separates the noise from the
signal: packed→code 7,461,826 B (compressed volumes re-pack
wholesale), **code→code 81,167 B — uncompressed code that actually
changed, the honest logic-change floor of "improve system
compatibility"** — plus 1,493 B data→code. This is the first
cross-release vendor differ on the corrected board, and it becomes
the byte-map baseline: if the 16/09 dump is flashed forward to 3645,
this map is what the diff will be read against.

## Front E — the version-number trap, measured on the family itself

The sibling's 3644 (TUF GAMING B550-PLUS, non-WIFI, same day, same
AGESA desc, same CAP structure) was acquired and byte-compared against
the WIFI II 3644: **10,741,113 bytes differ — 32.0% of the ROM**.
Same version number, same release date, same description, NOT the
same image — more bytes differ between two boards' same-numbered
releases than between two consecutive releases of one board (22.5%).
The law is now measured, not assumed: **a version number never
identifies an image; the identity key is (board, version), and only
the byte level settles it.** This is the quantitative ground truth
behind why question_3644 resisted three ledgers of evidence and why
the identity machine keys on ROM bytes and body hashes, never on
version strings.

## What the 16/09 dump now means

The dump protocol itself does not change — `dossier dump.rom` +
lenses, as registered. What changes is the reading, and it is
pre-registered here, before the dump exists:

- The expected profile is the MEASURED one from this ring: if the
  board is stock, the dump's scoreline should land ON the stranger
  point **{P-03, P-06, P-08, P-18} hit / 8 board-dependent misses /
  14 na**, with identity resolving to **known-clean against the
  acquired b550w2-3644.rom** (full-file or CAP-strip body, both
  conventions registered). Byte-identity to the acquisition + zero
  unregistered content = the clean dossier; any deviation is the
  board's own NVRAM story, readable through the existing coupling
  table.
- The oracle register stays frozen — 4/8/14 is a scoreline, not a
  correction. The transfer map (which predictions survive a
  same-vendor, same-socket, different-chipset move) is this ring's
  product and the first measured calibration of the oracle's
  cross-board reach.
- The release-41 machinery (P-20..P-26, dossier-pair) now has a REAL
  live target too: the WIFI II's own future releases (3645 is already
  acquired; the next vendor release is a dossier-pair away), and the
  registered null-model logic transfers with the pair discipline.

## Honesty ledger

- The founder's correction arrived BEFORE the dump — the best possible
  timing: the scoreline's interpretation is pre-registered against a
  measured expectation instead of being narrated after the fact.
- The 74-vs-60 unregistered accounting delta is flagged in the
  register and left as-is for ring 45 to reconcile; no smoothing.
- The IFR/PSP lens slots on B550 are loud-degraded nulls — the
  proposers' calibration does not transfer and was not pretended to.
- The WI-FI v1 ledger needed the parenthesized model string ("TUF
  GAMING B550-PLUS (WI-FI)"); the bare string answers FAIL —
  registered so the next fetch does not re-derive it.
- No frozen surface touched: bin/, lib/, tests/ 0 diff; the ring's
  measurements all came through the existing tracked instruments
  (fw36, fw42) plus acquisition — the repo's knowledge grew, the
  tool surface did not.
