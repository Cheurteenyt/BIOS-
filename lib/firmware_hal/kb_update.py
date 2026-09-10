"""Knowledge-base updater — the two-key rule applied to DATA (P4).

omarchy-firmware-cve-update refreshes the AM4 CVE knowledge base. It is
the ONLY component that ever writes the KB, and it writes nothing without
the same discipline as a T1 write:

  1. stage    — load the candidate KB (--file PATH or --from URL), fully
                validate its schema, compute its sha256, show the diff
                summary. NOTHING is activated (status: dry-run);
  2. confirm  — re-run with --confirm AND the sha256 shown at staging.
                A mismatch is a supply-chain red flag: refused, never
                "just applied".

Activation means writing the local override in XDG state
(cve-kb-override.json) and backing up the previous override. The watch
baseline is deliberately NOT reset: the next fw.cve.watch must see and
name the change (added/removed entries) — a KB transition that stays
invisible would defeat the drift mechanism.
The packaged KB (lib/firmware_hal/data/cve_am4.json) is never modified
at runtime: it moves only through git commits by maintainers.

The KB update is a data operation, not a firmware write — but it is
journaled (tool "kb.update") like everything else, because the whole
point of the journal is that nothing happens off the record.

Network note: --from URL uses the stdlib urllib on EXPLICIT human
request only. No collector, no timer, no tool ever refreshes the KB by
itself — the loop observes, the human feeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import cve_kb, journal


class KbRefused(Exception):
    """The candidate KB is invalid or the confirmation is missing/wrong."""


def _validate(kb: dict) -> list[str]:
    """Structural validation — refuse anything the tools could not reason on."""
    if not isinstance(kb, dict):
        raise KbRefused("top level must be an object")
    for key in ("scope", "generated", "entries"):
        if key not in kb:
            raise KbRefused(f"missing required key: {key}")
    entries = kb["entries"]
    if not isinstance(entries, list) or not entries:
        raise KbRefused("'entries' must be a non-empty list")
    ids = []
    for e in entries:
        if not isinstance(e, dict):
            raise KbRefused("entries must be objects")
        for key in ("id", "title", "year"):
            if key not in e:
                raise KbRefused(f"entry missing '{key}': {str(e)[:80]}")
        ids.append(e["id"])
    if len(ids) != len(set(ids)):
        raise KbRefused("duplicate entry ids")
    return ids


def _load_candidate(source: str, url: bool) -> tuple[dict, bytes]:
    if url:
        req = urllib.request.Request(source, headers={"User-Agent": "omarchy-firmware-kb"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    else:
        raw = Path(source).read_bytes()
    try:
        kb = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KbRefused(f"not valid JSON: {exc}") from None
    ids = _validate(kb)
    return _annotate(kb, ids, raw)


def _annotate(kb: dict, ids: list[str], raw: bytes) -> dict:
    """Everything the staging summary needs, computed once."""
    return {
        "kb": kb,
        "ids": ids,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def _overrides() -> tuple[Path, Path]:
    return cve_kb._override_path(), cve_kb._override_path().with_suffix(".prev.json")


def stage(source: str, url: bool = False) -> dict:
    cand = _load_candidate(source, url)
    current = cve_kb.load_kb()
    old_ids = {e.get("id") for e in current.get("entries", [])}
    new_ids = set(cand["ids"])
    return {
        "tool": "kb.update",
        "status": "dry-run",
        "source_kind": "url" if url else "file",
        "source": source,
        "sha256": cand["sha256"],
        "bytes": cand["bytes"],
        "generated": cand["kb"].get("generated"),
        "entries": len(cand["ids"]),
        "diff": {
            "added": sorted(new_ids - old_ids),
            "removed": sorted(old_ids - new_ids),
        },
        "note": ("nothing activated — re-run with --confirm --sha256 "
                 + cand["sha256"][:16] + "… (full hash) to activate"),
    }


def activate(source: str, url: bool, sha256: str) -> dict:
    if not sha256:
        raise KbRefused(
            "confirmation requires the exact sha256 shown at staging "
            "(--sha256 HEX) — the two-key rule applies to data too")
    cand = _load_candidate(source, url)
    if cand["sha256"].lower() != sha256.lower():
        raise KbRefused(
            f"sha256 mismatch: staged {cand['sha256'][:16]}…, given "
            f"{sha256[:16]}… — the file changed between stage and confirm "
            "(supply-chain guard); stage again")
    override, backup = _overrides()
    if override.exists():
        shutil.copy2(override, backup)  # keep one generation of rollback
    payload = json.dumps(cand["kb"], ensure_ascii=False, indent=1).encode("utf-8")
    override.write_bytes(payload)
    # NOTE: the watch baseline is intentionally NOT reset — the next
    # fw.cve.watch must name the change (added/removed entries).
    entry = journal.record("kb.update", "T0", ["kb.update", "--confirm"], "applied",
                           f"KB override activated: {len(cand['ids'])} entries, "
                           f"sha256 {cand['sha256'][:16]}…")
    return {
        "tool": "kb.update",
        "status": "applied",
        "sha256": cand["sha256"],
        "entries": len(cand["ids"]),
        "backup": str(backup) if backup.exists() else None,
        "journal_entry": entry,
        "note": "override active — fw.audit.cve and fw.cve.watch use it now; "
                "revert with --revert",
    }


def revert() -> dict:
    override, backup = _overrides()
    if not override.exists():
        entry = journal.record("kb.update", "T0", ["kb.update", "--revert"],
                               "refused", "no override to revert")
        return {"tool": "kb.update", "status": "refused",
                "note": "no local override installed — the packaged KB is "
                        "already in force", "journal_entry": entry}
    if backup.exists():
        shutil.copy2(backup, override)
        backup.unlink()
        note = "previous override restored"
    else:
        override.unlink()
        note = "override removed — packaged KB back in force"
    entry = journal.record("kb.update", "T0", ["kb.update", "--revert"], "applied", note)
    return {"tool": "kb.update", "status": "reverted", "note": note,
            "journal_entry": entry}


def status() -> dict:
    path = cve_kb.active_path()
    return {
        "tool": "kb.update",
        "status": "ok",
        "source": cve_kb.kb_source(),
        "path": str(path),
        "override_installed": cve_kb._override_path().exists(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="omarchy-firmware-cve-update",
        description="Refresh the AM4 CVE knowledge base — two-key rule: "
                    "stage first, confirm with the shown sha256.")
    src = ap.add_mutually_exclusive_group(required=False)
    src.add_argument("--file", metavar="PATH", help="stage from a local JSON file")
    src.add_argument("--from", dest="from_url", metavar="URL",
                     help="stage from a URL (explicit human request only)")
    ap.add_argument("--confirm", action="store_true",
                    help="activate the staged KB (with --sha256)")
    ap.add_argument("--sha256", metavar="HEX", default=None,
                    help="sha256 of the staged file — mandatory at confirm")
    ap.add_argument("--revert", action="store_true",
                    help="restore the previous override, or remove the override")
    ap.add_argument("--status", action="store_true",
                    help="show which KB is in force")
    ap.add_argument("--json", action="store_true", help="machine output")
    args = ap.parse_args(argv)
    if not (args.status or args.revert) and not (args.file or args.from_url):
        ap.error("one of --file / --from is required (or --revert / --status)")

    try:
        if args.status:
            data = status()
        elif args.revert:
            data = revert()
        elif args.confirm:
            data = activate(args.file or args.from_url,
                            url=args.from_url is not None, sha256=args.sha256)
        else:
            data = stage(args.file or args.from_url, url=args.from_url is not None)
    except KbRefused as exc:
        journal.record("kb.update", "T0", argv or [], "refused", str(exc)[:200])
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except (OSError, urllib.error.URLError) as exc:  # type: ignore[attr-defined]
        journal.record("kb.update", "T0", argv or [], "error", str(exc)[:200])
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for k, v in data.items():
            if k == "journal_entry":
                continue
            if isinstance(v, dict):
                print(f"{k}:")
                for k2, v2 in v.items():
                    print(f"  {k2}: {v2}")
            else:
                print(f"{k}: {v}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
