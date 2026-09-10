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

from firmware_hal import audit, boot, boot as bootmod, cli, cve_kb, diagnostics, fwupd, journal, sensors, smbios, tiers  # noqa: E402

FIX_A = ROOT / "tests" / "fixtures" / "b450-plus"
FIX_B = ROOT / "tests" / "fixtures" / "b550-f-old"

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
    tiers.assert_phase1("cpu.epp.set")
    check("tiers: T1 refused", False, "cpu.epp.set should have been refused")
except tiers.TierRefused:
    check("tiers: T1 refused", True)
try:
    tiers.assert_phase1("fw.flash.write")
    check("tiers: unknown T3 refused", False)
except tiers.TierRefused:
    check("tiers: unknown T3 refused", True)
check("tiers: contract = 9 tools", len(tiers.TOOL_TIERS) == 9)
check("tiers: 5 T0 implemented", len(tiers.IMPLEMENTED_T0) == 5)
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
check("audit: P2 read-only phase", "read-only" in (a.get("phase") or ""))

# ------------------------------------------------------------------ diag ---
# The physical diagnostics (vol. 3): every scenario must name THE fault,
# not a catch-all list. The scenarios are the pre-recorded physics.
SCEN = diagnostics.SCENARIO_DIR

sc_all = {p.stem for p in SCEN.glob("*.json")}
check("diag: 8 bundled scenarios", len(sc_all) == 8, str(sorted(sc_all)))


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

# MCP server: the fifth tool is declared T0
from firmware_hal import mcp_server  # noqa: E402
specs = {s["name"]: s["risk_tier"] for s in mcp_server._tool_specs()}
check("mcp: 5 tools declared", len(specs) == 5, str(specs))
check("mcp: fw.diag.thermal T0", specs.get("fw.diag.thermal") == "T0")

# -------------------------------------------------------------- output --
fails = [t for t in _tests if not t[1]]
verbose = "-v" in sys.argv
for name, ok, detail in _tests:
    if verbose or not ok:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not ok else ""))
print(f"\n{_tests.__len__() - len(fails)}/{len(_tests)} tests PASS"
      + (f" — {len(fails)} FAILURE(S)" if fails else " — the T0 base complies with the contract."))
sys.exit(1 if fails else 0)
