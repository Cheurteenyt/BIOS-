"""The dress rehearsal — the whole behavioural contract in one command.

Sept. 16 must be a replay day, not a discovery day. `rehearse` walks the
full surface a first session will touch — the 14-tool contract, every T0
collection, the T1 two-key gestures, the human-only T2 gates, the
12-signature diagnostic surface, the MCP handshake, the journal — and
checks each expected behaviour against whatever backend it runs on:

  --backend real (default)  the machine in front of you (day-0 drill)
  --backend twin            TWIN-1, the bundled rehearsal machine

Backend rule: structural expectations (exit codes, refusals, dry-run
plans, JSON shapes) hold on BOTH backends; content expectations (the
B450-PLUS board name, the named faults) apply to the twin only — on real
hardware the twin-only probes are reported as `skip`, honestly. The four
scenario probes are NOT twin-only: scenario mode is deterministic, so
they must also pass on the real machine.

The no-write guarantee: no probe ever performs a write gesture. The only
appearance of the human-confirm flag is in `stage-confirm-refused`, whose
expected outcome IS the refusal (exit 2) — a property the test suite
enforces by scanning build_probes().
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from . import journal, twin

NVME_GUID = "b2a1c3d4-0000-4000-8000-000000000001"
BOARD_GUID = "b2a1c3d4-0000-4000-8000-000000000003"

TOOL_TIERS = [
    "fw.audit.status", "fw.audit.cve", "fw.boot.inspect", "fw.update.check",
    "fw.cve.watch", "fw.diag.thermal", "fw.diag.storage", "fw.diag.gpu",
    "fw.diag.ram", "fw.diag.settings", "cpu.epp.set", "fans.curve.set",
    "fw.update.stage", "fw.rollback",
]

MCP_TOOLS = set(TOOL_TIERS[:12])

CURVE = {"hwmon": "nct6798", "pwm": 1, "points": [
    {"temp": 40, "pwm": 90}, {"temp": 60, "pwm": 140}, {"temp": 85, "pwm": 255}]}

# ----------------------------------------------------------------- plumbing


def _cli_bin() -> Path | None:
    env = os.environ.get("FW_CLI_BIN")
    if env and Path(env).is_file():
        return Path(env)
    here = Path(__file__).resolve().parents[2]
    for cand in (here / "bin" / "omarchy-firmware",
                 Path.home() / ".local" / "bin" / "omarchy-firmware"):
        if cand.is_file():
            return cand
    which = shutil.which("omarchy-firmware")
    return Path(which) if which else None


def _mcp_bin() -> Path | None:
    env = os.environ.get("FW_MCP_BIN")
    if env and Path(env).is_file():
        return Path(env)
    here = Path(__file__).resolve().parents[2]
    for cand in (here / "bin" / "omarchy-firmware-mcp",
                 Path.home() / ".local" / "bin" / "omarchy-firmware-mcp"):
        if cand.is_file():
            return cand
    which = shutil.which("omarchy-firmware-mcp")
    return Path(which) if which else None


def _payload(proc: subprocess.CompletedProcess) -> dict:
    data = None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return {"rc": proc.returncode, "out": proc.stdout, "err": proc.stderr,
            "json": data}


def _run_cli(cli: Path, argv: list[str], timeout: int = 60) -> dict:
    proc = subprocess.run(
        [sys.executable, str(cli), *argv],
        capture_output=True, text=True, timeout=timeout, check=False)
    return _payload(proc)


def _mcp_exchange(mcp: Path, env: dict) -> dict:
    """initialize -> tools/list -> one T0 call, over a real stdio session.

    Sequential request/reply (the pattern proven by tests/mcp_smoke.py):
    writing every request upfront races the server's session setup and the
    last call is silently dropped. A watchdog kills a hung server instead
    of blocking the rehearsal forever.
    """
    proc = subprocess.Popen(
        [sys.executable, str(mcp)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        bufsize=1, env=env)
    got: dict[int, dict] = {}
    err_ref = [""]

    def ask(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line) if line.strip() else None

    def session():
        try:
            r = ask({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "rehearsal",
                                               "version": "1.0"}}})
            if r and isinstance(r.get("id"), int):
                got[r["id"]] = r
            proc.stdin.write(json.dumps(
                {"jsonrpc": "2.0", "method": "notifications/initialized"})
                + "\n")
            proc.stdin.flush()
            r = ask({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            if r:
                got[2] = r
            r = ask({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                     "params": {"name": "fw.audit.status",
                                "arguments": {}}})
            if r:
                got[3] = r
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            err_ref[0] = str(exc)[:120]
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    worker = threading.Thread(target=session, daemon=True)
    worker.start()
    worker.join(timeout=90)
    if worker.is_alive():
        proc.kill()
        err_ref[0] = "MCP session hung past 90 s — killed"
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
    if not got and not err_ref[0]:
        # the server died before answering anything — surface its reason
        try:
            tail = (proc.stderr.read() or "").strip().splitlines()
            err_ref[0] = f"server rc={proc.returncode}: {tail[-1][:120]}" \
                if tail else f"server rc={proc.returncode}, no output"
        except (OSError, ValueError):
            err_ref[0] = f"server rc={proc.returncode}"
    return {"rc": proc.returncode or 0, "responses": got,
            "err": err_ref[0] or "", "out": ""}


# ------------------------------------------------------------------ checks
# Every check is a named function: (payload, ctx) -> (ok, observed).
# Explicit returns — no nested-paren lambda arithmetic.

def _ck_tiers(pv, c):
    missing = [t for t in TOOL_TIERS if t not in pv["out"]]
    ok = pv["rc"] == 0 and not missing and "T2" in pv["out"]
    detail = f"rc={pv['rc']}" + (f" missing={missing}" if missing else "")
    return ok, detail


def _ck_audit_status(pv, c):
    j = pv["json"] or {}
    board = (j.get("board") or {}).get("board_product", "")
    ok = (pv["rc"] == 0 and bool(j) and bool(board)
          and "journal_entry" in j
          and (not c["is_twin"] or "B450-PLUS" in board))
    return ok, f"rc={pv['rc']} board={board}"


def _ck_audit_cve(pv, c):
    n = len((pv["json"] or {}).get("findings", []))
    return pv["rc"] == 0 and n >= 1, f"rc={pv['rc']} findings={n}"


def _ck_cve_watch(pv, c):
    j = pv["json"] or {}
    keys = sorted(j.keys())[:6]
    ok = pv["rc"] == 0 and "kb" in j and "drift" in j \
        and "fwupd_cross_check" in j
    return ok, f"rc={pv['rc']} keys={keys}"


def _ck_boot(pv, c):
    j = pv["json"] or {}
    chain = str(j.get("chain", ""))
    ok = pv["rc"] == 0 and bool(j) \
        and (not c["is_twin"] or "Limine" in chain)
    return ok, f"rc={pv['rc']} chain={chain[:60]}"


def _ck_update_check(pv, c):
    ups = (pv["json"] or {}).get("updates")
    ok = pv["rc"] == 0 and isinstance(ups, list)
    return ok, f"rc={pv['rc']} updates={len(ups) if isinstance(ups, list) else '?'}"


def _ck_stage_plan(pv, c):
    j = pv["json"] or {}
    gates = len(j.get("gates", []))
    ok = (pv["rc"] == 0 and j.get("status") == "dry-run"
          and gates == 6
          and j.get("command") == ["fwupdmgr", "install", NVME_GUID])
    return ok, f"rc={pv['rc']} status={j.get('status')} gates={gates}"


def _ck_stage_board(pv, c):
    j = pv["json"] or {}
    ok = (pv["rc"] == 2 and j.get("status") == "refused"
          and "EZ Flash" in json.dumps(j))
    return ok, f"rc={pv['rc']} note={str(j.get('note', ''))[:80]}"


def _ck_stage_confirm_refused(pv, c):
    j = pv["json"] or {}
    ok = (pv["rc"] == 2
          and ("REFUSED" in (pv["err"] + pv["out"])
               or j.get("status") == "refused"))
    detail = f"rc={pv['rc']} err={pv['err'].strip()[:80]} status={j.get('status')}"
    return ok, detail


def _ck_rollback(pv, c):
    j = pv["json"] or {}
    return (pv["rc"] == 0 and j.get("status") == "refused-by-design",
            f"rc={pv['rc']} status={j.get('status')}")


def _ck_diag_scenarios(pv, c):
    first = pv["out"].splitlines()[0] if pv["out"].strip() else ""
    ok = pv["rc"] == 0 and bool(first) \
        and (not c["is_twin"] or "12" in first)
    return ok, f"rc={pv['rc']} out={first[:60]}"


def _finding_ids(pv):
    return [f.get("id") for f in (pv["json"] or {}).get("findings", [])]


def _ck_pump_dead(pv, c):
    j = pv["json"] or {}
    ids = _finding_ids(pv)
    ok = (pv["rc"] == 0 and j.get("verdict") == "critical"
          and ids[:1] == ["pump-dead"] and "interface-degraded" not in ids)
    return ok, f"rc={pv['rc']} verdict={j.get('verdict')} ids={ids}"


def _ck_no_paste(pv, c):
    ids = _finding_ids(pv)
    return (pv["rc"] == 0 and "interface-degraded" in ids,
            f"rc={pv['rc']} ids={ids}")


def _ck_heatwave(pv, c):
    ids = _finding_ids(pv)
    ok = (pv["rc"] == 0 and "thermal-protection-active" in ids
          and "coolant-hot" in ids)
    return ok, f"rc={pv['rc']} ids={ids}"


def _ck_undetermined(pv, c):
    j = pv["json"] or {}
    conf = (j.get("measurements") or {}).get("confidence")
    ok = (pv["rc"] == 0 and j.get("verdict") == "undetermined"
          and conf == "low")
    return ok, f"rc={pv['rc']} verdict={j.get('verdict')} confidence={conf}"


def _ck_diag_generic(pv, c):
    j = pv["json"] or {}
    return (pv["rc"] == 0 and "verdict" in j,
            f"rc={pv['rc']} verdict={j.get('verdict')}")


def _ck_diag_live(pv, c):
    j = pv["json"] or {}
    ok = pv["rc"] == 0 and bool(j) \
        and (not c["is_twin"] or j.get("verdict") == "undetermined")
    return ok, f"rc={pv['rc']} verdict={j.get('verdict')}"


def _ck_gate(pv, c):
    """The safety invariant: without the human gesture, nothing is written."""
    j = pv["json"] or {}
    refused = pv["rc"] == 2 and "REFUSED" in (pv["err"] + pv["out"])
    dryrun = pv["rc"] == 0 and j.get("status") == "dry-run"
    if refused:
        return True, "refused, exit 2 (gate held)"
    if dryrun:
        return True, "dry-run, nothing written"
    return False, f"UNSAFE: rc={pv['rc']} status={j.get('status')!r}"


def _ck_epp_plan(pv, c):
    j = pv["json"] or {}
    diff = len(j.get("diff", {}))
    backing = c["sysfs_epp"]
    untouched = backing is not None \
        and backing.read_text().strip() == "balance_performance"
    ok = (pv["rc"] == 0 and j.get("status") == "dry-run"
          and diff == 2 and untouched)
    return ok, f"rc={pv['rc']} status={j.get('status')} diff={diff} " \
               f"backing_untouched={untouched}"


def _ck_fans_gate(pv, c):
    gate_ok, gate_detail = _ck_gate(pv, c)
    if not c["is_twin"]:
        return gate_ok, gate_detail
    plan = len((pv["json"] or {}).get("plan_writes", []))
    ok = gate_ok and pv["rc"] == 0 and plan >= 5
    return ok, f"{gate_detail} plan_writes={plan}"


def _ck_fans_show(pv, c):
    j = pv["json"] or {}
    chips = j.get("chips") or []
    ok = pv["rc"] == 0 and bool(chips) \
        and (not c["is_twin"] or chips[0].get("name") == "nct6798")
    return ok, f"rc={pv['rc']} chips={str(chips)[:80]}"


def _ck_mcp(pv, c):
    if pv["rc"] != 0 and not pv["responses"]:
        return False, (f"server did not answer (rc={pv['rc']}) "
                       f"{pv['err'][:80]}")
    tools = (pv["responses"].get(2, {}).get("result") or {}).get("tools", [])
    listed = {t.get("name") for t in tools}
    ok_list = listed == MCP_TOOLS
    call3 = pv["responses"].get(3, {})
    call_ok = not c["is_twin"] or ("error" not in call3
                                   and bool(call3.get("result")))
    detail = (f"tools/list={len(listed)} (expected 12) "
              f"call3={'ok' if call_ok else 'missing'}")
    return ok_list and call_ok, detail


def _ck_journal(pv, c):
    entries = pv["json"] if isinstance(pv["json"], list) else []
    ok = (pv["rc"] == 0 and bool(entries)
          and all(e.get("ts") and e.get("tool") and e.get("status")
                  for e in entries))
    return ok, f"rc={pv['rc']} entries={len(entries)}"


def _ck_report(pv, c):
    j = pv["json"] or {}
    return (pv["rc"] == 0 and "verdict" in j and "days" in j,
            f"rc={pv['rc']} verdict={j.get('verdict')}")


# ------------------------------------------------------------------ probes


def build_probes(backend: str, ctx: dict) -> list[dict]:
    """The probe list — pure builder (no execution), scan-friendly.

    ctx keys: fixture (str|None), sysfs_epp (Path|None), curve (Path|None),
    mcp_env (dict), is_twin (bool).
    """
    fx = ["--fixture-dir", ctx["fixture"]] if ctx["fixture"] else []

    def p(pid, title, expected, argv, check, twin_only=False):
        return {"id": pid, "title": title, "expected": expected,
                "argv": argv, "check": check, "twin_only": twin_only}

    return [
        p("contract-tiers", "the 14-tool contract displays",
          "rc 0, all 14 tool names, T2 declared",
          ["tiers"], _ck_tiers),

        p("audit-status", "full inventory answers",
          "rc 0, board named, call journaled",
          ["audit", "status", "--json", *fx], _ck_audit_status),

        p("audit-cve", "version/CVE cross-check answers",
          "rc 0, at least one reasoned finding",
          ["audit", "cve", "--json", *fx], _ck_audit_cve),

        p("audit-cve-watch", "KB freshness + fwupd cross-check",
          "rc 0, kb + drift + fwupd_cross_check sections",
          ["audit", "cve-watch", "--json", *fx], _ck_cve_watch),

        p("boot-inspect", "boot chain answers",
          "rc 0, chain identified",
          ["boot", "inspect", "--json", *fx], _ck_boot),

        p("update-check", "fwupd local state answers",
          "rc 0, updates list present",
          ["update", "check", "--json", *fx], _ck_update_check),

        p("stage-plan-nvme", "T2 dry-run plan on the twin NVMe",
          "rc 0, status dry-run, six gates, exact command",
          ["update", "stage", "--device", NVME_GUID,
           "--reason", "rehearsal: day-0 drill", "--json", *fx],
          _ck_stage_plan, twin_only=True),

        p("stage-board-refused", "the board is NOT stageable (AM4 gap)",
          "rc 2, refused, EZ Flash path named",
          ["update", "stage", "--device", BOARD_GUID,
           "--reason", "rehearsal: the gap must stay honest", "--json", *fx],
          _ck_stage_board, twin_only=True),

        p("stage-confirm-refused", "the human gesture without a stated why",
          "rc 2, REFUSED — motivation gate cannot be waived",
          ["update", "stage", "--device", NVME_GUID,
           "--confirm", "--json", *fx],
          _ck_stage_confirm_refused, twin_only=True),

        p("rollback-inventory", "rollback stays a refusal-by-design",
          "rc 0, refused-by-design with the honest inventory",
          ["update", "rollback", "--json", *fx], _ck_rollback),

        p("diag-scenarios", "the bundled signature surface lists",
          "rc 0, scenarios available",
          ["diag", "scenarios"], _ck_diag_scenarios),

        p("diag-pump-dead", "S1: the dead pump is named, nothing invented",
          "rc 0, critical, finding #1 pump-dead, no invented paste",
          ["diag", "quick", "--scenario", "pump-dead",
           "--no-record", "--json"], _ck_pump_dead),

        p("diag-no-paste", "S3: the degraded interface is named",
          "rc 0, interface-degraded in the findings",
          ["diag", "quick", "--scenario", "no-paste",
           "--no-record", "--json"], _ck_no_paste),

        p("diag-heatwave", "S8: fold-back with a healthy interface",
          "rc 0, protection named, coolant saturation named",
          ["diag", "quick", "--scenario", "heatwave",
           "--no-record", "--json"], _ck_heatwave),

        p("diag-undetermined", "the owned 'I cannot name it' verdict",
          "rc 0, verdict undetermined, low confidence",
          ["diag", "quick", "--scenario", "undetermined",
           "--no-record", "--json"], _ck_undetermined),

        p("diag-storage", "SMART + PCIe links answer",
          "rc 0, verdict produced",
          ["diag", "storage", "--json", *fx], _ck_diag_generic),

        p("diag-gpu", "Xid history + clocks answer",
          "rc 0, verdict produced",
          ["diag", "gpu", "--json", *fx], _ck_diag_generic),

        p("diag-ram", "rated vs configured + EDAC answer",
          "rc 0, verdict produced",
          ["diag", "ram", "--json", *fx], _ck_diag_generic),

        p("diag-settings", "observable BIOS settings answer",
          "rc 0, verdict produced",
          ["diag", "settings", "--json", *fx], _ck_diag_generic),

        p("diag-live", "passive diagnostics without any scenario",
          "rc 0, honest undetermined verdict on sensorless hosts",
          ["diag", "quick", "--no-record", "--json"], _ck_diag_live),

        p("t1-epp-gate", "EPP write without the human gesture",
          "refused (rc 2) or dry-run (rc 0) — never applied",
          ["cpu", "epp", "set", "performance", "--json"], _ck_gate),

        p("t1-epp-dryrun-plan", "the dry-run plan carries the full diff",
          "rc 0, dry-run, diff of 2 cpus, backing file untouched",
          ["cpu", "epp", "set", "performance", "--json"],
          _ck_epp_plan, twin_only=True),

        p("t1-epp-undo-gate", "EPP undo without the human gesture",
          "refused (rc 2) or dry-run (rc 0) — never applied",
          ["cpu", "epp", "undo", "--json"], _ck_gate),

        p("t1-fans-gate", "fan curve write without the human gesture",
          "refused (rc 2) or dry-run (rc 0) — never applied",
          ["fans", "curve", "set", "--file", str(ctx["curve"]), "--json"],
          _ck_fans_gate),

        p("t1-fans-show", "fan curve read answers",
          "rc 0, chips listed",
          ["fans", "curve", "show", "--json"], _ck_fans_show),

        p("mcp-surface", "the MCP handshake and the exact 12-tool surface",
          "initialize ok, tools/list == 12 contract tools, T0 call answers",
          [], _ck_mcp),

        p("journal-integrity", "the access journal holds everything",
          "rc 0, entries parse, each has ts/tool/status",
          ["journal", "--json"], _ck_journal),

        p("report-digest", "the supervised-loop digest answers",
          "rc 0, verdict + per-day buckets",
          ["report", "--days", "1", "--json"], _ck_report),
    ]


# ------------------------------------------------------------------ runner


def _report_dir() -> Path:
    d = journal.state_dir() / "rehearse"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _prune_reports(keep: int = 10) -> None:
    reports = sorted(_report_dir().glob("rehearsal-*.json"))
    for old in reports[:-keep]:
        try:
            old.unlink()
        except OSError:
            pass


def run_rehearsal(backend: str = "real", *, write_report: bool = True) -> dict:
    cli = _cli_bin()
    if cli is None:
        return {"schema": "omarchy-firmware/rehearsal@1", "backend": backend,
                "verdict": "aborted",
                "error": "omarchy-firmware binary not found"}

    ctx: dict = {"fixture": None, "sysfs_epp": None, "curve": None,
                 "mcp_env": dict(os.environ), "is_twin": backend == "twin"}

    if backend == "twin":
        ctx["fixture"] = twin.resolve_fixture_dir("b450-plus")
        if not ctx["fixture"]:
            return {"schema": "omarchy-firmware/rehearsal@1",
                    "backend": backend, "verdict": "aborted",
                    "error": "twin assets not found (install.sh stages "
                             "them, or set FW_TWIN_DIR)"}
        applied = twin.apply_sysfs_env()
        epp = os.environ.get("FW_SYSFS_CPU")
        ctx["sysfs_epp"] = (Path(epp) / "cpu0" / "cpufreq"
                            / "energy_performance_preference") if epp else None
        ctx["mcp_env"] = {**os.environ,
                          "FW_FIXTURE_DIR": ctx["fixture"],
                          "FW_DIAG_SCENARIO": "no-paste"}
        twin_note = f"sysfs applied: {applied or 'none'}"
    else:
        twin_note = "live machine — twin assets untouched"

    curve_path = Path(tempfile.mkstemp(suffix=".json")[1])
    curve_path.write_text(json.dumps(CURVE), encoding="utf-8")
    ctx["curve"] = curve_path

    probes = build_probes(backend, ctx)
    rows, counts = [], {"pass": 0, "fail": 0, "skip": 0}
    try:
        for probe in probes:
            row = {"id": probe["id"], "title": probe["title"],
                   "expected": probe["expected"]}
            if probe.get("twin_only") and backend != "twin":
                row.update(status="skip",
                           observed="twin-only probe — day-0 covers it live")
                counts["skip"] += 1
            else:
                try:
                    if probe["id"] == "mcp-surface":
                        mcp = _mcp_bin()
                        if mcp is None:
                            pv = {"rc": 1, "responses": {}, "err":
                                  "omarchy-firmware-mcp not found", "out": ""}
                        else:
                            pv = _mcp_exchange(mcp, ctx["mcp_env"])
                    else:
                        pv = _run_cli(cli, probe["argv"])
                    ok, observed = probe["check"](pv, ctx)
                    row.update(status="pass" if ok else "fail",
                               observed=observed, rc=pv.get("rc"))
                    counts["pass" if ok else "fail"] += 1
                except Exception as exc:  # noqa: BLE001 — a crash is a fail
                    row.update(status="fail", observed=f"probe crashed: {exc}")
                    counts["fail"] += 1
            rows.append(row)
    finally:
        try:
            curve_path.unlink()
        except OSError:
            pass

    verdict = "green" if counts["fail"] == 0 else "red"
    report = {
        "schema": "omarchy-firmware/rehearsal@1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "backend": backend,
        "profile": twin.PROFILE if backend == "twin" else None,
        "note": twin_note,
        "counts": counts,
        "verdict": verdict,
        "probes": rows,
    }
    if write_report:
        out = _report_dir() / f"rehearsal-{time.strftime('%Y%m%d-%H%M%S')}.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        report["report_file"] = str(out)
        _prune_reports()
    journal.record("rehearse", "T0", ["rehearse", "--backend", backend],
                   "ok" if verdict == "green" else "fail",
                   f"{backend}: {counts['pass']} pass, {counts['fail']} fail, "
                   f"{counts['skip']} skip — {verdict}")
    return report


def render(report: dict) -> str:
    """Human rendering — one line per probe, day-0 readable."""
    if report.get("verdict") == "aborted":
        return f"rehearsal aborted: {report.get('error')}"
    lines = [f"== Dress rehearsal — backend: {report['backend']} "
             f"({report.get('note', '')}) =="]
    marks = {"pass": "PASS", "fail": "FAIL", "skip": "skip"}
    for r in report["probes"]:
        lines.append(f"  {marks[r['status']]:<4} {r['id']:<24} {r['title']}")
        if r["status"] != "pass":
            lines.append(f"           expected: {r['expected']}")
            lines.append(f"           observed: {r['observed']}")
    c = report["counts"]
    lines.append(f"verdict: {report['verdict']} — "
                 f"{c['pass']} pass, {c['fail']} fail, {c['skip']} skip")
    if report["backend"] == "real" and c["fail"]:
        lines.append(
            "note: content probes failed — if this is not the target "
            "machine, that is the honest answer (no board/sensors here); "
            "on the target it is a day-0 finding.")
    if report.get("report_file"):
        lines.append(f"report: {report['report_file']}")
    return "\n".join(lines)
