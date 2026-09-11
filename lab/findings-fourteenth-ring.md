# The fourteenth ring — the NVRAM opens, and the register renames itself

> Read-only. Six specimens: MSI B450 TOMAHAWK MAX `7C02v3G1`, Gigabyte
> B450 AORUS PRO `F67c`, ASRock B450 Steel Legend `10.41 Beta`,
> ASUS PRIME B450-PLUS `4655` + `3604`, ASUS TUF B450-PLUS GAMING
> `4645` (acquired this ring, the first specimen whose sha256 is
> certified by the vendor's own API field). Date: 2026-09-11.

## Front 1 — the premise corrected before the lens was built

The ring 11–13 register carried one line into this window: *"EVSA store
walk is day-0 inventory work."* The bytes refuted the premise before a
single line of the lens existed: **EVSA = 0 raw hits on all six
images**, and `$VSS` = 0 too — the 28 bare `VSS` strings in the MSI
image are code strings, not store headers. The NVRAM of these AMI-Aptio
AM4 boards is **NVAR**, the tagged AMI format whose entries literally
begin with the ASCII `NVAR` (12–28 occurrences per image, every one of
them landing inside one FFS-anchored store). The lens is named for what
the flash actually holds, and `vendor-specimens.json`'s EVSA line now
carries a visible correction. This is the day-0 discipline paying
early: the same correction made *after* the dump would have cost the
first hours of 16/09.

## Front 2 — the grammar imported, never remembered

The ring-11 FTYPE lesson (a type table written from memory was wrong
from `0x0A` on) is now applied at whole-grammar scale. The authority is
on disk, fetched 2026-09-11 from UEFITool's new_engine (BSD-2,
Nikolaj Schlej / LongSoft): `ksy/ami_nvar.ksy` (the Kaitai grammar),
`nvram.h` (the flag constants), `nvramparser.cpp` (the semantics).
Nothing is transcribed from memory; every rule in the walker cites its
source file. The semantics that matter: `next` is a 24-bit offset
**relative to the current entry** (0xFFFFFF = chain end); the GUID area
sits at the **end of the store and grows backwards** (index 0 = the
final 16 bytes); `data_only` entries take their identity from a
predecessor found by a backward link search; the ext-header checksum
sums everything after the 10-byte header plus the size bytes plus the
attributes byte, and is valid when the total is zero.

## Front 3 — the store anatomy, proven by the spec's own variables

Each board ships one FFS raw file (GUID `CEF5B9A3-476D-497F-9FDC-
E98143E0422C`) holding the NVRAM store — 130,952 bytes on ASUS, body
ending exactly at the 0x40000-aligned region boundary. The linear walk
crosses **one** variable and then appears to stop: `StdDefaults`
(GUID `4599D26F-1A11-49B8-…`, identical on all four vendors). It stops
because the second `NVAR` magic is not a sibling entry — it is the
first four bytes of StdDefaults' **data**. AMI ships factory defaults
as a store inside a variable: the outer store holds one variable, and
that variable's payload is a nested NVAR store carrying the real
defaults. The recursion (nvramparser.cpp 288–291) opens it.

One inversion was caught before any number was published: my first GUID
area read the slots front-to-back; the authority says back-to-front.
The proof is self-contained — `PlatformLang` and `Timeout` are
`gEfiGlobalVariableGuid` variables by UEFI spec, and only the corrected
direction resolves them to `8BE4DF61-93CA-11D2-AA0D-00E098032B8C` on
**every** specimen. The fix is recorded in both the script and the
artifact; the pre-fix numbers died unpublished.

Final walk results: 14 walks (7 FFS-anchored stores + 7 nested), zero
walk errors, zero broken links, clean terminators, free space uniformly
0xFF. The factory stores declare **no** `next` links at all — they are
linear. The link machinery is how NVAR represents variable *updates*;
it awaits the live dump.

## Front 4 — the factory grammar across four vendors

The nested stores carry 11–18 variables per board. Nine names are
shared by all six specimens — the AMI factory canon: `AMITSESetup`,
`NetworkStackVar`, `PCI_COMMON`, `PlatformLang`, `SecureBootSetup`,
`Setup`, `Timeout`, `UsbSupport`, `XhciDID`. Around that canon each
vendor plants its own tail: MSI `FixedBoot`/`FixedBootGroup`
(648 B boot defaults), Gigabyte `GcSensorVarName` (569 B),
ASRock `NetConfigData`/`SanitizeSetup`, ASUS `QFan`/`QFanConfig`
(fan curves), `SetupLedData`, `HddSmartInfo` and a 4,991-byte
`VARSTORE_OCMR_SETTINGS_N`. The Setup blob itself is per-board (628 B
Gigabyte, 677 B ASRock, 456 B ASUS, 1,428 B MSI) — its size tracks the
board's setup surface, and on day-0 the ring 6–7 IFR grammar reads it
as a varstore, closing the Q1↔NVRAM bridge on real silicon.

## Front 5 — the MSI mirror extends to NVRAM

Ring 13 registered the MSI double structure as "not a clone" for the
module layer. The NVRAM layer now confirms it: the mirror store carries
the same 12 factory names — but the default **data differs**.
`StdDefaults` is 2,683 B primary vs 3,227 B mirror, and the difference
is concentrated in `Setup`: 1,428 B vs 1,972 B, different sha256. The
mirror is a different factory configuration of the same grammar, not a
byte copy. Registered; root cause still not chased.

## Front 6 — the 3644 question narrows on real evidence

Three measurements this ring:

1. **The ring-11 "3644" zip is a 240-byte HTML error page** — no
   end-of-central-directory signature, sha256 `22fd6e575be583a4…`. It
   was never a firmware. H1 (contaminated acquisition metadata) is
   proven for the acquisition itself.
2. **Three official ledgers now checked**: PRIME B450-PLUS (39
   releases, 0318 → 4655, ring 12), TUF B450-PLUS GAMING (33 releases,
   0221 → 4645), TUF B450M-PLUS GAMING (33 releases, head 4645). **3644
   is in none of them.** The model-variant hypothesis (H2) is tested
   and empty for the three B450-PLUS-class products.
3. **TUF 4645 acquired** with a first: the ASUS API publishes a
   per-release sha256 (`AFA61809…`), the downloaded zip matches it
   byte-exactly — the project's first **vendor-certified** specimen.
   The 2,048-byte CAP wrapper proof reproduces on a third release
   (first FV at 0x40800 in CAP = 0x40000 in ROM).

H3 (published-but-unlisted, or a board identity none of the three
checked products covers) stays open — and now has decision paths: the
dump's version strings, its PSP blob fingerprints (38 changed between
3604 and 4655; the 4645 tree is acquired and parseable), and its NVRAM
defaults can each be matched against four ASUS-adjacent release
candidates on 16/09.

## Front 7 — the ritual retires a ring-13 caveat

The ring-13 honesty ledger carried one open admission: *"one run per
lens — the ring-10 reproducibility ritual has not been applied to
vendor pipelines yet."* Closed this ring: the NVAR lens was run twice
from birth (registers byte-identical, sha256 `eb839fc8…`), and the
ring-13 PSP lens was re-run — byte-identical to its saved register
(sha256 `46b42f9f…`). The vendor lens class is reproducible; the caveat
is retired.

## Honesty ledger

- Variable **data** is fingerprinted (sha256_16, sizes, printable
  heads), not interpreted field-by-field: each vendor's Setup blob is
  its own varstore layout, and reading it is ring 6–7 grammar applied
  on day-0, not guesswork here.
- The ext-header checksum path is implemented and exercised by **zero**
  entries — factory stores ship no ext headers on these six images.
  The path is ready for the live dump, where updates are expected to
  introduce them.
- The GUID-area direction bug existed, was caught by a spec-anchored
  self-test, and was fixed **before** any number left the scratch
  register. The wrong mapping survives nowhere.
- The 9-name factory canon is a statement about these six images, not
  about AMI in general; the census is reproducible from the artifact.
- 3644: H3 is open. Nothing in this ring claims the board's reported
  version is wrong — only that it matches no published ledger among
  the three checked products, and one bogus acquisition is buried.

## Consequences for day-0 (16/09)

- **The dump's NVRAM parses verbatim**: FFS anchor, linear walk,
  nested StdDefaults, backwards GUID area — the instrument runs on the
  dump without re-derivation.
- **The delta measurement is ready**: live variables minus this
  factory register = what the board actually wrote, per variable, with
  chain links and ext headers expected to appear for the first time.
- **The Q1 bridge lands on real silicon**: the dump's Setup blob is
  the byte-addressable initial state of the setup facade.
- **The identity question has three evidence paths**, all acquired and
  parseable: version strings, PSP blob fingerprints (3604 / 4655 /
  4645 trees), and NVRAM factory defaults. The dump decides which
  release — and which board — it really is.
