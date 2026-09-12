# Volume 5 doctrine — the sacrificial board

*Where "remplacer complètement le BIOS" becomes a legitimate experiment.*

## The scope decision (September 2026)

The user ruled: the founding constraint of the guard fleet stays
**+0 octet written** — and the *complete replacement* of an original
BIOS (coreboot/Dasharo over the vendor image) becomes **Volume 5 of the
study**, on dedicated hardware, after the 16/09 day-0. Never the day-0
machine. Never mixed with the guard.

## The non-negotiable sequence

1. **Dump first.** `flashrom -r original.bin` — read twice by flashrom,
   hashed (`sha256sum original.bin`), archived on TWO media. This dump
   is the recovery path AND the control group of the whole experiment.
2. **Identify before you write.** `flashrom --flash-name`; check the
   board's coreboot port status; check Boot Guard / FPF state (Intel) —
   a fused vendor key means the machine will never boot unsigned
   firmware: the experiment ends here, honestly.
3. **External programmer only for the first flash.** CH341A (16 MiB
   variant) + SOIC8 clip on the SPI chip, with the board's main power
   disconnected and the battery unplugged. EZ Flash / internal flashing
   comes only AFTER a known-good coreboot is running.
4. **Verify, never trust.** `flashrom -v coreboot.rom` after every
   write; a failed verification is a re-clip, not a reboot.
5. **The rollback path is rehearsed before it is needed.** Restoring
   `original.bin` from the external programmer must succeed once,
   deliberately, before the board is considered "ours".

## The rehearsal state (after ring 25)

The software wing of the sequence is rehearsed end to end — steps 3-4
remain hardware-gated, but everything around them is green:

- **the replacement image exists and boots** — coreboot 25.12
  (`cc0358747d2a-dirty`, QEMU q35, SeaBIOS payload) boots to its payload
  under the tree's own documented command: bootblock → romstage →
  postcar → ramstage → SeaBIOS rel-1.17.0, then the expected
  no-bootable-device branch (`lab/vol5-qemu-boot.json`); QEMU itself now
  runs root-less in the sandbox (10.0.11, deb-extraction lane);
- **the flash cycle is rehearsed file-level 5/5** — dump-twice, identify,
  write+verify, the flipped-byte failed-verify branch caught, rollback
  (`lab/vol5-cycle-rehearsal.json`, ring 24);
- **the read instruments exist on both worlds** — `fw.spi.map` for the
  vendor PI/FFS image, the ring-25 CBFS lens (`lab/vol5-cbfs-census.json`)
  for the coreboot world, each cross-cited; the boot confirmed the static
  census by consuming it (4/4 fetches, mcache 13/13).

What the bench day adds is only what software cannot rehearse: a real
clip on a real SOIC8, a real chip that answers `--flash-name`, and a real
rollback from the second medium. The dump-first rule does not move.

## Candidate machines (coreboot/Dasharo ports, as of late 2026)

> **Updated by ring 24** (`lab/vol5-board-matrix.json`): candidates
> verified against `src/mainboard` of the coreboot 25.12 release we
> actually built. The tree says `framework/azalea` is the **Framework 13
> AMD 7040** — an AMD/AGESA machine, so the study's PSP lens transfers
> directly (primary candidate for the coreboot lane); System76 has 13
> in-tree models; **the T440p is absent from 25.12**; **the ASRock Rack
> X470D4U lane is absent from 25.12** (zero hits across `src/` and
> `Documentation/`); and `asus/h610i-plus-d4` proves consumer-ASUS
> coreboot exists. "Port in tree" is not "port matured" — purchase-time
> checks remain. The bench decision (a second used B450) is a separate
> question and unchanged.

| Machine | Port status | Notes |
|---|---|---|
| Framework Laptop 13/16 | Dasharo (official) | the smoothest modern path |
| System76 machines | coreboot (vendor-shipped) | open EC too |
| ThinkPad x230 / T440p | coreboot, mature | the classic school; ME neutralizable with me_cleaner |
| ASUS B450-PLUS (our TWIN-1 donor) | **no port** | 16/09 machine: guard fleet, +0 octet, forever |
| Most consumer AM4 boards | no port | why the guard exists |

## What Volume 5 documents

- the complete before/after map: `fw.spi.map --dump original.bin` vs
  `fw.spi.map --dump coreboot.rom` — the same photograph, two firmwares;
- what the vendor firmware hid that coreboot shows (SMM sources, boot
  policy, FSP/AGESA versions, microcode levels);
- what the vendor firmware knew that coreboot must relearn (memory
  training quirks, EC coordination, S3 behaviour);
- the honest cost line: hours spent, risks taken, knowledge gained.

## The rule that does not bend

The lab replaces firmware; the guard fleet never does. The moment a
write crosses onto a machine someone depends on, it is not the lab
anymore — it is the thing this project exists to prevent.
