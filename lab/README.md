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

Every findings file carries the same honesty ledger: what is proven,
what is flagged, what stays an open question — and ends with its
consequences for day-0 (16/09).

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
