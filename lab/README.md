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
