"""fw.cve.watch — knowledge-base freshness and advisory drift (P4). T0.

The audit tool (fw.audit.cve) answers "where does THIS machine stand
against the known AM4 timeline?"; the watch answers "is the timeline
itself current, and what changed since the last look?" — the maintenance
half of the supervised loop (roadmap P4, "CVE watch").

It never touches the network. Refreshing the knowledge base is a
human-requested CLI (omarchy-firmware-cve-update) that obeys the two-key
rule like any write: stage, show the hash, confirm with the matching
--sha256. This tool only reads, correlates and records the baseline.

What it reports, in order:
  1. KB freshness — generated date, age in days, entry count, sha256,
     source (packaged vs local override);
  2. exposure — replay of the audit statuses (potential / unknown counts);
  3. drift — sha256 and per-entry hashes compared with the previous
     watch: added / changed / removed entry ids since then;
  4. fwupd cross-check — CVE ids advertised in fwupd release notes for
     the devices of this machine, correlated against the KB. Ids the KB
     does not know are listed as candidate advisories for the next KB
     revision: the agent proposes, the human decides (nothing is added
     automatically — "work from evidence").
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from . import cve_kb, fwupd, journal

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
_WATCH_STATE = "cve-watch.json"


def _state_path() -> Path:
    return journal.state_dir() / _WATCH_STATE


def _read_state() -> dict | None:
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_state(state: dict) -> None:
    try:
        _state_path().write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # the watch must never fail on its own bookkeeping


def _entry_hashes(kb: dict) -> dict[str, str]:
    out = {}
    for e in kb.get("entries", []):
        blob = json.dumps(e, sort_keys=True, ensure_ascii=False)
        out[e.get("id", "?")] = hashlib.sha256(blob.encode()).hexdigest()[:12]
    return out


def kb_info(kb: dict | None = None) -> dict:
    """Freshness of the ACTIVE knowledge base (override or packaged)."""
    if kb is None:
        kb = cve_kb.load_kb()
    path = cve_kb.active_path()
    try:
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        sha = None
    generated = kb.get("generated")
    age_days = None
    if generated:
        try:
            t = time.mktime(time.strptime(str(generated), "%Y-%m-%d"))
            age_days = max(0, int((time.time() - t) / 86400))
        except (ValueError, OverflowError):
            age_days = None
    return {
        "source": cve_kb.kb_source(),
        "path": str(path),
        "sha256": sha,
        "generated": generated,
        "age_days": age_days,
        "entry_count": len(kb.get("entries", [])),
        "stale": bool(age_days is None or age_days > 90),
    }


def _fwupd_advisories(fixture_dir, kb: dict) -> dict:
    """CVE ids advertised by fwupd release notes, correlated with the KB."""
    kb_cves: dict[str, str] = {}  # cve id -> kb entry id
    for e in kb.get("entries", []):
        blob = json.dumps(e, ensure_ascii=False)
        for cve in _CVE_RE.findall(blob):
            kb_cves.setdefault(cve.upper(), e.get("id", "?"))
    try:
        upd = fwupd.check_updates(fixture_dir, refresh=False)
    except Exception:  # noqa: BLE001 — degraded cross-check, stated not hidden
        return {"available": False}
    seen: dict[str, str] = {}
    for u in upd.get("updates", []):
        for cve in _CVE_RE.findall(str(u.get("details") or "")):
            seen.setdefault(cve.upper(), str(u.get("device")))
    correlated = {c: d for c, d in seen.items() if c in kb_cves}
    candidates = {c: d for c, d in seen.items() if c not in kb_cves}
    return {
        "available": True,
        "advisories": sorted(seen),
        "correlated": {c: kb_cves[c] for c in sorted(correlated)},
        "candidates": candidates,  # in fwupd notes but unknown to the KB
    }


def collect(fixture_dir=None) -> dict:
    # the KB file is parsed exactly ONCE per command and threaded through:
    # frugality is a hard constraint, and four parses could even disagree
    # if the KB changed under our feet mid-command.
    kb = cve_kb.load_kb()
    kb_i = kb_info(kb)
    sha = kb_i.get("sha256")

    audit = cve_kb.collect(fixture_dir, kb=kb)
    findings = audit.get("findings", [])
    exposed = sum(1 for f in findings if f["status"].startswith("potentially"))
    unknown = sum(1 for f in findings if f["status"].startswith("unknown"))

    # drift vs the previous watch ------------------------------------------
    prev = _read_state()
    if prev is None or not prev.get("sha256"):
        drift = {
            "status": "baseline-recorded",
            "note": "first watch: the current KB is the reference point",
        }
    elif prev.get("sha256") == sha:
        drift = {"status": "no-change", "since": prev.get("ts")}
    else:
        prev_h = prev.get("entry_hashes", {})
        cur_h = _entry_hashes(kb)
        drift = {
            "status": "changed",
            "since": prev.get("ts"),
            "added": sorted(set(cur_h) - set(prev_h)),
            "removed": sorted(set(prev_h) - set(cur_h)),
            "changed": sorted(k for k in set(cur_h) & set(prev_h)
                              if cur_h[k] != prev_h[k]),
        }

    state = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sha256": sha,
        "entry_hashes": _entry_hashes(kb),
    }
    _write_state(state)

    cross = _fwupd_advisories(fixture_dir, kb)

    parts = [
        f"KB {kb_i.get('generated')} ({kb_i.get('age_days')} d, "
        f"{kb_i.get('entry_count')} entries, source {kb_i.get('source')})",
        f"{exposed} potential exposure(s), {unknown} unknown, drift "
        f"{drift['status']}",
    ]
    if cross.get("available") and cross.get("candidates"):
        parts.append(
            f"{len(cross['candidates'])} fwupd advisory(ies) unknown to the KB "
            "— candidates for the next KB revision (human decides)")
    verdict = " ; ".join(parts) + (
        ". Refresh the KB with omarchy-firmware-cve-update if stale — "
        "two-key rule, nothing automatic." if kb_i.get("stale") else ".")

    return {
        "kb": kb_i,
        "exposure": {
            "potential": exposed,
            "unknown": unknown,
            "entries": len(findings),
        },
        "drift": drift,
        "fwupd_cross_check": cross,
        "verdict": verdict,
    }
