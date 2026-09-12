# Open Questions — The Investigation Map

> Status: living document. **No code surface changes during the 0.7.0 freeze.**
> Every question here is answerable **read-first**: zero bytes written to the SPI chip.
> Companions: `docs/spi-map.md` (the read-only cartography), `lab/coreboot-notes.md`
> (Volume 5 doctrine), `docs/security-doctrine.md` (the walls).

The ambition is the same as Omarchy's: **search everywhere**. The discipline is ours:
read everywhere, write never — until Volume 5, on dedicated sacrificial hardware.

Each question carries three horizons:

| Horizon | Meaning |
|---------|---------|
| NOW     | answerable today, read-only, on the twin or from public documentation |
| DAY-0   | answerable on the real board on 16/09, via `spi-map` and a saved dump |
| VOL-5   | requires Volume 5 (dedicated hardware, dump-first, external programmer) |

---

## Q1 — Does the firmware let us disable what we want? (the setup facade)

**Honest answer: no.** The setup screen is a facade in front of a much larger
machine. What the F2/Del menu exposes is a reader/writer of NVRAM variables
(typically one binary `Setup` blob) consumed by DXE drivers at boot. Three
layers hide the rest:

1. **Hidden options** — forms suppressed by vendor tokens; the variables exist,
   the UI never shows them.
2. **Policy locks** — registers the firmware itself write-protects (SPIBAR
   `BLE`/`SMM_BWP`, `IA32_FEATURE_CONTROL`, SMM lock MSRs).
3. **Silicon facts** — Boot Guard FPF fuses burned at the factory; ME behavior
   on consumer silicon; SMM is not negotiable.

**The measurable gap**: `{modules actually present in the image}` minus
`{options visible in setup}` = the hidden surface of the platform.

- NOW: `spi-map` on the synthetic image already enumerates DXE/SMM modules with
  names; the method is proven.
- RING-6 (the facade quantified in questions, not sentences): the IFR grammar
  re-derived spec-fresh (`{OpCode:8, Length:7, Scope:1}`, FORMS = 0x02 — see
  `lab/findings-sixth-ring.md`) lets the probe count the setup's actual
  questions per module: OVMF plain = **146 questions / 58 pages** across 11
  modules; secboot = **208 / 79** (SecureBootConfigDxe alone = 62). The same
  probe runs on the vendor dump — the ASUS setup gets its button count on
  day-0 without a single screenshot being interpreted by hand.
- RING-7 (the facade speaks and remembers — see `lab/findings-seventh-ring.md`):
  ring 6's locked list-header question dissolves as a category error (HII
  packages ship as length-prefixed blobs; the package list is built at runtime
  by `HiiAddPackages`), the SIBT string grammar is decoded, and the facade now
  renders **in words** — every question with its text (296/301 ids resolved on
  plain), its options with values, its **varstore name and byte offset**
  (`SECUREBOOT_CONFIGURATION`, `ISCSI_CONFIG_IFR_NVDATA` 17,724 B,
  `TCG2_CONFIGURATION` = 1 byte…), its defaults, and its condition:
  **48/146 (plain) / 64/202 (secboot) questions sit behind SUPPRESS_IF /
  GRAYOUT_IF / DISABLE_IF** — the hidden surface priced per question. The
  Q1 ↔ Q5 bridge (what the UI asks ↔ what NVRAM holds) is now structural,
  and OVMF turns out bilingual (5 en-US + 5 fr-FR strings packages in UiApp).
- RING-19 (the vendor facade quantified BEFORE the dump — see
  `lab/findings-nineteenth-ring.md`): the ring-6 grammar ported to six
  vendor-representative specimens, 100 % of form packages valid by exact
  consumption; the vendor facades carry **6,360-8,646 questions across
  732-1,104 pages** (MSI the largest at 8,646/1,104, Setup alone 4,222;
  ASUS 7,975 → 8,273 across its own chronology), AMD's CBS dominating every
  board (513-1,178 questions per CPU-family variant). The hidden surface
  INVERTS: ~zero SUPPRESS/GRAYOUT/DISABLE conditions across 46,000+ vendor
  questions (exactly one SUPPRESS_IF in the corpus) — on vendor boards the
  hiding is VARIABLE-level (unexposed `Setup` fields, ring 14), not
  question-level. The day-0 screenshot delta now has an expected magnitude,
  not just a method.
- RING-20 (the unasked bytes — see `lab/vendor-unasked.json`): the hidden
  surface is now priced in BYTES per vendor. Gates reproduce ring 19's
  question totals exactly on five specimens, then coverage lands: 84-90 %
  of varstore bytes are never referenced by any question, and the `Setup`
  blob itself carries 142-567 never-asked bytes per board (ASUS 456/142,
  MSI 1,428/567, Gigabyte 628/247, ASRock 677/260). The IFR-side Setup
  sizes match ring 14's NVRAM side exactly — the Q1↔Q5 bridge closes from
  both ends, and day-0's Setup row has an expected magnitude to land on.
- RING-21 (the hidden map — see `lab/vendor-hidden-map.json`): the pricing
  becomes a MAP — the never-asked `Setup` offsets as merged
  [offset, length) ranges, per vendor. The ASUS layout is FROZEN across
  4.5 years: 3604 and 4655 carry the same 456-B store, the same 142
  never-asked bytes, the same 27 ranges at the same offsets. The hidden
  surface is fragmented, not one tail block (MSI: 567 B in 166 ranges).
  Knowledge-only: the map prices what a setup_var-style editor COULD
  address; the zero-write doctrine is untouched. Day-0 now has an
  offset-level expectation, not just a magnitude.
- RING-23 (the vocabulary clock — see `lab/vendor-vocabulary-clock.json`):
  the string layer behind the questions is decoded along the nine ASUS
  rungs (ring 7 package discovery + ring 8 UCS2/SCSU decode, 27 modules
  / 29 packages / ~5K distinct strings per rung). The facade's WORDS
  move at their own frontiers, disjoint from the body-churn clock:
  the security waves (legacy-SMM retirement 4202, wave-2 4604, the big
  AGESA rebuilds) land ZERO new words — the vendor does not advertise
  security work. The ONE security-flavored option ever exposed is
  `PSP RPMC Switch`, born exactly at the armor release 3802, help text
  stamped by the vendor "for test purpose only, NOT FOR PRODUCTION!!".
  Day-0 gains word-level expectations (RPMC present, `Stability Boost`
  on 4631+-lineage builds).
- DAY-0: real module list vs. a manual inventory of every setup screen
  (screenshots). The delta is what the vendor ships but does not show.
- VOL-5: per-vendor NVRAM editors (`setup_var`, AMISCE, SCEWIN) — referenced
  for knowledge only; they **write** if used on a live machine, so they stay
  out of every machine in the guard fleet.

## Q2 — Display without a graphics card?

**Honest answer: pre-OS, correct.** No GPU and no iGPU means no GOP (UEFI) and
no VBIOS OpROM (legacy CSM), which means no framebuffer and a black screen.
But three channels never die:

- **Serial / UART** — on boards that expose a header or a vendor debug console;
- **POST codes on port 80h** — readable with a two-digit debug card;
- **BMC/IPMI** — server boards only; not our case.

**And the doctrine makes it mostly irrelevant for the agent**: the agent lives
in the Linux runtime, and Linux draws (KMS, simpledrm). The firmware only needs
a display when the firmware itself is broken — and then the display is dead by
definition. That is exactly why Volume 5 demands an external programmer: when
the screen is gone, the chip socket becomes the screen.

- NOW: `lab/ovmf-smoke.sh` is headless by construction — the serial log *is*
  the display. Proof that boot does not require display. **Massive
  campaign (2026-09-11):** real VBIOS ROMs parsed — display pre-OS is
  literally an Option ROM (0x55AA/PCIR, x86 code, e.g. vendor
  0x1234:0x1111); a real DSDT table was read at header level too. The
  display is a swappable driver with a physical body. **Second ring
  (2026-09-11):** the shipped NVRAM itself proves the doctrine —
  `ConOut`/`ErrOut` in the real variable store decode to a `PNP0501`
  serial UART at **115200 8N1** (`EFI_UART_DEVICE_PATH` shape, verified
  against the bytes), `ConIn` adds a `PNP0303` keyboard. The never-dying
  channel is a first-class console in the shipped store, not a lab
  artifact. **Third ring (2026-09-11) — the facade has a price tag:**
  the setup's own vocabulary, read from the bytes — UiApp 165 distinct
  utf-16 strings, BdsDxe 95 (including the Debian fingerprint
  "Grub Bootloader"), SecureBootConfigDxe 99 ("Are you sure you want to
  delete PK? Secure boot will be disabled!"), Tcg2ConfigDxe 64 (the
  TPM screens). ~423 sentences across 4 modules vs 115 DXE modules —
  the hidden surface has a denominator and a method now (utf-16
  census per setup module, transferable to day-0 screenshots).
- DAY-0: does the board expose a UART header or a vendor debug path? Physical
  inspection + vendor datasheet.
- VOL-5: serial debug builds (coreboot console over UART) on sacrificial
  hardware only.

## Q3 — The kill-list: what can actually be switched off?

A per-board table to fill progressively. Shape:
`feature / setup toggle? / NVRAM variable / enforced by / consequence if off`.

Seed rows: Secure Boot, TPM, ME (HAP/MEI disable), CSM, network stack, USB
legacy, iGPU, hyperthreading, cores, SMM. Known shape so far: everything
setup-exposed is switchable; ME is partial on consumer silicon (full disable
often means no POST); Boot Guard is never (fused).

- NOW: seed from the vendor manual and coreboot board notes.
  **Massive campaign (2026-09-11) seeds for TWIN-1 (B450-PLUS):** no
  coreboot port exists anywhere on the web (standing claim holds); the
  B450 family ships USB BIOS FlashBack — a CPU-independent VENDOR
  rescue path (verify the physical button at day-0; it writes the
  chip, so it stays outside our hands, Volume 5 rules only); ASUS
  boards also carry a .CAP USB recovery path; AMD Platform Secure Boot
  (PSP) is the AMD Boot Guard — silicon again.
- DAY-0: verify each toggle against the real setup screens and the dump.
  **Second ring (2026-09-11) adds the row vocabulary:** the kill-list rows
  have a byte-level anatomy now — each switch is an NVRAM variable with a
  namespace GUID, attributes, and an owner module; the security x-ray
  maps who carries `SecureBootEnable` / `CustomMode` (`SecureBootConfigDxe`
  + the variable service only). Deletion is a state-byte flip — a killed
  feature leaves archaeology until FTW reclaim. **Third ring
  (2026-09-11) adds the amputation lists:** `lab/ovmf-kill-list.json` —
  the blueprint's first machine-readable kill-list with GUIDs; the
  network stack alone is 21 modules (Snp→Mnp→Arp→DHCP→IP→UDP→TCP→
  TLS→HTTP→PXE→iSCSI), plus storage (18), usb (6), display (6) for
  context. "Will not ship" now has a GUID-precise meaning.

## Q4 — Who enforces the walls? (the enforcement map)

The five walls from `lab/coreboot-notes.md`, each with an owner:

| Wall | Owner |
|------|-------|
| Boot Guard | FPF fuses (factory) |
| ME | silicon policy (Intel) |
| SPI write protection | SPIBAR (`BLE`, `SMM_BWP`) set by firmware |
| SMM | CPU ring -2, handlers in the image |
| EC | separate chip, separate firmware, **never on the SPI bus** |

- NOW: table drafted; per-board assignment pending real data.
  **Massive campaign (2026-09-11):** the AMD half of the map is
  prepared — PSP Directory (`$PSP`) / BIOS Directory (`$BDIR`) tables
  located via the FET pointer chain (coreboot PSP Integration Guide;
  dayzerosec/3mdeb); the lens is written and validated on non-AMD
  images (honest zeros), waiting for the real dump. **Second ring
  (2026-09-11):** the OVMF enforcement map is concrete — nearly every
  driver waits on `VariableArch`/`VariableWriteArch` (28/29 depex PUSHes;
  the write gate is the platform's critical path); the security
  namespaces are carried by exactly two modules (`SecureBootConfigDxe`,
  the variable service); strict-NX changes **zero** module topology
  (145 vs 145 GUIDs) — policy is census-invisible, so day-0 must read
  PCDs/policy, not just module lists.
- DAY-0: `$BPM`/`$KSH` presence from `spi-map` (existence only — fused vs.
  deactivated is NOT determinable from the image, and the tool says so).
  **Third ring (2026-09-11) — the policy is localizable, and the AMD
  walls get a checklist:** Debian's strict-NX vs secboot differ in
  exactly THREE bytes — one in BdsDxe `.text`, two in IScsiDxe
  `.text`, everything else (DxeCore, PcdDxe, all PEIMs/SMM)
  byte-identical: the PCD database is identical, so policy is NOT a
  platform bake but compiled per-module, and NO census below hash-diff
  can see it — the day-0 rule is hash-diff against a known-good
  reference (same module list proves nothing). Upstream context: the
  W^X/NX-clean boot-chain work (kraxel; Fedora Edk2Security). On the
  AMD side: the SPI window (`0xFED80000` family) exposes up to FOUR
  Rom Protect ranges (coreboot #4094) — the AMD mirror of Intel's
  PR0-PR4; the SMM lock is an MSR (`0xC0010111`, SMM_LOCK bit 0,
  IOActive); and the PSP **shares the SPI flash storage with the
  system BIOS** (coreboot PSP doc) — any Volume-5 protect decision
  has two consumers of the same silicon.
- RING-19 (who signs, and what ships — see `lab/vendor-pe-trust.json`):
  the NX story completes the policy picture — vendor silicon arms
  ZERO of 5,707 modules NX_COMPAT where OVMF arms a handful, so on
  AMI-Aptio the PE flag is not the enforcement channel either. And
  the factory trust material is now measured: **zero
  EFI_SIGNATURE_LIST in any of the 13 images** — the DER chains ship
  raw (runtime-assembled lists), and ONLY ASUS carries in-image
  signing material (12 → 18 certs, leaf = TW 23638777 = ASUS,
  timestamp chain 2021 → 2025, a fourth dating signal); MSI,
  Gigabyte and ASRock ship none — their enforcement story is not
  readable from the image alone. Day-0 adds a fifth first-hour
  fingerprint: the 18-cert DER set for this board.
- RING-22 (the collapsed census and the frozen whitelist — see
  `lab/vendor-der-inventory.json`, `lab/vendor-armor-chipdb.json`):
  two refinements land on the wall map. First, the ASUS trust
  material collapses: the "12 → 18 certs" are SIGHTINGS (each cert
  shipped 3× across the store copies); the factory chain is 4 → 6
  DISTINCT certificates whose COUNT freezes at 3810 while the BODIES
  rotate — the DigiCert timestamp chain re-issues at five ladder
  frontiers (2021 → 2025) and the ASUS signing leaf renews at 4631 —
  so the wall's signature chain is MAINTAINED, not static, and the
  rotation itself is the sharper dating signal. PRIME 4655 and TUF
  4645 carry identical sets. Second, the flash armor's SPI chip
  whitelist (46 families, the `AMD rom armor` table) is byte-identical
  across all five vendors and FROZEN since 3802 — the armor's chip
  knowledge is AMI-generic infrastructure that stopped learning in
  2022 (knowledge-only: the zero-write doctrine is untouched).
- RING-23 (the churn atlas — see `lab/vendor-churn-atlas.json`): the
  armor walls get a MODULE ROSTER instead of a score. Every FFS body
  hashed along the nine rungs: the wave-1 armor is exactly five files
  born at 3802 (`FlashSmiDxe`, `FlashSmiSmm`, `PrepareWhiteListSmm`,
  `SbRomArmorSmm`, freeform `89BE47F4`), wave-2 adds exactly two at
  4604 (`02076249`, `4EB43107`) — ring 18's 5/7→7/7 decomposed at GUID
  granularity; the legacy SMM retirement is exactly two deaths
  (`827E45A4` at 4202, `21782819` at 4402). The quiet pair 3802|3810
  is the ladder's quietest frontier at FFS granularity too (45 moved
  bodies, zero births/deaths). Day-0's first-hour read: ~613 FFS
  files, the quintet present, the legacy pair absent on ≥4402 builds.

## Q5 — What does NVRAM really hold? (the hidden settings)

The `Setup` variable is a binary struct, mostly undocumented. Read-only
enumeration reveals names and sizes; field semantics stay vendor-internal
until someone parses them offline.

- NOW: `spi-map` NVRAM section enumerates variable names with an honest
  heuristic label. **First real answer (lab world, OVMF):** a populated
  real store yields real names (`BootOrder`, `SecureBootEnable`, `KEK`,
  `dbx`, `certdb`, …) — and the heuristic also catches utf-16 strings
  inside variable DATA (boot-entry descriptions); the "labels only"
  label is exactly what covers that. See `lab/ovmf-findings.md`.
  **Second ring (2026-09-11) — the store is a journal, walked byte by
  byte:** 39 records (21 live / 18 deleted / 0 aborted) per populated
  store; the authenticated variable format is the DEFAULT (all three
  shipped variants, even without Secure Boot); deletion = state-byte
  flip, so a real store keeps boot archaeology (console enumeration
  retried 5–6×, `BootOrder` deleted twice, `CustomMode` flipped thrice);
  the keyring parsed with a mini-DER walker (PK/KEK/db = X509,
  `dbx` = the SHA-256 of the empty string — a placeholder that revokes
  nothing); `certdb` is a 4-byte integrity record, not a signature
  list; `EVSA` marker absent — 0.7.1 taxonomy confirmed. See
  `lab/findings-second-ring.md` + `lab/ovmf-keyring.json`.
- DAY-0: real names/counts, read-only; deeper parsing happens **offline from
  `day0-spi.bin`**, never on the live machine. **Third ring (2026-09-11)
  — the store is priced:** the populated stores use 4.82 %/3.44 % of
  the `0x3FFB8` region (95 %+ free); the vendor's own boot history
  rewrote 3,468 B of superseded journal records
  (ConIn/ConOut/ErrOut/CustomMode/BootOrder/VendorKeysNv); 278,528 B
  live beyond the store as FTW working + spare. The zero-write
  doctrine's wear share: **0.00 %** of every number in the table — the
  same budget walk on day-0 prices the vendor baseline before we
  touch anything.

## Q6 — What talks before Linux? (the boot chain census)

SEC → PEI → DXE → BDS → shim → kernel. Every module that runs before the
kernel has a GUID and often a UI name — and `spi-map` extracts both.

- NOW: **first real census performed (lab world, OVMF, 2026-09-11).**
  The compression wall inside the image was pierced in-memory
  (stdlib `lzma`, read-only): 115 DXE modules named on the plain
  build — full network stack (DHCP→IP→TCP→TLS→HTTP→iSCSI/PXE),
  storage, display, crypto, config UI — and 9 SMM modules on the
  SMM_REQUIRE build. Key lesson: a naive scan of a compressed image
  counts almost nothing; the census must decompress before counting.
  Full census: `lab/ovmf-findings.md`. **Second ring (2026-09-11):**
  the chain is resolved to file level and by position — `Boot0000`
  = UiApp (`462CAA21…`, FFS type-0x09, 114 KB) inside the DXEFV
  (FvName `7CB8BDC9…`, proven at the ext-header position); `BootOrder`
  is DELETED in the shipped store — BDS rebuilds the order each boot;
  the whole 4 MiB flash (VARS+CODE) reassembled and re-read by the
  frozen `spi-map` (3 FVs, honest summary) — the tool's first
  whole-flash rehearsal. Also: 37 DXE drivers ship with **no depex at
  all** (spine by absence), zero BEFORE/AFTER constraints, and the
  two most-waited protocols are `PcdProtocol` and
  `DevicePathUtilities`. **Third ring (2026-09-11) — the firmware's
  own chain closes the loop:** the first instruction at 0xFFFFFFF0 is
  not a jump but a CR0 fork (`mov eax,cr0; test al,1; jz` + 16-bit
  and 32-bit branches) whose BOTH targets land inside the ResetVector
  file (`1BA0062E…`, raw, 2,872 B, top of flash); then SecMain
  (45,566 B) → the LZMA wall (1,569,609 B → 16,122,000 B, ×10.3) →
  PeiCore (28,602 B) + 14 PEIMs → DxeIpl (50,110 B) → DxeCore
  (139,390 B) → BdsDxe (86,650 B) → UiApp (114,414 B), every hop with
  GUID/offset/size; the DXEFV FvName read at the inner ext header
  (`0x60` — note: > HeaderLength, the bytes win) confirms `7CB8BDC9…`
  from a second independent position; and the code budget closes
  exactly: 3,440,640 + 212,992 = 3,653,632 B.
- DAY-0: the module list **is** the census — expect compression
  (LZMA or Tiano sections) on a vendor image; 0 visible modules means
  "decompress next", not "empty firmware". Flag anything network-ish
  (HTTP boot, AMT/MEI helpers) and anything storage-ish (RAID OpROM).
- VOL-5: measuring what any of it actually *does* (behavior, not presence).

## Q7 — What runs when we are not looking? (SMM, ring -2)

SMM handlers execute invisible to the OS, triggered by SMIs, at higher
privilege than anything Linux can inspect. Presence and names are visible in
the image; behavior is not.

- NOW: `spi-map` counts SMM modules separately (`smm_drivers` summary
  field). **First real answer (lab world, OVMF):** on the SMM_REQUIRE
  build, variable services move INSIDE SMM — `PiSmmCore`,
  `PiSmmCpuDxeSmm`, `VariableSmm`, `SmmLockBox` — one setup-visible
  feature (Secure Boot) restructures the platform's privilege
  topology. Also learned: two files can share a UI name (`CpuDxe`
  twice, distinct GUIDs) — names are labels, GUIDs are identity.
  **Second ring (2026-09-11):** the migration is itemized —
  `VarErrorFlag` moves from `VariableRuntimeDxe` into `VariableSmm`,
  `TcgMorLockSmm` appears (even the MOR lock goes to ring -2), every
  SMM servant carries a depex while `PiSmmCore` needs none; the
  secure-boot build also amputates the UEFI Shell and its dynamic
  commands (an unsigned-code surface removed, not just relocated);
  and the authenticated variable FORMAT is the default everywhere —
  Secure Boot moves the service, not the format.
- RING-20 (the SMM quorum — see `lab/vendor-smm-quorum.json`): ring -2 read
  across four vendors at identity level. The four named armor modules ship
  under the SAME GUIDs on MSI/Gigabyte/ASRock — the flash armor is
  AMI-generic, not an ASUS customization; `SbRomArmorSmm` has three bodies
  (MSI and ASRock byte-identical). An 83-GUID spine sits in all five
  specimens; OVMF's SMM reference set overlaps each vendor by exactly 4
  GUIDs. MSI's frozen 2023-03 cliff still carries the legacy SMM ASUS
  retired at 4202 — the retirement calendar holds across vendors. Day-0
  expectation: the dumped board's armor GUIDs are the corpus-wide ones, not
  ASUS-only ones.
- DAY-0: the real SMM module names, read-only.
- VOL-5: deeper analysis only on sacrificial hardware.

## Q8 — What can Linux see that the firmware hides? (the runtime mirror)

dmidecode, efivarfs listings, MSR access, PCIe config space — a runtime mirror
of firmware state. Cross-checking the mirror against the image (what the
firmware declares vs. what the machine reports) is future digital-twin
enrichment. **Noted as a post-freeze lever; no tool added during the freeze.**

- NOW: **the mirror is an environment property** (campaign, 2026-09-11):
  probed from inside a containerized VM — DMI absent, efivarfs absent,
  ACPI tables absent, iomem synthetic. A truncated mirror says
  "containerized environment", not "tool failure". On bare-metal
  TWIN-1 the mirror opens fully; `capture --live` provenance-tags both
  worlds either way. **Second ring (2026-09-11) — the contract, doc
  side:** efivarfs entries are `Name-GUID` files with a u32 attribute
  prefix — the same bits read from the store; reading is zero-write by
  construction; TimeBasedAuth variables (PK/KEK/db/dbx) require signed
  sets — the keyring parsed in the second ring is exactly what makes an
  unsigned SetVariable fail; and the measurement channel (TPM PCRs 0–7
  at `/sys/class/tpm/tpm0/pcr-sha256/N`, event log under
  `/sys/kernel/security/tpm0/`) is a read-only truth probe of "what
  booted". TPM modules present in BOTH OVMF builds (`Tcg2Dxe`,
  `TcgMor`; `TcgMorLockSmm` on secboot). **Third ring (2026-09-11) —
  the mirror sees what the flash never shipped:** the unified 4 MiB
  image contains ZERO ACPI/SMBIOS table signatures (DSDT, FACP, RSDT,
  XSDT, APIC, HPET, `_SB_`, `RSD PTR `, `_SM_`, SMBIOS, BGRT, WAET —
  all honest zeros); the only occurrences inside the inflated payload
  are generator constants inside AcpiTableDxe, QemuFwCfgAcpiPlatform,
  SmbiosDxe, BootGraphicsResourceTableDxe. Beyond shipped/absent there
  is a third category — RUNTIME-BUILT — so the mirror's ACPI/SMBIOS
  tables are things the firmware BUILDS; a hit in a vendor image must
  be classified table-shipped (raw section) vs generator-string
  (inside a PE) by position.
- RING-21 (the ACPI lens — see `lab/vendor-acpi.json`): the
  classification is now measured on BOTH sides, and the vendor side is
  the INVERSE of OVMF's. Admission is by checksum (an ACPI table sums
  to zero over its declared length) — a real table validates where a
  generator string cannot. The vendor ships the AML only: 4 distinct
  DSDT variants + 18-23 SSDTs per board, checksum-valid raw sections
  inside the compressed FV, and BUILDS every static table — ZERO
  FACP/APIC/MCFG/HPET/IVRS bytes in any of twelve images (a whole-image
  scan found one `FACP` occurrence on 4655: garbage inside compressed
  data). And a seventh dating signal fell out: the DSDT clock — three
  main-body generations across the ASUS ladder, moving at 4202→4402
  (where the DSDT SHRANK 2,141 B, the same release the legacy SMM
  fully retired) and 4604→4631; the compiler string (INTL 2014-09-25)
  never moves, so the body hash is the honest movement signal. No
  table body is byte-identical across all twelve boards.
- RING-22 (the SSDT clock — see `lab/vendor-ssdt-clock.json`): the AML
  atlas widens past the DSDT and the last sentence above is REFINED by
  measurement — no VENDOR-COMPILED body is shared, but AMD's own AML
  layer is: 74 distinct `ALIB` bodies (OEMID `AMD`, creator `MSFT`)
  corpus-wide, **6 of them byte-identical across all 13 boards**, shipped
  EMBEDDED (not as raw sections) where ring 21's model could not see
  them. And the SSDT SET is an EIGHTH dating clock with frontiers
  disjoint from the DSDT's: one `AOD` table (rev 15→153) swaps at the
  armor release 3802; the CPM family rewrites wholesale (15 bodies) at
  the AGESA 1.2.0.8 release 4003; the quiet pair 3802|3810 stays quiet
  under both AML clocks — the sixth independent agreement.

---

## How day-0 feeds this map (16/09)

| `spi-map` output section | Questions it advances |
|--------------------------|----------------------|
| descriptor (regions)          | Q4 (wall ownership) |
| firmware volumes + FFS census | Q6 (boot chain census) |
| DXE/SMM module names          | Q1 (hidden surface delta), Q7 (ring -2) |
| NVRAM variable names          | Q3 (kill-list), Q5 (hidden settings) |
| ME region + version           | Q3 (ME partial disable), Q4 |
| `$BPM`/`$KSH` presence        | Q4 (Boot Guard) |

Second-ring offline probes (run on `day0-spi.bin` after the day-0 capture,
never on the live machine): NVRAM journal walk + keyring subjects (Q3, Q5),
boot-option device-path decode (Q6), depex census + security x-ray (Q1, Q4,
Q7), TPM PCR read from Linux (Q8).

Third-ring instruments (same rule — offline from the dump, never live):
whole-image FFS hash diff vs a known-good reference (Q4 — the only
policy-grade census), ACPI/SMBIOS signature scan with table-shipped vs
generator-string classification (Q8), utf-16 vocabulary census per setup
module (Q1), NVRAM budget walk — used/deleted/free/superseded bytes (Q5),
network-family module classification (Q3), AMD-side read-only checklist:
Rom Protect ranges in the SPI window, SMM-lock MSR, PSP/chipset
co-consumers of the chip (Q4).

The protocol stays: `capture --live` → `rehearse` → `rehearse-diff --latest`,
optionally `sudo omarchy-firmware spi-map --save-dump day0-spi.bin` + sha256.

Sixth-ring instrument (same rule — offline from the dump, never live): the
IFR question census (`ring6_ifr_probe.py` in the sandbox, artifact
`lab/ovmf-ifr-census.json`) — pierce, FFS walk, forms packages, exact-
consumption opcode walk; counts questions/options/pages per setup module
(Q1), vendor vs OVMF comparable.

Seventh-ring instrument (same rule — offline from the dump, never live):
the facade render (`ring7_facade_probe.py` in the sandbox, artifact
`lab/ovmf-ifr-facade.json`) — length-prefixed blob model (no list header
to anchor), SIBT string decode, scope-tracked IFR dissection; renders the
vendor facade in words with varstore names, offsets, defaults and
per-question conditions (Q1, Q5), vendor vs OVMF comparable in the same
terms.

Twenty-first-ring instruments (same rule — offline from the dump, never
live): the microcode clock (`vendor-microcode.json` — psptool 0x66 scan,
raw directory read, seconds: newest patch date year-buckets the build,
the 19-patch set corroborates the rung), the DSDT clock
(`vendor-acpi.json` — checksum-admitted DSDT body hash against the
three-generation atlas), the hidden map (`vendor-hidden-map.json` —
never-asked Setup ranges at offset level), and the ACPI shipped-vs-built
census (expect DSDT+SSDT shipped, zero FACP bytes — any FACP byte in the
dump would be a corpus first).

Twenty-fourth ring / Volume 5 in software (no chip touched): the
replacement firmware exists — coreboot 25.12 built for QEMU q35
(SeaBIOS payload) through three root-less toolchain walls (iasl + the
cached xcompile, 32-bit libgcc for the unwrapped `__udivmoddi4`, the
`-print-libgcc-file-name` lie under `-m32` fixed by a wrapper); the
first before/after photograph is taken (`lab/vol5-qemu-photograph.json`:
vendor PI/FFS2 vs coreboot CBFS — no shared container, so a CBFS lens
is registered as the Volume-5 additive instrument task); the flash
cycle is rehearsed file-level 5/5 (`lab/vol5-cycle-rehearsal.json`,
failed-verify branch included); the candidate matrix is verified
against the 25.12 tree (`lab/vol5-board-matrix.json` — azalea = AMD
in-tree; T440p and X470D4U absent; two AM4 refutations). Open on this
axis: QEMU boot of the built image (no QEMU binary without root), the
CBFS lens as code, and the purchase-time board-status checks.

Twenty-fifth ring — the ring-24 registrations resolved in software:
the CBFS lens IS code now (`lab/vol5-cbfs-census.json` — FMAP + CBFS
walked spec-fresh from the 25.12 tree headers imported at runtime,
13/13 identical vs cbfstool AND vs the ring-24 photograph, the payload
segment table decoded, the image self-describing via its defconfig +
`cc0358747d2a-dirty` build stamp); the "no QEMU without root" wall fell
to the deb-extraction playbook (QEMU 10.0.11 running root-less in the
sandbox); and the built image BOOTS (`lab/vol5-qemu-boot.json` — exit 0
under TCG, the four-stage chain to SeaBIOS 1.17.0 and the expected
no-bootable-device branch; the runtime confirms the static census 4/4
fetches + mcache 13/13). Still open on this axis: the purchase-time
board-status checks (hardware purchase), the azalea build rehearsal
(needs the vendor blob submodules — registered, not attempted), and the
bench-day rehearsal itself (dump-first, external programmer — gated on
the sacrificial hardware).

Twenty-sixth ring — the chain gains its OS and its numbers: a bootable
disk manufactured root-less (byte-by-byte cpio-newc initramfs, hand-built
objcopy UKI), and BOTH worlds boot it with the kernel self-qualifying its
firmware mode from inside Linux (`lab/vol5-os-boot.json`: bios via
SeaBIOS+syslinux on the ring-24 specimen unchanged; uefi via OVMF's
fw_cfg loader; 3/3 runs each, clean S5 power-down). The study's first
measured A/B (`lab/vol5-ab-timing.json`): same q35/TCG/512 MiB/kernel —
kernel start 4.57 s vs 3.46 s, userspace 7.49 s vs 6.46 s, the kernel
stage invariant at ~3 s, so the whole delta is the firmware stage; TCG
and the OVMF-as-vendor-proxy limits are registered next to the numbers.
Open on this axis: the hand-built UKI loads and STARTS under OVMF but
stays silent (earlyprintk debugging, next session), the syslinux/GRUB
rejection of a valid FAT behind a hand-written MBR partition (superfloppy
workaround), azalea rehearsal (vendor blob submodules), the purchase-time
board-status checks, and the bench day itself (dump-first, external
programmer — gated on the sacrificial hardware).

Twenty-seventh ring — the ring-26 silence is RESOLVED, and the study owns
a loader (`lab/vol5-fw27.json`): the "UKI stays silent" thread decomposed
into three measured root causes, none of them earlyprintk — RC1 the
`.cmdline`/`.initrd` PE sections are inert on the x86 stub (systemd-stub's
food; the control arm speaks and panics with the initramfs still embedded
in its own PE), RC2 the decompression-buffer knife-edge (the misleading
"Failed to decompress kernel" is `efi_random_alloc` returning
EFI_OUT_OF_RESOURCES before any decompressor runs; fw_cfg floor measured
128✗/192✓, alloc_size ∈ (~55, ~120] MiB; the UKI's 13.2 MiB pre-load
flips the 512 MiB disk path), RC3 empty LoadOptions = a kernel that boots
mute (earlyprintk closes with its true answer: delivering the cmdline is
the whole game). Front 27b builds FW27, the study's own EFI stub (~260
lines on gnu-efi 3.0.18, LoadFile2 defined from UEFI 2.10 §13.6): it
speaks on ConOut, dumps the memory map the vendor's mute RELEASE build
never prints, consumes its own sections, serves the initrd through
EFI_LOAD_FILE2 (implementing the 6.12 consumer's EFI_BUFFER_TOO_SMALL
probe contract — a registered spec divergence), LoadImages the pristine
`\boot\vmlinuz` from the same volume and hands it a CHAR16-widened
cmdline. The full chain — no shell, no boot entry, no fw_cfg — is green
3/3 at 512 MiB with the kernel's own line naming OUR protocol as the
initrd source. Open on this axis: the syslinux/GRUB rejection of a valid
FAT behind a hand-written MBR partition (superfloppy workaround, class
named), azalea rehearsal (vendor blob submodules), the purchase-time
board-status checks, the bench day itself (dump-first, external
programmer — gated on the sacrificial hardware), and the FW27 follow-ups
(memory-map full dump for bench-day correlation, earlyprintk-vs-our-
LoadOptions A/B on TCG timings, and the stub as the pattern for the
bench-day observability instrument if the vendor firmware stays silent),
and the FW28 follow-ups (why the exception handler's fxsave stack page
is present-but-RO in the broken-SMMSTORE RELEASE lane — the one open
sub-question of wall 28-w4; the AcpiPlatform "start failed: Aborted"
observation in the coreboot world; and the SMMSTORE lane on REAL
writable flash at bench day as the calibration point for the 28-w4
q35 wall).

## Discipline

None of the eight questions requires a single byte written to the SPI chip.
The map is read-first by construction: the questions that could only be
answered by writing are Volume 5 questions, and Volume 5 answers them with a
dump in one hand and the original image in the other — before any flash,
every time.
