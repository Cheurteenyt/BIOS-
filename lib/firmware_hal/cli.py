"""Reference CLI — one implementation, three consumers (vol. 2, ch. 6).

The CLI is the only functional reference; the MCP server is just a typed
wrapper around it. Every T0 call goes through here, gets journaled, and
prints human-readable or --json output depending on the consumer (the agent
asks for --json, the human keeps the default). T1 calls go through _guard_t1:
same journaling, status carried (dry-run / applied / rolled-back / refused).

    omarchy-firmware audit status [--json] [--fixture-dir DIR]
    omarchy-firmware audit cve       [--json] [--fixture-dir DIR]
    omarchy-firmware audit cve-watch [--json] [--fixture-dir DIR]  (T0, P4)
    omarchy-firmware boot inspect [--json] [--fixture-dir DIR]
    omarchy-firmware update check [--json] [--refresh] [--fixture-dir DIR]
    omarchy-firmware update stage --device GUID [--reason TEXT] [--confirm]
                                   [--cancel] [--fixture-dir DIR]  (T2, human)
    omarchy-firmware update rollback [--json] [--fixture-dir DIR]  (T2, by design)
    omarchy-firmware diag quick   [--json] [--scenario NAME] [--no-record]
    omarchy-firmware diag probe   [--json] [--seconds N] [--scenario NAME]
    omarchy-firmware diag scenarios            — list the bundled scenarios
    omarchy-firmware diag storage [--json] [--fixture-dir DIR]   (T0)
    omarchy-firmware diag gpu     [--json] [--fixture-dir DIR]   (T0)
    omarchy-firmware diag ram     [--json] [--fixture-dir DIR]   (T0)
    omarchy-firmware diag settings [--json] [--fixture-dir DIR]  (T0)
    omarchy-firmware cpu epp set VALUE [--confirm] [--json]      (T1, dry-run default)
    omarchy-firmware cpu epp undo [--confirm] [--json]           (T1 rollback)
    omarchy-firmware fans curve show  [--json]                   (read)
    omarchy-firmware fans curve set --file FILE [--confirm]      (T1, dry-run default)
    omarchy-firmware fans curve undo [--confirm] [--json]        (T1 rollback)
    omarchy-firmware journal [N]
    omarchy-firmware report [--days N] [--json]  — supervised-loop digest (P4)
    omarchy-firmware twin         — the digital twin: profile + resolved assets
    omarchy-firmware rehearse [--backend twin|real] [--json]
                                  — the dress rehearsal: the whole behavioural
                                    contract in one command (day-0 drill)
    omarchy-firmware selftest     — full demo on the twin fixtures
    omarchy-firmware tiers        — display the T0-T3 contract
    omarchy-firmware mcp          — start the MCP stdio server
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import actions, audit, boot, cve_kb, cve_watch, diagnostics, fwupd, gpu, journal, ram, rehearse, report, rollback, settings as settings_mod, smbios, stage, storage, tiers, twin


def _emit(data: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print(_render(data))


def _render(data: dict) -> str:
    """Compact human rendering: section titles + key: value lines."""
    lines: list[str] = []

    def walk(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("error", "warning") and v:
                    lines.append(f"  {prefix}{k}: ⚠ {v}")
                elif isinstance(v, (dict, list)):
                    if v:
                        lines.append(f"{prefix}{k}:")
                    walk(v, prefix + "  ")
                elif v is not None:
                    lines.append(f"{prefix}{k}: {v}")
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    one = "; ".join(
                        f"{k}={v}" for k, v in item.items()
                        if v is not None and k not in ("device_path", "rationale", "details")
                    )
                    lines.append(f"  {prefix}- {one}")
                    if item.get("rationale"):
                        lines.append(f"    {prefix}↳ {item['rationale']}")
                else:
                    lines.append(f"  {prefix}- {item}")
        else:
            lines.append(f"  {prefix}{obj}")

    walk(data)
    return "\n".join(lines)


def _guard(tool: str, argv: list[str], fn, args, *, fixture: bool):
    """Journal the T0 call, execute, and emit — the single Phase 1 flow."""
    try:
        tier = tiers.assert_phase1(tool)
    except tiers.TierRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    try:
        data = fn()
        data["journal_entry"] = journal.record(
            tool, tier, argv, "ok",
            _summary_of(data), fixture=fixture,
        )
        _emit(data, args.json)
        return 0
    except Exception as exc:  # noqa: BLE001 — the boundary CLI tells everything
        journal.record(tool, tier, argv, "error", str(exc)[:200], fixture=fixture)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _summary_of(data: dict) -> str:
    for key in ("verdict", "status"):
        if data.get(key):
            return str(data[key])[:160]
    if data.get("board", {}).get("board_product"):
        return f"board {data['board']['board_product']}"
    return "inventory completed"


def _guard_t1(tool: str, argv: list[str], fn, args, *, fixture: bool = False):
    """T1 flow: journal with the action status, exit code per outcome."""
    try:
        tier = tiers.assert_phase1(tool)
    except tiers.TierRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    try:
        data = fn()
        status = data.get("status", "dry-run")
        data["journal_entry"] = journal.record(
            tool, tier, argv, status, _summary_t1(data), fixture=fixture)
        _emit(data, args.json)
        return 2 if status == "refused" else 0
    except actions.ActionRefused as exc:
        journal.record(tool, tier, argv, "refused", str(exc)[:200], fixture=fixture)
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 — the boundary CLI tells everything
        journal.record(tool, tier, argv, "error", str(exc)[:200], fixture=fixture)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _summary_t1(data: dict) -> str:
    if data.get("status") == "dry-run":
        n = len(data.get("diff", {}) or data.get("plan_writes", []) or {})
        return f"dry-run plan ({n} change(s)) — nothing written"
    if data.get("status") == "applied":
        n = data.get("applied_writes")
        if n is None:
            n = len(data.get("applied") or {})
        return f"applied: {n} write(s), backup #{data.get('backup_id')}"
    if data.get("status") == "rolled-back":
        return f"rolled back: {len(data.get('restored', {}))} value(s) restored"
    return str(data.get("note") or data.get("status"))[:160]


# T2 statuses and their exit codes: a refusal is an answer here, not a
# crash — refused-by-design exits 0 because the inventory IS the result.
_T2_EXIT = {"dry-run": 0, "staged": 0, "cancelled": 0, "reverted": 0,
            "applied": 0, "ok": 0, "refused-by-design": 0,
            "refused": 2, "error": 1}


def _guard_t2(tool: str, argv: list[str], fn, args, *, fixture: bool = False):
    """T2 flow: journal with the transaction status, exit code per outcome."""
    try:
        tier = tiers.tier_of(tool)
    except tiers.TierRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    try:
        data = fn()
        status = data.get("status", "dry-run")
        data["journal_entry"] = journal.record(
            tool, tier, argv, status,
            str(data.get("note") or data.get("verdict") or status)[:200],
            fixture=fixture)
        _emit(data, args.json)
        return _T2_EXIT.get(status, 1)
    except Exception as exc:  # noqa: BLE001 — the boundary CLI tells everything
        journal.record(tool, tier, argv, "error", str(exc)[:200], fixture=fixture)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _render_diag(data: dict) -> str:
    """Human rendering of the diagnostic: verdict first, evidence next."""
    m = data.get("measurements", {})
    lines = [
        f"verdict : {data.get('verdict')}  (mode {data.get('mode')}, "
        f"confidence {m.get('confidence')}, source: {data.get('source')})",
        f"readings: Tctl {m.get('tctl_med')} °C | ambient {m.get('ambient_med')} °C "
        f"| coolant {m.get('coolant_med')} °C | VRM {m.get('vrm_med')} °C "
        f"| P {m.get('power_med')} W | R_th {m.get('r_th')} °C/W",
    ]
    if not data.get("findings"):
        lines.append("no finding — nothing nameable on these sensors.")
    for f in data.get("findings", []):
        lines.append(f"\n[{f['severity'].upper()}] {f['title']}  (confidence {f['confidence']})")
        lines.append(f"  finding    : {f['hypothesis']}")
        lines.append(f"  next steps : {f['next_steps']}")
        evidence = " ; ".join(f"{k}={v}" for k, v in f["evidence"].items())
        lines.append(f"  evidence   : {evidence}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omarchy-firmware",
        description="T0 firmware base (read-only) — audit + thermal diagnostics, omarchy-firmware plan.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--json", action="store_true", help="machine output (for the agent)")
        sp.add_argument("--fixture-dir", metavar="DIR", default=None,
                        help="read collections from fixtures (tests/demo)")

    pa = sub.add_parser("audit", help="firmware audit (status | cve)")
    asub = pa.add_subparsers(dest="audit_cmd", required=True)
    s1 = asub.add_parser("status", help="full inventory: board, BIOS, boot, fwupd, sensors")
    common(s1)
    s2 = asub.add_parser("cve", help="version / known-CVE cross-check (vol. 1, ch. 5)")
    common(s2)
    s2w = asub.add_parser("cve-watch", help="KB freshness, drift, fwupd advisory cross-check (P4)")
    common(s2w)

    pb = sub.add_parser("boot", help="boot chain (inspect)")
    bsub = pb.add_subparsers(dest="boot_cmd", required=True)
    s3 = bsub.add_parser("inspect", help="efibootmgr entries, UKI/Limine, snapshots")
    common(s3)

    pu = sub.add_parser("update", help="firmware updates (check | stage | rollback)")
    usub = pu.add_subparsers(dest="update_cmd", required=True)
    s4 = usub.add_parser("check", help="local fwupd state — 15-min cache, no network")
    s4.add_argument("--refresh", action="store_true",
                    help="refresh LVFS metadata (the only network access, on request)")
    common(s4)
    s4s = usub.add_parser("stage", help="stage a fwupd update (T2 — HUMAN only, dry-run default)")
    s4s.add_argument("--device", metavar="GUID", default=None,
                     help="exact fwupd GUID of the target device")
    s4s.add_argument("--reason", metavar="TEXT", default=None,
                     help="why this update — mandatory at confirm, journaled")
    s4s.add_argument("--confirm", action="store_true",
                     help="execute the staging (default: plan only — a HUMAN gesture)")
    s4s.add_argument("--cancel", action="store_true",
                     help="mark the pending transaction cancelled (before reboot)")
    common(s4s)
    s4r = usub.add_parser("rollback", help="rollback inventory — refused by design, honest answer (T2)")
    common(s4r)

    pd = sub.add_parser("diag", help="physical diagnostics (vol. 3-4)")
    dsub = pd.add_subparsers(dest="diag_cmd", required=True)
    d1 = dsub.add_parser("quick", help="passive: 3 reads, immediate verdict, frugal one-shot")
    d1.add_argument("--scenario", metavar="NAME", default=None,
                    help="pre-recorded series (tests / demo without hardware)")
    d1.add_argument("--no-record", action="store_true",
                    help="do not write the baseline")
    common(d1)
    d2 = dsub.add_parser("probe", help="active: controlled load N s, time constant, decay")
    d2.add_argument("--seconds", type=int, default=30, help="load duration (10-120 s, default 30)")
    d2.add_argument("--scenario", metavar="NAME", default=None,
                    help="simulated probe on a scenario (without hardware)")
    d2.add_argument("--no-record", action="store_true")
    common(d2)
    d3 = dsub.add_parser("scenarios", help="list the bundled thermal scenarios")
    common(d3)
    d4 = dsub.add_parser("storage", help="NVMe/SATA SMART + PCIe links (vol. 4)")
    common(d4)
    d5 = dsub.add_parser("gpu", help="Xid history, clock limits, BAR1, link width (vol. 4)")
    common(d5)
    d6 = dsub.add_parser("ram", help="rated vs configured speed, EDAC counters (vol. 4)")
    common(d6)
    d7 = dsub.add_parser("settings", help="observable BIOS settings audit (vol. 4)")
    common(d7)

    pc = sub.add_parser("cpu", help="T1 CPU actions (epp)")
    csub = pc.add_subparsers(dest="cpu_cmd", required=True)
    ce = csub.add_parser("epp", help="energy performance preference (T1, reversible)")
    esub = ce.add_subparsers(dest="epp_cmd", required=True)
    es1 = esub.add_parser("set", help="set EPP on every CPU (dry-run unless --confirm)")
    es1.add_argument("value", metavar="VALUE",
                     help="one of the available preferences (e.g. balance_performance)")
    es1.add_argument("--confirm", action="store_true",
                     help="apply for real (default: dry-run plan only)")
    common(es1)
    es2 = esub.add_parser("undo", help="restore the last backed-up EPP values")
    es2.add_argument("--confirm", action="store_true")
    common(es2)

    pf = sub.add_parser("fans", help="T1 fan actions (curve)")
    fsub = pf.add_subparsers(dest="fans_cmd", required=True)
    fc = fsub.add_parser("curve", help="Smart Fan curve on nct67xx (T1, reversible)")
    fsub2 = fc.add_subparsers(dest="curve_cmd", required=True)
    fs1 = fsub2.add_parser("set", help="write a curve (dry-run unless --confirm)")
    fs1.add_argument("--file", metavar="FILE", required=True,
                     help='JSON: {"hwmon": "nct6798", "pwm": 1, '
                          '"points": [{"temp": 40, "pwm": 90}, ...]}')
    fs1.add_argument("--confirm", action="store_true",
                     help="apply for real (default: dry-run plan only)")
    common(fs1)
    fs2 = fsub2.add_parser("undo", help="restore the last backed-up curve")
    fs2.add_argument("--confirm", action="store_true")
    common(fs2)
    fs3 = fsub2.add_parser("show", help="read current modes and curves (no write)")
    common(fs3)

    pj = sub.add_parser("journal", help="T0 access journal")
    pj.add_argument("limit", nargs="?", type=int, default=20)
    pj.add_argument("--json", action="store_true")

    pt = sub.add_parser("twin", help="the digital twin: profile and resolved assets")
    pt.add_argument("--json", action="store_true")
    prh = sub.add_parser("rehearse", help="the dress rehearsal — the whole "
                                            "behavioural contract, one command")
    prh.add_argument("--backend", choices=["twin", "real"], default="real",
                     help="twin = TWIN-1 fixtures (rehearsal); "
                          "real = this machine (day-0 drill)")
    prh.add_argument("--no-report", action="store_true",
                     help="do not write the rehearsal report file")
    prh.add_argument("--json", action="store_true")

    pr = sub.add_parser("report", help="supervised-loop digest (P4): days, tools, write statuses")
    pr.add_argument("--days", type=int, default=5, help="window in days (default 5)")
    pr.add_argument("--json", action="store_true")

    sub.add_parser("selftest", help="full demo on bundled fixtures")
    sub.add_parser("tiers", help="display the T0-T3 contract")
    sub.add_parser("mcp", help="start the MCP stdio server (4 T0 tools)")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)

    if args.cmd == "audit" and args.audit_cmd == "status":
        return _guard("fw.audit.status", argv,
                      lambda: audit.collect(args.fixture_dir), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "audit" and args.audit_cmd == "cve":
        return _guard("fw.audit.cve", argv,
                      lambda: cve_kb.collect(args.fixture_dir), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "audit" and args.audit_cmd == "cve-watch":
        return _guard("fw.cve.watch", argv,
                      lambda: cve_watch.collect(args.fixture_dir), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "boot" and args.boot_cmd == "inspect":
        return _guard("fw.boot.inspect", argv,
                      lambda: boot.collect(args.fixture_dir), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "update" and args.update_cmd == "check":
        return _guard("fw.update.check", argv,
                      lambda: fwupd.check_updates(args.fixture_dir, args.refresh), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "update" and args.update_cmd == "stage":
        if args.cancel:
            return _guard_t2("fw.update.stage", argv, stage.cancel, args,
                             fixture=args.fixture_dir is not None)
        if not args.device:
            print("update stage: --device GUID is required (or --cancel)",
                  file=sys.stderr)
            return 2
        if args.confirm:
            return _guard_t2(
                "fw.update.stage", argv,
                lambda: stage.apply(args.device, args.reason,
                                    fixture_dir=args.fixture_dir), args,
                fixture=args.fixture_dir is not None)
        return _guard_t2(
            "fw.update.stage", argv,
            lambda: stage.plan(args.device, args.fixture_dir, reason=args.reason),
            args, fixture=args.fixture_dir is not None)

    if args.cmd == "update" and args.update_cmd == "rollback":
        return _guard_t2("fw.rollback", argv,
                         lambda: rollback.inventory(args.fixture_dir), args,
                         fixture=args.fixture_dir is not None)

    if args.cmd == "diag" and args.diag_cmd == "scenarios":
        rows = diagnostics.list_scenarios()
        if getattr(args, "json", False):
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        elif not rows:
            print("no bundled scenario (tests/fixtures/scenarios/).")
        else:
            print(f"Bundled thermal scenarios ({len(rows)}):\n")
            for r in rows:
                meta = r.get("meta", {})
                print(f"  {r['name']:<24} {meta.get('title', '')}")
                print(f"    {'cooling ' + str(meta.get('cooling')) if meta.get('cooling') else ''}"
                      f"{' — ' + meta.get('note', '') if meta.get('note') else ''}")
        return 0

    if args.cmd == "diag" and args.diag_cmd in ("quick", "probe"):
        record = not args.no_record
        secs = getattr(args, "seconds", 30) if args.diag_cmd == "probe" else None
        scen = getattr(args, "scenario", None)
        if args.diag_cmd == "probe" and scen is None and args.fixture_dir is None:
            if secs is not None and not (10 <= secs <= 120):
                print("probe: --seconds must be between 10 and 120", file=sys.stderr)
                return 2
        try:
            data = diagnostics.quick(scenario=scen, fixture_dir=args.fixture_dir,
                                     record=record, probe_seconds=secs)
        except FileNotFoundError as exc:
            journal.record("fw.diag.thermal", "T0", argv, "error", str(exc)[:200],
                           fixture=scen is not None or args.fixture_dir is not None)
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        data["journal_entry"] = journal.record(
            "fw.diag.thermal", "T0", argv, "ok", str(data.get("verdict"))[:160],
            fixture=scen is not None or args.fixture_dir is not None)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(_render_diag(data))
        return 0

    if args.cmd == "diag" and args.diag_cmd in (
            "storage", "gpu", "ram", "settings"):
        tool = {"storage": "fw.diag.storage", "gpu": "fw.diag.gpu",
                "ram": "fw.diag.ram", "settings": "fw.diag.settings"}[args.diag_cmd]
        fn = {"storage": storage.collect, "gpu": gpu.collect,
              "ram": ram.collect, "settings": settings_mod.collect}[args.diag_cmd]
        return _guard(tool, argv, lambda: fn(args.fixture_dir), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "cpu" and args.cpu_cmd == "epp":
        if args.epp_cmd == "set":
            return _guard_t1("cpu.epp.set", argv,
                             lambda: actions.epp_set(args.value, confirm=args.confirm),
                             args)
        return _guard_t1("cpu.epp.set", argv,
                         lambda: actions.epp_set(undo=True, confirm=args.confirm), args)

    if args.cmd == "fans" and args.fans_cmd == "curve":
        if args.curve_cmd == "set":
            try:
                curve = json.loads(Path(args.file).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"ERROR: curve file unreadable: {exc}", file=sys.stderr)
                return 1
            return _guard_t1("fans.curve.set", argv,
                             lambda: actions.fans_curve_set(curve, confirm=args.confirm),
                             args)
        if args.curve_cmd == "undo":
            return _guard_t1("fans.curve.set", argv,
                             lambda: actions.fans_curve_set(undo=True, confirm=args.confirm),
                             args)
        # fans curve show — a read, still through the journal
        return _guard("fans.curve.set", argv,
                      lambda: actions.fans_curve_show(), args, fixture=False)

    if args.cmd == "journal":
        entries = journal.show(args.limit)
        if getattr(args, "json", False):
            print(json.dumps(entries, ensure_ascii=False, indent=2))
        elif not entries:
            print("journal empty — no call recorded yet.")
        else:
            for e in entries:
                mark = " (fixture)" if e.get("fixture") else ""
                print(f"{e['ts']}  {e['tool']:<18} {e['tier']}  {e['status']}{mark}")
                print(f"    {e['summary']}")
        return 0

    if args.cmd == "report":
        data = report.collect(days=max(1, args.days))
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"Supervised-loop report — {data['verdict']}")
            for day, b in data["days"].items():
                print(f"\n  {day}: {b['calls']} call(s), {b['errors']} error(s)")
                for t, n in b["tools"].items():
                    print(f"    {t:<20} x{n}")
                sts = ", ".join(f"{s} x{n}" for s, n in b["statuses"].items())
                if sts:
                    print(f"    statuses: {sts}")
            print("\nReview each raised finding against reality; mark the "
                  "false positives. That annotated journal is the P4 evidence.")
        return 0

    if args.cmd == "twin":
        data = twin.describe()
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            prof = data["profile"]
            print(f"{prof['name']} — {prof['story']}")
            for k in ("board", "cpu", "gpu", "storage", "cooling", "boot"):
                print(f"  {k:<8}: {prof[k]}")
            print(f"  assets  : {', '.join(prof['assets']['fixtures'])} "
                  f"+ {prof['assets']['scenarios']} scenarios "
                  f"+ sysfs ({', '.join(prof['assets']['sysfs'])})")
            print(f"  resolved: {data['source']} — root {data['asset_root']}")
            print(f"  honesty : {prof['cannot_prove']}")
            print("\nRehearse against it: omarchy-firmware rehearse --backend twin")
        return 0

    if args.cmd == "rehearse":
        data = rehearse.run_rehearsal(backend=args.backend,
                                      write_report=not args.no_report)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(rehearse.render(data))
        return 0 if data.get("verdict") == "green" else 1

    if args.cmd == "selftest":
        fx = twin.resolve_fixture_dir("b450-plus")
        if fx is None:
            print("twin fixtures not found (repo tests/ or installed twin)",
                  file=sys.stderr)
            return 1
        fx = Path(fx)
        print(f"== demo on the twin ({twin.TWIN_NAME}: {fx.name}) — "
              f"no hardware required ==")
        for tool, fn in (
            ("fw.audit.status", lambda: audit.collect(str(fx))),
            ("fw.audit.cve", lambda: cve_kb.collect(str(fx))),
            ("fw.boot.inspect", lambda: boot.collect(str(fx))),
            ("fw.update.check", lambda: fwupd.check_updates(str(fx))),
            ("fw.cve.watch", lambda: cve_watch.collect(str(fx))),
            ("fw.diag.storage", lambda: storage.collect(str(fx))),
            ("fw.diag.gpu", lambda: gpu.collect(str(fx))),
            ("fw.diag.ram", lambda: ram.collect(str(fx))),
            ("fw.diag.settings", lambda: settings_mod.collect(str(fx))),
        ):
            data = fn()
            print(f"\n--- {tool} (T0) ---")
            _emit(data, as_json=False)
        scen_dir = fx.parent / "scenarios"
        for name in ("healthy-liquid", "no-paste", "pump-dead"):
            p = scen_dir / f"{name}.json"
            if p.exists():
                data = diagnostics.quick(scenario=name, record=False)
                print(f"\n--- fw.diag.thermal (T0) — {name} ---")
                print(_render_diag(data))
        print("\nEvery call above was journaled: `omarchy-firmware journal`")
        return 0

    if args.cmd == "tiers":
        print("Tool contract (vol. 2 table 5.1 + vol. 3 diagnostics + P4) — one declared tier per tool:\n")
        for tool, tier in tiers.TOOL_TIERS.items():
            if tool in tiers.IMPLEMENTED_T0:
                mark = "✓ read-only"
            elif tool in tiers.IMPLEMENTED_T1:
                mark = "✓ two-key reversible"
            elif tool == "fw.update.stage":
                mark = "human-only CLI (P4)"
            elif tool == "fw.rollback":
                mark = "refused-by-design (P4)"
            else:
                mark = "… later phase"
            print(f"  {tool:<18} {tier}   {mark}")
        print("\nTier meanings:")
        for t, meaning in tiers.TIER_MEANING.items():
            print(f"  {t}: {meaning}")
        print("\nT3 — no call path exists for flashing; the human executes EZ Flash.")
        return 0

    if args.cmd == "mcp":
        from . import mcp_server
        return mcp_server.serve()

    return 1
