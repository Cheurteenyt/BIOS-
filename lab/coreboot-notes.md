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

## Candidate machines (coreboot/Dasharo ports, as of late 2026)

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
