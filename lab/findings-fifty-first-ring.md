# The fifty-first ring — the factory law of the ReBAR chain: what the
# vendor actually ships

*Ring 51 · 2026-09-15 · instrument `lab/fw51-rebarfact.py` · crown
`lab/vendor-rebarfact-register.json` · composing frozen fw49 (and through
it fw37/fw43); the NVAR grammar is the ring-14 walker carried verbatim*

## The founder's word, third pass: the factory

Ring 49 measured the ReBAR AXIS (the option exists at Setup-varstore
0x1BB, wrapped in SUPPRESS_IF/GRAY_OUT); ring 50 measured its LANGUAGE
({0x00: Disabled, 0x01: Auto} — no Enabled, the founder's "c'est en
auto" byte-true). One question remained, and it is the sharpest one for
the symptom: **what does the vendor actually SHIP in those bytes?** The
option says Auto; the form's conditions are measured; but the factory
state of the chain — what a shipped board holds before anyone touches it
— had never been read. Ring 51 reads it from two independent sources and
crosses them:

- **SOURCE N (NVRAM)** — the AMI NVAR store's `StdDefaults` variable
  (GUID 4599D26F-1A11-49B8-B91F-858745CFF824) carries a NESTED NVAR
  store whose inner `Setup` variable (GUID EC87D643-EBA4-4BB5-A1E5-
  3F3E36B20DA9, 515 B on the WIFI II) is the factory canon,
  byte-addressable at the very voffs the name table gave rings 49/50.
  The ring-14 grammar reads it verbatim — and the **B550 acquisitions
  had never been parsed before this ring** (ring 14's specimens were
  the six B450 boards).
- **SOURCE I (IFR)** — the Setup module's own constructs: the ONE_OF
  option flags (EFI_IFR_FLAG_DEFAULT 0x10) and the DEFAULT statements
  (op 0x5B — the "ami value ops" ring 49 kept raw).

## Front A — the B550 factory store, first parse

Each 32-MiB B550 acquisition carries TWO NVAR stores (both SPI windows,
FFS anchors `0x40078` and `0x1040078` — the ring-17 double-structure
position), each holding EXACTLY ONE outer variable: `StdDefaults`
(6,823 B WIFI II / 6,822 B sibling), byte-identical across the two
windows of every image. The nested store walks clean: 17 entries, zero
walk errors, zero broken links. The inner `Setup` blob is 515 B (WIFI
II) / 514 B (sibling) — matching the ring-50 IFR varstore census (515
B): the ring-20 bridge holds on B550, from the NVRAM side. The entry
inventory names the B550 factory grammar (first time): Setup,
PlatformLang, Timeout, AMITSESetup, PcieSataModVar, XhciDID,
SetupLedData, NV_SIO0_LD2 (the sibling generation's SIO lane; B450
carries NV_SIO0_LD1 plus QFanConfig, absent here), SetupHWMOneof, QFan,
UsbSupport, NetworkStackVar, HddSmartInfo, SecureBootSetup (7 B, GUID
7B59104A-C00D-4158-… — the SecureVarPresent varstore's GUID family,
ring 50's neighbor), VARSTORE_OCMR_SETTINGS_N (5,371 B), and
SIBoardItemControl. **No `SystemAccess` anywhere** — the grayout gate
ships factory-open (absence reads as unrestricted).

## Front B — THE FACTORY LAW (the headline)

The five gates, read from the factory canon and crossed with the IFR
defaults (b550w2-3644; identical on 3645 and nw-3644):

| gate | voff | factory | IFR default (layout A) | verdict |
|---|---|---|---|---|
| MmioAddrLimit | 0x1B6 | **0x27** | 0x27 (one statement) | agree |
| Above4gDecode | 0x1BA | **0x00 Disabled** | 0x00 (ids 0 and 1) | agree |
| **ResizeBarSupport** | **0x1BB** | **0x00 Disabled** | **0x00 (ids 0 and 1)** | agree |
| SriovSupport | 0x1BC | **0x00 Disabled** | 0x00 (ids 0 and 1) | agree |
| CsmSupport | 0x1F2 | **0x00 Disabled** | 0x00 (ids 0 and 1) | agree |

**The vendor ships the whole decode chain OFF.** ReBAR's factory byte
is Disabled — the option cannot say "Auto" on a factory-fresh board.
And the design is coherent: with Above 4G Decoding shipped at 0x00, the
ring-49 SUPPRESS_IF hides the ReBAR question entirely — a factory board
does not even show it. The user's path is: enable Above 4G first (the
question appears), then ReBAR can hold Auto. The two sources AGREE on
every gate of every image (15/15 crosses) — ring 49's raw `5B-06` ops
are now RESOLVED as standard EFI_IFR_DEFAULT statements (DefaultId 0
and 1, both 0x00 for the decode family), the layout DERIVED per
question by the chooser (unique default-ids + option-value membership;
ambiguous and raw-only stay unclaimed — L1).

## Front C — the founder's word, re-read

The consequence lands on the founder's sentence: *"il détecte mal
alors que c'est en auto"*. Measured against the factory law, **"c'est
en auto" is a WRITTEN state, not the factory state**: his live NVRAM
must hold 0x01 at 0x1BA (else the question is hidden and he could not
read it on his screen) and — if the form truly shows Auto — 0x01 at
0x1BB. Someone or something engaged the chain on his board: his own
earlier settings pass, a vendor assistant, or a defaults-load on a
release whose live state differed. Which of these is the 16/09 dump's
to name: the live-minus-factory delta (ring-14's protocol, gate-scoped)
reads the board's history byte by byte. The symptom itself ("détecte
mal") now lives in exactly three places: the Auto heuristic's own
decisions (vendor code — the named open question), the vendor help's
remaining conditions (a ReBAR-capable GPU; CSM — whose factory byte
0x00 says the board ships UEFI-only), or the OS half (diag-gpu's BAR1
≤ 256 MiB). The firmware half of the story is now measured end to end.

## Front D — the pair laws, at the factory level

- **Release 3644 → 3645: factory-INVARIANT** — the StdDefaults blobs
  byte-identical (sha16 `c127f5cb3e69cbb5` both), the Setup blobs
  byte-identical (sha16 `8fddea6c421714c3`, zero diff spans), every
  gate byte equal. The cert-only release (rings 47-50) cannot move the
  factory canon — the invariance chain now reaches the NVRAM floor.
- **Board 3644 ↔ nw-3644: invariant MODULO the blob tail** — the gate
  bytes equal on all five gates; the ONE-BYTE factory delta (Setup 515
  vs 514 B) sits in span [513, 514] at the blob's end, no gate within
  reach. Ring 49/50's "invariant modulo one byte" law now has its
  NVRAM-floor witness, and the mover is not even the same byte.
- **B450 null (PRIME B450-PLUS 3604, 2022): the SAME disabled chain** —
  Above4gDecode 0x00 @0x18A, ResizeBarSupport 0x00 @0x18B (the field
  has sat in the name table since 2022, IFR-coherent, agreeing with
  the factory blob of 456 B), SriovSupport 0x00 @0x18C, MmioAddrLimit
  0x27 @0x187 (no IFR default statement on that construct — recorded,
  not claimed). The anticipated generational CONTRAST died: the factory
  law is generation-wide. CsmSupport on B450 stays UNMEASURED — its
  name-table meta reads 0x0, reported and never claimed (L1).

## Pre-registration ledger (frozen in the instrument source before measurement)

| PR | claim | verdict |
|---|---|---|
| PR-1 | factory ReBAR == 0x01 (Auto) — founder-anchored | **REFUTED** — 0x00; "c'est en auto" is a written state (the pre-named alternative) |
| PR-2 | factory Above4g == 0x01 — else the chain is dead-on-arrival | **REFUTED** — 0x00; the chain IS dead-on-arrival and coherent (the question ships hidden) |
| PR-3 | factory CSM == 0x00 | hit |
| PR-4 | the two sources agree on every gate; the informative miss was pre-named (nvram-outranks-ifr) | hit — 15/15 crosses; the miss did not happen |
| PR-5 | release pair factory-invariant | hit — zero diff spans |
| PR-6 | board pair gate-equal, delta outside the gates | hit — span [513, 514] |
| PR-7 | SystemAccess absent from every StdDefaults | hit |
| PR-8 | outer store = StdDefaults only, all three | hit |
| PR-9 | B450 3604: Above4g 0x00 + ReBAR 0x00; CSM unmeasured as pre-stated | hit — the contrast died, the law is generation-wide |

7 hit / 2 REFUTED — and both refutations were pre-named in the
instrument source as the informative outcomes, per the rings 45/47/48/50
precedent.

## Instrument and battery

`lab/fw51-rebarfact.py` (modes `fact` / `pair` / `null450` / `day0` /
`selftest` / `manifest`), four laws (L1 bytes-over-guesses — the IFR
layout derived per question, never assumed; L2 anchors-before-marks —
the B550 gates reproduce the ring-49 crown, the stores reproduce the
probe-measured shape, the B450 null runs under its own board-relative
constructs; L3 zero writes; L4 compose-on-frozen — fw49 imported, the
ring-14 NVAR grammar carried verbatim and pinned by KATs). First runs
caught four instrument bugs and one bad KAT (a dict double-inversion
that starved the question scan; a crown-scope leak onto the B450 null;
a tautological R4 gate; an ill-chosen raw-only case) — final **13/13
with the crown live**. The crown `vendor-rebarfact-register.json`
written once by `scripts/ring51_register.py` (assertions on every
structural anchor, PR verdicts derived from fresh measurements,
roundtrip). Battery: 323/323, MCP smoke OK (12 tools), fw35 36/36,
fw42 23/23, fw46 38/38, fw47 32/32, fw48 32/32, fw49 11/11, fw50 15/15,
fw51 13/13, frozen surface 0 diff (bin/lib/tests).

## Day-0 reading (what the dump owes us — the five-gate byte court)

The factory canon is now the fixed reference the dump is judged
against. In order:

1. **Factory identity**: the dump's StdDefaults blob must reproduce
   sha16 `c127f5cb3e69cbb5` — else flash history, read with fw48's
   marks before anything else.
2. **Live-minus-factory, gate-scoped**: the dump's outer store will
   carry live variables (the CAP ships StdDefaults only); read the
   live `Setup` blob at 0x1B6/0x1BA/0x1BB/0x1BC/0x1F2 and delta against
   the factory canon per gate.
3. **The expectations, reversed by this ring**: live Above4g expected
   **0x01** (the founder SEES the question), live ReBAR expected
   **0x01** (he reads Auto), live CSM expected 0x00 (factory-faithful).
   A live byte breaking expectation IS the measured story: above4g-drift
   (the chain broken at gate 1), rebar-drift (the form shows Auto, the
   NVRAM holds Disabled), csm-drift (the vendor's own NOTE violated).
4. **SystemAccess live**: the factory ships none; a live 0x01 means the
   option is GRAYED on the board — a restricted-session story, not a
   detection story.
5. **All-five-faithful at the engaged values** ⇒ the firmware chain is
   engaged and byte-faithful, and the symptom lives in the Auto
   heuristic (vendor code) or the OS half — `omarchy-firmware diag-gpu`
   (gpu-bar1-small: BAR1 ≤ 256 MiB), `lspci` "Physical Resizable BAR",
   `dmesg` rebar lines, `/proc/iomem` above the 4 GB line.

## The honesty ledger

- The NVAR grammar is a VERBATIM copy of the ring-14 probe walker (its
  /tmp home is volatile), pinned by R-tier KATs and by the store-shape
  anchors; semantics were never re-derived from memory.
- The IFR layout (A = standard EFI_IFR_DEFAULT) is a DERIVATION from
  uniqueness + option-membership, not an assumption; the chooser
  reports ambiguous and raw-only states and claims nothing there
  (the B450 Mmio construct's missing default statement is recorded,
  not decoded).
- CsmSupport on B450 stays UNMEASURED (name-table meta 0x0) — reported,
  never claimed.
- PR-1/PR-2's refutations were pre-named in the instrument source
  before the bytes were read; the frozen register carries the
  consequences, the claims stay as written.
- Who or what wrote 0x01 into the founder's live chain is NOT claimed —
  the dump's live-minus-factory delta answers the board-side history;
  the heuristic's internals remain vendor-code territory.
