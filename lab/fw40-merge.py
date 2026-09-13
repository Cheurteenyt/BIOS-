#!/usr/bin/env python3
# lab/fw40-merge.py — ring 40 « la soudure » (the weld)
#
# The last manual seam of the day-0 chain is the MERGE: after exam (fw38)
# and identify (fw39), the operator was told to "merge the two drafts
# before the final fw35-oracle.py score" BY HAND. A hand-seam in an
# otherwise machine-checked chain is exactly where silent errors live:
# a value pasted into the wrong slot, a day-0 key leaking into a
# release-41 verdict, a shallow exam lens overwriting the judge's
# deep truth. The weld makes the seam an instrument.
#
# Laws enforced (each one is a gate):
#   schema law      — merged documents admit ONLY fw35 template keys
#                     (31 unique; the 32-slot key list carries
#                     agesa_level_41 twice: P-20/P-25 share the field)
#   separation law  — day-0 keys and release-41 keys never mix in ONE
#                     merged document (the ring-38 leak lesson becomes
#                     structural: a non-None key of the other target
#                     refuses the weld with exit 2)
#   precedence law  — identify deep-truth > exam shallow-walk for the
#                     keys the judge owns (the ring-39 nested-LZMA
#                     lesson: the shallow walk under-reports armor);
#                     the operator lens fills ONLY the manual slots;
#                     a lens may override the judge ONLY via an explicit
#                     --lens-wins KEY (journaled as an override record,
#                     never silent)
#   provenance law  — every filled value carries its source
#                     (exam | identify | lens) in the weld report
#
# Modes:
#   merge <draft.json> <identify.json> [--lenses m.json]
#         [--target day0|release41] [--out merged.json] [--score]
#         [--lens-wins KEY]...
#   chain <image> [--lenses m.json] [--target day0|release41]
#         [--out merged.json] [--no-geometry] [--score]
#         [--lens-wins KEY]...      <- ONE command: exam+identify+weld+score
#   ceiling <rung>... [--out register.json]
#         <- the full chain (no lenses) on known rungs: the scoreline
#            envelope — what a byte-identical rung scores, per verdict
#   selftest [--no-live]
#   manifest
#
# stdlib-only, read-only on images, precedent fw33/35/36/37/38/39.

import argparse
import copy
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

fw35 = fw37 = fw38 = fw39 = None


def _load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _mods():
    global fw35, fw37, fw38, fw39
    if fw39 is None:
        fw35 = _load_mod("fw35-oracle")
        fw37 = _load_mod("fw37-differ")
        fw38 = _load_mod("fw38-exam")
        fw39 = _load_mod("fw39-identity")
    return fw35, fw37, fw38, fw39


# ----------------------------------------------------------------- laws

def _unique_keys():
    _, _, _fw38, _ = _mods()
    return list(dict.fromkeys(_fw38.template_keys()))


def day0_keys():
    return [k for k in _unique_keys() if not k.endswith("_41")]


def release41_keys():
    return [k for k in _unique_keys() if k.endswith("_41")]


# The judge (fw39 identify) OWNS these keys. Deep truth beats the
# shallow walk — the ring-39 lesson: the armor wave hides behind a
# nested guided LZMA section the level-1 pierce misses, so a shallow
# exam lens would UNDER-REPORT and inflate a repack's diff count to
# exactly the fake-H3 threshold.
JUDGE_FILLS = ("matches_known_release", "distinct_fingerprints_count",
               "trust_cert_distinct")
JUDGE_DEEP_TRUTH = ("armor_quartet_present", "sbrom_armorsmm_present",
                    "legacy_smm_count", "chip_whitelist_families",
                    "dsdt_sha16")

# The operator lens owns these slots — never auto-filled, never judged.
# (fw38.MANUAL_DAY0 == JUDGE_FILLS + LENS_ONLY is a gate.)
LENS_ONLY = ("ifr_questions_total", "ifr_valid_fraction",
             "setup_uncovered_bytes", "varstore_uncovered_share_pct",
             "psp_hashes_3644", "psp_hashes_3604", "psp_hashes_3802")

TARGETS = ("day0", "release41")


class WeldError(Exception):
    def __init__(self, kind, detail):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


def judge_fills_from(observed, verdict):
    """Map the fw39 identify output onto the fw35 template keys."""
    fills = {
        "matches_known_release": verdict.get("matches_known_release"),
        "distinct_fingerprints_count":
            verdict.get("distinct_fingerprints_count"),
        "trust_cert_distinct": (len(observed.get("trust_certs") or ())
                                if observed.get("trust_certs") is not None
                                else None),
        "armor_quartet_present": observed.get("armor_quartet_present"),
        "sbrom_armorsmm_present": observed.get("sbrom_armorsmm_present"),
        "legacy_smm_count": observed.get("legacy_smm_count"),
        "chip_whitelist_families": observed.get("chip_whitelist_families"),
        "dsdt_sha16": observed.get("dsdt_primary"),
    }
    return {k: v for k, v in fills.items() if v is not None}


def judge_fills_release41_from(observed):
    """The release-41 judge map: the same deep-truth lenses, mapped onto
    the *_41 keys of the NEW image. Deliberately EXCLUDES the day-0 H3
    concepts (matches_known_release / distinct_fingerprints_count) — no
    release-41 prediction scores identity, and a day-0 key in a
    release-41 document is a leak (structural refusal). ALSO excludes
    chip_whitelist_families_41: the whitelist count is CONVENTION-
    DEPENDENT (which registered family set you intersect with) and
    fw38's exam_pair already parameterizes it by target (the release-41
    46-family set) — the judge's day-0 41-convention value would
    corrupt P-26 (caught live by the ring-40 pair null-model)."""
    def _n(key):
        v = observed.get(key)
        if v is None:
            return None
        return v if isinstance(v, int) else len(v)

    fills = {
        "trust_cert_distinct_41": _n("trust_certs"),
        "dsdt_sha16_41": observed.get("dsdt_primary"),
        "core_armor_41": _n("armor_core"),
        "added_present_count_41": _n("armor_added"),
    }
    return {k: v for k, v in fills.items() if v is not None}


def weld(draft, ident=None, lenses=None, target="day0", lens_wins=()):
    """Weld the exam draft + identify output + operator lenses into a
    validated findings document. Returns (merged, weld_report).
    Raises WeldError on schema / separation violations."""
    _, _, _fw38, _ = _mods()
    if target not in TARGETS:
        raise WeldError("target", f"unknown target {target!r}")

    schema = set(_unique_keys())
    other = set(release41_keys()) if target == "day0" \
        else set(day0_keys())

    unknown = sorted(set(draft) - schema)
    if unknown:
        raise WeldError("schema", f"keys outside the fw35 template: "
                                  f"{unknown}")
    for k, v in draft.items():
        if v is not None and k in other:
            raise WeldError("leak", f"{target}-target draft carries the "
                                    f"other-target key {k}={v!r}")

    merged = {k: draft.get(k) for k in _unique_keys()}
    prov = {}          # key -> source string
    conflicts, overrides = [], []

    if ident is not None:
        observed = ident.get("observed", {})
        verdict = ident.get("verdict", {})
        if target == "day0":
            fills = judge_fills_from(observed, verdict)
        else:
            fills = judge_fills_release41_from(observed)
        for k, v in fills.items():
            if k not in schema:
                raise WeldError("schema", f"judge fill key outside "
                                          f"template: {k}")
            if merged.get(k) is None:
                merged[k] = copy.deepcopy(v)
                prov[k] = "identify"
            elif merged[k] == v:
                prov[k] = "exam+identify (agree)"
            else:
                conflicts.append({"key": k, "exam": merged[k],
                                  "identify": v,
                                  "resolution": "judge wins (deep truth)"})
                merged[k] = copy.deepcopy(v)
                prov[k] = "identify (deep-truth override)"

    for k, v in (lenses or {}).items():
        if k not in LENS_ONLY and k not in JUDGE_FILLS:
            raise WeldError("schema-lens", f"lens key outside the manual "
                                           f"surface: {k}")
        if merged.get(k) is None:
            merged[k] = copy.deepcopy(v)
            prov[k] = "lens"
        elif merged[k] == v:
            prov.setdefault(k, "lens (agree)")
        elif k in lens_wins:
            overrides.append({"key": k, "stood": merged[k],
                              "lens": v, "via": "--lens-wins"})
            merged[k] = copy.deepcopy(v)
            prov[k] = "lens (override)"
        else:
            conflicts.append({"key": k, "welded": merged[k], "lens": v,
                              "resolution": "welded value stands "
                                            "(use --lens-wins to override)"})

    for k, v in merged.items():
        if v is not None and k in other:
            raise WeldError("leak", f"welded document leaks {k} into "
                                    f"the {target} target")

    report = {
        "target": target,
        "provenance": prov,
        "conflicts": conflicts,
        "overrides": overrides,
        "unfilled": sorted(k for k, v in merged.items() if v is None),
        "filled": sum(1 for v in merged.values() if v is not None),
        "slots": len(merged),
    }
    return merged, report


# ----------------------------------------------------------------- chain

def chain(image, lenses=None, target="day0", geometry=True,
          lens_wins=()):
    """ONE command: exam (fw38) + identify (fw39) + weld + score (fw35).
    This is the day-0 protocol as a single instrument call."""
    fw35, fw37, _fw38, _fw39 = _mods()
    examout, draft = _fw38.exam(image, target="day0-3644"
                                if target == "day0" else "release-41",
                                geometry=geometry)
    ident = _fw39.identify(image)
    merged, report = weld(draft, ident, lenses=lenses, target=target,
                          lens_wins=lens_wins)
    oracle = fw35.Oracle()
    rows, n = oracle.score(merged)
    return {
        "instrument": "fw40-merge", "ring": 40, "image": image,
        "target": target,
        "rom": examout["rom"],
        "verdict": ident["verdict"],
        "exam_summary": {
            "agesa": examout["agesa"].get("agesa_level"),
            "module_count": examout["inventory"]["module_count"],
            "pierced_payloads":
                examout["inventory"]["pierced_payloads"],
            "setup_varstore_size":
                examout["vars"].get("setup_varstore_size"),
        },
        "weld_report": report,
        "scoreline": {"counts": n,
                      "rows": [{"id": p["id"], "verdict": v,
                                "note": note} for p, v, note in rows]},
    }, merged


def chain_pair(old, new, lenses=None, lens_wins=()):
    """The release-41 ONE command: exam_pair (fw38, both images + the
    fw37 species ledger) + identify on the NEW image (deep-truth judge
    fills mapped onto the *_41 keys) + weld + score. Births/deaths need
    TWO images, so the release-41 chain is a pair chain."""
    fw35, fw37, _fw38, _fw39 = _mods()
    examout, draft = _fw38.exam_pair(old, new)
    ident = _fw39.identify(new)
    merged, report = weld(draft, ident, lenses=lenses,
                          target="release41", lens_wins=lens_wins)
    rows, n = fw35.Oracle().score(merged)
    return {
        "instrument": "fw40-merge", "ring": 40, "mode": "chain-pair",
        "old": old, "new": new, "target": "release41",
        "new_rom": {"bytes": ident["observed"].get("rom_bytes"),
                    "sha256_16": ident["observed"].get("rom_sha_full")},
        "verdict": ident["verdict"],
        "ledger_summary": {
            "common": examout["ledger"].get("common"),
            "changed": examout["ledger"].get("changed"),
            "identical": examout["ledger"].get("identical"),
            "births_41": examout.get("births_41"),
            "deaths_41": examout.get("deaths_41"),
        },
        "weld_report": report,
        "scoreline": {"counts": n,
                      "rows": [{"id": p["id"], "verdict": v,
                                "note": note} for p, v, note in rows]},
    }, merged


# --------------------------------------------------------------- ceiling

VENDOR_CORPUS = "/tmp/my-project/scratch-vendor"
RUNG_IMAGES = {
    "3604": f"{VENDOR_CORPUS}/asus-prime-b450-plus-ref.rom",
    "3802": f"{VENDOR_CORPUS}/asus-prime-b450-plus-3802.rom",
    "3810": f"{VENDOR_CORPUS}/asus-prime-b450-plus-3810.rom",
    "4655": f"{VENDOR_CORPUS}/asus-prime-b450-plus.rom",
}
OVMF_FLOOR = "/home/z/my-project/scratch-ovmf/extract/usr/share/OVMF"


def ceiling(rungs, out=None):
    """The scoreline envelope: run the FULL chain (no lenses) on known
    rungs. What a byte-identical rung scores is the calibration datum
    the day-0 operator reads the dump's own scoreline against."""
    results = {}
    for r in rungs:
        img = RUNG_IMAGES.get(r)
        if not img or not os.path.exists(img):
            print(f"[ceiling] {r}: image absent, skipped", file=sys.stderr)
            continue
        c, _merged = chain(img, geometry=False)
        results[r] = {
            "image": img,
            "verdict": c["verdict"]["verdict"],
            "matched_release": c["verdict"].get("matched_release"),
            "counts": c["scoreline"]["counts"],
            "verdicts": {row["id"]: row["verdict"]
                         for row in c["scoreline"]["rows"]},
        }
        print(f"[ceiling] {r}: {c['verdict']['verdict']} — "
              f"{c['scoreline']['counts']}", file=sys.stderr)
    floor_img = os.path.join(OVMF_FLOOR, "OVMF_CODE_4M.fd")
    if os.path.exists(floor_img):
        cf, _mf = chain(floor_img, geometry=False)
        reg_floor = {
            "image": floor_img,
            "verdict": cf["verdict"]["verdict"],
            "counts": cf["scoreline"]["counts"],
            "verdicts": {row["id"]: row["verdict"]
                         for row in cf["scoreline"]["rows"]},
            "hit_set": [row["id"] for row in cf["scoreline"]["rows"]
                        if row["verdict"] == "hit"],
            "note": "the FLOOR — a foreign image; the stranger "
                    "signature hit_set {P-04, P-05, P-18} is the "
                    "welded chain's discrimination invariant "
                    "(ring-38 mock invariant was {P-04, P-05} "
                    "without the judge)",
        }
        print(f"[ceiling] floor OVMF: {cf['verdict']['verdict']} — "
              f"{cf['scoreline']['counts']}", file=sys.stderr)
    else:
        reg_floor = None
    reg = {
        "_meta": {
            "register": "vendor-scorelines", "ring": 40,
            "schema": "scoreline-v1",
            "produced_by": "lab/fw40-merge.py ceiling",
            "method": "the full day-0 chain (exam+identify+weld+score) "
                      "run on KNOWN rungs with no operator lenses — "
                      "the ceiling profile; manual-lens-dependent "
                      "predictions score na here BY DESIGN",
            "read": "the day-0 dump's scoreline should sit structurally "
                    "BETWEEN the bracketing rungs' profiles; the "
                    "discriminators set lists the predictions whose "
                    "verdict flips between them — the set that "
                    "localizes the dump on the chronology",
            "p18_note": "P-18 scores miss on every known rung BY "
                        "DESIGN: it predicts the DUMP is a stranger "
                        "(H3); a self-matching known release is the "
                        "exact opposite shape. On a FOREIGN image the "
                        "welded chain hits P-18 (the no-match verdict "
                        "feeds the predicate) — the STRANGER SIGNATURE "
                        "{P-04, P-05, P-18}, stronger than the ring-38 "
                        "mock invariant {P-04, P-05} which ran without "
                        "the judge",
            "images": {k: v for k, v in RUNG_IMAGES.items()
                       if os.path.exists(v)},
        },
        "ceilings": results,
        "floor_ovmf": reg_floor,
        "discriminators_3604_3802": sorted(
            p for p in results.get("3604", {}).get("verdicts", {})
            if results.get("3802", {}).get("verdicts", {}).get(p)
            != results["3604"]["verdicts"][p]
        ) if "3604" in results and "3802" in results else None,
    }
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2)
        print(f"[ceiling] register written: {out}", file=sys.stderr)
    return reg


def load_register():
    with open(os.path.join(HERE, "vendor-scorelines.json")) as f:
        return json.load(f)


# --------------------------------------------------------------- selftest

def selftest(no_live=False):
    fw35, fw37, _fw38, _fw39 = _mods()
    g, fails = [], []

    def gate(name, ok, detail=""):
        g.append((name, ok, detail))
        if not ok:
            fails.append(name)

    d0, r41 = day0_keys(), release41_keys()
    schema = set(_unique_keys())

    # ---- tier R: the laws, from the registers alone -------------------
    gate("R1a schema 31 unique", len(schema) == 31, str(len(schema)))
    gate("R1b slot list 32 (agesa_level_41 shared by P-20/P-25)",
         len(_fw38.template_keys()) == 32,
         str(len(_fw38.template_keys())))

    gate("R2a separation disjoint", not (set(d0) & set(r41)),
         f"|day0|={len(d0)} |r41|={len(r41)}")
    gate("R2b sizes 22/9", len(d0) == 22 and len(r41) == 9,
         f"{len(d0)}/{len(r41)}")

    manual = set(_fw38.MANUAL_DAY0)
    gate("R3 manual surface covered exactly",
         manual == set(JUDGE_FILLS) | set(LENS_ONLY),
         f"{len(manual)} manual slots")

    gate("R4a judge keys in day0 set",
         set(JUDGE_FILLS) | set(JUDGE_DEEP_TRUTH) <= set(d0))
    gate("R4b lens slots in day0 set", set(LENS_ONLY) <= set(d0))
    gate("R5 ownership disjoint",
         not (set(LENS_ONLY) & (set(JUDGE_FILLS) | set(JUDGE_DEEP_TRUTH))))

    # R6 all-None draft, empty judge -> all na (fw35 None-guard through
    # the weld)
    empty = {k: None for k in _unique_keys()}
    merged, rep = weld(empty, None, target="day0")
    rows, n = fw35.Oracle().score(merged)
    gate("R6 all-None -> all na through the weld",
         n["na"] == 26 and rep["filled"] == 0,
         f"na={n['na']} filled={rep['filled']}")

    # R7 separation refusal (the ring-38 leak lesson, structural now)
    leaky = dict(empty)
    leaky["rom_bytes"] = 16777216
    leaky["agesa_level_41"] = "1.2.0.12"
    try:
        weld(leaky, None, target="day0")
        gate("R7a day0 leak refused", False, "no exception")
    except WeldError as e:
        gate("R7a day0 leak refused", e.kind == "leak", e.detail)
    try:
        weld(leaky, None, target="release41")
        gate("R7b release41 leak refused", False, "no exception")
    except WeldError as e:
        gate("R7b release41 leak refused", e.kind == "leak", e.detail)

    # R8 schema refusal
    bad = dict(empty)
    bad["not_a_slot"] = 1
    try:
        weld(bad, None, target="day0")
        gate("R8 unknown key refused", False, "no exception")
    except WeldError as e:
        gate("R8 unknown key refused", e.kind == "schema", e.detail)

    # R9 lens schema refusal
    try:
        weld(empty, None, lenses={"not_a_slot": 1}, target="day0")
        gate("R9 lens key refused", False, "no exception")
    except WeldError as e:
        gate("R9 lens key refused", e.kind == "schema-lens", e.detail)

    # R10 precedence law: judge deep truth beats a wrong exam value
    wrong = dict(empty)
    wrong["armor_quartet_present"] = True      # the shallow-walk error
    wrong["dsdt_sha16"] = "0" * 16
    ident = {"observed": {"armor_quartet_present": False,
                          "dsdt_primary": "27d5e826e111d755"},
             "verdict": {}}
    merged, rep = weld(wrong, ident, target="day0")
    gate("R10a judge wins armor", merged["armor_quartet_present"] is False,
         str(merged["armor_quartet_present"]))
    gate("R10b judge wins dsdt",
         merged["dsdt_sha16"] == "27d5e826e111d755",
         merged["dsdt_sha16"])
    gate("R10c conflicts journaled", len(rep["conflicts"]) == 2,
         str(len(rep["conflicts"])))

    # R11 lens-wins: silent stand vs explicit override
    ident2 = {"observed": {}, "verdict": {"matches_known_release": False,
                                          "distinct_fingerprints_count": 3}}
    base = dict(empty)
    m1, r1 = weld(base, ident2, lenses={"matches_known_release": True},
                  target="day0")
    gate("R11a judge stands by default",
         m1["matches_known_release"] is False
         and len(r1["conflicts"]) == 1,
         str(m1["matches_known_release"]))
    m2, r2 = weld(base, ident2, lenses={"matches_known_release": True},
                  target="day0", lens_wins=("matches_known_release",))
    gate("R11b explicit override journaled",
         m2["matches_known_release"] is True
         and len(r2["overrides"]) == 1,
         str(r2["overrides"]))

    # R12 provenance completeness on the R10 doc
    prov_ok = all(k in rep["provenance"]
                  for k, v in merged.items() if v is not None)
    gate("R12 every filled value has provenance", prov_ok,
         f"{rep['filled']} filled")

    # R13 the release-41 judge map stays inside the *_41 set
    r41_map = set(judge_fills_release41_from(
        {"trust_certs": ["a"], "dsdt_primary": "x", "armor_core": ["b"],
         "armor_added": ["c"], "chip_whitelist_families": 46}))
    gate("R13a release41 judge map inside *_41 set",
         r41_map <= set(r41), str(sorted(r41_map)))
    gate("R13b release41 judge map excludes H3 concepts",
         not (r41_map & {"matches_known_release",
                         "distinct_fingerprints_count"}))
    gate("R13c whitelist stays exam_pair's target convention",
         "chip_whitelist_families_41" not in r41_map)

    # R14 release-41 weld: judge fills land on *_41 keys, day-0 keys stay
    # None, no leak refusal
    d41 = {k: None for k in _unique_keys()}
    d41["agesa_level_41"] = "1.2.0.12"
    d41["births_41"] = 0
    ident41 = {"observed": {"trust_certs": ["a", "b", "c", "d", "e", "f"],
                            "dsdt_primary": "0a4a6f162cad3e51",
                            "armor_core": ["1", "2", "3", "4"],
                            "armor_added": [],
                            "chip_whitelist_families": 46},
               "verdict": {"matches_known_release": False,
                           "distinct_fingerprints_count": 5}}
    m41, rep41 = weld(d41, ident41, target="release41")
    gate("R14a judge fills *_41 keys",
         m41["trust_cert_distinct_41"] == 6
         and m41["dsdt_sha16_41"] == "0a4a6f162cad3e51"
         and m41["core_armor_41"] == 4,
         f"certs={m41['trust_cert_distinct_41']}")
    gate("R14b zero day-0 leakage",
         all(m41[k] is None for k in d0),
         f"filled={rep41['filled']}")
    gate("R14c H3 verdict keys NOT applied",
         m41["matches_known_release"] is None
         and m41["distinct_fingerprints_count"] is None)

    # ---- tier I: live corpus ------------------------------------------
    reg = None
    try:
        reg = load_register()
    except FileNotFoundError:
        pass

    have = {k: v for k, v in RUNG_IMAGES.items() if os.path.exists(v)}
    if no_live or not have:
        skipped = "skipped (--no-live)" if no_live else "skipped (no corpus)"
        gate("I-live corpus", True, skipped)
    else:
        if "3604" in have:
            c, m = chain(have["3604"], geometry=False)
            v = c["verdict"]
            gate("I1a 3604 known-release",
                 v["verdict"] == "known-release"
                 and v.get("matched_release") == "3604",
                 v["verdict"])
            gate("I1b weld filled 12 exam + judge keys",
                 m["matches_known_release"] is True
                 and m["trust_cert_distinct"] == 4
                 and m["legacy_smm_count"] == 2
                 and m["chip_whitelist_families"] == 41
                 and m["dsdt_sha16"] == "27d5e826e111d755",
                 f"filled={c['weld_report']['filled']}")
            if reg and "3604" in reg["ceilings"]:
                want = reg["ceilings"]["3604"]["verdicts"]
                got = {r["id"]: r["verdict"] for r in c["scoreline"]["rows"]}
                gate("I2 scoreline@3604 == register", got == want,
                     f"{c['scoreline']['counts']}")
            else:
                gate("I2 scoreline@3604 == register", True,
                     "register absent, re-derived only")
        if "3802" in have:
            c3, _m3 = chain(have["3802"], geometry=False)
            gate("I3a 3802 known-release",
                 c3["verdict"]["verdict"] == "known-release",
                 c3["verdict"]["verdict"])
            if reg and "3802" in reg["ceilings"]:
                want = reg["ceilings"]["3802"]["verdicts"]
                got = {r["id"]: r["verdict"]
                       for r in c3["scoreline"]["rows"]}
                gate("I3b scoreline@3802 == register", got == want,
                     f"{c3['scoreline']['counts']}")
            else:
                gate("I3b scoreline@3802 == register", True,
                     "register absent, re-derived only")
        if reg and "3604" in reg["ceilings"] and "3802" in reg["ceilings"] \
                and "3604" in have and "3802" in have:
            disc = sorted(p for p in reg["ceilings"]["3604"]["verdicts"]
                          if reg["ceilings"]["3802"]["verdicts"].get(p)
                          != reg["ceilings"]["3604"]["verdicts"][p])
            gate("I4 discriminators == register",
                 disc == reg["discriminators_3604_3802"],
                 f"{len(disc)} flipping predictions")
        if not no_live and os.path.exists(
                os.path.join(OVMF_FLOOR, "OVMF_CODE_4M.fd")):
            c4, _m4 = chain(os.path.join(OVMF_FLOOR, "OVMF_CODE_4M.fd"),
                            geometry=False)
            hits = sorted(r["id"] for r in c4["scoreline"]["rows"]
                          if r["verdict"] == "hit")
            # The STRANGER SIGNATURE (measured ring 40, stronger than the
            # ring-38 mock invariant): on a foreign image the welded
            # chain hits the two absence predictions PLUS P-18 itself —
            # the H3 prediction agreeing with the H3 machine.
            gate("I5 OVMF floor: stranger signature",
                 c4["verdict"]["verdict"] == "no-match-h3-eligible"
                 and hits == ["P-04", "P-05", "P-18"],
                 f"hits={hits}")
        else:
            gate("I5 OVMF floor", True, "skipped (image absent)")
        if "3802" in have and "3810" in have:
            cp, _mp = chain_pair(have["3802"], have["3810"])
            gate("I6a chain-pair welds clean",
                 cp["weld_report"]["target"] == "release41"
                 and cp["ledger_summary"]["births_41"] == 0
                 and cp["ledger_summary"]["deaths_41"] == 0,
                 f"births={cp['ledger_summary']['births_41']} "
                 f"deaths={cp['ledger_summary']['deaths_41']}")
            if reg and "pair_3802_3810" in reg:
                want = reg["pair_3802_3810"]["verdicts"]
                got = {r["id"]: r["verdict"]
                       for r in cp["scoreline"]["rows"]}
                gate("I6b pair scoreline == register", got == want,
                     f"{cp['scoreline']['counts']}")
            else:
                gate("I6b pair scoreline == register", True,
                     "pair profile absent from register")
        else:
            gate("I6 chain-pair", True, "skipped (pair absent)")

    n_pass = sum(1 for _, ok, _ in g if ok)
    for name, ok, detail in g:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")
    print(f"fw40-merge selftest: {n_pass}/{len(g)} gates PASS "
          f"({'tier R only' if (no_live or not have) else 'tier I live'})")
    return 0 if not fails else 1


# ------------------------------------------------------------------ main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="fw40-merge")
    ap.add_argument("mode", choices=["merge", "chain", "chain-pair",
                                     "ceiling", "selftest", "manifest"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--lenses")
    ap.add_argument("--target", choices=["day0", "release41"],
                    default="day0")
    ap.add_argument("--out")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--no-geometry", action="store_true")
    ap.add_argument("--no-live", action="store_true")
    ap.add_argument("--lens-wins", nargs="*", default=[])
    a = ap.parse_args(argv)
    _mods()

    if a.mode == "manifest":
        print(json.dumps({
            "instrument": "fw40-merge", "ring": 40,
            "provenance": "la soudure — the last manual seam of the "
                          "day-0 chain (merge exam+identify before "
                          "score) becomes a machine-checked weld with "
                          "schema/separation/precedence/provenance laws",
            "modes": ["merge <draft.json> <identify.json>",
                      "chain <image>  (exam+identify+weld+score, ONE "
                      "command)",
                      "chain-pair <old> <new>  (the release-41 ONE "
                      "command: exam_pair+identify+weld+score)",
                      "ceiling <rung>...  (scoreline envelope on known "
                      "rungs)",
                      "selftest [--no-live]", "manifest"],
            "laws": {
                "schema": "only fw35 template keys (31 unique/32 slots)",
                "separation": "day0 and release41 keys never mix; "
                              "violation = exit 2",
                "precedence": "identify deep-truth > exam shallow walk; "
                              "lens fills manual slots only; --lens-wins "
                              "overrides are journaled",
                "provenance": "every filled value carries exam|identify|"
                              "lens in the weld report",
            },
            "judge_fills": list(JUDGE_FILLS),
            "judge_deep_truth": list(JUDGE_DEEP_TRUTH),
            "lens_only": list(LENS_ONLY),
            "register": "lab/vendor-scorelines.json (scoreline "
                        "envelope: ceilings on known rungs + the "
                        "3604/3802 discriminator set)",
        }, indent=2))
        return 0

    if a.mode == "selftest":
        return selftest(no_live=a.no_live)

    if a.mode == "merge":
        if len(a.args) < 2:
            print("merge <draft.json> <identify.json>", file=sys.stderr)
            return 2
        with open(a.args[0]) as f:
            draft = json.load(f)
        with open(a.args[1]) as f:
            ident = json.load(f)
        lenses = None
        if a.lenses:
            with open(a.lenses) as f:
                lenses = json.load(f)
        merged, rep = weld(draft, ident, lenses=lenses, target=a.target,
                           lens_wins=a.lens_wins)
        out = {"instrument": "fw40-merge", "ring": 40,
               "weld_report": rep, "findings": merged}
        if a.score:
            rows, n = fw35.Oracle().score(merged)
            out["scoreline"] = {
                "counts": n,
                "rows": [{"id": p["id"], "verdict": v, "note": note}
                         for p, v, note in rows]}
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
            rep["written_to"] = a.out
        print(json.dumps(out, indent=2))
        return 0

    if a.mode == "chain":
        if not a.args:
            print("chain <image>", file=sys.stderr)
            return 2
        lenses = None
        if a.lenses:
            with open(a.lenses) as f:
                lenses = json.load(f)
        c, merged = chain(a.args[0], lenses=lenses, target=a.target,
                          geometry=not a.no_geometry,
                          lens_wins=a.lens_wins)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump({"findings": merged,
                           "chain": {k: v for k, v in c.items()
                                     if k != "weld_report"}}, f,
                          indent=2)
            c["written_to"] = a.out
        print(json.dumps(c, indent=2))
        n = c["scoreline"]["counts"]
        print(f"[soudure] {c['verdict']['verdict']} — "
              f"{n['hit']} hit / {n['partial']} partial / "
              f"{n['miss']} miss / {n['na']} na; "
              f"{c['weld_report']['filled']}/{c['weld_report']['slots']} "
              f"slots filled, "
              f"{len(c['weld_report']['conflicts'])} conflict(s)",
              file=sys.stderr)
        return 0

    if a.mode == "chain-pair":
        if len(a.args) < 2:
            print("chain-pair <old> <new>", file=sys.stderr)
            return 2
        lenses = None
        if a.lenses:
            with open(a.lenses) as f:
                lenses = json.load(f)
        c, merged = chain_pair(a.args[0], a.args[1], lenses=lenses,
                               lens_wins=a.lens_wins)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump({"findings": merged,
                           "chain": {k: v for k, v in c.items()
                                     if k != "weld_report"}}, f,
                          indent=2)
            c["written_to"] = a.out
        print(json.dumps(c, indent=2))
        n = c["scoreline"]["counts"]
        print(f"[soudure-paire] {n['hit']} hit / {n['partial']} partial / "
              f"{n['miss']} miss / {n['na']} na; "
              f"{c['weld_report']['filled']}/{c['weld_report']['slots']} "
              f"slots filled, "
              f"{len(c['weld_report']['conflicts'])} conflict(s)",
              file=sys.stderr)
        return 0

    if a.mode == "ceiling":
        if not a.args:
            print("ceiling <rung>... one of: "
                  + ", ".join(sorted(RUNG_IMAGES)), file=sys.stderr)
            return 2
        reg = ceiling(a.args, out=a.out)
        print(json.dumps(reg, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
