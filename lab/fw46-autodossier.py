#!/usr/bin/env python3
"""fw46-autodossier — the auto-dossier: the day-0 chain fused into ONE
command (propose -> anchor-marks -> compose -> dossier), measured.

After ring 45 the B550 day-0 protocol was THREE commands and one
memory: fw45 propose (L2-transfer gates + review table) -> operator
review -> fw42 dossier --lenses. The operator was the only place the
three stages met — the exact class of failure the ring-38/40/42 welds
exist to eliminate, one layer higher. fw46 fuses them: ONE command
that proposes, marks every slot against the stock-3644 anchor, hands
the operator's corrections their L1 precedence, and lands the full
triptych dossier — with the WHOLE provenance chain (proposal -> mark
-> journal -> dossier) in ONE artifact.

THE COUNT-BLINDNESS FIND (this ring's measured lesson): the ring-45
review marks compared PSP sets by COUNT. The release delta 3644->3645
swaps 37 body hashes INSIDE a 203-hash set — a count anchor reads
"== stock-3644 anchor" on 3645 and the review table would HIDE the
very discriminator law the register proclaims
(psp_discriminates_3644_vs_3645). fw46 anchors the SETS (the
203/194/193 sha256_16 strings, registered from the crown run) — the
3645 mark becomes "!=" with added 37 / removed 37, and the
count-blindness is asserted BOTH ways in the selftest
(count == AND set != on the same proposal).

Four laws:

  L1 CORRECTIONS-BEAT-PROPOSALS  a --lenses key replaces the proposal
                 for that slot and is journaled operator_correction;
                 proposals are defaults, never overrides of the
                 operator.
  L2 CALIBRATION-BEFORE-FUSION  fw45's L2-transfer gates run first:
                 every B550 anchor re-derives before anything is
                 proposed, composed, or fused; a broken basis refuses
                 the fusion whole.
  L3 LOUD DEGRADATION           a slot neither proposed nor corrected
                 is ABSENT from the lenses (the weld loud-degrades
                 it); omissions carry their reasons in the same
                 artifact.
  L4 ZERO WRITES                read-only on images; the only files
                 written are the --out documents the operator asked
                 for.

Modes:
  fused <image> [--target day0|release41] [--lenses corrections.json]
        [--review-only] [--out out.json] [--quiet]
        the ONE day-0 command: propose -> marks -> compose ->
        (dossier | review stop), one artifact, full chain.
  selftest     two-tier gates (R + I live — propose, discriminator,
               compose, and the full crown dossier)
  manifest     registers + instruments
"""

import argparse
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, "/home/z/my-project/repo-bios/lib")

RING = 46
_M = {}

_LENS_REG = os.path.join(HERE, "vendor-b550-lens.json")
_REG = os.path.join(HERE, "vendor-autodossier-register.json")

REF_TARGET = "b550w2-3644"      # the crown basis image (ring 44 sha16 5f7a0e439772c160)
DISC_TARGET = "b550w2-3645"     # the discriminator probe (0a1b5bda5be78e4b)

# the LENS_ONLY slots whose anchor is a SET (registered in the
# autodossier register), with their ring-45 COUNT fallbacks.
SET_SLOTS = ("psp_hashes_3644", "psp_hashes_3604", "psp_hashes_3802")
COUNT_FALLBACK = {
    "psp_hashes_3644": "psp_hash_count",
    "psp_hashes_3604": "psp_hashes_3604_count",
    "psp_hashes_3802": "psp_hashes_3802_count",
}


class Refusal(Exception):
    """L1/L2/L3 refusal — loud, claimed, exit 2."""


# ---------------------------------------------------------------- loading

def _load_mod(name):
    key = f"_{name}"
    if key not in _M:
        path = os.path.join(HERE, name + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        _M[key] = m
    return _M[key]


def _mods():
    """(fw38, fw40, fw42, fw45) — the four surfaces the fusion sits on.
    fw46 sits on top, never instead: the exam, the weld, the triptych
    and the lens layer are consumed, not re-implemented."""
    return (_load_mod("fw38-exam"), _load_mod("fw40-merge"),
            _load_mod("fw42-dossier"), _load_mod("fw45-b550-lens"))


def _reg(path):
    if not os.path.exists(path):
        raise Refusal(f"missing register {os.path.basename(path)} — the "
                      "frozen surface is the only basis this instrument "
                      "accepts")
    with open(path) as f:
        return json.load(f)


def lens_register():
    return _reg(_LENS_REG)


def autodossier_register():
    return _reg(_REG)


# ---------------------------------------------------------------- marks

def marks_for(props, exp, set_anchors=None):
    """Per-slot anchor marks. Set slots compare SETS when a set anchor
    is registered (added/removed deltas made visible); otherwise they
    fall back to the ring-45 count anchor (kind=count, the
    count-blind convention this ring corrects). Scalars compare
    identity against the day0_lens_expectation.stock_3644 row."""
    set_anchors = set_anchors or {}
    out = {}
    for k in sorted(props):
        v = props[k]
        if isinstance(v, list):
            if k in set_anchors:
                a = set(set_anchors[k])
                p = set(v)
                out[k] = {
                    "status": "==" if p == a else "!=",
                    "kind": "set",
                    "proposed_count": len(p), "anchor_count": len(a),
                    "added": len(p - a), "removed": len(a - p),
                }
            elif COUNT_FALLBACK.get(k) in exp:
                n = exp[COUNT_FALLBACK[k]]
                out[k] = {
                    "status": "==" if len(v) == n else "!=",
                    "kind": "count", "proposed_count": len(v),
                    "anchor": n,
                    "note": "count anchor — set-blind (ring-45 "
                            "convention); register the set to see "
                            "added/removed",
                }
            else:
                out[k] = {"status": "no-anchor", "kind": "set",
                          "proposed_count": len(v)}
        else:
            if k in exp:
                out[k] = {"status": "==" if v == exp[k] else "!=",
                          "kind": "scalar", "proposed": v,
                          "anchor": exp[k]}
            else:
                out[k] = {"status": "no-anchor", "kind": "scalar",
                          "proposed": v}
    return out


# ---------------------------------------------------------------- compose

def compose(props, omitted, corrections, f40):
    """L1 composition: corrections beat proposals, per slot, journaled.
    A correction outside LENS_ONLY or aimed at a judge-owned slot is a
    refusal (the ring-40 separation law is not the operator's to
    lift). A correction on an OMITTED slot lands — that is the review
    moment working. Returns (lenses, journal)."""
    corrections = corrections or {}
    unknown = sorted(set(corrections) - set(f40.LENS_ONLY))
    judge_hit = sorted(set(unknown) & set(f40.JUDGE_FILLS))
    if judge_hit:
        raise Refusal(f"L1: corrections on judge-owned slots: "
                      f"{judge_hit} — the judge fills those from "
                      "fw39-identify; the operator reviews, the judge "
                      "owns")
    if unknown:
        raise Refusal(f"L1: corrections outside LENS_ONLY: {unknown} — "
                      f"LENS_ONLY is {sorted(f40.LENS_ONLY)}")
    lenses, journal = {}, {}
    for k in sorted(f40.LENS_ONLY):
        if k in corrections:
            lenses[k] = corrections[k]
            journal[k] = "operator_correction"
        elif k in props:
            lenses[k] = props[k]
            journal[k] = "proposal"
        # neither -> absent from the lenses (L3; the weld loud-degrades)
    return lenses, journal


# ---------------------------------------------------------------- fused

def _set_anchors_or_none():
    """The registered PSP set anchors (present after ring-46
    registration). Absent register -> None (marks fall back to the
    count convention; the fused mode says so, loudly)."""
    if not os.path.exists(_REG):
        return None
    r = _reg(_REG)
    return r.get("psp_set_anchors") or None


def _print_review(image, target, stage1, marks_src):
    props, omitted = stage1["proposals"], stage1["omitted"]
    mk, journal = stage1["marks"], stage1["journal"]
    ncorr = sum(1 for v in journal.values()
                if v == "operator_correction")
    print(f"fused {os.path.basename(image)} target={target}  [fw46, "
          f"marks vs {marks_src}]")
    print(f"  stage1 propose: {len(props)} slots proposed, "
          f"{len(omitted)} omitted  [fw45 L2-transfer gates ran first]")
    for k in sorted(props):
        m = mk.get(k, {})
        st = m.get("status", "?")
        kind = m.get("kind", "?")
        if kind == "set":
            print(f"    {k:<30} {st}  (set {m['proposed_count']} vs "
                  f"{m['anchor_count']}, added {m['added']}, "
                  f"removed {m['removed']})")
        elif kind == "count":
            print(f"    {k:<30} {st}  (count {m['proposed_count']} vs "
                  f"{m['anchor']}) — set-blind convention")
        elif kind == "scalar":
            print(f"    {k:<30} {st}  ({m['proposed']} vs "
                  f"{m['anchor']})")
        else:
            print(f"    {k:<30} {st}")
    for k in sorted(omitted):
        print(f"    OMIT {k:<26} {omitted[k]}")
    print(f"  journal: {sum(1 for v in journal.values() if v == 'proposal')}"
          f" proposal, {ncorr} operator_correction "
          f"(L1: corrections beat proposals, always)")
    if journal:
        for k in sorted(journal):
            if journal[k] == "operator_correction":
                print(f"    corrected {k} = "
                      f"{json.dumps(stage1['lenses_composed'][k])[:80]}")
    print("  law L1: a proposal is not a measurement — pass corrected "
          "values as --lenses on the next run; they win.")


def fused(image, target="day0", corrections=None, review_only=False,
          out=None, quiet=False):
    """The ONE day-0 command. L2 first (fw45.propose re-derives every
    anchor or refuses), then marks, then L1 composition, then — unless
    --review-only — the fw42 triptych dossier with the composed
    lenses. Returns (stage1, dossier_or_None)."""
    _f38, f40, f42, f45 = _mods()
    if target not in ("day0", "release41"):
        raise Refusal(f"unknown target {target!r}")

    # --- L2 calibration-before-fusion (propose refuses on a broken
    #     basis; nothing downstream runs)
    props, omitted, prov = f45.propose(image, out=None)

    # --- the anchor marks (set anchors when registered)
    exp = f45.lens_register().get("day0_lens_expectation", {}) \
                            .get("stock_3644", {})
    sets = _set_anchors_or_none()
    marks_src = ("vendor-autodossier-register.json set anchors"
                 if sets else "count fallback (register absent)")
    mk = marks_for(props, exp, sets)

    # --- L1 composition (corrections beat proposals)
    lenses, journal = compose(props, omitted, corrections, f40)

    stage1 = {"proposals": props, "omitted": omitted,
              "provenance": prov, "marks": mk,
              "marks_source": marks_src, "journal": journal,
              "lenses_composed": lenses,
              "expectation_source": "vendor-b550-lens.json "
                                    "day0_lens_expectation.stock_3644"}
    _print_review(image, target, stage1, marks_src)
    if review_only:
        if out:
            _write_doc(out, {"instrument": "fw46-autodossier",
                             "ring": RING, "mode": "review-only",
                             "image": os.path.abspath(image),
                             "target": target, "stage1": stage1})
        return stage1, None

    # --- the triptych (fw42 unchanged; Refusal classes are per-module
    #     — the ring-42 boundary lesson — so every downstream loud
    #     error is re-claimed as THIS module's refusal, never swallowed)
    try:
        d, merged = f42.dossier(image, lenses=lenses, target=target)
    except Refusal:
        raise
    except Exception as e:
        raise Refusal(f"fused refused: the dossier chain raised "
                      f"{type(e).__name__}: {e}")

    if out:
        _write_doc(out, {"instrument": "fw46-autodossier",
                         "ring": RING, "mode": "fused",
                         "image": os.path.abspath(image),
                         "target": target, "stage1": stage1,
                         "dossier": d, "findings": merged})
    if quiet:
        f42.show_summary(d)
    else:
        f42.show(d)
    return stage1, d


def _write_doc(path, doc):
    """The ONLY write sites of this instrument (L4; grep-policed by
    gate R4)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
    print(f"written: {path}")


# ---------------------------------------------------------------- selftest

def selftest():
    """Two-tier gates. Tier R: the laws, the mark/compose KATs, the
    register well-formedness, the zero-writes police. Tier I live: the
    anchors re-derive through propose on the ref target, the
    discriminator fires BOTH ways on 3645 (set != while count ==),
    corrections beat proposals through the real weld, and the CROWN —
    the full fused dossier on b550w2-3644.rom, the day-0 chain in one
    call, its scoreline confronted to the registered measurement."""
    _f38, f40, f42, f45 = _mods()
    ok = [0]
    fails = []

    def gate(name, cond, detail=""):
        if cond:
            ok[0] += 1
            print(f"  PASS {name}")
        else:
            fails.append(name)
            print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))

    def refused(name, fn, want=()):
        try:
            fn()
            gate(name, False, "no refusal raised")
        except Refusal as e:
            gate(name, not want or any(w in str(e) for w in want),
                 str(e))
        except Exception as e:
            gate(name, False,
                 f"wrong error class {type(e).__name__}: {e}")

    src = open(os.path.abspath(__file__), encoding="utf-8").read()

    # ---------------- tier R
    print("tier R — the laws, the KATs, the register")
    try:
        exp = f45.lens_register().get("day0_lens_expectation", {}) \
                                .get("stock_3644", {})
        gate("R1 the 7 LENS_ONLY slots all anchor (3 sets + 4 scalars)",
             set(SET_SLOTS) == set(COUNT_FALLBACK)
             and {COUNT_FALLBACK.get(k, k) for k in f40.LENS_ONLY}
             <= set(exp)
             and len(f40.LENS_ONLY) == 7,
             f"set={SET_SLOTS} fallback={COUNT_FALLBACK}")
    except Exception as e:
        gate("R1 the 7 LENS_ONLY slots all anchor", False, str(e))

    exp_kat = {"ifr_questions_total": 14431,
               "ifr_valid_fraction": 1.0,
               "psp_hash_count": 203,
               "setup_uncovered_bytes": 161,
               "varstore_uncovered_share_pct": 85.73}
    try:
        mk = marks_for({"ifr_questions_total": 14431}, exp_kat)
        gate("R2 scalar mark ==",
             mk["ifr_questions_total"]["status"] == "=="
             and mk["ifr_questions_total"]["kind"] == "scalar")
        mk = marks_for({"ifr_questions_total": 9999}, exp_kat)
        gate("R2b scalar mark !=",
             mk["ifr_questions_total"]["status"] == "!="
             and mk["ifr_questions_total"]["anchor"] == 14431)
        mk = marks_for({"psp_hashes_3644": ["a", "b"]},
                       exp_kat, {"psp_hashes_3644": ["a", "b"]})
        gate("R2c set mark == (added 0, removed 0)",
             mk["psp_hashes_3644"]["status"] == "=="
             and mk["psp_hashes_3644"]["added"] == 0
             and mk["psp_hashes_3644"]["removed"] == 0)
        mk = marks_for({"psp_hashes_3644": ["a", "c"]},
                       exp_kat, {"psp_hashes_3644": ["a", "b"]})
        gate("R2d set mark != with deltas (1/1)",
             mk["psp_hashes_3644"]["status"] == "!="
             and mk["psp_hashes_3644"]["added"] == 1
             and mk["psp_hashes_3644"]["removed"] == 1)
        mk = marks_for({"psp_hashes_3644": list(range(203))}, exp_kat)
        gate("R2e count fallback kind=count (the blind convention)",
             mk["psp_hashes_3644"]["status"] == "=="
             and mk["psp_hashes_3644"]["kind"] == "count"
             and mk["psp_hashes_3644"]["anchor"] == 203)
        mk = marks_for({"mystery_slot": 3}, exp_kat)
        gate("R2f unknown slot -> no-anchor (never invented)",
             mk["mystery_slot"]["status"] == "no-anchor")
    except Exception as e:
        gate("R2 marks KATs", False, str(e))

    props_kat = {"setup_uncovered_bytes": 161,
                 "psp_hashes_3644": ["a"]}
    try:
        lenses, journal = compose(props_kat, {}, {}, f40)
        gate("R3 defaults: proposals compose, journaled proposal",
             lenses == props_kat
             and set(journal.values()) == {"proposal"})
        lenses, journal = compose(props_kat, {},
                                  {"setup_uncovered_bytes": 999}, f40)
        gate("R3b correction wins, journaled operator_correction (L1)",
             lenses["setup_uncovered_bytes"] == 999
             and journal["setup_uncovered_bytes"]
             == "operator_correction"
             and journal["psp_hashes_3644"] == "proposal")
        refused("R3c correction outside LENS_ONLY refused",
                lambda: compose(props_kat, {}, {"nope": 1}, f40),
                want=["LENS_ONLY"])
        refused("R3d correction on judge-owned slot refused",
                lambda: compose(props_kat, {},
                                {f40.JUDGE_FILLS[0]: 1}, f40),
                want=["judge-owned"])
        lenses, journal = compose(
            {}, {"setup_uncovered_bytes": "no Setup row (L3 loud)"},
            {"setup_uncovered_bytes": 5}, f40)
        gate("R3e correction on an OMITTED slot lands (the review "
             "moment working)",
             lenses.get("setup_uncovered_bytes") == 5
             and journal.get("setup_uncovered_bytes")
             == "operator_correction")
    except Exception as e:
        gate("R3 compose KATs", False, str(e))

    wpat = 'open(path, ' + '"w"'
    n_writes = src.count(wpat)
    gate("R4 L4 zero-writes: exactly ONE write site (_write_doc)",
         n_writes == 1 and 'def _write_doc' in src,
         f"write sites={n_writes}")
    gate("R4b the four laws stated in source",
         all(s in src for s in
             ("L1 CORRECTIONS-BEAT-PROPOSALS", "L2 CALIBRATION-BEFORE"
              "-FUSION", "L3 LOUD DEGRADATION", "L4 ZERO WRITES")))

    try:
        reg = autodossier_register()
        fs = reg.get("fused_stock_3644", {})
        sc = fs.get("scoreline", {})
        gate("R5 register: crown scoreline 6/1/10/9",
             (sc.get("hit"), sc.get("partial"), sc.get("miss"),
              sc.get("na")) == (6, 1, 10, 9), str(sc))
        gate("R5b crown hit/partial sets",
             sorted(fs.get("hit_set") or [])
             == ["P-03", "P-06", "P-08", "P-13", "P-16", "P-18"]
             and sorted(fs.get("partial_set") or []) == ["P-15"])
        gate("R5c crown journal 7 proposal / 0 correction",
             sum(1 for v in (fs.get("journal") or {}).values()
                 if v == "proposal") == 7
             and sum(1 for v in (fs.get("journal") or {}).values()
                     if v == "operator_correction") == 0)
        gate("R5d crown marks all == (the stock basis)",
             fs.get("marks_all_equal") is True)
        gate("R5e crown identity == the ring-44 stranger point",
             fs.get("identity_verdict") == "no-match-h3-eligible"
             and fs.get("identity_coupling") == "coherent-foreign"
             and fs.get("profile") == "stranger")
        sa = reg.get("psp_set_anchors", {})
        gate("R5f set anchors 203/194/193",
             [len(sa.get(k) or []) for k in SET_SLOTS]
             == [203, 194, 193],
             str({k: len(sa.get(k) or []) for k in SET_SLOTS}))
        disc = reg.get("discriminator_3645", {})
        gate("R5g discriminator: set != 37/37 AND count == 203 "
             "(count-blindness asserted both ways)",
             disc.get("psp_set_mark") == "!="
             and disc.get("added") == 37 and disc.get("removed") == 37
             and disc.get("count_mark") == "=="
             and disc.get("proposed_count") == 203
             and disc.get("anchor_count") == 203,
             str(disc))
        gate("R5h measured_vs_derived agree (6/1/10/9 was derived in "
             "ring 45, measured here)",
             reg.get("measured_vs_derived", {}).get("agreement")
             == "agree")
    except Refusal as e:
        gate("R5 register well-formed", False, f"REFUSAL {e}")
    except Exception as e:
        gate("R5 register well-formed", False, str(e))

    try:
        imgs = f45.lens_register().get("images", {})
        gate("R6 ref/discriminator sha16 == the ring-44 acquisitions",
             imgs.get(REF_TARGET, {}).get("rom_sha256_16")
             == "5f7a0e439772c160"
             and imgs.get(DISC_TARGET, {}).get("rom_sha256_16")
             == "0a1b5bda5be78e4b",
             str({k: imgs.get(k, {}).get("rom_sha256_16")
                  for k in (REF_TARGET, DISC_TARGET)}))
    except Exception as e:
        gate("R6 ref/discriminator sha16", False, str(e))

    # ---------------- tier I (live)
    print("tier I — live: propose, discriminate, compose, crown")
    files = f45.acq_files()
    ref, disc_img = files.get(REF_TARGET), files.get(DISC_TARGET)
    gate("I0 acquisitions on disk (ring-44 vendor-verified)",
         bool(ref) and os.path.exists(ref) and bool(disc_img)
         and os.path.exists(disc_img),
         f"ref={ref} disc={disc_img}")

    props_ref = omitted_ref = mk_ref = None
    try:
        props_ref, omitted_ref, _prov = f45.propose(ref, out=None)
        exp = f45.lens_register().get("day0_lens_expectation", {}) \
                                .get("stock_3644", {})
        mk_ref = marks_for(props_ref, exp, _set_anchors_or_none())
        gate("I1 propose ref target: 7/7 slots, 0 omitted",
             len(props_ref) == 7 and not omitted_ref,
             f"{len(props_ref)} props, {len(omitted_ref)} omitted")
        gate("I1b every ref mark == (added 0 / removed 0 on the sets)",
             all(m["status"] == "==" for m in mk_ref.values())
             and all(mk_ref[k]["added"] == 0
                     and mk_ref[k]["removed"] == 0 for k in SET_SLOTS),
             str({k: v["status"] for k, v in mk_ref.items()}))
    except Exception as e:
        gate("I1 propose on the ref target", False, str(e))

    try:
        props_d, _o, _p = f45.propose(disc_img, out=None)
        exp = f45.lens_register().get("day0_lens_expectation", {}) \
                                .get("stock_3644", {})
        mk_d = marks_for(props_d, exp, _set_anchors_or_none())
        m = mk_d["psp_hashes_3644"]
        gate("I2 THE DISCRIMINATOR: 3645 set mark != 37/37",
             m["status"] == "!=" and m["added"] == 37
             and m["removed"] == 37, str(m))
        gate("I2b COUNT-BLINDNESS: the same proposal counts == 203 "
             "(a count anchor would have hidden the discriminator)",
             m["proposed_count"] == 203 and m["anchor_count"] == 203)
        quartet = ("ifr_questions_total", "ifr_valid_fraction",
                   "setup_uncovered_bytes",
                   "varstore_uncovered_share_pct")
        gate("I2c release IFR identity: the quartet marks ==",
             all(mk_d[k]["status"] == "==" for k in quartet),
             str({k: mk_d[k]["status"] for k in quartet}))
    except Exception as e:
        gate("I2 discriminator on 3645", False, str(e))

    try:
        corr = {"setup_uncovered_bytes": 999}
        lenses, journal = compose(props_ref, omitted_ref, corr, f40)
        gate("I3 live compose: 6 proposal + 1 operator_correction",
             sum(1 for v in journal.values() if v == "proposal") == 6
             and sum(1 for v in journal.values()
                     if v == "operator_correction") == 1)
        _eo, draft = _f38.exam(ref, target="day0-3644", geometry=False)
        merged, rep = f40.weld(draft, None, lenses=lenses,
                               target="day0")
        gate("I3b the corrected value lands through the real weld",
             merged.get("setup_uncovered_bytes") == 999
             and str(rep.get("provenance", {}).get(
                 "setup_uncovered_bytes", "")).startswith("lens"))
        merged2, _rep2 = f40.weld(
            draft, None,
            lenses=compose(props_ref, omitted_ref, None, f40)[0],
            target="day0")
        landed = [k for k in props_ref if merged2.get(k) == props_ref[k]]
        gate("I3c pure proposals: 7/7 survive the weld unchanged",
             len(landed) == 7, f"landed {len(landed)}/7")
    except Exception as e:
        gate("I3 compose + weld on B550", False, str(e))

    tmpdir = tempfile.TemporaryDirectory()
    try:
        tmpdoc = os.path.join(tmpdir.name, "crown.json")
        stage1, d = fused(ref, target="day0", corrections=None,
                          out=tmpdoc, quiet=True)
        counts = d["readings"]["oracle"]["counts"]
        gate("I4 THE CROWN: fused stock-3644 scoreline 6/1/10/9",
             (counts.get("hit"), counts.get("partial"),
              counts.get("miss"), counts.get("na")) == (6, 1, 10, 9),
             str(counts))
        rows = d["readings"]["oracle"]["rows"]
        hits = sorted(r["id"] for r in rows if r["verdict"] == "hit")
        partials = sorted(r["id"] for r in rows
                          if r["verdict"] == "partial")
        gate("I4b hit set {P-03,P-06,P-08,P-13,P-16,P-18} + "
             "partial {P-15}",
             hits == ["P-03", "P-06", "P-08", "P-13", "P-16", "P-18"]
             and partials == ["P-15"],
             f"hits={hits} partial={partials}")
        coh = d["coherence"]
        gate("I4c identity/coupling/profile == the stranger point",
             d["readings"]["identity"]["verdict"]
             == "no-match-h3-eligible"
             and coh["identity_coupling"] == "coherent-foreign"
             and coh["profile"] == "stranger")
        gate("I4d stage1 marks all == and journal 7 proposal",
             all(m["status"] == "=="
                 for m in stage1["marks"].values())
             and set(stage1["journal"].values()) == {"proposal"})
        rep = d.get("weld_report", {})
        prov_ok = all(str(rep.get("provenance", {}).get(k, ""))
                      .startswith("lens") for k in f40.LENS_ONLY)
        gate("I4e the weld journals the 7 composed lenses (L1)",
             prov_ok, str({k: rep.get("provenance", {}).get(k)
                           for k in sorted(f40.LENS_ONLY)}))
        gate("I5 artifact roundtrip (mode/journal/dossier coherent)",
             _reload_check(tmpdoc))
    except Exception as e:
        gate("I4 the crown fused dossier", False, str(e))
    finally:
        tmpdir.cleanup()

    total = ok[0] + len(fails)
    print(f"fw46-autodossier selftest: {ok[0]}/{total} gates "
          f"{'PASS' if not fails else 'FAIL'}")
    if fails:
        for f in fails:
            print(f"  FAILED GATE: {f}")
    return 0 if not fails else 1


def _reload_check(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return (doc.get("mode") == "fused"
            and doc.get("instrument") == "fw46-autodossier"
            and set(doc.get("stage1", {}).get("journal", {}).values())
            == {"proposal"}
            and doc.get("dossier", {}).get("readings", {})
            .get("oracle", {}).get("counts", {}).get("hit") == 6
            and doc.get("stage1", {}).get("proposals", {})
            .get("psp_hashes_3644"))


# ---------------------------------------------------------------- manifest

def manifest():
    """The instrument's self-description (the fw35 manifest law)."""
    modes = ["fused <image> [--target day0|release41] [--lenses "
             "corrections.json] [--review-only] [--out out.json] "
             "[--quiet]", "selftest", "manifest"]
    regs = {
        "basis": "vendor-b550-lens.json (ring 45: the 57 B550 anchor "
                 "rows + 10 shared B450 rows + day0_lens_expectation)",
        "this_ring": "vendor-autodossier-register.json (the crown "
                     "measurement + the PSP SET anchors + the "
                     "discriminator both-ways)",
        "upstream": ["vendor-ledger-b550w2.json (ring 44: the "
                     "acquisitions + the stranger point)",
                     "vendor-oracle.json (ring 35: the frozen 26)"],
    }
    print(json.dumps({
        "instrument": "fw46-autodossier", "ring": RING,
        "title": "the auto-dossier: the day-0 chain fused into one "
                 "command, measured",
        "modes": modes,
        "laws": ["L1 corrections-beat-proposals",
                 "L2 calibration-before-fusion",
                 "L3 loud degradation", "L4 zero writes"],
        "chain": ["fw45.propose (L2-transfer gates)",
                  "marks_for (set anchors vs stock-3644)",
                  "compose (L1 journal)",
                  "fw42.dossier (the triptych + coherence)"],
        "registers": regs,
        "discriminator_law": "the PSP set separates 3644 from 3645 "
                             "(37/37 inside a 203-hash set); the IFR "
                             "quartet cannot — the count anchor is "
                             "blind to it, the set anchor is not",
    }, indent=1))
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="fw46-autodossier")
    ap.add_argument("mode", choices=["fused", "selftest", "manifest"])
    ap.add_argument("image", nargs="?", default=None)
    ap.add_argument("--target", choices=["day0", "release41"],
                    default="day0")
    ap.add_argument("--lenses", dest="lenses_path", default=None)
    ap.add_argument("--review-only", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if a.mode == "manifest":
        return manifest()
    if a.mode == "selftest":
        return selftest()

    if not a.image:
        print("fused <image> [--review-only] [--lenses corrections.json]"
              " [--out out.json]", file=sys.stderr)
        return 2
    corrections = None
    if a.lenses_path:
        try:
            with open(a.lenses_path, encoding="utf-8") as f:
                corrections = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"REFUSAL: cannot read the corrections file "
                  f"{a.lenses_path}: {e}", file=sys.stderr)
            return 2
    try:
        fused(a.image, target=a.target, corrections=corrections,
              review_only=a.review_only, out=a.out, quiet=a.quiet)
        return 0
    except Refusal as e:
        print(f"REFUSAL: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
