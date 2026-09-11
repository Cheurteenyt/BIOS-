# The seventh ring — the facade speaks and remembers (2026-09-11)

> Companion to `ovmf-findings.md` (the first OVMF reading) and the rings
> one through six. Same campaign, same rules: read-only, zero bytes
> written, surface freeze untouched. Instruments: `ring7_facade_probe.py`
> plus the `ring7_debug1*`/`ring7_debug2*` chain (sandbox), machinery
> reused verbatim from `ring6_ifr_probe.py`. Artifact:
> `ovmf-ifr-facade.json` (this repo). All opcode values parsed from the
> EDK2 spec header at runtime — zero memory-encoded constants, the
> ring-6 discipline held.

## Front R1 — the S2 lock was a category error: no package list ever ships

Ring 6 registered one lock: the package-LIST headers of the big IFR
carriers (UiApp, SecureBootConfigDxe, Tcg2ConfigDxe…) refuse to close,
while the forms packages themselves validate by exact consumption. The
hexdumps dissolve it: **the PE never contained a package list**.

- Every forms package is immediately preceded by a u32 equal to its own
  size **+ 4**: `0x00f9` before the `0x00f5` UiApp form, `0x012d` before
  `0x0129`, `0x088e` before `0x088a` — the length-prefixed blob model
  `{ u32 total }{ EFI_HII_PACKAGE_HEADER + body }`, prefix included.
  Verified on **20/21** forms packages across the secboot build (the 21st
  sits next to what reads as an address constant, `0x0c001700`; its
  validity still rests on exact consumption).
- The spec list header (`EFI_HII_PACKAGE_LIST_HEADER { GUID; PackageLength }`,
  re-derived from the header file — GUID first, length at +16) appears
  **zero times** in UiApp and SecureBootConfigDxe: ring 6's forward scan,
  re-run, closes zero candidates on both. The `{GUID, PackageLength,
  packages…, END}` list is a **runtime construction** — `HiiAddPackages`
  assembles it from the driver's blobs when the driver starts.
- The two honest exceptions: `tftpDynamicCommand` and `httpDynamicCommand`
  on the plain build still close as real lists (`0x04 → 0xDF`, strings +
  END). Real lists exist in the wild — they just are not how VFR drivers
  ship their forms.
- Ring 6's ledger sentence "the same five small carriers validate"
  narrows to those two; the other three were blob framing misread as
  lists. The S2 entry self-corrects here, as the ring-5 entry did in
  ring 6.

Day-0 consequence: the vendor instrument must enumerate **packages**, not
lists — a vendor "setup module" is a folder of length-prefixed blobs, and
nothing guarantees a list header to anchor on.

## Front R2 — the SIBT layer decoded (the strings stop being opaque)

The string-information-block grammar, spec-fresh: blocks carry **no
explicit length** (except EXT1/2/4 wrappers), string ids are **sequential
from 1**, `SKIP1/SKIP2` advance the id without defining it, `DUPLICATE`
aliases an earlier id. The walk must reach `SIBT_END` with ≤ 3 bytes of
residual before the package end — that is the validator, and it is as
strict as ring 6's exact consumption.

- 25 strings packages resolved on plain, 28 on secboot, across the setup
  modules — including BdsDxe's (21 ids: "A configuration change was
  requested to %s this computer's TPM…"), closing the ring-3 observation
  that its 95 utf-16 strings are data **consumed by** forms, never owners
  of any.
- The STRING package header itself byte-confirms the spec: `HdrSize`,
  `StringInfoOffset` = 0x34 = 4 + 4 + 4 + 32 (LanguageWindow) + 2
  (LanguageName) + "en-US\0" — the offset lands exactly after the
  language tag on every carrier checked.

## Front R3 — the facade in words (en-US, and fr-FR)

Every question now carries its text. Resolution is per forms package,
best-coverage English-first pairing against the module's strings
packages: **296/301 ids resolved on plain, 369/375 on secboot** (98 %+;
the handful of singletons are registered, not hidden).

What the setup actually says, read from bytes, not screenshots:

- "Secure Boot Mode" — Standard Mode (0) / Custom Mode (1)
- "Signature Format" — X509 CERT SHA256 / SHA384 / SHA512 / X509 CERT
- "Internet Protocol" — IP4 (0) / IP6 (1)
- "iSCSI Mode" — Disabled / Enabled / Enabled for MPIO
- "Disk Memory Type:" — Boot Service Data / Reserved
- "Policy" — automatic / manual

And the finding nobody ordered: **the OVMF facade is bilingual**. UiApp
ships 5 en-US **and** 5 fr-FR strings packages — same ids, same list, the
spec's multi-language shape done right. The sampled fr-FR text is largely
untranslated ("File Explorer", "Device Manager"): bilingual support is a
structure, not a translation. On day-0 the same probe reads the vendor's
languages before reading anything else.

## Front R4 — the facade's memory: varstores, offsets, defaults

The dissection (scope-stack walk: questions attach to forms, options and
defaults attach to the innermost open question) names what the setup
**writes**:

- 11 standard varstores on plain / 12 on secboot, each a named NVRAM
  blob: `SECUREBOOT_CONFIGURATION` (100 B),
  `ISCSI_CONFIG_IFR_NVDATA` (**17,724 B** — the largest), `BmmData`
  (3,576 B), `IP6_CONFIG_IFR_NVDATA` (1,592 B),
  `HTTP_BOOT_CONFIG_IFR_NVDATA` (662 B), `IP4_CONFIG2_IFR_NVDATA`
  (608 B), `VlanNvData` (104 B), `TLS_AUTH_CONFIG_IFR_NVDATA` (74 B),
  `MainFormState` (36 B) — plus Tcg2's three EFI varstores:
  `TCG2_CONFIGURATION` (**1 byte** — the TPM switch),
  `TCG2_CONFIGURATION_INFO` (9 B), `TCG2_VERSION` (16 B).
- This is the Q1 ↔ Q5 bridge, structurally: facade question → varstore
  id → byte offset inside a named variable. The "Setup blob is mostly
  undocumented" answer of open-questions Q5 now has a method: the blob's
  field map is literally the IFR question table.
- The hidden surface gets its per-question price: **48/146 questions
  (plain) and 64/202 (secboot) sit behind SUPPRESS_IF / GRAYOUT_IF /
  DISABLE_IF** — conditions whose operands (EQ_ID_VAL against varstore
  offsets) are also decoded.
- One more spec correction worth keeping: `EFI_IFR_QUESTION_HEADER` is
  **11 bytes** (statement 4 + question id 2 + varstore id 2 + varstore
  info 2 + flags 1), byte-proven by CHECKBOX lengths (`0x0e` = 2 + 11 +
  1). With it, the walk reproduces ring 6 exactly: **146/146 questions
  attached on plain, options 33/33** — two independent methods, one
  number.

## Day-0 consequences

- The chain pierce → FFS → PE32 → length-prefixed blobs → SIBT + IFR is
  vendor-ready end to end: on the ASUS dump it renders the vendor facade
  in words (pages, questions, options, conditions), names every varstore
  and default, and reads the languages — no screenshot is ever
  interpreted by hand.
- The agent's explanations get their source material: "this page asks
  this, writes that offset of that variable, defaults to this value" is
  now a lookup, not a guess.
- The ring-6 instrument and the ring-7 render agree on OVMF (146/146);
  on the vendor image the same double-run becomes the sanity check.

## Honesty ledger

- **pkg3** (SecureBootConfigDxe, `direct_0xa7f18`, secboot + snakeoil):
  its head carries two records with **opcode 0x00 — undefined in the
  current EDK2 header** — followed by three free-floating ONE_OF_OPTIONs
  and two ENDs; the rest is real IFR (DISABLE_IF/EQ_ID_VAL/TEXT, a
  CHECKBOX, a DATE and a TIME question bound to varstore id 1, REFs, and
  a scoped FORM id 0x15 whose scope does not close inside the package).
  Its 6 question-class histogram occurrences are therefore counted by
  ring 6's flat histogram (secboot 208) but **not** structurally attached
  by the facade walk (202). The difference is exactly these 6, fully
  located; no interpretation is forced.
- SCSU-encoded strings (block types 0x10–0x13) are recorded as `<scsu>`
  placeholders — the state machine is not implemented; every porteur that
  matters walked with residual 0 under UCS2.
- 5 string ids (plain) / 6 (secboot) fail resolution — singletons per
  package, plausibly cross-package references; registered.
- The prefix model is proven on forms packages; strings packages are
  found by direct SIBT-validated discovery without assuming the prefix —
  the framing of the one prefix-MISS package is part of the pkg3 entry.
- The closing list headers of tftp/http dynamic commands are accepted as
  real lists; their GUID field is not decoded (registered).
