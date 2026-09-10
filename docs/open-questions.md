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
  the display. Proof that boot does not require display.
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
- DAY-0: verify each toggle against the real setup screens and the dump.

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
- DAY-0: `$BPM`/`$KSH` presence from `spi-map` (existence only — fused vs.
  deactivated is NOT determinable from the image, and the tool says so).

## Q5 — What does NVRAM really hold? (the hidden settings)

The `Setup` variable is a binary struct, mostly undocumented. Read-only
enumeration reveals names and sizes; field semantics stay vendor-internal
until someone parses them offline.

- NOW: `spi-map` NVRAM section enumerates variable names with an honest
  heuristic label.
- DAY-0: real names/counts, read-only; deeper parsing happens **offline from
  `day0-spi.bin`**, never on the live machine.

## Q6 — What talks before Linux? (the boot chain census)

SEC → PEI → DXE → BDS → shim → kernel. Every module that runs before the
kernel has a GUID and often a UI name — and `spi-map` extracts both.

- DAY-0: the module list **is** the census. Flag anything network-ish
  (HTTP boot, AMT/MEI helpers) and anything storage-ish (RAID OpROM).
- VOL-5: measuring what any of it actually *does* (behavior, not presence).

## Q7 — What runs when we are not looking? (SMM, ring -2)

SMM handlers execute invisible to the OS, triggered by SMIs, at higher
privilege than anything Linux can inspect. Presence and names are visible in
the image; behavior is not.

- NOW: `spi-map` counts SMM modules separately (`smm_drivers` summary field).
- DAY-0: the real SMM module names, read-only.
- VOL-5: deeper analysis only on sacrificial hardware.

## Q8 — What can Linux see that the firmware hides? (the runtime mirror)

dmidecode, efivarfs listings, MSR access, PCIe config space — a runtime mirror
of firmware state. Cross-checking the mirror against the image (what the
firmware declares vs. what the machine reports) is future digital-twin
enrichment. **Noted as a post-freeze lever; no tool added during the freeze.**

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

The protocol stays: `capture --live` → `rehearse` → `rehearse-diff --latest`,
optionally `sudo omarchy-firmware spi-map --save-dump day0-spi.bin` + sha256.

## Discipline

None of the eight questions requires a single byte written to the SPI chip.
The map is read-first by construction: the questions that could only be
answered by writing are Volume 5 questions, and Volume 5 answers them with a
dump in one hand and the original image in the other — before any flash,
every time.
