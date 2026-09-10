# spi-map — the map of the invisible

One step beyond the runtime frontier. Everything the tool normally
reads (sysfs, SMBIOS, dmidecode, MSR, fwupd) stops at the edge of the
flash chip. `fw.spi.map` crosses that edge — **read-only** — and
inventories what lives below: the firmware volumes, the DXE and SMM
modules, the variable stores, the ME/PSP region, the boot manifests.
This is the "things never seen" of the study: 99.9 % of users never
look inside their own SPI image, and the vol. 4 pathologies (mislocked
regions, vulnerable SMM modules, stale ME) sit there at the source.

## The rule, restated with a stricter accent

- **+0 octet means zero bytes written.** The chip is read (flashrom
  itself reads twice: read + verify), parsed, and never touched. There
  is no code path in this module that can write to the flash — the
  only flashrom invocation is `flashrom -r <tempfile>`.
- **Explicit, never ambient.** The read never runs by default:
  - `omarchy-firmware capture` (the default photograph) never reads
    the SPI — proven by a structural test;
  - `omarchy-firmware capture --spi-read` adds the `spi_map` section,
    and the snapshot carries `"spi_read": true` plus a `spi_note`;
  - `omarchy-firmware spi-map` is the standalone form.
- **Not in the MCP surface, by design.** An SPI read is a declared
  gesture of the human or the agent at the CLI — not a tool a model
  may reach ambiently. The MCP conformance smoke stays at 12 tools.
- **Honest failure.** No flashrom, not root, kernel lockdown, timeout:
  the map answers `"status": "unavailable"` with the reason, and the
  capture keeps going. A failed read is reported, never guessed.

## Usage

```bash
# the standalone map (live read — root required, flashrom installed)
sudo omarchy-firmware spi-map

# analyse an existing dump offline (no root, no flashrom needed)
omarchy-firmware spi-map --dump day0-spi.bin

# keep the raw dump for offline tools (UEFITool, uefi-firmware-parser…)
sudo omarchy-firmware spi-map --save-dump day0-spi.bin
sha256sum day0-spi.bin            # the dump is the recovery path too

# inside the day-0 photograph, when wanted
sudo omarchy-firmware capture --live --spi-read
```

The temporary dump is deleted after parsing unless `--save-dump` keeps
a copy; the JSON map itself always carries the image SHA-256.

## What the map tells (and what it refuses to invent)

| Section | Content | Honesty label |
|---|---|---|
| `image` | size, SHA-256, read cost in ms | exact |
| `descriptor` | FLVALSIG, FLMAP0/FRBA, the five FLREG regions (descriptor, BIOS, ME, GbE, PDR) with base/limit | exact (classic PCH layout; AMD boards carry PSP in the "ME" region) |
| `firmware_volumes` | every `_FVH` volume with verified header checksum, filesystem GUID (FFS2/FFS3/NV stores), file counts by type | exact |
| `dxe_drivers` / `smm_drivers` | GUIDs + UI names of DXE and SMM modules | GUIDs exact; names read from the UI sections, `null` when absent |
| `nvram` | variable NAMES found in the variable-store FVs | **heuristic** (utf-16 strings), labelled as such |
| `me` | region presence, size, `$MN2` manifest, version | version is an **ASCII heuristic**, labelled as such |
| `boot_guard` | `$BPM` / `$KSH` manifest presence | presence only — **the fused-vs-deactivated state is NOT determinable from the image alone** (the FPF fuses are not readable here), and the map says so |

The map measures itself: every collection carries its `ms`, and the
whole result is diffable — two maps (before/after a BIOS update, or
vendor image vs coreboot image) expose exactly what changed below the
runtime frontier.

## Why this exists (the September 2026 ruling)

The complete replacement of a vendor BIOS — coreboot/Dasharo over the
original image — is a legitimate *destination*, but on dedicated,
sacrificial hardware, and as **Volume 5 of the study** ("the machine
reconstructed"): see `lab/coreboot-notes.md` for the dump-first
doctrine, the programmer requirement and the candidate machines. On
machines people depend on — starting with the 16/09 day-0 board — the
rule stays what it has always been: **the agent explains, the firmware
protects, and not one byte is written.**

`lab/ovmf-smoke.sh` is the risk-free half of the same curiosity: the
replacement firmware (OVMF) boots inside a disposable VM, and what it
says in its own boot log is the first experiment of the lab.
