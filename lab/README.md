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

| Path | What it is |
|---|---|
| `ovmf-smoke.sh` | boot OVMF in QEMU, headless, capture the boot log — the first "replacing the firmware" experiment, fully reversible by Ctrl-C |
| `coreboot-notes.md` | the Volume 5 doctrine: the sacrificial board, dump-first, programmer, candidate machines |

## Why a lab at all (the honest answer)

Replacing the vendor BIOS unlocks things the runtime can never see: a
readable SMM, a sovereign boot policy, a neutralizable ME. It also
destroys the object of study — every Omarchy user out there runs vendor
firmware, and the guard exists for *their* machines. The lab is where
both truths coexist: here we replace, we instrument, we break; in the
guard fleet we read, we explain, and we write zero bytes.
