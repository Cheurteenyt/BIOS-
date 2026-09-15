# The fifty-second ring — the grammar of the Setup variable: what the
# vendor's own shipped C source says the 515 bytes ARE, and the census
# of who reads them

*Ring 52 · 2026-09-15 · instrument `lab/fw52-rebargram.py` · crown
`lab/vendor-rebargram-register.json` · composing frozen fw49 (and
through it fw37/fw43); the IFR machinery is the ring-49/50 walk,
the NVAR grammar the ring-14 walker carried verbatim (ring 51)*

## The founder's word, fourth pass: the grammar

Ring 49 measured the ReBAR AXIS (the option at Setup-varstore 0x1BB,
its SUPPRESS_IF/GRAY_OUT wrappers, the pair laws); ring 50 the
LANGUAGE ({0x00: Disabled, 0x01: Auto} — no Enabled, "c'est en auto"
byte-true); ring 51 the FACTORY LAW (the whole decode chain ships OFF,
15/15 source crosses — the founder's Auto is a written state). One
thing none of the three could say: **what ARE those 515 bytes, by
name?** Rings 49–51 addressed the Setup variable's bytes through three
lenses (the IFR question space, the string package, the NVRAM canon);
none could name the field at 0x1BB in the vendor's own vocabulary. Ring
52 measures the GRAMMAR — and finds the vendor ships it INSIDE the
image, as C source.

## Front T — the SETUP_DATA text (SOURCE T)

Every ASUS acquisition carries a raw C-source FFS file (GUID
AB017B39-014F-4A69-A457-7E16B09DE825, 53,050 B on the WIFI II):
the AMI `SETUP_DATA` structure declaration — 396 named fields with
C types, packed size **515 B — byte-equal to the measured Setup
variable** of ring 50's varstore census and ring 51's factory blob.
The walk is mechanical and KAT-pinned (arrays, u16/u32 boundaries, and
the UINTN refusal: a pointer-typed field would poison the packed walk
and the instrument refuses — measured census UINT8 ×379, UINT16 ×7,
UINT32 ×9, UINT64 ×1, four fixed arrays, **zero UINTN**; KAT-3
enforces the refusal forever).

Every gate field lands EXACTLY on the ring-49 crown voffs:

| field | voff |
|---|---|
| MmioAddrLimit | 0x1B6 |
| Above4gDecode | 0x1BA |
| ResizeBarSupport | 0x1BB |
| SriovSupport | 0x1BC |
| CsmSupport | 0x1F2 |

**A THIRD independent source agrees** — the IFR census (ring 50) and
the NVRAM canon (ring 51) named the offsets; the image's own C source
now names the fields. The grammar names every byte of the varstore the
first three rings only addressed. The byte the Auto heuristic will one
day read is `SETUP_DATA.ResizeBarSupport` — a field with a name, a
packed offset the image itself documents, and a factory value of 0x00
(ring 51).

The B450 null carries its OWN generation's text (50,486 B): 361
fields, packed **456 B == the measured B450 blob**, gates at
0x187/0x18A/0x18B/0x18C — landing on ring 51's reliable name-table
anchors; `CsmSupport` is text-claimed only (0x1B9 — the register's 0x0
meta stays unclaimed, per the ring-51 rule). **The grammar law is
generation-wide.**

## Front E — the executors (SOURCE E): who reads the Setup variable

The census of EC87D643-GUID carriers (modules that reference the Setup
variable's GUID): **34 consumers per acquisition, the SAME GUID set
across release and board** (set sha16 `a0da64f48529c2a3` on all three
B550 acquisitions). Exactly TWO consumers are ≥ 1 MB:

- the **bridge** `49818FD1-7413-4C71-84CF-6BFE670C6496` — 4,254,978 B,
  stringless PE32+, .text 4.2 MB, carrying the UTF-16 variable names
  L"Setup"/L"QFan"/L"SetupLedData": the ASUS policy-bridge shape;
- the **owner** `899407D7` — the Setup module itself (1,421,242 B,
  ×24 GUID refs), the varstore's proprietor. (PR-5's refutation IS
  this: the probe-formed claim forgot the owner; the corrected law —
  exactly two ≥ 1 MB readers, each identified — is enforced by
  selftest I3.)

Pair laws of the bridge: **release-invariant** (sha16
`cbf56bec7d3cfaac` on 3644 AND 3645 — the 16/09 flash cannot change
the ReBAR executor's code) and **board-variant** (`f2fbd03edccf722a`
on nw-3644); **B550-generation** — absent on the B450 null, which runs
its own consumer set (32 consumers, no ≥ 4 MB module). The name-table
carrier `64BEA199` (the ring-49 offset table) is present on all four
images: release-invariant (`c3af43f04b68d805`, 37,454 B) but
**board-variant** (`0afc22419271b572` on nw-3644, same size) — the
carrier joins the board-marker class (the ring-48 DSDT pattern, at
module level).

**The Auto heuristic is now BOUNDED, not read**: behind 34 readers,
inside one 4.25 MB release-invariant binary. Its internal logic stays
vendor-code territory (the named open question since ring 49, the
SystemAccess precedent) — but the byte it reads, the offset it reads
it at, the name the vendor gives it, and the code block that reads it
are all measured.

## Front P — the pair laws and the NAMED tail

Grammar pair laws: release 3644→3645 text **sha16-equal**
(`9bfea5a1540da7f1`); board 3644↔nw-3644 differs (`eef483c4097bffff`)
and the delta is **NAMED — the field `MyAsusControl`** (@0x201, span
[513,514]) present on the WIFI II and absent on the sibling (396 vs
395 fields). **Ring 51's anonymous tail span [513,514] gets its field
name**: the single byte-pair that distinguishes the WIFI II's Setup
variable from its sibling's is an ASUS control field, not a decode
gate — every gate of the ReBAR chain sits at the same voff on both
boards.

## Front C — the census laws

- **The decode family is Setup-grammar-owned, never CBS-owned**: the
  names Above4gDecode/ResizeBarSupport are ABSENT from every
  CBS_CONFIG text on both generations (B550 carries four CBS texts,
  B450 three). No AMD CBS override path for the decode chain — the
  Setup variable is the single point of truth.
- **SystemAccess is ABSENT from every SETUP_DATA text** — the grayout
  gate is not a Setup field; ring 50's varstore independence gains its
  text anchor.
- **The 1M/2M/4M/8M u32 ladder is NOT executor evidence** (PR-11,
  refuted by probe and kept visible): a generic data pattern with
  dozens of owners in debug/GUID-table contexts. The census counts
  GUID references, not lucky bytes.

## The dump card, extended (day-0 additions)

The 16/09 dump inherits TWO new identities on top of rings 48–51's
marks, both flash-immune (release-invariant):

- **grammar identity**: SETUP_DATA text sha16 `9bfea5a1540da7f1`,
  packed 515 — a different sha is an acquisition-mismatch marker;
- **executor identity**: bridge sha16 `cbf56bec7d3cfaac`, consumer
  count 34, consumer-set sha16 `a0da64f48529c2a3`, name-table sha16
  `c3af43f04b68d805`.

The live gate court is unchanged (ring 51's reversed expectations:
live Above4g 0x01, live ReBAR 0x01, live CSM 0x00) — but the delta
protocol now speaks FIELD NAMES: the live-minus-factory delta reads
`Above4gDecode`, `ResizeBarSupport`, `CsmSupport` by name, straight
from the image's own C source.

## The honesty ledger

- PR-5, PR-8, PR-11's refutations were pre-named informative outcomes
  (PR-5/PR-11 in the instrument source before the bytes were read) or
  are kept visible in the frozen register (PR-8) — the claims stay as
  written, the corrections carry the law (selftest I3 enforces the
  owner-vs-reader census).
- The text walk claims an offset only from the walked text (L1); the
  crown cross re-extracts ring 49's anchors live and refuses loud on
  mismatch (L2); R4's KAT feeds shifted text and expects the refusal.
- B450's CsmSupport stays UNMEASURED (text-claimed 0x1B9 only; the 0x0
  meta unclaimed) — reported, never claimed, per the ring-51 rule.
- The Auto heuristic's internals are NOT decoded — bounded, named,
  release-invariant, but vendor-code territory; nobody here patches a
  4.25 MB AGESA binary (L3 zero writes; the frozen surface untouched).
- Who or what wrote 0x01 into the founder's live chain remains
  UNCLAIMED — the dump's live-minus-factory delta answers the
  board-side history (ring 14's protocol, gate-scoped).
