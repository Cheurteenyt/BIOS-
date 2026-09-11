# The lab — the disposable machine

The guard (the `omarchy-firmware` tool, the repo root) lives under one
founding rule: **+0 octet — the running machine's firmware is never
written, and its deeper layers are only read through an explicit
`--spi-read` gesture**. The lab exists because some questions can only
be answered by *replacing* firmware — and those questions are answered
here, on machines that exist to be broken.

## The doctrine (three sentences)

1. The lab is **disposable by construction**: a VM first (QEMU + OVMF),
   a sacrificial board later — never the day-0 machine, never a machine
   anyone depends on.
2. Everything learned here is **transferable knowledge**, not a fork of
   the guard: the lab informs the study (volumes 4 and 5), it does not
   change the tool's contract, its tiers, or its +0 octet rule.
3. **Replacing the original firmware is legitimate in the lab** — the
   original image is dumped, hashed and archived BEFORE any write, and
   the write itself goes through an external programmer on real
   hardware. A lab without a backup is just a brick factory.

## What lives here

### The findings (chronological, Markdown, the narrative)

| File | What it is |
|---|---|
| `ovmf-findings.md` | the first real firmware the parser has read: the LZMA compression wall pierced in pure stdlib (0 visible modules ≠ empty firmware → full census restored), the 4 MiB / 16 MiB geometry |
| `findings-first-ring.md` | the massive investigation, 7 fronts: species census, ROM chains, the physical trust chain, the PSP lens |
| `findings-second-ring.md` | 7 fronts: the NVRAM journal walked byte by byte, the boot chain resolved by position, the dependency web, the security x-ray |
| `findings-third-ring.md` | 7 fronts: the NX policy is three bytes (hash-diff or nothing), the first instruction is a CR0 fork, the facade quantified (~423 sentences), the NVRAM priced |
| `findings-fourth-ring.md` | 7 fronts: the gates x-ray, the PE provenance (zero timestamps, no PDB), the entropy atlas (58.9 % void), the SMM anatomy |
| `findings-fifth-ring.md` | 3 fronts: enrollment is data (secboot == ms == snakeoil, byte-identical), the facade package layer anchored, ACPI is templates not tables |
| `findings-sixth-ring.md` | 2 fronts: the IFR grammar re-derived spec-fresh (FORMS = 0x02, `{OpCode:8, Length:7, Scope:1}` — why ring 5 locked), the facade counted in QUESTIONS (146 plain / 208 secboot, 21/21 packages close exactly) |
| `findings-seventh-ring.md` | 4 fronts: the S2 lock was a category error (length-prefixed blobs, no package list ever ships — HiiAddPackages builds it at runtime), the SIBT layer decoded, the facade rendered in words (en-US + fr-FR), the facade's memory (varstores named, offsets, defaults, 48/146 questions behind a condition) |
| `findings-eighth-ring.md` | 3 fronts: the dispatch graph (DEPEX as a DAG — zero BEFORE/AFTER, hubs by fan-in, apriori declared order, gate delta empty where modules are shared), the string closure (SCSU = zero real blocks, SKIP2 lives only in fr-FR, the last ids are the null marker + collisions), and pkg3 dissolved (a spurious exact-consumption anchor nested inside the real package — the flat 208 was 202 + 6 double-counted patterns) |
| `findings-ninth-ring.md` | 3 fronts + the owed render check: the GUID nameplate (618/618 occurrences across 13 artifacts named, 209 distinct GUIDs, zero raw cells left — the 245-B formset was the File Explorer formset, the keyring owner is EnrollDefaultKeys' own FILE_GUID), the signature-list lens (PK/KEK/db/dbx record-by-record, the dbx = sha256("") byte-exact in both enrolled stores, 1000-entry synthetic dbx parsed in 2.3 ms), and the weight map (DXEFV 31→41.5% used, secboot grows +87 KB inside the outer slack, the swap = +18 SMM modules − Shell and its dynamic commands, net +810 KB) |
| `findings-tenth-ring.md` | the general rehearsal: the 14-stage pipeline chained end-to-end for the first time (run 1 = 14/14 exit 0 in 25.4 s but 3 artifacts byte-changed — verdict PARTIAL), the nondeterminism classified into three species (set-iteration order in ms-delta, artifact/producer staleness in scsu — the regenerated superset adopted, wall-clock noise in siglist — registered, not pretended stable), the facade's mid-chain churn recorded as converging data, run 2 = REPRODUCIBLE (16/16 end-identical, zero restored), and the day-0 vendor-image protocol fixed as a repo document |
| `findings-eleventh-ring.md` | the instrument meets real vendor silicon: two AMI-Aptio AM4 specimens acquired at the CDN (MSI B450 TOMAHAWK MAX 7C02v3G1 — the frozen 2023 cliff; Gigabyte B450 AORUS PRO F67c — the living line, Aug 2026, CVE-2026-6726/6727 fixed), the nesting rule bites its own registry (case-sensitive FS-GUID lookup rejected 24/24 valid FVs — fixed, both bug and catch registered), the OVMF LZMA grammar crosses to vendor silicon (453/498 modules pierced, 77.5/84.7 % UI-named, MSI's AGESA 1.2.0.8 byte-verified), the same bones measured (275 shared module GUIDs, jaccard 0.549), and the dispatch layer reads 100 % (228/228 + 278/278 DEPEX parsed, PcdProtocol hub fan-in 202/270 vs OVMF's 56) |
| `findings-twelfth-ring.md` | the quorum: the blocked files find their way (ASRock's 403 passes to a full browser header set; ASUS's official GetPDBIOS API names the canonical CDN URL — 4655 and 3604 acquired as CAPs), the latest-official ledger verified per vendor and the ring-11 3644 claim corrected visibly (no such BIOS in the official ASUS ledger — the metadata was Gigabyte F67c's), the 2,048-byte CAP wrapper proven by first-FV delta, the same instruments imported verbatim on two new boards (ASRock 633 modules 60.3 % named, DEPEX 253/253; ASUS 600 modules, DEPEX 286/286), the packaging lens (ASUS: 384 VERSION sections, ONE UI — the nameplate goes structurally blind), and the quorum matrix (living lines cluster 0.70–0.78, the frozen 2023 MSI is the outlier 0.54–0.58, 41–43 GUIDs shared with OVMF each) |
| `findings-thirteenth-ring.md` | the two lenses: the VERSION-strings lens refutes itself (1,992 sections, 100 % PI-spec str@2, but 8 distinct strings — build numbers, not names; the ASUS blindness is structural), the names recovered anyway by the GUID join (665-GUID map, zero real conflicts, ASUS 0.002 → 0.593 — DXE 0.83 / SMM 0.86; the UefiRaid case: the one real version string, '1.0' → '9.3.0.00308', catches ASUS up with the quorum), and the PSP lens (74/74 directories parse, fletcher32-validate and cross-check against psptool 3.6 on all five specimens; $BSP zero closed by source — the real magics are $BHD/$BL2; the PSP layer churns 38/75 blobs between ASUS releases while packaging stands still; PspFtpmHandler in every board) |
| `findings-fourteenth-ring.md` | the NVRAM opens and the register renames itself: the ring-11 "EVSA" premise dies by scan (EVSA=0, $VSS=0 on all six — the format is AMI NVAR), the grammar imported from UEFITool's Kaitai spec file-by-file (never from memory), the store anatomy proven by the spec's own variables (PlatformLang/Timeout resolve to gEfiGlobalVariableGuid on every board after the GUID-area direction fix — caught before publication), the factory grammar across four vendors (one outer StdDefaults variable whose DATA is a nested NVAR store; 9 shared names + per-vendor tails), the MSI mirror is not an NVRAM clone either (Setup 1,428 B vs 1,972 B), the 3644 question narrows (the ring-11 zip = a 240-byte HTML page; 3644 absent from THREE official ledgers; TUF 4645 acquired — the first vendor-sha256-certified specimen), and the reproducibility ritual retires the ring-13 "one run per lens" caveat (NVAR 2 runs identical; PSP re-run identical) |
| `findings-fifteenth-ring.md` | what an update changes, and the chain that holds: the release-delta lens diffs PRIME B450-PLUS 3604 (2022) vs 4655 (2026) file-by-file at body-hash granularity (616 GUID set: 285 unchanged / 322 changed / 7 added / 2 removed — 46.3 % of the board byte-identical across 4.5 years; the churn is the AGESA family — AmdApcb*/AmdCcx*/AmdCpm* — with AmdCcxZen3Dxe growing 71,958 → 85,942 B; the 7 ADDED modules are ASUS flash hardening: PrepareWhiteListSmm, SbRomArmorSmm, FlashSmiSmm, FlashSmiDxe; the ring-14 NVRAM anchor re-derived independently — same 130,952 B size, different content), and the second generale: the six vendor lenses chained in protocol order (unwrap → census → versions → PSP → NVAR → depex), run 1 = COMPLETE-NOT-IDENTICAL, the ritual catches the SAME species ring 10 caught (set-iteration key order in phases_delta — one `sorted()` at the source), run 2 = REPRODUCIBLE (6 stages × 2 runs, all registers byte-identical, ~8 s per chain — the day-0 vendor table is fixed) |
| `findings-sixteenth-ring.md` | the levels, the waves, the nine bytes: byte forensics on the same-size pairs (AcpiTableDxe changed by exactly 9 bytes in 8 spans of 1-2 B inside cmp/jcc sequences — a surgical patch; ACPI rewrote 58.5 % of itself at constant size; the NVRAM anchor's 778-B diff lands exactly in the HWM/QFan default region — NV_SIO0_LD1, SetupHWMOneof, QFan — the factory fan defaults moved; and the "one-byte change" revealed as a wholesale payload replacement sharing 0 % of its overlap — body-hash identity vindicated by its own edge case), the pierced AGESA lens closes all four 'unverified' claims (ASUS 4655 = 1.2.0.12, 3604 = 1.2.0.6b, TUF 4645 = 1.2.0.F — NEWLY VERIFIED; MSI/Gigabyte/ASRock MATCH — zero vendor lies; the strings sit 2.7-2.9 MiB into the decompressed 0x9c0000 FV where the raw scan could never look), and the flash-armor bisect over the official ledger (40 entries now, was 39): the armor arrived in TWO WAVES — core SMM set by 4202 (2023-08-02, first verified carrier, bracketing the LogoFail year) and complete at 4604 (2024-04-08); one legacy SMM module retired in stages (1/2 at 4202, 0/2 by 4402); day-0 gets a versioned armor checklist and a third independent dating signal |

Every findings file carries the same honesty ledger: what is proven,
what is flagged, what stays an open question — and ends with its
consequences for day-0 (16/09). The ring-5 opcode lock was resolved by
ring 6 (spec-fresh grammar); ring 6's list-header lock was resolved by
ring 7 (a category error — the list never ships); ring 7's last
registration (pkg3) was dissolved by ring 8 (a decoy anchor nested
inside the real package — the flat count double-counted 6 patterns);
each ledger self-corrects where the answer lands.

### The artifacts (JSON, the evidence)

| File | Produced by | What it is |
|---|---|---|
| `ovmf-census.json` | first ring | the module census of the real OVMF builds (PenetrateLZMA → FFS walk) |
| `ovmf-keyring.json` | second ring | the NVRAM trust store decoded: PK / KEK / db / dbx, 39/39 records, X.509 subjects |
| `ovmf-kill-list.json` | third ring | the GUIDed amputation lists: network 21 modules, storage 18, USB 6, display 6 |
| `ovmf-build-delta.json` | fourth ring | the FFS hash matrix across builds — the only census that sees policy |
| `ovmf-pe-provenance.json` | fourth ring | PE header provenance: zero timestamps, no PDB paths, the NX badge |
| `ovmf-ms-delta.json` | fifth ring | secboot vs ms vs snakeoil: 144/144 modules byte-identical — trust is configuration |
| `ovmf-ifr-grammar.json` | fifth ring | the HII package-list hunt: what validated, what stays locked (opcode layer) |
| `ovmf-acpi-footprint.json` | fifth ring | checksum-validated ACPI/SMBIOS scan of 5 builds: templates in builders, zero finished tables |
| `ovmf-ifr-census.json` | sixth ring | the per-module IFR census: questions / options / pages per setup module, validated by exact consumption |
| `ovmf-ifr-facade.json` | seventh ring | the facade rendered: formsets / forms / questions with resolved text (en-US + fr-FR), options with values, varstores with names and sizes, defaults, per-question conditions |
| `ovmf-depex-dag.json` | eighth ring | the dispatch graph: postfix-evaluated DEPEX classes, hub fan-in (PcdProtocol 62, DevicePathUtilities 54…), the apriori declared order per FV, the cross-build gate delta (changed-while-present = {}) |
| `ovmf-scsu-strings.json` | eighth ring | the SIBT block census (SCSU = 0 real blocks; SKIP2 only in fr-FR; header-faithful closes 110/110), the UTS#6 decoder + 5/5 self-tests, the observed string-header bytes, the id-resolution closure (id 0 = null marker, cross-module matches = collisions) |
| `ovmf-pkg3-head.json` | eighth ring | the pkg3 autopsy: anchor and shift grids, hexdumps, the nested-span proof, the covering STRING record, the real formset guid byte-equal to the tianocore source, the 208 = 202 + 6 accounting |
| `ovmf-guid-names.json` | ninth ring | the nameplate: every GUID in the 13 artifacts resolved (618/618, 209 distinct) against 11 .dec inventories + census + kill-list + the edk2 master tree; the closes that retire ring-8 "?"s (PcdPeim apriori entry, File Explorer formset, EnrollDefaultKeys-as-owner) |
| `ovmf-siglist.json` | ninth ring | the trust store unpacked: PK/KEK/db/dbx record-by-record with named owners and X.509 fingerprints, the sha256("") dbx placeholder verified by value in both enrolled stores, the synthetic 1000-entry scale rehearsal (2.3 ms, exact) |
| `ovmf-weight-map.json` | ninth ring | the frugality ledger in bytes: per-FV accounting (header/data/padding/tail) on 3 builds, named top consumers (TlsDxe ≈ 1 MB, Shell 894 KB), the by-name swap delta (+18 SMM modules − 9 incl. the Shell, net +810 KB), the FvbServicesSmm false-FV dismissal |
| `ovmf-rehearsal.json` | tenth ring | the general rehearsal record: the 14-stage chain (census → keyring → build-delta → pe-provenance → ring5 → ifr-census → facade → final → depex → scsu → pkg3 → guid-names → siglist → weight-map) timed on 4 specimens with pre/post canonical-content comparison, per-stage churn data, verdict REPRODUCIBLE — the ring-9 claim "only new inventories on the vendor image" proven, not asserted |
| `vendor-specimens.json` | eleventh ring | the first vendor-silicon register: two AMI-Aptio AM4 flash maps (MSI 32 MB dual-structure, Gigabyte 16 MB) with nesting-rule-validated FVs, the pierced census (453/498 modules by phase, UI-named shares, AGESA byte-verified where present), the cross-vendor GUID intersection (275 shared, jaccard 0.549 — the "same bones" claim measured), the 100 % DEPEX parse with PcdProtocol hub dominance (202/270 fan-in), and the acquisition honesty (ASRock 403-blocked, ASUS deferred to the day-0 dump; both entries carry visible ring-12 corrections) |
| `vendor-acquisition.json` | twelfth ring | the sourcing ledger: per-vendor latest-official verification (ASUS GetPDBIOS API 39-entry ledger, MSI/GB/ASRock official listings), verbatim URLs and full zip sha256 for all five acquisitions, the blockage stories with their ways found (WAF header-set completeness, canonical API naming), the 2,048-byte CAP wrapper proof, and the 3644 question with its decision path |
| `vendor-quorum.json` | twelfth ring | the quorum evidence: ASRock and ASUS census summaries (top FVs, phases, named shares, DEPEX 100 % with hub tables, PSP/BSP hits, AGESA verification status), the packaging lens (ASUS 384 VERSION / 1 UI section — the nameplate blindness measured), and the pairwise GUID-identity matrix across the four vendors plus the OVMF reference rows (41–43 shared each) |
| `vendor-versions.json` | thirteenth ring | the VERSION-strings lens, measured: the decode convention decided by bytes (1,992 main-region sections, 100 % PI-spec str@2), the vocabulary that refutes the ring-12 candidate (8 distinct strings, seven placeholders — '1.0' ×1,860), the GUID join that recovers the names anyway (665-GUID map, 2 pseudo-conflicts, ASUS 4655 0.002 → 0.593 named — DXE 0.83, SMM 0.86), the UefiRaid case (C74F06D2: '1.0' → '9.3.0.00308', the one version change in four years, caught up with ASRock/GB/MSI), the 600-row ASUS named-module register for day-0, the MSI mirror asymmetry (+16 files, 0x97000 bytes longer), and the cross-release packaging stability (414/415 strings identical 2022→2026) |
| `vendor-psp.json` | thirteenth ring | the PSP lens: magic scan with $BSP/$BIO re-scanned to zero (the verified magics are $PSP/$PL2 and $BHD/$BL2 — the ring-11 zero closed by source), 74/74 directories fletcher32-validated and cross-checked against psptool 3.6 (type tables imported at runtime, never transcribed from memory), the full ASUS PSP/BIOS directory trees per release, the cross-release churn (37 blobs identical, 38 changed — bootloader, TOS, SMU, ABL0-7 move while some instances survive byte-identical), the constants (PspFtpmHandler everywhere, DRAM/HMAC/RPMC key machinery in the bootloader strings), and the psptool 32-MiB address-label join lesson |
| `vendor-nvram.json` | fourteenth ring | the NVRAM lens: the AMI NVAR store, first parse across six specimens — FFS-anchored store → one outer StdDefaults variable → nested defaults store (11–18 variables per board), the backwards GUID area self-tested by the UEFI spec's own variables, the factory canon (9 names shared by all six) with per-vendor tails, the MSI mirror delta (Setup 1,428 vs 1,972 B), zero walk errors / zero broken links / clean terminators on 14 walks, and the day-0 delta protocol (live minus factory) |
| `vendor-ledger-tuf.json` | fourteenth ring | the 3644 evidence file: the ring-11 "3644 zip" proven a 240-byte HTML error page, three official ASUS ledgers checked (PRIME B450-PLUS 39 releases, TUF B450-PLUS GAMING 33, TUF B450M-PLUS GAMING 33 — 3644 in none), and the TUF 4645 acquisition with the project's first vendor-certified sha256 (the API's own per-release hash, matched byte-exactly; CAP wrapper proof reproduces on a third release) |
| `vendor-release-delta.json` | fifteenth ring | the release-delta lens: PRIME B450-PLUS 3604 vs 4655 diffed at FFS-body sha256 granularity (outer AND pierced-inner volumes), the 616-GUID delta (285 unchanged / 322 changed / 7 added / 2 removed, 46.3 % untouched), the changed-by-phase histogram (DXE 201, SMM 65, freeform 42), 269 changed modules named by the 532-GUID quorum join (53 recorded as GUIDs, never invented), the seven added flash-armor modules, the one-byte 80,232 → 80,231 raw change, the NVRAM anchor cross-check (same size, different content), and the honesty entries (body-hash vs header bits; two releases measured of 39; AGESA level strings not recovered) |
| `vendor-day0-chain.json` | fifteenth ring | the second generale: the six-stage vendor chain (unwrap → census → versions → PSP → NVAR → depex) in protocol order, two full runs, per-stage exit+existence verdicts and chain identity judged at the end — run 1 COMPLETE-NOT-IDENTICAL (the ritual catches set-iteration key order in versions.phases_delta, the ring-10 species returning on schedule), fix at source, run 2 REPRODUCIBLE (all six registers byte-identical, ~8 s per chain), and the reading: the 16/09 dump joins this chain as a seventh specimen in the first hour |
| `vendor-agesa.json` | sixteenth ring | the pierced AGESA lens: every specimen's AGESA level byte-verified from raw AND LZMA-decompressed content (ASUS 4655 = 1.2.0.12, 3604 = 1.2.0.6b, TUF 4645 = 1.2.0.F — the four ring-11/12 'unverified' blanks closed; MSI 1.2.0.8, Gigabyte 1.2.0.12, ASRock 1.2.0.E all MATCH their vendor claims — zero vendor lies detected), the strings located 2.7-2.9 MiB into the decompressed 0x9c0000 payload (the raw scan could never see them), Gigabyte's SMU side-harvest (3.4.1.1-3.4.2.4, fourteen distinct), and the day-0 use: the dump's AGESA level is one regex away once its volumes are pierced |
| `vendor-flash-armor.json` | sixteenth ring | the flash-armor bisect: the official API ledger re-fetched (40 releases, 0318→4655), 13 intermediates bounded to 4 downloads + 2 free sentinels, per-probe presence sets written after every probe — the answer is two waves (core SMM armor by 4202 = 2023-08-02, first verified carrier, inside the LogoFail year; complete 7/7 at 4604 = 2024-04-08; 4402 straddles at 5/7), the legacy SMM retirement staged (1/2 at 4202, 0/2 by 4402), the vendor-sha256 provenance honesty (published only for newer releases), and the day-0 checklist: five GUIDs expected from 4202, seven from 4604, two legacy expected gone by 4402 |
| `vendor-byte-forensics.json` | sixteenth ring | the WHAT behind ring-15's WHO: same-size changed modules diffed byte-by-byte (GUIDs read from the ring-15 register, never from memory) — AcpiTableDxe's 9 bytes in 8 surgical spans, ACPI's 58.5 % rewrite at constant size, the NVRAM anchor's 778 B landing exactly in the HWM/QFan default region, and 1DF36FF9 exposed as a wholesale replacement (0 % overlap after a 16-B prefix) that the 'one-byte size delta' story completely misdescribed; span geometry structural, never a disassembly |

### The instruments

| Path | What it is |
|---|---|
| `ovmf-smoke.sh` | boot OVMF in QEMU, headless, capture the boot log — the first "replacing the firmware" experiment, fully reversible by Ctrl-C |
| `coreboot-notes.md` | the Volume 5 doctrine: the sacrificial board, dump-first, programmer, candidate machines |

The one-shot probe scripts (`*_probe.py`, `ring5_probe.py`, `ring4_lib`) are
**session instruments of the sandbox, deliberately not tracked here** —
they read the downloaded OVMF images from sandbox paths and print
`bytes written: 0`; the findings quote them, the JSON artifacts are
their durable output. The repo tracks knowledge, not scratch.

## Why a lab at all (the honest answer)

Replacing the vendor BIOS unlocks things the runtime can never see: a
readable SMM, a sovereign boot policy, a neutralizable ME. It also
destroys the object of study — every Omarchy user out there runs vendor
firmware, and the guard exists for *their* machines. The lab is where
both truths coexist: here we replace, we instrument, we break; in the
guard fleet we read, we explain, and we write zero bytes.
