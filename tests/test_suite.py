#!/usr/bin/env python3
"""T0 base test suite — runs without hardware, without pytest.

    python3 tests/test_suite.py            # the whole test pack
    python3 tests/test_suite.py -v         # verbose

Covers, in the spirit of the project rule of vol. 2 (ch. 9):
  - the parsers (smbios, boot, fwupd) on realistic fixtures;
  - the CVE reasoning (recent board vs old board);
  - the access journal (T0 journaled, including on error);
  - the structural out-of-scope refusal (T1/T2 declared, not implemented;
    unknown tool; no T3 call path);
  - the CLI end to end (--json, fixtures, exit code).
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

os.environ.setdefault("XDG_STATE_HOME", tempfile.mkdtemp())  # isolated journal

from firmware_hal import actions, audit, boot, boot as bootmod, cli, cve_kb, diagnostics, fwupd, gpu, journal, mcp_server, ram, sensors, settings as settings_mod, smbios, storage, tiers  # noqa: E402

FIX_A = ROOT / "tests" / "fixtures" / "b450-plus"
FIX_B = ROOT / "tests" / "fixtures" / "b550-f-old"
FIX_CLEAN = ROOT / "tests" / "fixtures" / "b450-plus-clean"

_tests: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    _tests.append((name, bool(cond), detail))


# ---------------------------------------------------------------- smbios ---
b = smbios.collect(FIX_A)
check("smbios: board read", b.get("board_product") == "TUF Gaming B450-PLUS GAMING", str(b))
check("smbios: BIOS 3644", b.get("bios_version") == "3644")
check("smbios: ISO date", b.get("bios_date") == "2026-08-12", str(b.get("bios_date")))
check("smbios: AM4 socket", b.get("cpu_socket") == "Socket AM4")
check("smbios: 5950X CPU", "5950X" in (b.get("cpu_model") or ""))
check("smbios: is_am4", smbios.is_am4(b) is True)
check("smbios: ASUS desktop note", "motherboard" in (b.get("system_note") or ""))

b2 = smbios.collect(FIX_B)
check("smbios B: B550-F", b2.get("board_product") == "ROG STRIX B550-F GAMING")
check("smbios B: 2023 date", b2.get("bios_date") == "2023-10-18")

# ------------------------------------------------------------------ boot ---
bt = boot.collect(FIX_A)
check("boot: 3 entries", len(bt.get("entries", [])) == 3, str(bt.get("entries")))
check("boot: order", bt.get("boot_order") == ["0002", "0001", "0000"])
check("boot: BootCurrent", bt.get("boot_current") == "0002")
check("boot: order names", bt.get("boot_order_names", [""])[0] == "Omarchy Linux (UKI)")
check("boot: Limine+UKI chain", "Limine" in bt.get("chain", ""), str(bt.get("chain")))
kinds = {e["kind"] for e in bt["entries"]}
check("boot: windows identified", "windows" in kinds)
check("boot: UKI file extracted", any(e["file"] == r"\EFI\Linux\omarchy-6.12-lts.efi" for e in bt["entries"]))
check("boot: no order warning", not bt.get("warnings_w", bt.get("warnings")) or all("BootCurrent" not in w for w in bt.get("warnings", [])))

# warning: BootCurrent != first of BootOrder (a case detectable without ESP)
synthetic = "BootCurrent: 0000\nBootOrder: 0001,0000\nBoot0000* Windows\tHD(1,GPT,x)/File(\\EFI\\Microsoft\\Boot\\bootmgfw.efi)\nBoot0001* Limine\tHD(1,GPT,x)/File(\\EFI\\Limine\\LimineX64.efi)\n"
syn = bootmod._parse(synthetic)
check("boot: consistency warning", any("BootCurrent" in w for w in syn["warnings"]), str(syn["warnings"]))

# ----------------------------------------------------------------- fwupd ---
fd = fwupd.collect_devices(FIX_A)
check("fwupd: 3 devices", fd.get("device_count") == 3, str(fd.get("device_count")))
check("fwupd: board out of LVFS", fd.get("motherboard_in_lvfs") is False,
      "System Firmware must not count as an LVFS motherboard")
check("fwupd: HSI:4", (fd.get("security") or {}).get("host_security_id") == "HSI:4")
check("fwupd: 1 HSI failure", (fd.get("security") or {}).get("failures") == 1)
up = fwupd.check_updates(FIX_A)
check("fwupd: NVMe update detected", any(u["device"].startswith("Samsung") for u in up.get("updates", [])), json.dumps(up)[:200])

# ------------------------------------------------------------------- cve ---
c = cve_kb.collect(FIX_A)
stat = {f["id"]: f["status"] for f in c["findings"]}
check("cve: recent board LogoFAIL fixed", stat["logofail-2023"].startswith("probably"), stat["logofail-2023"])
check("cve: recent board Sinkclose fixed", stat["sinkclose-2023-31315"].startswith("probably"))
check("cve: 2026 CVE unknown status", stat["cve-2026-6726"].startswith("unknown"), stat["cve-2026-6726"])
check("cve: T3 verdict present", "T3" in c.get("verdict", ""), c.get("verdict", ""))

c2 = cve_kb.collect(FIX_B)
stat2 = {f["id"]: f["status"] for f in c2["findings"]}
check("cve B: LogoFAIL exposed", stat2["logofail-2023"].startswith("potentially"), stat2["logofail-2023"])
check("cve B: Sinkclose exposed", stat2["sinkclose-2023-31315"].startswith("potentially"))
check("cve B: fTPM fixed (2023 > 2022)", stat2["ftpm-stutter-2022"].startswith("probably"))
check("cve B: rationale cited", all(f["rationale"] for f in c2["findings"]))

# -------------------------------------------------------------- journal ---
td = tempfile.mkdtemp()
os.environ["XDG_STATE_HOME"] = td
e = journal.record("fw.audit.status", "T0", ["test"], "ok", "test write")
journal_ok = journal.journal_path().exists()
check("journal: written", e["ts"] != "" and journal_ok)
check("journal: re-readable", journal.show()[0]["tool"] == "fw.audit.status")

# ---------------------------------------------------------------- tiers ---
try:
    tiers.assert_phase1("fw.update.stage")
    check("tiers: T2 refused (update.stage)", False, "should have been refused")
except tiers.TierRefused as exc:
    # P4: the refusal names the human CLI path — the agent prepares, the human applies
    check("tiers: T2 refused (update.stage)", "update stage --device" in str(exc), str(exc))
try:
    tiers.assert_phase1("fw.rollback")
    check("tiers: T2 refused (rollback)", False, "should have been refused")
except tiers.TierRefused as exc:
    check("tiers: T2 refused (rollback)", "inventory" in str(exc), str(exc))
try:
    tiers.assert_phase1("fw.flash.write")
    check("tiers: unknown T3 refused", False)
except tiers.TierRefused:
    check("tiers: unknown T3 refused", True)
check("tiers: contract = 14 tools", len(tiers.TOOL_TIERS) == 14)
check("tiers: 10 T0 implemented", len(tiers.IMPLEMENTED_T0) == 10)
check("tiers: cve.watch declared T0", tiers.tier_of("fw.cve.watch") == "T0"
      and "fw.cve.watch" in tiers.IMPLEMENTED_T0)
check("tiers: 2 T1 implemented", len(tiers.IMPLEMENTED_T1) == 2)
check("tiers: epp declared T1", tiers.tier_of("cpu.epp.set") == "T1")
check("tiers: fans declared T1", tiers.tier_of("fans.curve.set") == "T1")
check("tiers: T1 accepted by scope", tiers.assert_phase1("cpu.epp.set") == "T1")
check("tiers: no T3 path", "fw.flash.write" not in tiers.TOOL_TIERS)

# ------------------------------------------------------------------ cli ---
os.environ["XDG_STATE_HOME"] = td
rc = cli.main(["audit", "status", "--json", "--fixture-dir", str(FIX_A)])
check("cli: audit status rc=0", rc == 0)
rc = cli.main(["audit", "cve", "--json", "--fixture-dir", str(FIX_A)])
check("cli: audit cve rc=0", rc == 0)
rc = cli.main(["boot", "inspect", "--json", "--fixture-dir", str(FIX_A)])
check("cli: boot inspect rc=0", rc == 0)
rc = cli.main(["update", "check", "--json", "--fixture-dir", str(FIX_A)])
check("cli: update check rc=0", rc == 0)
rc = cli.main(["journal", "5", "--json"])
check("cli: journal rc=0", rc == 0)
entries = journal.show(5)
check("cli: calls journaled", len(entries) >= 4 and all(x.get("tier") == "T0" for x in entries))
check("cli: fixture mark", sum(1 for x in entries if x.get("fixture")) >= 4)

# ---------------------------------------------------------------- audit ---
a = audit.collect(FIX_A)
check("audit: composite", a.get("board", {}).get("board_product") and a.get("boot", {}).get("chain"))
check("audit: sensors", a.get("sensors", {}).get("chip_count") == 2, json.dumps(a.get("sensors"))[:120])
check("audit: P4 phase declared", "P4" in (a.get("phase") or ""), a.get("phase"))

# ------------------------------------------------------------------ diag ---
# The physical diagnostics (vol. 3): every scenario must name THE fault,
# not a catch-all list. The scenarios are the pre-recorded physics.
SCEN = diagnostics._scenario_dir()

sc_all = {p.stem for p in SCEN.glob("*.json")}
check("diag: 12 bundled scenarios", len(sc_all) == 12, str(sorted(sc_all)))


def _run(scen, baseline=None):
    data = diagnostics.load_scenario(scen)
    return diagnostics.diagnose(data["samples"], data.get("meta", {}), baseline=baseline)


r = _run("healthy-liquid")
check("diag healthy: healthy verdict", r["verdict"].startswith("healthy"), r["verdict"])
check("diag healthy: no finding", r["findings"] == [], str(r["findings"]))
check("diag healthy: fans read", r["measurements"]["fans"].get("pump") == 1850)

r = _run("no-paste")
ids = {f["id"] for f in r["findings"]}
check("diag paste: critical verdict", r["verdict"] == "critical", r["verdict"])
check("diag paste: interface named", "interface-degraded" in ids, str(ids))
check("diag paste: R_th critical >= 0.55", (r["measurements"]["r_th"] or 0) >= 0.55,
      str(r["measurements"]["r_th"]))
check("diag paste: instant rise", "instant-rise" in ids)
check("diag paste: throttle named", "thermal-protection-active" in ids,
      "the power fold-back must be said out loud")

r = _run("pump-dead")
ids = [f["id"] for f in r["findings"]]
check("diag pump: critical verdict", r["verdict"] == "critical", r["verdict"])
check("diag pump: finding #1 = pump", ids and ids[0] == "pump-dead", str(ids))
check("diag pump: no double-diagnosed interface",
      "interface-degraded" not in ids, "the pump explains everything — no invented paste")

r = _run("radiator-fan")
ids = {f["id"] for f in r["findings"]}
check("diag fan: critical verdict", r["verdict"] == "critical", r["verdict"])
check("diag fan: head at 0", "fan-zero-rpm" in ids)
check("diag fan: coolant hot", "coolant-hot" in ids)
check("diag fan: healthy R_th (die->liquid path fine)",
      0.2 <= (r["measurements"]["r_th"] or 9) <= 0.32, str(r["measurements"]["r_th"]))

r = _run("vrm-hot")
ids = {f["id"] for f in r["findings"]}
check("diag vrm: attention verdict", r["verdict"] == "attention", r["verdict"])
check("diag vrm: vrm-hot finding", "vrm-hot" in ids)

r = _run("v12-sag")
ids = {f["id"] for f in r["findings"]}
check("diag 12v: attention verdict", r["verdict"] == "attention", r["verdict"])
check("diag 12v: low rail detected", "v12-low" in ids)

r = _run("case-fan-dead")
ids = {f["id"] for f in r["findings"]}
check("diag casefan: attention verdict", r["verdict"] == "attention", r["verdict"])
check("diag casefan: dead head named", "fan-zero-rpm" in ids, str(ids))
check("diag casefan: interface stays healthy (the AIO hides it)",
      0.2 <= (r["measurements"]["r_th"] or 9) <= 0.32, str(r["measurements"]["r_th"]))

r = _run("runaway")
ids = {f["id"] for f in r["findings"]}
check("diag runaway: critical verdict", r["verdict"] == "critical", r["verdict"])
check("diag runaway: undamped slope named", "runaway" in ids, str(ids))
check("diag runaway: no instant-rise (85 °C reached late)",
      "instant-rise" not in ids, str(ids))

r = _run("heatwave")
ids = {f["id"] for f in r["findings"]}
check("diag heatwave: attention verdict", r["verdict"] == "attention", r["verdict"])
check("diag heatwave: fold-back observed", "thermal-protection-active" in ids,
      str(ids))
check("diag heatwave: interface stays healthy (the room is the cause)",
      0.2 <= (r["measurements"]["r_th"] or 9) <= 0.41, str(r["measurements"]["r_th"]))
check("diag heatwave: radiator saturation named", "coolant-hot" in ids)

r = _run("hot-nvme")
ids = {f["id"] for f in r["findings"]}
check("diag nvme: hotspot named", "hot-sensor" in ids, str(ids))
check("diag nvme: one finding per sensor, no duplication", len(ids) == 1, str(ids))
check("diag nvme: CPU verdict stays honest",
      r["verdict"].startswith("healthy"), r["verdict"])

# trend: the scenario alone stays under the absolute thresholds (honesty);
# the longitudinal baseline is what names the slow degradation.
r0 = _run("trend-dust")
check("diag trend: no baseline, nothing invented", r0["findings"] == [], str(r0["findings"]))
BASELINE = [{"ts": "2026-03-05", "mode": "probe", "rth": 0.24, "dt_idle": None, "tctl_med": None}]
r = _run("trend-dust", baseline=BASELINE)
ids = {f["id"] for f in r["findings"]}
check("diag trend: old baseline -> degradation named",
      "gradual-degradation" in ids and r["verdict"] == "attention", str(ids))
YOUNG_BASELINE = [{"ts": time.strftime("%Y-%m-%d"), "mode": "probe", "rth": 0.24}]
check("diag trend: recent baseline ignored", _run("trend-dust", baseline=YOUNG_BASELINE)["findings"] == [])

r = _run("undetermined")
check("diag undetermined: owned verdict", r["verdict"] == "undetermined", r["verdict"])
check("diag undetermined: low confidence", r["measurements"]["confidence"] == "low")

# normalization: the standard audit fixture reduces to a canonical sample
sn = diagnostics.normalize(sensors.collect(FIX_A)["chips"])
check("diag normalize: Tctl read", sn["tctl"] == 52.4, str(sn))
check("diag normalize: ambient = SYSTIN", sn["ambient"] == 38.0)
check("diag normalize: fan1 kept", sn["fans"].get("fan1_input") == 1150)

# CLI end to end
os.environ["XDG_STATE_HOME"] = td
rc = cli.main(["diag", "quick", "--scenario", "no-paste", "--json"])
check("cli: diag quick rc=0", rc == 0)
rc = cli.main(["diag", "quick", "--scenario", "nonexistent", "--json"])
check("cli: diag unknown scenario rc=1", rc == 1)
rc = cli.main(["diag", "scenarios", "--json"])
check("cli: diag scenarios rc=0", rc == 0)
last = journal.show(2)
check("cli: diag journaled",
      all(e["tool"] == "fw.diag.thermal" and e["tier"] == "T0" for e in last),
      str(last))

# MCP server: the twelve tools are declared with their tiers
from firmware_hal import mcp_server as _mcp_server  # noqa: E402
specs = {s["name"]: s["risk_tier"] for s in _mcp_server._tool_specs()}
check("mcp: 12 tools declared", len(specs) == 12, str(specs))
check("mcp: fw.cve.watch T0", specs.get("fw.cve.watch") == "T0")
check("mcp: T2 tools NOT in MCP surface",
      "fw.update.stage" not in specs and "fw.rollback" not in specs)
check("mcp: fw.diag.thermal T0", specs.get("fw.diag.thermal") == "T0")
check("mcp: 4 new T0 declared",
      all(specs.get(f"fw.diag.{t}") == "T0"
          for t in ("storage", "gpu", "ram", "settings")))
check("mcp: T1 tools declared",
      specs.get("cpu.epp.set") == "T1" and specs.get("fans.curve.set") == "T1")

# ------------------------------------------------------------- storage ---
# The b450-plus fixture set encodes: healthy NVMe, SATA with reallocated +
# pending sectors, NVMe controller on a degraded PCIe link.
st = storage.collect(FIX_A)
ids = {f["id"] for f in st["findings"]}
check("storage: nvme read", any(d["kind"] == "nvme" for d in st["disks"]))
check("storage: nvme itself healthy",
      not any(i.startswith("storage-nvme") for i in ids), str(ids))
check("storage: sata reallocated named (defective)",
      "storage-sata-reallocated" in ids, str(ids))
check("storage: sata pending named", "storage-sata-pending" in ids, str(ids))
check("storage: pcie link degraded named (mis-adjusted)",
      "storage-pcie-degraded" in ids, str(ids))
check("storage: unsafe-shutdown ratio stays honest (3/412)",
      "storage-unsafe-shutdowns" not in ids, str(ids))
check("storage: verdict critical", st["verdict"] == "critical", st["verdict"])
check("storage: findings carry category",
      all(f.get("category") in ("defective", "mis-adjusted", "degraded")
          for f in st["findings"]))
check("storage: evidence on every finding",
      all(f.get("evidence") and f.get("next_steps") for f in st["findings"]))

st_clean = storage.collect(FIX_CLEAN)
check("storage clean: healthy verdict", st_clean["verdict"] == "healthy",
      json.dumps(st_clean["findings"])[:200])
check("storage clean: no finding", st_clean["findings"] == [])
check("storage clean: absent SATA tolerated",
      not any(d["kind"] == "sata" for d in st_clean["disks"]))

# synthetic: GPU link width degraded (x8 out of x16) is named by fw.diag.gpu
tmp_lspci = Path(tempfile.mkdtemp())
(tmp_lspci / "lspci.txt").write_text(
    (FIX_A / "lspci.txt").read_text().replace(
        "Speed 8GT/s (downgraded), Width x16", "Speed 8GT/s (downgraded), Width x8", 1))
gp_syn = gpu.collect(tmp_lspci)
check("gpu synthetic: width degraded named",
      "gpu-pcie-degraded" in {f["id"] for f in gp_syn["findings"]},
      str(gp_syn["findings"])[:200])

# ----------------------------------------------------------------- gpu ---
gp = gpu.collect(FIX_A)
ids = {f["id"] for f in gp["findings"]}
check("gpu: xid errors named", "gpu-xid-errors" in ids, str(ids))
check("gpu: xid codes parsed (13, 62)",
      sorted({x["code"] for x in gp.get("xid_errors", [])}) == [13, 62],
      str(gp.get("xid_errors")))
check("gpu: xid 13/62 = attention, not panic", gp["verdict"] == "attention",
      gp["verdict"])
check("gpu: BAR1 256 MiB -> ReBAR finding", "gpu-bar1-small" in ids, str(ids))
check("gpu: no thermal slowdown (Not Active in fixture)",
      "gpu-thermal-slowdown" not in ids, str(ids))
check("gpu: driver read", gp["nvidia"]["driver"] == "580.82.09",
      str(gp["nvidia"]))
check("gpu: GSP firmware read (vol. 1 ch. nvidia)",
      gp["nvidia"]["gsp_firmware"] == "580.82.09")
check("gpu: x16 link not flagged", "gpu-pcie-degraded" not in ids)

gp_clean = gpu.collect(FIX_CLEAN)
check("gpu clean: healthy verdict", gp_clean["verdict"] == "healthy",
      json.dumps(gp_clean["findings"])[:200])
check("gpu clean: no Xid in log", gp_clean.get("xid_errors") == [])
check("gpu clean: BAR1 8192 -> no finding",
      "gpu-bar1-small" not in {f["id"] for f in gp_clean["findings"]})

# synthetic: Xid 79 (fell off the bus) is the critical class
tmp_dmesg = Path(tempfile.mkdtemp())
(tmp_dmesg / "dmesg.txt").write_text(
    "[  9.00] nvidia: module loaded\n"
    "[ 10.00] NVRM: Xid (PCI:0000:01:00): 79, GPU has fallen off the bus\n")
gp79 = gpu.collect(tmp_dmesg)
check("gpu synthetic: Xid 79 critical",
      gp79["verdict"] == "critical"
      and gp79["findings"][0]["id"] == "gpu-xid-errors",
      json.dumps(gp79["findings"])[:200])

# ----------------------------------------------------------------- ram ---
rm = ram.collect(FIX_A)
ids = {f["id"] for f in rm["findings"]}
check("ram: xmp-off named (2133 vs 3600)", "ram-xmp-off" in ids, str(ids))
check("ram: 2 populated, 2 empty",
      rm["slots"]["populated"] == 2 and rm["slots"]["empty"] == 2,
      str(rm["slots"]))
check("ram: total 32 GB", rm["total_installed_gb"] == 32)
check("ram: ECC absence reported honestly",
      rm["ecc"]["available"] is False and rm["ecc"]["smbios_type"] == "None")
check("ram: verdict attention", rm["verdict"] == "attention", rm["verdict"])
check("ram: next step cites the profile",
      all("XMP/EXPO/DOCP" in f["next_steps"] for f in rm["findings"]
          if f["id"] == "ram-xmp-off"))

rm_clean = ram.collect(FIX_CLEAN)
check("ram clean: configured = rated 3600",
      all(m["configured_speed"] == 3600 for m in rm_clean["modules"]
          if (m.get("size") or "").startswith("16")),
      json.dumps(rm_clean["modules"])[:200])
check("ram clean: healthy verdict", rm_clean["verdict"] == "healthy")
check("ram clean: no finding", rm_clean["findings"] == [])

# synthetic: EDAC uncorrected errors -> critical
tmp_edac = Path(tempfile.mkdtemp())
(tmp_edac / "edac.json").write_text(
    '{"mc": [{"id": "mc0", "ce_count": 12, "ue_count": 3}]}')
(tmp_edac / "dmidecode-memory.txt").write_text(
    (FIX_A / "dmidecode-memory.txt").read_text())
rm_err = ram.collect(tmp_edac)
ids = {f["id"] for f in rm_err["findings"]}
check("ram synthetic: uncorrected errors critical",
      "ram-uncorrected-errors" in ids and rm_err["verdict"] == "critical",
      str(ids))

# ------------------------------------------------------------ settings ---
se = settings_mod.collect(FIX_A)
ids = {f["id"] for f in se["findings"]}
check("settings: svm off named", "settings-virtualization-off" in ids, str(ids))
check("settings: epp pinned named", "settings-epp-pinned" in ids, str(ids))
check("settings: fans on bios default named",
      "settings-fans-bios-default" in ids, str(ids))
check("settings: iommu off (info) named", "settings-iommu-off" in ids, str(ids))
check("settings: secure boot read (on)", se["secure_boot"]["enabled"] is True)
check("settings: needs_bios_check lists the invisible",
      len(se["needs_bios_check"]) >= 4, str(se["needs_bios_check"]))
check("settings: ReBAR honesty (in needs_bios_check, not a finding)",
      any("Resizable BAR" in x for x in se["needs_bios_check"]))
check("settings: verdict attention", se["verdict"] == "attention", se["verdict"])

se_clean = settings_mod.collect(FIX_CLEAN)
check("settings clean: no attention finding",
      not any(f["severity"] == "attention" for f in se_clean["findings"]),
      json.dumps(se_clean["findings"])[:200])

# -------------------------------------------- T1 actions: epp (two keys) ---
T1_STATE = tempfile.mkdtemp()  # isolated rollback store
os.environ["XDG_STATE_HOME"] = T1_STATE
T1_TMP = Path(tempfile.mkdtemp())
cpu_root = T1_TMP / "cpu"
for n in (0, 1):
    d = cpu_root / f"cpu{n}" / "cpufreq"
    d.mkdir(parents=True)
    (d / "energy_performance_available_preferences").write_text(
        "default performance balance_performance balance_power power\n")
    (d / "energy_performance_preference").write_text("balance_performance\n")
os.environ["FW_SYSFS_CPU"] = str(cpu_root)

EPP0 = cpu_root / "cpu0" / "cpufreq" / "energy_performance_preference"
EPP1 = cpu_root / "cpu1" / "cpufreq" / "energy_performance_preference"

r = actions.epp_set("performance")
check("t1 epp: dry-run by default", r["status"] == "dry-run", str(r)[:120])
check("t1 epp: dry-run changes nothing",
      EPP0.read_text().strip() == "balance_performance")
check("t1 epp: plan carries the diff", len(r["diff"]) == 2, str(r.get("diff"))[:120])

try:
    actions.epp_set("bogus")
    check("t1 epp: invalid value refused", False)
except actions.ActionRefused as exc:
    check("t1 epp: invalid value refused", "available" in str(exc), str(exc)[:120])

r = actions.epp_set("performance", confirm=True)
check("t1 epp: confirm applies", r["status"] == "applied", str(r)[:200])
check("t1 epp: value written on both cpus",
      EPP0.read_text().strip() == "performance"
      and EPP1.read_text().strip() == "performance")
check("t1 epp: backup stored", r.get("backup_id") is not None
      and (journal.state_dir() / "rollback" / "epp.json").exists())

r = actions.epp_set("performance", confirm=True)
check("t1 epp: idempotent re-run is a dry-run note",
      r["status"] == "dry-run" and "already" in r.get("note", ""), str(r)[:120])

r = actions.epp_set(undo=True, confirm=True)
check("t1 epp: undo rolls back", r["status"] == "rolled-back", str(r)[:200])
check("t1 epp: previous values restored",
      EPP0.read_text().strip() == "balance_performance")

r2 = actions.epp_set(undo=True)  # no confirm: dry-run plan
check("t1 epp: undo without confirm is a dry-run", r2["status"] == "dry-run")

# ------------------------------------------------ T1 actions: fans curve ---
hw_root = T1_TMP / "hwmon" / "hwmon0"
hw_root.mkdir(parents=True)
(hw_root / "name").write_text("nct6798\n")
(hw_root / "pwm1").write_text("128\n")
(hw_root / "pwm1_enable").write_text("2\n")
for k, (t, p) in enumerate([(40, "64"), (60, "128"), (80, "255")], start=1):
    (hw_root / f"pwm1_auto_point{k}_temp").write_text(f"{t}\n")
    (hw_root / f"pwm1_auto_point{k}_pwm").write_text(f"{p}\n")
os.environ["FW_SYSFS_HWMON"] = str(T1_TMP / "hwmon")

CURVE = {"hwmon": "nct6798", "pwm": 1, "points": [
    {"temp": 40, "pwm": 90}, {"temp": 60, "pwm": 140},
    {"temp": 85, "pwm": 255}]}  # 3 points = the 3 slots the tmp chip exposes

try:
    actions.fans_curve_set({"hwmon": "nct6798", "pwm": 1, "points": [
        {"temp": 40, "pwm": 90}, {"temp": 55, "pwm": 120},
        {"temp": 70, "pwm": 180}, {"temp": 85, "pwm": 255}]})
    check("t1 fans: more points than slots refused", False,
          "dropping a point could drop the mandatory 255 tail")
except actions.ActionRefused:
    check("t1 fans: more points than slots refused", True)

for bad, why in (
        ({"hwmon": "nct6798", "pwm": 1, "points": [
            {"temp": 40, "pwm": 90}, {"temp": 85, "pwm": 200}]},
         "last point pwm != 255"),
        ({"hwmon": "nct6798", "pwm": 1, "points": [
            {"temp": 40, "pwm": 90}, {"temp": 95, "pwm": 255}]},
         "last point temp > 90"),
        ({"hwmon": "nct6798", "pwm": 1, "points": [
            {"temp": 60, "pwm": 90}, {"temp": 50, "pwm": 255}]},
         "temps not ascending"),
        ({"hwmon": "nct6798", "pwm": 1, "points": [{"temp": 40, "pwm": 90}]},
         "single point")):
    try:
        actions.fans_curve_set(bad)
        check(f"t1 fans: refused ({why})", False)
    except actions.ActionRefused as exc:
        check(f"t1 fans: refused ({why})",
              any(frag in str(exc).lower()
                  for frag in ("curve", "point", "255", "90", "temp")),
              str(exc)[:120])

try:
    actions.fans_curve_set({"hwmon": "coretemp", "pwm": 1, "points": CURVE["points"]})
    check("t1 fans: unsupported chip refused", False)
except actions.ActionRefused:
    check("t1 fans: unsupported chip refused", True)

r = actions.fans_curve_set(CURVE)
check("t1 fans: dry-run by default", r["status"] == "dry-run")
check("t1 fans: plan lists the writes", len(r["plan_writes"]) >= 5, str(r)[:150])
check("t1 fans: dry-run writes nothing", (hw_root / "pwm1_enable").read_text().strip() == "2")

r = actions.fans_curve_set(CURVE, confirm=True)
check("t1 fans: confirm applies", r["status"] == "applied", str(r)[:200])
check("t1 fans: mode switched to hardware curve (5)",
      (hw_root / "pwm1_enable").read_text().strip() == "5")
check("t1 fans: point temps written",
      (hw_root / "pwm1_auto_point3_temp").read_text().strip() == "85")
check("t1 fans: last point is 255 (mechanical guard honoured)",
      (hw_root / "pwm1_auto_point3_pwm").read_text().strip() == "255")

r = actions.fans_curve_set(undo=True, confirm=True)
check("t1 fans: undo rolls back", r["status"] == "rolled-back", str(r)[:200])
check("t1 fans: previous curve restored",
      (hw_root / "pwm1_enable").read_text().strip() == "2"
      and (hw_root / "pwm1_auto_point1_pwm").read_text().strip() == "64")

show = actions.fans_curve_show()
check("t1 fans: show lists the chip", show["chips"][0]["name"] == "nct6798")

# ------------------------------------------------------ MCP T1 dry-run ---
os.environ["FW_SYSFS_CPU"] = str(cpu_root)
r = _mcp_server._run_tool("cpu.epp.set", {"value": "performance"})
check("mcp: epp dry-run default", r["status"] == "dry-run", str(r)[:150])
check("mcp: epp dry-run journaled", r["journal_entry"]["status"] == "dry-run")
r = _mcp_server._run_tool("cpu.epp.set", {"value": "performance", "confirm": True})
check("mcp: confirm applies", r["status"] == "applied", str(r)[:150])
actions.epp_set(undo=True, confirm=True)  # leave the tree as found

# -------------------------------------------------------- CLI end to end ---
os.environ["XDG_STATE_HOME"] = T1_STATE
for sub in ("storage", "gpu", "ram", "settings"):
    rc = cli.main(["diag", sub, "--json", "--fixture-dir", str(FIX_A)])
    check(f"cli: diag {sub} rc=0", rc == 0)
rc = cli.main(["cpu", "epp", "set", "performance", "--json"])
check("cli: epp set dry-run rc=0", rc == 0)
rc = cli.main(["cpu", "epp", "set", "bogus", "--json"])
check("cli: epp invalid refused rc=2", rc == 2)
rc = cli.main(["cpu", "epp", "set", "performance", "--confirm", "--json"])
check("cli: epp confirm applied rc=0", rc == 0)
rc = cli.main(["cpu", "epp", "undo", "--confirm", "--json"])
check("cli: epp undo rc=0", rc == 0)
rc = cli.main(["fans", "curve", "show", "--json"])
check("cli: fans show rc=0", rc == 0)
curve_file = T1_TMP / "curve.json"
curve_file.write_text(json.dumps(CURVE))
rc = cli.main(["fans", "curve", "set", "--file", str(curve_file), "--json"])
check("cli: fans set dry-run rc=0", rc == 0)
rc = cli.main(["fans", "curve", "set", "--file", str(curve_file),
               "--confirm", "--json"])
check("cli: fans set applied rc=0", rc == 0)
rc = cli.main(["fans", "curve", "undo", "--confirm", "--json"])
check("cli: fans undo rc=0", rc == 0)

t1_entries = [e for e in journal.show(50) if e["tier"] == "T1"]
check("cli: T1 calls journaled with statuses",
      len(t1_entries) >= 5
      and {e["status"] for e in t1_entries} >= {"dry-run", "applied", "rolled-back"},
      str([(e["tool"], e["status"]) for e in t1_entries])[:200])
check("cli: every T1 journal entry carries a truthful status",
      all(e["status"] in ("dry-run", "applied", "rolled-back", "refused",
                          "error", "ok")  # ok = the read-only show, T0 flow
          for e in t1_entries))


# -------------------------------------------------------------------- P4 ---
# Phase 4 — the supervised loop: fw.cve.watch (T0), the two-key KB
# updater, the human-gated T2 staging and the refusal-by-design rollback.
from firmware_hal import cve_watch, kb_update, report, rollback, stage  # noqa: E402

# --- fw.cve.watch: freshness, baseline, drift ------------------------------
w = cve_watch.collect(FIX_A)
check("watch: kb info present",
      w["kb"]["sha256"] and w["kb"]["entry_count"] == len(cve_kb.load_kb()["entries"]),
      json.dumps(w["kb"])[:150])
check("watch: age_days is a sane int", w["kb"]["age_days"] is not None and w["kb"]["age_days"] >= 0)
check("watch: exposure replay matches the audit",
      w["exposure"]["entries"] == 5, json.dumps(w["exposure"]))
check("watch: first run records the baseline", w["drift"]["status"] == "baseline-recorded")
w2 = cve_watch.collect(FIX_A)
check("watch: unchanged KB -> no change", w2["drift"]["status"] == "no-change")
check("watch: fwupd cross-check available", w2["fwupd_cross_check"]["available"] is True)
check("watch: candidate advisory found (CVE-2026-4478 unknown to the KB)",
      "CVE-2026-4478" in w2["fwupd_cross_check"]["candidates"],
      json.dumps(w2["fwupd_cross_check"])[:200])

# --- kb.update: the two-key rule applied to DATA ----------------------------
kb_tmp = Path(tempfile.mkdtemp(prefix="ofw-kb-"))
base = cve_kb.load_kb()
new_kb = dict(base)
new_kb["entries"] = list(base["entries"]) + [
    {"id": "test-new-advisory-2026", "title": "Test advisory", "year": 2026,
     "severity": "medium", "fixed_from_bios_date": None}]
new_kb["generated"] = time.strftime("%Y-%m-%d")
kb_file = kb_tmp / "kb.json"
kb_file.write_text(json.dumps(new_kb, ensure_ascii=False), encoding="utf-8")
import hashlib  # noqa: E402
kb_sha = hashlib.sha256(kb_file.read_bytes()).hexdigest()

staged = kb_update.stage(str(kb_file))
check("kb: stage is a dry-run", staged["status"] == "dry-run")
check("kb: stage shows the full hash", staged["sha256"] == kb_sha)
check("kb: nothing activated at stage", not cve_kb._override_path().exists())
try:
    kb_update.activate(str(kb_file), url=False, sha256=None)
    check("kb: confirm without sha refused", False)
except kb_update.KbRefused:
    check("kb: confirm without sha refused", True)
try:
    kb_update.activate(str(kb_file), url=False, sha256="0" * 64)
    check("kb: sha mismatch refused (supply-chain guard)", False)
except kb_update.KbRefused:
    check("kb: sha mismatch refused (supply-chain guard)", True)
applied = kb_update.activate(str(kb_file), url=False, sha256=kb_sha)
check("kb: activate with the exact sha applies", applied["status"] == "applied")
check("kb: override now in force", cve_kb.kb_source() == "override")
check("kb: load_kb returns the override", cve_kb.load_kb()["generated"] == new_kb["generated"])
w3 = cve_watch.collect(FIX_A)
check("watch: drift names the added entry after an override",
      w3["drift"]["status"] == "changed"
      and "test-new-advisory-2026" in w3["drift"]["added"],
      json.dumps(w3["drift"])[:200])
rev = kb_update.revert()
check("kb: revert restores the packaged KB", rev["status"] == "reverted"
      and cve_kb.kb_source() == "packaged")
# corrupt override: the tools fall back to the packaged KB instead of crashing
cve_kb._override_path().write_text("{not json", encoding="utf-8")
check("kb: corrupt override falls back to packaged", cve_kb.kb_source() == "packaged")
cve_kb._override_path().unlink()

# updater CLI end to end
rc = kb_update.main(["--file", str(kb_file), "--json"])
check("kb cli: stage rc=0", rc == 0)
rc = kb_update.main(["--file", str(kb_file), "--confirm",
                     "--sha256", "deadbeef"])
check("kb cli: wrong sha rc=2", rc == 2)
rc = kb_update.main(["--file", str(kb_file), "--confirm", "--sha256", kb_sha, "--json"])
check("kb cli: confirm rc=0", rc == 0)
rc = kb_update.main(["--revert", "--json"])
check("kb cli: revert rc=0", rc == 0)

# --- fw.update.stage: T2, human-only ----------------------------------------
GUID_NVME = "b2a1c3d4-0000-4000-8000-000000000001"
GUID_BOARD = "b2a1c3d4-0000-4000-8000-000000000003"

plan_nvme = stage.plan(GUID_NVME, fixture_dir=str(FIX_A))
check("stage: NVMe plan dry-run",
      plan_nvme["status"] == "dry-run" and plan_nvme["tier"] == "T2",
      json.dumps(plan_nvme["gates"])[:250])
check("stage: NVMe plan passes all hard gates",
      all(g["result"] in ("pass", "pending") for g in plan_nvme["gates"]),
      json.dumps(plan_nvme["gates"])[:250])
check("stage: command sheet is exact",
      plan_nvme["command"] == ["fwupdmgr", "install", GUID_NVME]
      or plan_nvme["command"][0] == "fwupdmgr", str(plan_nvme["command"]))
check("stage: plan states the rollback reality",
      "FlashBack" in plan_nvme["rollback_reality"])

plan_board = stage.plan(GUID_BOARD, fixture_dir=str(FIX_A))
check("stage: motherboard refused (AM4 LVFS gap, T3 path named)",
      plan_board["status"] == "refused"
      and "EZ Flash" in json.dumps(plan_board["gates"]),
      json.dumps(plan_board["gates"])[:250])
plan_unknown = stage.plan("00000000-0000-4000-8000-0000000000ff",
                          fixture_dir=str(FIX_A))
check("stage: unknown GUID refused (exact match only)",
      plan_unknown["status"] == "refused")

plan_no_reason = stage.apply(GUID_NVME, reason=None, fixture_dir=str(FIX_A))
check("stage: apply without a reason refused (bad-action barrage)",
      plan_no_reason["status"] == "refused" and "motivation" in json.dumps(plan_no_reason))

# fake fwupdmgr: the staged path without touching any real tool
fake_bin = kb_tmp / "fake-fwupdmgr"
fake_bin.write_text(
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "if len(sys.argv) >= 3 and sys.argv[1] == 'install':\n"
    "    print('Staged update for', sys.argv[2]); sys.exit(0)\n"
    "print('unexpected call', sys.argv); sys.exit(9)\n")
fake_bin.chmod(0o755)
os.environ["FW_FWUPD_BIN"] = str(fake_bin)
# the confirm path is exercised through the CLI — the human gesture
rc = cli.main(["update", "stage", "--device", GUID_NVME,
               "--reason", "vendor security fix (test)", "--confirm",
               "--fixture-dir", str(FIX_A), "--json"])
check("stage: CLI confirm with reason + fake fwupdmgr rc=0", rc == 0)
txj = json.loads((stage._transaction_path()).read_text(encoding="utf-8"))
check("stage: transaction recorded with the reason",
      txj.get("reason") == "vendor security fix (test)"
      and txj.get("status") == "staged")
check("stage: transaction states the tool never reboots",
      "NEVER reboots" in txj.get("note", ""))
check("stage: staged call journaled by the CLI boundary",
      journal.show(1)[0]["tool"] == "fw.update.stage"
      and journal.show(1)[0]["status"] == "staged", str(journal.show(1)))
# failing fwupdmgr: honest error, nothing staged (direct call, no journal check)
bad_bin = kb_tmp / "bad-fwupdmgr"
bad_bin.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(3)\n")
bad_bin.chmod(0o755)
os.environ["FW_FWUPD_BIN"] = str(bad_bin)
tx = stage._transaction_path()
tx.unlink() if tx.exists() else None
st_bad = stage.apply(GUID_NVME, reason="test", fixture_dir=str(FIX_A))
check("stage: fwupd failure -> status error, nothing staged",
      st_bad["status"] == "error", json.dumps(st_bad)[:200])
os.environ["FW_FWUPD_BIN"] = str(fake_bin)
rc = cli.main(["update", "stage", "--device", GUID_NVME,
               "--reason", "re-stage for cancel test", "--confirm",
               "--fixture-dir", str(FIX_A), "--json"])
check("stage: re-stage via CLI works after an error", rc == 0)
rc = cli.main(["update", "stage", "--cancel", "--json"])
check("stage: CLI cancel rc=0 and journaled cancelled",
      rc == 0 and journal.show(1)[0]["status"] == "cancelled",
      str(journal.show(1)))
rc = cli.main(["update", "stage", "--cancel", "--json"])
check("stage: second CLI cancel rc=2 (refused honestly)",
      rc == 2 and journal.show(1)[0]["status"] == "refused")
del os.environ["FW_FWUPD_BIN"]

# MCP refuses T2 with the pointer to the human path
try:
    _mcp_server._run_tool("fw.update.stage")
    check("mcp: fw.update.stage refused (T2 human-only)", False)
except tiers.TierRefused as exc:
    check("mcp: fw.update.stage refused (T2 human-only)",
          "update stage --device" in str(exc), str(exc)[:150])

# stage CLI end to end
rc = cli.main(["update", "stage", "--device", GUID_NVME,
               "--fixture-dir", str(FIX_A), "--json"])
check("cli: update stage plan rc=0 (dry-run journaled)", rc == 0)
rc = cli.main(["update", "stage", "--json"])
check("cli: update stage without --device rc=2", rc == 2)

# --- fw.rollback: the refusal-by-design with the inventory -------------------
inv = rollback.inventory(FIX_A)
check("rollback: refused by design",
      inv["status"] == "refused-by-design" and inv["tier"] == "T2")
check("rollback: T1 store visible",
      set(inv["t1_rollback_store"]) == {"epp", "fans"},
      json.dumps(inv["t1_rollback_store"]))
check("rollback: fwupd history parsed (2 past events)",
      inv["fwupd_history"]["available"] and len(inv["fwupd_history"]["events"]) == 2,
      json.dumps(inv["fwupd_history"])[:200])
check("rollback: machine truth names FlashBack as the human path",
      any("FlashBack" in m for m in inv["machine_truth"]))
rc = cli.main(["update", "rollback", "--fixture-dir", str(FIX_A), "--json"])
check("cli: update rollback rc=0 (an answer, not an error)", rc == 0)
check("cli: rollback journaled refused-by-design",
      journal.show(1)[0]["tool"] == "fw.rollback"
      and journal.show(1)[0]["status"] == "refused-by-design")

# --- report: the supervised-loop digest --------------------------------------
n_before = len(journal.show(10 ** 6))
rep = report.collect(days=5)
n_after = len(journal.show(10 ** 6))
check("report: view only — does not journal itself", n_before == n_after)
check("report: totals include the statuses written so far",
      rep["totals_by_status"].get("ok", 0) >= 1
      and rep["totals_by_status"].get("staged", 0) >= 1,
      json.dumps(rep["totals_by_status"]))
check("report: today is in the window",
      time.strftime("%Y-%m-%d") in rep["days"], str(sorted(rep["days"])))
check("report: verdict mentions refused-by-design count",
      "refused" in rep["verdict"], rep["verdict"])
rc = cli.main(["report", "--json"])
check("cli: report rc=0", rc == 0)

# cve-watch CLI end to end (journaled like every T0 read)
rc = cli.main(["audit", "cve-watch", "--fixture-dir", str(FIX_A), "--json"])
check("cli: audit cve-watch rc=0", rc == 0)
check("cli: cve-watch journaled", journal.show(1)[0]["tool"] == "fw.cve.watch")


# -------------------------------------------------------------------- P5 ---
# Phase 5 — the digital twin (TWIN-1) and the dress rehearsal: the whole
# behavioural contract executable in one command, long before the machine.
from firmware_hal import rehearse, twin  # noqa: E402

# --- twin: the profile and its resolution ------------------------------------
prof = twin.PROFILE
check("twin: the profile names the reference machine",
      prof["name"] == "TWIN-1" and "B450-PLUS" in prof["board"]
      and "5950X" in prof["cpu"] and "3070" in prof["gpu"])
fx_twin = twin.resolve_fixture_dir("b450-plus")
check("twin: fixture set resolves to a real board directory",
      bool(fx_twin) and (Path(fx_twin) / "dmidecode.txt").exists())
scen = twin.resolve_scenario_dir()
check("twin: 12 bundled scenarios resolve",
      scen is not None and len(list(scen.glob("*.json"))) == 12)

sysfs_saved = {k: os.environ.get(k) for k in ("FW_SYSFS_CPU", "FW_SYSFS_HWMON")}
for k in sysfs_saved:
    os.environ.pop(k, None)
applied = twin.apply_sysfs_env()
check("twin: sysfs env applied (cpu + hwmon)",
      "FW_SYSFS_CPU" in applied and "FW_SYSFS_HWMON" in applied,
      str(applied))
check("twin: epp backing file is a real preferences tree",
      (Path(applied["FW_SYSFS_CPU"]) / "cpu0" / "cpufreq"
       / "energy_performance_available_preferences").exists())
override = tempfile.mkdtemp(prefix="ofw-twin-")
(Path(override) / "b450-plus").mkdir()
os.environ["FW_TWIN_DIR"] = override
check("twin: FW_TWIN_DIR override wins",
      twin.resolve_fixture_dir("b450-plus")
      == str(Path(override) / "b450-plus"))
os.environ.pop("FW_TWIN_DIR", None)

# --- rehearse: the whole contract, green on TWIN-1 ----------------------------
rep = rehearse.run_rehearsal("twin", write_report=True)
check("rehearse: green on TWIN-1", rep["verdict"] == "green",
      rehearse.render(rep)[:500])
check("rehearse: the probe surface is locked at 28",
      len(rep["probes"]) == 28, str(len(rep["probes"])))
check("rehearse: all probes pass, none skipped on the twin",
      rep["counts"] == {"pass": 28, "fail": 0, "skip": 0},
      json.dumps(rep["counts"]))
check("rehearse: probe ids unique (diff-stable report)",
      len({p["id"] for p in rep["probes"]}) == len(rep["probes"]))
check("rehearse: report written and schema-tagged",
      bool(rep.get("report_file")) and Path(rep["report_file"]).exists()
      and rep["schema"] == "omarchy-firmware/rehearsal@1")
check("rehearse: journaled as rehearse",
      journal.show(1)[0]["tool"] == "rehearse"
      and journal.show(1)[0]["status"] == "ok")

# --- rehearse: the no-write guarantee, enforced by construction ----------------
twin_ctx = {"fixture": twin.resolve_fixture_dir(), "sysfs_epp": None,
            "curve": Path(tempfile.gettempdir()) / "ofw-curve.json",
            "mcp_env": {}, "is_twin": True}
probes_t = rehearse.build_probes("twin", twin_ctx)
confirm_ids = [q["id"] for q in probes_t
               if any(a == "--confirm" for a in q["argv"])]
check("rehearse: the human-confirm flag appears ONLY where refusal is "
      "the expected outcome",
      confirm_ids == ["stage-confirm-refused"], str(confirm_ids))
gate_ids = {"t1-epp-gate", "t1-epp-undo-gate", "t1-fans-gate"}
check("rehearse: every write-gesture probe asserts 'never applied'",
      all("never applied" in q["expected"]
          for q in probes_t if q["id"] in gate_ids) and len(gate_ids) == 3)

real_probes = rehearse.build_probes("real", dict(twin_ctx, is_twin=False))
twin_only_ids = {q["id"] for q in real_probes if q.get("twin_only")}
check("rehearse: twin-only probes marked for honest skip on real",
      twin_only_ids == {"stage-plan-nvme", "stage-board-refused",
                        "stage-confirm-refused", "t1-epp-dryrun-plan"},
      str(sorted(twin_only_ids)))
check("rehearse: scenario probes stay deterministic on the real machine",
      all(not q.get("twin_only") for q in real_probes
          if q["id"] in {"diag-pump-dead", "diag-no-paste", "diag-heatwave",
                         "diag-undetermined"}))

# restore the T1 sysfs environment for any later section
for k, v in sysfs_saved.items():
    if v is not None:
        os.environ[k] = v


# -------------------------------------------------------------- output --
fails = [t for t in _tests if not t[1]]
verbose = "-v" in sys.argv
for name, ok, detail in _tests:
    if verbose or not ok:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
print(f"\n{_tests.__len__() - len(fails)}/{len(_tests)} tests PASS"
      + (f" — {len(fails)} FAILURE(S)" if fails else " — the T0 base complies with the contract."))
sys.exit(1 if fails else 0)
