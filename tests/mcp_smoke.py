#!/usr/bin/env python3
"""MCP conformance smoke test — initialize + tools/list + real tool calls.

    python3 tests/mcp_smoke.py          # requires the optional 'mcp' package

Proves, over a real stdio session against bin/omarchy-firmware-mcp:
  - the initialize/2024-11-05 handshake answers;
  - tools/list exposes exactly the 12 contract tools (10 T0 + 2 T1);
  - tools/call fw.diag.thermal names the fixture fault;
  - tools/call fw.audit.cve returns findings;
  - tools/call fw.cve.watch reports KB freshness and the fwupd cross-check;
  - tools/call cpu.epp.set without confirm is a DRY-RUN (nothing written).

Exit code 0 = conformance proved; 1 = any deviation; 77 = mcp missing.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

try:
    import mcp  # noqa: F401
except ImportError:
    print("mcp package not installed — smoke skipped (77). "
          "pip install mcp to run it.")
    sys.exit(77)

os.environ["XDG_STATE_HOME"] = tempfile.mkdtemp()  # isolated journal
os.environ["FW_FIXTURE_DIR"] = str(ROOT / "tests" / "fixtures" / "b450-plus")
os.environ["FW_DIAG_SCENARIO"] = "no-paste"  # thermal demo without hardware

# Hermetic T1 environment: a tiny fake sysfs tree, so the epp call is a
# deterministic dry-run regardless of the host (CI runners have no EPP).
TMP = Path(tempfile.mkdtemp())
CPU = TMP / "cpu"
for n in (0, 1):
    d = CPU / f"cpu{n}" / "cpufreq"
    d.mkdir(parents=True)
    (d / "energy_performance_available_preferences").write_text(
        "default performance balance_performance balance_power power\n")
    (d / "energy_performance_preference").write_text("balance_performance\n")
os.environ["FW_SYSFS_CPU"] = str(CPU)

EXPECTED = {"fw.audit.status", "fw.audit.cve", "fw.boot.inspect",
            "fw.update.check", "fw.cve.watch", "fw.diag.thermal",
            "fw.diag.storage", "fw.diag.gpu", "fw.diag.ram",
            "fw.diag.settings", "cpu.epp.set", "fans.curve.set"}

init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "mcp-smoke", "version": "0.3"}}}
ready = {"jsonrpc": "2.0", "method": "notifications/initialized"}
list_tools = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
call_thermal = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "fw.diag.thermal", "arguments": {}}}
call_cve = {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "fw.audit.cve", "arguments": {}}}
call_watch = {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
              "params": {"name": "fw.cve.watch", "arguments": {}}}
call_epp = {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "cpu.epp.set",
                       "arguments": {"value": "performance"}}}

proc = subprocess.Popen(
    [sys.executable, str(ROOT / "bin" / "omarchy-firmware-mcp")],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
)


def ask(obj):
    """Send one message and read one reply (JSON-RPC responses end with \n)."""
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line) if line.strip() else None


def notify(obj):
    """Send a notification — by design, no reply is ever sent back."""
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


failures = []


def expect(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}"
          + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


try:
    r = ask(init)
    expect("initialize 2024-11-05 answered",
           r and r.get("result", {}).get("protocolVersion") == "2024-11-05", str(r)[:160])
    notify(ready)  # notification: no reply — never read after it

    r = ask(list_tools)
    names = {t["name"] for t in r["result"]["tools"]}
    expect("tools/list = the 12 contract tools", names == EXPECTED,
           f"got {sorted(names)}")
    expect("12 tools listed", len(r["result"]["tools"]) == 12)

    r = ask(call_thermal)
    payload = json.loads(r["result"]["content"][0]["text"])
    expect("fw.diag.thermal names the fixture fault",
           payload["verdict"] == "critical"
           and any(f["id"] == "interface-degraded" for f in payload["findings"]),
           json.dumps(payload)[:200])
    expect("thermal call journaled",
           payload.get("journal_entry", {}).get("tool") == "fw.diag.thermal")

    r = ask(call_cve)
    payload = json.loads(r["result"]["content"][0]["text"])
    expect("fw.audit.cve returns findings",
           len(payload.get("findings", [])) == 5, json.dumps(payload)[:200])

    r = ask(call_watch)
    payload = json.loads(r["result"]["content"][0]["text"])
    expect("fw.cve.watch reports KB freshness",
           payload.get("kb", {}).get("entry_count") == 5
           and payload["kb"].get("sha256"), json.dumps(payload)[:200])
    expect("fw.cve.watch records the baseline",
           payload.get("drift", {}).get("status") == "baseline-recorded")
    expect("fw.cve.watch journaled",
           payload.get("journal_entry", {}).get("tool") == "fw.cve.watch")

    r = ask(call_epp)
    payload = json.loads(r["result"]["content"][0]["text"])
    expect("cpu.epp.set without confirm = dry-run",
           payload.get("status") == "dry-run", json.dumps(payload)[:300])
    expect("epp dry-run journaled as dry-run",
           payload.get("journal_entry", {}).get("status") == "dry-run")
    epp_file = CPU / "cpu0" / "cpufreq" / "energy_performance_preference"
    expect("epp dry-run wrote nothing",
           epp_file.read_text().strip() == "balance_performance")
finally:
    proc.terminate()

print()
if failures:
    print(f"MCP CONFORMANCE FAILED: {len(failures)} check(s): {failures}")
    sys.exit(1)
print("MCP CONFORMANCE OK — 12 tools, journaled, T1 dry-run by default.")
