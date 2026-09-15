# The fiftieth ring — the ReBAR language: what the options actually say

*Ring 50 · 2026-09-15 · instrument `lab/fw50-rebarlang.py` · crown
`lab/vendor-rebarlang-register.json` · composing frozen fw49 (and through
it fw37/fw43)*

## The founder's word, finished at the byte

Ring 49 froze the ReBAR AXIS — the option exists ("Resize BAR Support",
ONE_OF qid 0x20F at Setup-varstore 0x1BB), its conditions are wrapped
around it (SUPPRESS_IF `Above4gDecode==0`, GRAY_OUT_IF `qid 0x361==1`),
its pair law is measured (release-invariant, board-invariant modulo one
qid byte) — and left three questions open, honestly: the option-label
tokens 3/4/5 ("SCSU-compressed, garbage windows"), the identity of the
grayout operand qid 0x361, and the CSM question's page. The founder had
said: *"le reshade bar ... il détecte mal alors que c'est en auto"*. The
axis was measured; the LANGUAGE — what the options actually SAY — was
not. Ring 50 measures the language, and both corrects ring 49 and names
its grayout operand.

## Front A — the strings package and the base law (the correction)

The Setup module (1,421,088 B, sha16 `d1f8b81801258527`) carries ONE
standard HII STRING package header directly above the forms' closing
ENDs (`29 02` ×4): `EFI_HII_PACKAGE_HEADER` at 367586 — Length
**0x041DC2** (269,762 B), Type **0x04** (STRINGS), HdrSize **0x34**,
StringInfoOffset **0x34**, LanguageWindow[16] **all-zero** (the ring-8
corpus's seeding rule applies verbatim), LanguageName **1**, tag
**"en-US"**. The blocks are the AMI variant of SIBT: id-less
`SIBT_STRING_UCS2`-style runs (marker 0x14, utf16z text, NUL-NUL) — and
therefore **block ordinal k IS StringId k+1**, verified by walking the
map forward from the floor and reaching the ring-49 anchor in EXACTLY
**1280 steps** with the anchor text "Above 4G Decoding" at tok 1281.
StringId 1 = the language name "English" — the package's own
LanguageName field references it, the HII convention closes both ways.

**THE CORRECTION (kept visible, the frozen ring-49 register never
rewritten):** ring 49's open question claimed toks 3/4/5 live in an
"SCSU-compressed strings package the ring-8 walker cannot cleanly
decode". Measured: they are PLAIN UTF-16 at the package floor. The
failure mode was ring 49's own backward walker — `entry_before` skips
empty entries (its marker test `pe[p]==0x14 && pe[p+1]!=0` rejects an
empty entry's marker) and the unvalidated 1400-step `anchor_table` walk
runs past the table floor into machine code. The census:
**50 mis-steps over 1280 backward steps**, with `''` at tok 2 and a
cluster of five empties around ordinal 121 among the offenders. The
honest index is the FORWARD map from the measured floor; `nulllang`
keeps the census as a permanent measurement.

## Front B — THE VOCABULARY (the founder byte-true)

The floor labels: tok 1 "English", tok 2 "", **tok 3 "Enabled"**, **tok 4
"Disabled"**, **tok 5 "Auto"**, tok 6 "Setup", tok 7 "Setup", tok 8
"Main". The decoding family's ONE_OF vocabularies, measured live:

| question | qid | options |
|---|---|---|
| Above4gDecode | 0x20E | 0x00 **Disabled** / 0x01 **Enabled** |
| **ResizeBarSupport** | **0x20F** | 0x00 **Disabled** / 0x01 **Auto** |
| SriovSupport | 0x210 | 0x00 **Disabled** / 0x01 **Enabled** |
| CsmSupport | 0x2900 | 0x00 **Disabled** / 0x01 **Enabled** |
| CsmSupport+1 (0x2901) | | Ignore / UEFI only / Legacy only |
| MmioAddrLimit | 0x310 | 38bit (256GB) … 43bit (8TB) |

**The ReBAR question is the ONLY one of the family whose positive value
is Auto — and "Enabled" does not exist for it at all.** The founder's
"c'est en auto" is byte-true (value 0x01 IS the "Auto" label, tok 5);
and the vendor UI offers no way to force ReBAR on: the Auto heuristic is
the ONLY path to engagement. "Il détecte mal alors que c'est en auto" is
now a measured sentence: the option said Auto because Auto is what it
says; the detection chain below it did not fire. The vendor help text
(tok 1404) documents the chain verbatim — 64-bit PCI decoding (Above 4G
Decoding), CSM disabled in the Boot section, a ReBAR-capable GPU — and
the IFR adds the structural gate: when `Above4gDecode == 0` the whole
ReBAR question is SUPPRESSED (hidden), not merely disabled.

## Front C — the grayout operand NAMED (SystemAccess)

qid **0x361** (sibling **0x35F**) is a hidden NUMERIC — op 0x07, prompt
tok 0, help 0 — bound to **varstore 4, offset 0x0000**, u8, range
[0x00, 0xFF]. Varstore 4 is declared at the formset head: name
**"SystemAccess"**, size **1 byte**, GUID
`E770BB69-BCB4-4D04-9E97-23FF9456FEAC`. The GRAY_OUT predicate reads
`SystemAccess[0] == 1`: the ReBAR option grays out when the AMI TSE
session-privilege variable holds 1 — a restricted setup session (the
"Access Level" labels sit in the same floor region: "User",
"Administrator"). The precise value semantics (0 vs 1 vs 2) live in the
TSE binary, not the IFR — named, not semantically decoded; the open
question is registered.

The varstore census (op 0x24 declarations, 51+ rows) also names the
neighborhood: vsid 1 "Setup" (515 B declared, GUID
`EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9`, with AMI's region-chunk
convention stacking further same-vsid declarations: "SetupCpuFeatures",
"SetupAPMFeatures", "SetupLedData"…), vsid 2/3 "PlatformLang(Codes)",
vsid 49 "VendorKeys", 50 "SetupMode", 51 "SecureBoot",
48 **"SecureVarPresent"** (6 B, GUID
`7B59104A-C00D-4158-87FF-F04D6396A915`).

## Front D — the two "extra WIFI questions" corrected

The ring-49 pair law said the sibling's question space is "two questions
shorter, the WIFI questions it lacks". Measured, that reading is
**REFUTED**: the WIFI II's extra qids 0x35D/0x35E are hidden questions
reading **SecureVarPresent[0]** and **SecureVarPresent[4]** (varstore
48, the Secure Boot variable-presence bitmap) — Secure Boot
variable-presence readers, nothing to do with wifi. The grayout
operand's shift (0x361 → 0x35F) is the knock-on effect of those two
Secure-Boot questions, not of wifi ones. Correction named, kept visible,
the frozen register untouched (rings 45/47/48 precedent).

## Front E — the pair law at the language level

The language is **INVARIANT** across all three acquisitions: toks 1..8
identical on 3644 / 3645 / nw-3644; the four sisters' option
vocabularies identical; the package header identical on 3644/3645
(269,762 B) and the sibling's 177 B shorter (269,585 B, floor at
367530). The only measured mover remains the grayout operand's qid
(0x361 ↔ 0x35F) — ring 49's pair law re-derived one level up: **the
16/09 flash changes nothing in what the options SAY; the stock NVRAM
bytes 0x1BA/0x1BB decide the chain on the dumped board.**

## Pre-registration ledger (frozen in the instrument source before measurement)

| PR | claim | verdict |
|---|---|---|
| PR-1 | forward count floor→anchor == 1280 (tok = ordinal + 1) | hit |
| PR-2 | ReBAR ONE_OF = {0x00: Disabled, 0x01: Auto}, no third option | hit |
| PR-3 | Above4g/Sriov/Csm = {Disabled, Enabled}; ReBAR the only Auto | hit |
| PR-4 | grayout qid 0x361 = hidden NUMERIC u8, vsid 4, voff 0 | hit |
| PR-5 | varstore 4 = "SystemAccess", 1 B, GUID E770BB69… | hit |
| PR-6 | varstore 48 = "SecureVarPresent"; the extra questions read it — ring 49's "WIFI questions" refuted | hit (refutation kept visible) |
| PR-7 | language invariant across all three acquisitions | hit |
| PR-8 | ring 49's SCSU reading corrected: plain UTF-16; the walker was the failure | hit (correction kept visible) |

## Instrument and battery

`lab/fw50-rebarlang.py` (modes `lang` / `pair` / `nulllang` / `selftest`
/ `manifest`), four laws (L1 labels-over-guesses — forward map from a
MEASURED floor, count both ways; L2 anchors-before-marks — the four
sisters must reproduce the ring-49 crown or refuse; L3 zero writes; L4
compose-on-frozen — `entry_before` used only where its semantics are
proven). Selftest first run 12/15 (three TEST bugs: a gate pointed at
the wrong synthetic entry, a leftover nonsensical clause, a tag decoded
with its NUL; then a KAT calling the wrapper instead of the inner
walker); final **15/15** with the crown live. The crown
`vendor-rebarlang-register.json` written once by
`scripts/ring50_register.py` (assertion-gated, roundtrip-checked).
Battery: 323/323, MCP smoke OK, fw35 36/36, fw49 11/11, fw50 15/15,
frozen surface 0 diff (bin/lib/tests).

## Day-0/day-1 reading (what the dump and the live board owe us)

The ReBAR language is invariant under the flash, so the day-0 dump
carries the stock chain. On the live board, "il détecte mal alors que
c'est en auto" now has a byte-level checklist, in order:

1. **Above 4G Decoding must be Enabled** — else the ReBAR question is
   hidden entirely (SUPPRESS_IF) and Auto can never engage.
2. **Resize BAR Support reads Auto** — byte-confirmed as the only
   positive value; there is no "Enabled" to force.
3. **CSM disabled in the Boot section** (the vendor help's own NOTE;
   CsmSupport 0x2900 = Disabled).
4. **A ReBAR-capable GPU** in the PCIe slot.
5. **The setup session unrestricted** — SystemAccess[0] == 1 grays the
   option out; enter the setup with administrator rights.

Then the OS half: `omarchy-firmware diag-gpu` (`gpu-bar1-small` fires
when BAR1 ≤ 256 MiB = ReBAR off), `sudo lspci -vv -s <gpu> | grep -A4
"Physical Resizable BAR"`, `dmesg | grep -iE 'rebar|resizable'`, GPU
BARs above the 4 GB line in `/proc/iomem`. The founder's symptom is no
longer "the BIOS half is not observable from the OS": both halves are
anchored, and the chain has five named gates, each readable before any
hardware is touched.

## The honesty ledger

- Ring 49's register is frozen; both of its refuted readings (SCSU
  labels, "WIFI questions") live HERE, named, with the measurements that
  refute them.
- The floor/base law was verified on one anchor (tok 1281) with a
  1280-step count; a second anchor cross-check exists (tok 1283
  "SR-IOV Support" forward) but the map beyond ~2000 entries was never
  exercised — the fan-page and Boot-Configuration strings above the
  census regions remain unanchored by this ring.
- SystemAccess's value semantics and the SecureVarPresent bitmap's field
  order are named, not decoded — they live in vendor binaries, and the
  instrument refuses to guess.
- The `nulllang` census is a measurement of a FLAW — it stays in the
  instrument as long as `entry_before` stays in the frozen surface it
  composes on.
