# The forty-ninth ring — the ReBAR axis: the founder's mis-detected Auto, measured to the byte (2026-09-15)

> Companion to rings one through forty-eight. Same campaign, same
> rules: read-only over downloaded vendor images, zero bytes written
> anywhere but the lab record. Instruments this ring:
> `fw49-rebar.py` (TRACKED, new) composing on the unchanged fw37/43
> machinery, with the ring-8 string layer reached through a NEW
> decoder for the Setup module's own string format. Artifact:
> `vendor-rebar-register.json` (this repo, via
> `scripts/ring49_register.py`), one write, assertion-gated,
> roundtrip-checked. The trigger: the founder's report — *"le reshade
> bar ... il détecte mal alors que c'est en auto"* — and the repo's
> own diag-gpu, which renders the OS half of Resizable BAR
> (`gpu-bar1-small`, BAR1 <= 256 MiB) and states the BIOS half is
> "not observable from the OS". Ring 49 makes the BIOS half
> observable, on the vendor image, before the 16/09 dump.

## Front A — the vocabulary law: the option is called something else

The first measurement is a negative that explains the founder's
difficulty. Scanning the three B550 acquisitions — raw AND recursively
LZMA-pierced (16 top-level guided sections, 50 hits total, ~48.6 MB
decompressed per image) — the canonical vocabulary is ABSENT:

- "Resizable", "Re-Size", "ReBAR", "Smart Access": **zero hits**,
  ASCII and UTF-16LE alike.
- What IS present: "Above 4G Decoding", "Above 4GB MMIO Limit"
  ("...works only when 'Above 4G decoding' is enabled"), "UMA Above
  4G" (CBS), and — the find — the ASCII token **`ResizeBarSupport`**
  in the AMI SMM name-table driver
  (`64BEA199-7C6C-4F51-B0DA-F42C897DA5CC`, file type 0x0A, whose PE
  carries the field-name table outside `image_modules`' 0x07/0x08/0x09
  filter — the ring-43 filter is correct for its census, and this
  ring walks around it without touching it).

The name table decodes as a field -> Setup-varstore-offset map
(u16 at slot+0x30, verified on five independent fields and on the
sequential Sata* rows): `MmioAddrLimit 0x1B6`, **`Above4gDecode
0x1BA`, `ResizeBarSupport 0x1BB`, `SriovSupport 0x1BC`**,
`CsmSupport 0x1F2` — single-byte fields, the ReBAR switch sitting
literally between Above-4G and SR-IOV. The visible label resolves
through the Setup module's packed-UTF-16 string table (utf16z entries
separated by ONE 0x14 byte — the AMI cousin of the ring-3 OVMF
packing), anchored on the measured pair (tok 1281 = "Above 4G
Decoding", verified BOTH ways per law L1):

- tok 1403 = **"Resize BAR Support"** — the ASUS label. Not
  "Resizable BAR": the vendor's own string drops the "able", which is
  why every canonical-name search of the image finds nothing.
- tok 1404 = the help text, verbatim, and it is the vendor
  documenting the whole detection chain itself:

> "If the system has Resize BAR capable PCIe Devices, this option
> Enables or Disables Resize BAR Support.(Only if System Support 64
> bit PCI Decoding) NOTE: To enable Resize BAR Support to fully
> harness GPU memory, please navigate to Boot section and disable
> CSM(Compatibility Support Module)."

## Front B — the question, measured (the axis triptych)

The Setup module (name literally "Setup", 1,421,088 B) yields its IFR
through fw43's `direct_forms` (28 candidates; the AMI setup's package
lists do not close — the ring-43 convention holds). The axis
questions, extracted live and asserted against the crown:

| field | voff | qid | tok | label (anchored) | op |
|---|---|---|---|---|---|
| Above4gDecode | 0x1BA | 0x20E | 1281 | Above 4G Decoding | ONE_OF |
| **ResizeBarSupport** | **0x1BB** | **0x20F** | **1403** | **Resize BAR Support** | **ONE_OF** |
| SriovSupport | 0x1BC | 0x210 | 1283 | SR-IOV Support | ONE_OF |

The ReBAR ONE_OF (61-byte construct, sha16 per acquisition below):

- options: **{0x00 -> tok 4, 0x01 -> tok 5}** plus the AMI value ops
  (0x5B-06) carrying 00000000 / 01000000. Two options only — no
  third state in the form grammar.
- predicates, both measured: **SUPPRESS_IF (qid 0x20E == 0)** — qid
  0x20E IS Above4gDecode: the option vanishes from the form when
  Above 4G Decoding holds 0 — and **GRAY_OUT_IF (qid 0x361 == 1)** —
  a hidden question (prompt tok 0 in the walked candidates), identity
  open, with the vendor help naming the CSM condition independently.

## Front C — the pair law (the ring's product)

- **Release pair (3644 -> 3645): `rebar-axis-invariant`.** Same
  qids/toks/voffs, same construct hash, same name table, same help
  text. The release the board will meet on 16/09 changes NOTHING on
  this axis — consistent with rings 47-48 (the release rotates one
  DER certificate, not one setup bit). The ReBAR reading pre-registered
  for the dump is therefore the stock-3644 reading, unchanged.
- **Board pair (3644 <-> nw-3644):
  `rebar-axis-invariant-modulo-grayout-qid`.** The 61-byte construct
  differs by EXACTLY ONE BYTE: the grayout operand's question id,
  **0x361 (WIFI II) vs 0x35F (sibling)** — the sibling's question
  space is two questions shorter (the WIFI questions it lacks), and
  the ReBAR predicate shifts with it. The option itself, its values,
  its label, its help and its name-table slot are identical: the
  feature is the same feature on both boards; only the address of one
  predicate operand moves.
- The name table itself transfers verbatim across all three
  acquisitions (same fields, same offsets) — the SMM-side view of the
  axis is board-invariant.

## Front D — the day-0/day-1 chain (why the founder "détecte mal")

The OS half is already mechanized in the repo: `fw.diag.gpu` renders
`gpu-bar1-small` when nvidia-smi's BAR1 Total is <= 256 MiB — "With
Above 4G decoding + Resizable BAR the CPU can map the whole VRAM; at
256 MiB the BIOS default (not a fault) is active" — and its own next
steps say the fix is "not observable from the OS". Ring 49 closes
that gap with the firmware half, measured:

1. The option exists on this board at this exact firmware:
   "Resize BAR Support", PCI page, ONE_OF {0x00, 0x01}, default
   state per the form grammar's first option (Auto), invariant under
   the 3645 release.
2. "Auto" is conditional BY CONSTRUCTION: SUPPRESS_IF on
   Above4gDecode == 0, GRAY_OUT_IF on the hidden qid 0x361 == 1, and
   the vendor help's own three conditions — 64-bit PCI decoding, CSM
   disabled in the Boot section, a ReBAR-capable GPU. A board where
   CSM is enabled will silently keep ReBAR off while the option reads
   Auto: exactly "il détecte mal alors que c'est en auto", explained
   at the byte level, before any hardware is touched.
3. Linux verification (omarchy, 16/09): `omarchy-firmware diag-gpu`
   (gpu-bar1-small fires when ReBAR is off), `sudo lspci -vv` on the
   GPU for the "Physical Resizable BAR" capability's current size,
   `dmesg | grep -iE 'rebar|resizable'`, and GPU BARs above the 4 GB
   line in /proc/iomem once Above 4G decoding is active.

## The honesty ledger

- Pre-registered assertions all held (register gates): label
  "Resize BAR Support", qids 0x20E/0x20F/0x210, toks 1281/1403/1283,
  voffs 0x1BA/0x1BB/0x1BC, name-table offsets, release invariant,
  board invariant-modulo-one-byte.
- Kept open, not smoothed: (1) the common option-label tokens 3/4/5
  live in the SCSU-compressed strings package the ring-8 walker
  cannot cleanly decode — Auto/Enabled/Disabled stay unresolved by
  string walk (the axis labels are anchor-resolved and unaffected);
  (2) qid 0x361/0x35F's identity (hidden question; the CSM condition
  is documented by the vendor help, not yet bound to a walked
  question); (3) the CSM question itself lives in the Boot formset,
  outside this ring's walked bodies.
- The instrument's first selftest run: 3/6 (four real bugs: the voffs
  dict inverted, an exclusive scan bound, the packed-table backward
  walk landing on the current separator, and the ONE_OF depth model);
  final **11/11** with the crown live. The measurements were never in
  doubt — the gates were.
