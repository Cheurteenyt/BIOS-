# Diagnostics catalog — the named findings

Volume 4 of the study answers the "think about everything" demand with a
systematic grid: every component can fail in one of four families, and every
family has a distinct repair path. The thermal engine (P2) implements the
cooling slice; Phase 3 implements the storage, GPU, RAM and settings slices
(below). This catalog is the shared vocabulary between the engine, the docs
and the agents.

## The grid: four failure families

| Family | Meaning | Repair path |
|---|---|---|
| **Misconfigured** | the part is fine, the setting is wrong | software (T1 setting, or guided manual step) |
| **Firmware bug** | vendor BIOS itself misbehaves | BIOS update (T3 guided, human executes) |
| **Defective** | the hardware is broken | hands on the machine (human), replacement |
| **Degraded** | slow drift (dust, drying paste) | maintenance + baseline comparison (time) |

## The 12 hardware findings

| Finding | Family | Measurable evidence (already-exposed kernel sources) | Confidence | Remedy tier |
|---|---|---|---|---|
| pump-dead | defective | pump RPM ≈ 0 + Tctl > 80 °C (`/sys/class/hwmon`) | high (with coolant sensor) | hands |
| fan-zero-rpm | defective / misconfigured | fan RPM ≈ 0 + PWM curve | medium | hands or T1 curve |
| coolant-hot | misconfigured (airflow) / degraded | ΔT coolant−ambient ≥ 15 °C | medium | hands + T1 |
| interface-degraded | degraded (paste) / defective (mount) | R_th = ΔT/P ≥ 0.42-0.55 °C/W steady state | high with power counter | hands |
| instant-rise | degraded (paste) | 85 °C reached < 8 s under controlled load | medium | hands |
| runaway | defective (cooling) | sustained slope ≥ 0.5 °C/s near Tjmax | medium | hands |
| thermal-protection-active | any upstream cause | plateau ≥ Tjmax + measured power fold-back | high | root cause |
| insufficient-cooling | degraded | plateau 78-90 °C under load | medium | hands + T1 |
| vrm-hot | misconfigured (airflow) / degraded | VRM ≥ 89 °C under sustained load | medium | hands + T1 |
| v12-low | defective (PSU/cabling) | +12 V rail < 11.40 V (ADC ± 3 %) | low → multimeter | hands |
| hot-sensor | misconfigured (local airflow) | generic sensor ≥ 85 °C | medium | hands |
| gradual-degradation | degraded (dust, drying paste) | R_th / ΔT drift ≥ 25 % vs baseline ≥ 7 days | medium | maintenance |

## The 6 BIOS-side misconfigurations

| Finding | Family | Evidence source | Remedy tier |
|---|---|---|---|
| RAM running below spec (XMP/EXPO off) | misconfigured | dmidecode type 17 configured vs capable speed | guided manual (T3-like) |
| fan curve too lax | misconfigured | PWM curve + thermal signatures above | T1 curve (dry-run) |
| boot entry disorder | misconfigured | efibootmgr BootCurrent ∉ head of BootOrder | T2 staged write |
| stale NVRAM entries | misconfigured | efibootmgr entries with missing `.efi` on ESP | T2 staged write |
| energy profile suboptimal (EPP) | misconfigured | `energy_performance_preference` + workload | T1 write (dry-run) |
| firmware out of CVE policy | misconfigured (maintenance) | fw.audit.cve date inference | T3 guided update |

## The P3 findings — storage, GPU, RAM, settings

Implemented in Phase 3 (`fw.diag.storage`, `fw.diag.gpu`, `fw.diag.ram`,
`fw.diag.settings`), same finding shape as the thermal engine (id, severity,
category = the grid family, evidence, next steps, confidence):

| Finding id | Tool | Family | Measurable evidence | Remedy tier |
|---|---|---|---|---|
| storage-nvme-media-errors | storage | defective | `media_errors > 0` (smartctl) | hands, backup now |
| storage-nvme-spare-low | storage | defective | `available_spare <= threshold` | hands, replace |
| storage-nvme-wear-high | storage | degraded | `percentage_used >= 90` | maintenance plan |
| storage-nvme-hot | storage | degraded | controller ≥ 70 °C | hands (heatsink/airflow) |
| storage-unsafe-shutdowns | storage | misconfigured | unsafe/power-cycles > 10 % | habit + UPS check |
| storage-sata-failing | storage | defective | SMART overall FAILED | hands, replace |
| storage-sata-reallocated | storage | defective | Reallocated_Sector_Ct > 0 | hands, replace |
| storage-sata-pending | storage | degraded | Current_Pending_Sector > 0 | long SMART test, recheck |
| storage-sata-cable | storage | misconfigured | UDMA_CRC_Error_Count > 0 | reseat/replace the cable |
| storage-pcie-degraded | storage | misconfigured | LnkSta width/speed < LnkCap | reseat, riser, BIOS slot cfg |
| gpu-xid-errors | gpu | defective (suspected) | NVRM Xid lines (79/94/95 = critical) | reseat, power, stock clocks |
| gpu-thermal-slowdown | gpu | degraded | "HW Slowdown: Thermal" active | cooling, paste, airflow |
| gpu-bar1-small | gpu | misconfigured | BAR1 ≤ 256 MiB (ReBAR off) | optional BIOS enable (invisible) |
| gpu-pcie-degraded | gpu | misconfigured | link width < capable | reseat, riser, bifurcation |
| ram-xmp-off | ram | misconfigured | configured < rated, JEDEC default | BIOS profile (invisible) |
| ram-mixed-modules | ram | misconfigured | differing sizes/rated speeds | matched pairs |
| ram-uncorrected-errors | ram | defective | EDAC ue_count > 0 | memtest, replace DIMM |
| ram-corrected-errors | ram | degraded | EDAC ce_count ≥ 100 | stock tuning, baseline |
| settings-virtualization-off | settings | misconfigured | svm/vmx flag absent | BIOS enable (invisible) |
| settings-iommu-off | settings | misconfigured | no groups, no cmdline param | optional enable |
| settings-epp-pinned | settings | misconfigured | EPP = performance/power | T1 `cpu epp set` |
| settings-fans-bios-default | settings | misconfigured | all pwm_enable ∈ {0,2} | T1 `fans curve set` |
| settings-secure-boot-off | settings | misconfigured | efivar SecureBoot = 0 | guided re-enable |

The mis-adjusted-vs-defective distinction (vol. 4's founding question) is
carried by each finding's `category` field, so the agent can say not only
*what* is wrong but *which kind of repair* it implies.

## Reading the table as an agent

- **Evidence, not vibes.** Every row's evidence column cites sources the
  kernel already exposes — SMART/NVMe, LnkSta/AER, Xid + clock event
  reasons, rasdaemon/MCE, dmidecode, `pwm_enable`, EPP, efibootmgr. The
  engine correlates; it does not divine.
- **Confidence is part of the finding.** `low` means "invite a second
  instrument (multimeter, reseating)", not "shout a verdict".
- **Remedies stay tiered.** Misconfigured-in-software rows become T1 writes
  (dry-run, rollback) in P3+; anything with a screwdriver or a flashing
  USB stick stays human.
- **The catalog grows by contract.** A new finding = a new id, a new
  signature, a new scenario fixture, a new test that makes the engine name
  THE fault — see AGENTS.md §4.

## What is deliberately NOT here

- Failure modes with no measurable signal on this platform (e.g. a pump
  without a dedicated header label is not identifiable as a pump — the base
  prefers to ignore it than to invent it).
- Anything whose diagnosis would require writing to the machine.
- Vendor-specific heuristics that cannot be justified by a published
  physical or logical mechanism.
