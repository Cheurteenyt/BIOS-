# Vendor BIOS heritage — what they shipped, what we keep, what we answer

Every design decision in this repository must hold against one question:
*what did the vendor BIOSes actually do before us, and why is our answer
better, or deliberately the same?* This document is that audit, kept next
to the code it governs. The vendor landscape below is the one measured in
volume 1 of the study (AM4 desktop boards, 2022-2026): ASUS, MSI,
Gigabyte, ASRock — four AMI-Aptio firmwares with the same bones and the
same blind spots.

## 1. The vendor landscape we build on

| Vendor | AM4 desktop state (measured in the study) | Consequence for this repo |
|---|---|---|
| ASUS | Active — B450-PLUS Gaming at BIOS 3644, AGESA 1.2.0.12 (Aug 2026), security-driven releases | The reference fixture board; updates exist, but are EZ Flash-only |
| MSI | Frozen — B450 Max BIOS line stopped March 2023 | The support cliff is real; a runtime layer outlives it |
| Gigabyte | Sparse — 2E45-era releases | Same cliff; Smart Fan 6 stays setup-UI-only |
| ASRock | Slow cadence (Sept 2025 era) | Same; trajectory B of the study (ASRock Rack X470D4U + coreboot) remains the alternative |

One structural fact from volume 1 drives our update posture: **desktop
AM4 boards are absent from the LVFS catalogue** — `fwupdmgr` sees no BIOS
capsules for them, so the vendor's only flash path is EZ Flash / Q-Flash /
M-Flash from the setup UI. That is why our T2 staging targets fwupd
*devices* (SSDs, docks, etc.), and BIOS updates stay a **T3 guided
walkthrough the human executes** — the vendor's own path, honestly kept.

## 2. What the vendor BIOS actually does — feature by feature

| Vendor feature (AM4, setup UI) | What it really does | Structural limit |
|---|---|---|
| Hardware Monitor page | Shows live temps, fan RPM, voltages as raw numbers, polled by the Super I/O | Human-read, poll-only: no correlation, no thresholds beyond the shutdown, no memory of yesterday |
| Q-LED / Debug LED / Q-Code | POST checkpoints and halt codes on the board or a two-digit display | Names a *phase*, never a *fault* — "d5" is not "your DIMM is not seated" |
| Beep codes | Coarse audio POST (memory, video) | Pre-UEFI heritage: 4-5 signals, then silence forever after boot |
| Q-Fan / Smart Fan / Fan Control | Static per-header PWM/DC curves stored in NVRAM, tuned once by hand | Accepts a curve that caps cooling; no degradation awareness; silent forever after |
| Settings profiles | Save/load a settings blob to USB or NVRAM | No diff, no history, no record of who changed what when |
| EZ Flash / Q-Flash / M-Flash | USB flash from setup UI, FlashBack on some boards | The only BIOS update path on AM4 desktop; no CVE context shown |
| XMP/EXPO/DOCP, SVM, IOMMU, Secure Boot, ReBAR toggles | Off or default by policy | The BIOS *causes* the most common misconfigurations and never lists them as such |
| Overheat protection | Tjmax throttle, then shutdown; "CPU Over Temperature Error!" POST halt | Names the symptom, never the cause; says nothing between boots |
| Chassis intrusion header | A switch that reports the case was opened | The closest a vendor gets to naming a physical fault — a binary switch |
| OS companions (Armoury Crate, AI Suite, GCC, Polychrome) | Resident, RGB-first, telemetry-laden bloatware; Fan Xpert lives here, not in the BIOS | Vendors already crossed the runtime line — badly. This is the anti-pattern, not a model |

The last row matters for coherence: **the vendors themselves moved fan
tuning and monitoring to the OS** — they just did it with resident
bloatware. Our move to the runtime is not a novelty to justify; it is the
vendor's own direction, executed without the daemon.

## 3. The four absences — what no vendor BIOS does, mapped to our answer

1. **Name the fault.** Vendors stop at raw values and halt codes. The
   engine here names 12 thermal findings plus the storage/GPU/RAM/settings
   slices with quantified evidence and confidence — the runtime successor
   of the beep code ([diagnostics-catalog.md](diagnostics-catalog.md)).
2. **Remember.** Nothing survives a vendor BIOS reboot except settings.
   The 200-entry dated baseline (S12) is the memory no BIOS has — drift,
   dust, drying paste become visible over days, for a ~0.03 % duty cycle
   ([frugality.md](frugality.md)).
3. **Correlate.** A vendor page will display 12.1 V and 90 °C side by
   side without a word. S1-S12 exist precisely to cross-check sensors
   (pump RPM vs Tctl vs coolant; power fold-back vs plateau) and to
   refuse double-diagnosis (a dead pump suppresses the paste verdict).
4. **Warn about itself.** No BIOS ever announced "this AGESA fixes the
   fTPM stutter you have". `fw.audit.cve` + `fw.cve.watch` do, from the
   packaged KB with date-based inference owned as such
   ([architecture.md](architecture.md)).

## 4. The coherence matrix

| Vendor BIOS does | This repo answers with | Coherent because |
|---|---|---|
| Hardware Monitor page | `fw.diag.thermal` (T0) — same Super I/O sensors via hwmon | Same data, plus correlation, thresholds, names, baseline |
| Q-Fan / Smart Fan curves | `fans.curve.set` (T1) + `settings-fans-bios-default` detection | Replaces the static curve, mechanically guarded: no curve that caps cooling ever writes |
| Settings profiles | Access journal + T1 backup store + T2 transaction record | Every change leaves a dated, replayable trace — profiles with accountability |
| EZ Flash / Q-Flash / M-Flash | T3 walkthrough; fwupd staging only where LVFS exists | The vendor flash path stays the vendor's; we prepare, the human executes |
| Beep codes / POST codes | Named findings S1-S12 + P3 slices | The same idea — a signal that means something — at runtime resolution |
| Chassis intrusion switch | The journal (`omarchy-firmware journal`) | Who, what, when — instead of a latch |
| AGESA security releases | `fw.audit.cve` + `fw.cve.watch` + two-key KB updater | Awareness at runtime; the flash itself stays human (T3) |
| Armoury Crate / Fan Xpert | One-shot CLI + optional disabled-by-default timer, +0 bytes SPI | The vendor's own runtime move, minus the daemon, minus the bloat |
| XMP/EXPO defaults left off | `fw.diag.ram` (`ram-xmp-off`: rated vs configured) | The misconfiguration the vendor ships is the first one listed |
| SVM/IOMMU/SecureBoot/ReBAR toggles | `fw.diag.settings` — the invisible listed honestly | Nothing is toggled from here; the agent explains, the human flips |
| MemTest86 embedding (some boards) | EDAC counters + guided human memtest | Honest scope: we detect, we never replace the vendor's test |

## 5. What we deliberately keep from the vendors

Coherence also means not "fixing" what was right:

- **The BIOS keeps its four irreplaceable jobs** — platform wake, memory
  training, trust chain, recovery (volume 1's conclusion). We duplicate
  none of them; +0 bytes of SPI flash is the acceptance criterion.
- **The BIOS stays the final thermal guard rail.** Tjmax throttling and
  emergency shutdown are never fought or bypassed; S8 *watches* the
  fold-back happen and explains it. Rule 6 of the doctrine encodes this.
- **The ADC's honesty.** Vendor Super I/O voltage reads carry ±3 % error;
  the vendor never pretended otherwise and neither do we — `v12-low`
  ships with low confidence and a multimeter recommendation, not a
  verdict.
- **The update path.** On AM4 desktop the vendor path is EZ Flash, and we
  do not invent a second one: staging exists for LVFS-covered devices,
  the BIOS itself stays human-flash, guided and checksummed.

## 6. Lessons from vendor history — and the guard each one bought

| Vendor-history event | What it taught | Guard in this repo |
|---|---|---|
| fTPM stutter (2022, AGESA 1.2.0.7) | Vendor fixes land only in BIOS updates users hear about late | CVE KB with `fixed_from_bios_date` inference; awareness does not wait for a Reddit thread |
| LogoFAIL (2023) | The setup UI's own parsers are attack surface | Nothing here parses firmware images; the KB is data, changed only under the two-key rule (sha256 staged, confirmed, revertible) |
| Sinkclose / CVE-2023-31315 (2024) | Vendor SMI handlers are privileged attack surface | No SMM/SMI code exists; +0 bytes SPI means no new handler to attack |
| MSI's 2023 freeze | Firmware support ends before the hardware dies | Everything runs at runtime: the layer keeps improving after the vendor stops |
| Armoury Crate era | The vendor OS layer became the bloatware cautionary tale | Frugality is a measured budget: one-shot ~0.3 s, no daemon, no embedded model, timer disabled by default |
| "CPU Over Temperature Error!" | Naming a symptom without a cause helps no one | Every finding carries evidence, hypothesis, next steps, confidence — and "undetermined" is a valid answer |

## 7. The coherence test, in one sentence

> **Same sensors as the vendor's Hardware Monitor, same flash path as the
> vendor's EZ Flash, same respect for the BIOS's own guard rails — plus
> the naming, the memory, the correlation and the CVE awareness the
> vendor never shipped.**
