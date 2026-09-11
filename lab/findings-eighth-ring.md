# The eighth ring — the dispatch graph, the string closure, and the package that never was (2026-09-11)

> Companion to `ovmf-findings.md` and rings one through seven. Same
> campaign, same rules: read-only, zero bytes written, surface freeze
> untouched. Instruments: `ring8_depex_dag.py`, `ring8_scsu_strings.py`,
> `ring8_pkg3_head.py`, with machinery reused verbatim from `ring4_lib`,
> `ring6_ifr_probe` and `ring7_facade_probe`. Ground truth for front C
> fetched from tianocore master this run (`SecureBootConfig.vfr`,
> `SecureBootConfigNvData.h`, `SecureBootConfigHii.h`). All opcode and
> SIBT tables parsed from the EDK2 spec header at runtime — the ring-6
> discipline held, and it caught this ring twice (RAW = 0x19 not 0x01;
> SKIP2 = 0x21 with a u16 count). Artifacts: `ovmf-depex-dag.json`,
> `ovmf-scsu-strings.json`, `ovmf-pkg3-head.json` (this repo).

## Front R1 — the dispatch graph: DEPEX is a DAG of protocol gates

Ring 2 counted DEPEX opcodes flatly; ring 8 evaluates every expression
as the postfix program it is, builds the graph, and reads the declared
dispatch order next to the derived one.

- **Zero BEFORE/AFTER in any build.** Every one of the 92 DEPEX sections
  on plain (14 PEI + 78 DXE) and 101 on secboot (17 PEI + 76 DXE + 8
  SMM) gates purely on protocol/PPI pushes — not one hard ordering
  constraint exists. OVMF's dispatch order is 100 % dependency-driven.
- **Zero FALSE expressions** — no compiled-out driver ships with a
  depex that can never dispatch. The spine: 37 DXE drivers with no
  depex at all (dispatch immediately, ordered only by the dispatcher's
  iteration) plus 3 TRUE-only expressions.
- The structural classes are chain-dominated: AND-chains of 2–14 gates
  (13 modules sit on 13–14-gate chains), 17–19 complex (OR/NOT)
  expressions, one single-gate per ~9 drivers.
- **The hubs** (fan-in, secboot): PcdProtocol **62**, DevicePathUtilities
  **54**, VariableArch 29, VariableWriteArch 29, CpuIo 22, MetronomeArch
  21, ResetArch 21, HiiDatabase 21, BdsArch 20. The platform's real
  chokepoint is the PCD protocol — every dynamic-PCD consumer waits on
  `PcdDxe`.
- **The declared order exists anyway**: both apriori files are present
  and parsed. PEI apriori: 1 entry. DXE apriori: DevicePathDxe, PcdDxe,
  AmdSevDxe, TdxDxe — and FvbServicesRuntimeDxe on plain only (5
  entries → 4 on secboot, exactly the variable-stack swap of ring 4).
- **The gate delta between builds is empty where it matters**:
  `changed_while_present = {}`. No module shared by plain and secboot
  ever changes its DEPEX class — the secboot build swaps whole modules
  in/out (17 added, 8 removed) and never re-gates a shared driver.
  And strictnx is byte-equal to secboot across the whole layer: the
  NX policy of ring 3/4 lives in `.text`, not in dispatch gating.

Day-0: one pass now yields the vendor's complete dispatch web — hubs,
spine, declared apriori order, and the BEFORE/AFTER count, which will
not be zero on a vendor image. The count itself becomes a finding.

## Front R2 — the SCSU layer and the last unresolved strings

- **The census**: 44 / 33 / 33 SIBT-closing strings packages (plain /
  secboot / snakeoil), all closing with residual 0 — 110/110. (Ring 7's
  25/28 counted packages inside forms-carrying modules only; both
  definitions are recorded.)
- **SKIP blocks exist after all — two per build, both SKIP2 (0x21), both
  in fr-FR packages** (DriverHealthManagerDxe, UiApp), and both packages
  close cleanly under the header-faithful u16 reading. The SKIP1/SKIP2
  width question is closed: the header wins, and ring 7's swapped
  widths never met a real SKIP block in the packages it paired.
- **SCSU blocks (0x10–0x13): zero occurrences in the corpus.** The
  ring-7 ledger line was precautionary. The state machine is now
  implemented anyway — SQn quotes, SCn/SDn window switching, SQU
  unicode quotes, SCU unicode mode — with 5/5 synthetic self-tests, so
  the grammar is complete even where the corpus is silent.
- The bytes also fixed the decoder's seeds: **compiled string packages
  ship LanguageWindow all-zeros** (not the UTS#6 defaults), no
  CharSet/PrintableLanguageName byte precedes the language tag, and
  `HdrSize == StringInfoOffset == 0x34`. The decoder's rule is
  therefore byte-driven: package windows if any word is non-zero,
  UTS#6 defaults otherwise.
- **The last unresolved ids are accounted, not hidden.** Ring 7's
  5/6 misses decompose into: one **id 0 per build — the spec's NULL
  string marker**, not a string at all; and 3–4 ids that matched other
  modules' packages **numerically only** — the "matched" text differs
  across builds ("Press F12 " vs "***NEW FILE***" for the same id) and
  is semantically foreign. Collisions, not cross-package references.
  Every genuinely needed string resolves within its own module.

Day-0: the vendor instrument can promise **total string accounting** —
every id is either resolved, the null marker, or a recorded collision
with its candidate texts. No silent `<placeholder>` survives.

## Front R3 — pkg3 never existed (the op-00 head dissolved)

Ring 7 registered one unresolved structure: SecureBootConfigDxe's
"second forms package" (273 B, secboot + snakeoil) whose head carried
two opcode-0x00 records — undefined in the EDK2 header — followed by
free-floating ONE_OF_OPTIONs, an unclosed FORM scope, and a 6-question
gap between the flat histogram (208) and the structural walk (202).

- The **alternative-anchor grid** (±24 B) proves the anchor was unique:
  exactly one type-0x02 header candidate opens at δ=0. The framing was
  never the problem.
- The **decisive fact is overlap**: pkg3's span (687896…688169) sits
  entirely inside the real 2186-byte package's span (686244…688430).
  **pkg3 is not a package — it is a spurious exact-consumption anchor
  nested inside the real one.**
- The **covering record** names it: a STRING question (op 0x1C, len 16)
  at 687889 — the "op-00 head" bytes are that record's raw field bytes
  plus the following real records, re-chained by the decoy anchor into
  something that looks like IFR. Exact consumption was necessary but
  never sufficient: the same bytes also admit a VARSTORE@+2 reading
  that consumes exactly and yields absurd fields (varstore_id 6545,
  size 6656, empty name). Consumption ≠ semantics.
- The **real package** walks clean: 289 records, exact close, **zero
  undefined opcodes, scope balance exactly 0** — ring 7's "unclosed
  FORM scope" was the same decoy artifact. Its single formset carries
  guid `5daf50a5-ea81-4de2-8f9b-cabda9cf5c14` — **byte-equal to
  `SECUREBOOT_CONFIG_FORM_SET_GUID` from tianocore master** — with 17
  forms including 0x15 = `SECUREBOOT_ENROLL_SIGNATURE_TO_DBT` (named
  from `SecureBootConfigNvData.h`), and varstore id 1 =
  `SECUREBOOT_CONFIGURATION` (the VFR's `varid 0x0001`). Source and
  bytes agree to the digit.
- The module's other small package (245 B) is real and self-consistent:
  its own formset `fe561596-e6bf-41a6-8376-c72b719874d0`, forms
  0x1000/0x2000/0x3000, 4 ACTIONs, 2 GUID-extension ops.
- **The accounting closes**: ring 6's flat 208 = ring 7's structural
  202 + the 6 question-class byte patterns the decoy chain counted a
  second time. The facade's structural walk was the true number all
  along.

Day-0: the direct exact-consumption finder gains the **nesting rule** —
a candidate whose span sits inside another candidate's span is a decoy
until the outer walk fails. One line of doctrine, bought with a week of
honest confusion, and it prevents the same false package from being
sold to the agent on the ASUS dump.

## Honesty ledger

- The SCSU decoder's unicode-mode return convention (the 0x0F0F pair)
  and SD selectors above 0x67 are **registered, not byte-provable**:
  the corpus contains zero SCSU blocks to exercise them.
- The LanguageWindow all-zeros fallback rule is likewise registered
  without a real consumer.
- The 245-B second formset's identity is not named beyond its bytes
  (guid, form ids, opcode histogram recorded).
- The 3–4 cross-module id collisions per build are recorded with their
  candidate texts; the bytes alone cannot distinguish an intentional
  runtime reference from numeric coincidence — the across-build
  instability argues coincidence.
- DEPEX hub names beyond the ring-2 curated public-registry subset stay
  raw GUIDs; the PEI apriori's single entry (9B3ADA4F-…) has no UI name
  in the census and is registered as "?".

## The ledger self-correction chain, one line per ring

Ring 5 locked the opcode layer → ring 6 re-derived the grammar
spec-fresh (and its own list-header lock) → ring 7 dissolved the list
as a category error → ring 8 dissolved its predecessor's last
registration (pkg3) as a double count and closed the string layer by
accounting. Every lock so far has resolved to "the question was better
than its premise" — which is why the instrument, not the answer, is the
deliverable.
