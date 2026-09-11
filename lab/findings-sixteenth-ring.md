# The sixteenth ring — the levels, the waves, the nine bytes (2026-09-11)

> Companion to rings one through fifteen. Same campaign, same rules:
> read-only over downloaded vendor images, zero bytes written anywhere
> but the lab record. Instruments this ring: `ring16_byte_forensics.py`,
> `ring16_agesa_lens.py`, `ring16_armor_bisect.py`,
> `ring16_armor_wave1.py` (sandbox) — the ring-15 walk and the
> first-contact machinery imported verbatim, no grammar rewritten.
> Artifacts: `vendor-agesa.json`, `vendor-flash-armor.json`,
> `vendor-byte-forensics.json` (this repo). The directive: continue
> the massive investigation. The ring closed three debts ring 15 had
> registered: what the same-size changes actually contain, where the
> AGESA level hides, and when the flash armor arrived.

## Front 1 — byte forensics: nine bytes against six thousand

Ring 15 measured WHO changed. The same-size pairs are the purest
laboratory: no padding, no relocation — only content. Four targets
from the ring-15 register (GUIDs read from the register, never from
memory):

**`AcpiTableDxe` changed by exactly 9 bytes** — eight spans of one to
two bytes, every one landing in compare/branch code sequences. That
is a surgical patch: the vendor's engineers touched eight decisions
in an 18-KB driver and shipped it inside a release that also moved
half a board. At the other extreme, **`ACPI` (16D0A23E) rewrote
6,215 of its 10,646 bytes (58.5 %) at constant size** — mid-size
spans clustered in the 2465-2900 AML/code region plus scattered
single-byte edits: a genuine rework that kept its footprint.

**The NVRAM anchor** (`CEF5B9A3…`, ring 14's store) changed 778
bytes: one header-area byte at offset 4, then 17-26-byte spans
clustered at 759-977 — precisely the HWM/QFan default-value region
(the span contexts carry `NV_SIO0_LD1`, `SetupHWMOneof`, `QFan`).
ASUS retuned the fan/monitoring defaults between releases; the
factory NVRAM register now knows *which defaults moved*.

**The "one-byte change" was a mirage.** `1DF36FF9` (80,232 → 80,231
B) shares only a 16-byte prefix and then matches 0 % across the
whole overlap: the payload was replaced wholesale at the same GUID,
the size delta a coincidence. Body-hash identity saw the truth;
size comparison never could — the ring-15 method vindicated by its
own edge case.

## Front 2 — the AGESA lens, pierced: all six levels byte-verified

Ring 11 byte-verified MSI's `ComboAM4v2PI 1.2.0.8` in the raw blob;
the same scan returned zero on ASUS, Gigabyte, ASRock — and the
ring-12/14 registers carried four "unverified" AGESA claims into
day-0. The lens this ring extends the scan to the *pierced interior*
(every LZMA-decompressed inner volume, the OVMF pattern applied
board-wide). The levels were there all along, roughly 2.7-2.9 MiB
into the decompressed 0x9c0000 payload:

| Specimen | AGESA (byte-verified) | Claim | Verdict |
|---|---|---|---|
| ASUS PRIME 4655 (2026) | `1.2.0.12` | unverified | **NEWLY VERIFIED** |
| ASUS PRIME 3604 (2022) | `1.2.0.6b` | unverified | **NEWLY VERIFIED** |
| ASUS TUF 4645 (2026) | `1.2.0.F` | unverified | **NEWLY VERIFIED** |
| MSI 7C02v3G1 (2023) | `1.2.0.8` | 1.2.0.8 | MATCHES |
| Gigabyte F67c (2026) | `1.2.0.12` | 1.2.0.12 | MATCHES |
| ASRock 10.41 (2025) | `1.2.0.E` | 1.2.0.E | MATCHES |

Zero vendor lies detected; four blanks filled. Side harvest:
Gigabyte's image also yields SMU firmware versions
3.4.1.1-3.4.2.4 (fourteen distinct). On day-0 the dump's AGESA level
is one regex away once its volumes are pierced — a third
independent dating signal beside version strings and NVRAM defaults.

## Front 3 — the flash-armor bisect: two waves, one security year

Ring 15 found seven modules ADDED to the board between 2022 and
2026 — the flash-path armor (`PrepareWhiteListSmm`, `SbRomArmorSmm`,
`FlashSmiSmm`, `FlashSmiDxe` + three unnamed files). When did they
arrive? The official API ledger was re-fetched (40 entries now —
ring 12 recorded 39; one release aged in) and the 13 intermediate
releases bisected with the proven walker. Sentinels free (3604:
armor 0/7, removed 2/2 — 4655: armor 7/7, removed 0/2); four
official downloads; register written after every probe.

The answer is **two waves, not one**:

- **Wave 1 — by 4202 (2023-08-02)**: the core SMM armor
  (`FlashSmiSmm`, `FlashSmiDxe`, `PrepareWhiteListSmm`,
  `SbRomArmorSmm` + one freeform) is present, 5/7. Releases 3802,
  3810, 4003 between 3604 and 4202 were not probed (bounded
  download budget) — "present by", not "introduced at". One of the
  two REMOVED legacy SMM modules was still present at 4202 (1/2)
  and gone by 4402 — the retirement was staged too.
- **Wave 2 — 4604 (2024-04-08)**: the set completes, 7/7 — the DXE
  helper (4EB43107) and the second freeform join. 4402 (2024-01-08)
  sat in between with 5/7.

The security reading: the core wave brackets the LogoFail disclosure
window (2023). ASUS hardened the flash path on this board line
inside exactly that year — consistent with an industry-wide
response, not a random refresh. Day-0 consequence: if the dump
proves older than 4202, the *absence* of the five core GUIDs is
itself a finding (flash-path hardening absent); at 4604+ the full
seven are expected, and their absence would be an anomaly.

Provenance note: the vendor publishes per-release sha256 only for
newer entries (4631 verified byte-exact this ring; 4402/4604/4202
carry none — their provenance rests on the official CDN URL alone,
recorded as such).

## Honesty ledger

- GUIDs for every target came from the ring-15 register by name
  match; one candidate list was drafted from memory, caught in
  self-review, and discarded before the first run — the rule held.
- The wave-1 verdict logic shipped with a case-sensitivity bug
  (`v` not lowered against the lowercased claim); it mislabeled
  ASRock as REFUTES-CLAIM. Caught on the same output that exposed
  it, fixed at source, re-run — all verdicts correct. The wrong
  labels survive only in the conversation, never in a register or
  artifact.
- Span geometry is structural, not a disassembly: cmp/jcc readings
  come from instruction-byte shapes in the context windows; no
  opcode semantics are claimed beyond that.
- ACPI/AcpiTableDxe interpretations rest on ONE target file pair;
  they characterise those modules, not ASUS ACPI practice at large.
- The bisect boundary logic assumes monotonic presence; the staged
  wave discovery (5/7 at 4402) is exactly why the register records
  per-probe presence sets, not just the final boundary.

## Consequences for day-0 (16/09)

- **Three independent dating signals are now calibrated**: version
  strings (ring 13), NVRAM factory defaults (ring 14 — now with the
  3604-vs-4655 HWM/QFan diff as a fingerprint), and the AGESA level
  (this ring). The dump's identity can be triangulated three ways.
- **The flash-armor checklist is versioned**: five GUIDs expected
  from 4202 on, seven from 4604 on, two legacy modules expected
  gone by 4402. The dump's presence set lands on this timeline.
- **The byte-forensic method is proven on real vendor pairs**:
  same-size diffs give surgical answers (9 bytes) at zero risk —
  the ideal first-hour measurement on the dump against 3604/4655.
