"""Reference CLI — one implementation, three consumers (vol. 2, ch. 6).

The CLI is the only functional reference; the MCP server is just a typed
wrapper around it. Every T0 call goes through here, gets journaled, and
prints human-readable or --json output depending on the consumer (the agent
asks for --json, the human keeps the default).

    omarchy-firmware audit status [--json] [--fixture-dir DIR]
    omarchy-firmware audit cve    [--json] [--fixture-dir DIR]
    omarchy-firmware boot inspect [--json] [--fixture-dir DIR]
    omarchy-firmware update check [--json] [--refresh] [--fixture-dir DIR]
    omarchy-firmware diag quick   [--json] [--scenario NAME] [--no-record]
    omarchy-firmware diag probe   [--json] [--seconds N] [--scenario NAME]
    omarchy-firmware diag scenarios            — list the bundled scenarios
    omarchy-firmware journal [N]
    omarchy-firmware selftest     — full demo on fixtures and scenarios
    omarchy-firmware tiers        — display the T0-T3 contract
    omarchy-firmware mcp          — start the MCP stdio server
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import audit, boot, cve_kb, diagnostics, fwupd, journal, smbios, tiers


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

    pb = sub.add_parser("boot", help="boot chain (inspect)")
    bsub = pb.add_subparsers(dest="boot_cmd", required=True)
    s3 = bsub.add_parser("inspect", help="efibootmgr entries, UKI/Limine, snapshots")
    common(s3)

    pu = sub.add_parser("update", help="firmware updates (check)")
    usub = pu.add_subparsers(dest="update_cmd", required=True)
    s4 = usub.add_parser("check", help="local fwupd state — 15-min cache, no network")
    s4.add_argument("--refresh", action="store_true",
                    help="refresh LVFS metadata (the only network access, on request)")
    common(s4)

    pd = sub.add_parser("diag", help="physical thermal diagnostics (vol. 3)")
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

    pj = sub.add_parser("journal", help="T0 access journal")
    pj.add_argument("limit", nargs="?", type=int, default=20)
    pj.add_argument("--json", action="store_true")

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

    if args.cmd == "boot" and args.boot_cmd == "inspect":
        return _guard("fw.boot.inspect", argv,
                      lambda: boot.collect(args.fixture_dir), args,
                      fixture=args.fixture_dir is not None)

    if args.cmd == "update" and args.update_cmd == "check":
        return _guard("fw.update.check", argv,
                      lambda: fwupd.check_updates(args.fixture_dir, args.refresh), args,
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

    if args.cmd == "selftest":
        fx = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "b450-plus"
        if not fx.exists():
            print(f"fixtures not found: {fx}", file=sys.stderr)
            return 1
        print(f"== demo on fixtures ({fx.name}) — no hardware required ==")
        for tool, fn in (
            ("fw.audit.status", lambda: audit.collect(str(fx))),
            ("fw.audit.cve", lambda: cve_kb.collect(str(fx))),
            ("fw.boot.inspect", lambda: boot.collect(str(fx))),
            ("fw.update.check", lambda: fwupd.check_updates(str(fx))),
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
        print("Tool contract (vol. 2 table 5.1 + vol. 3 diagnostics) — one declared tier per tool:\n")
        for tool, tier in tiers.TOOL_TIERS.items():
            mark = "✓ implemented" if tool in tiers.IMPLEMENTED_T0 else "… later phase"
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
