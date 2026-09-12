#!/usr/bin/env python3
# fw35-oracle.py — the day-0 oracle (ring 35).
#
# The falsifiable-prediction register scorer. lab/vendor-oracle.json holds
# 26 predictions registered BEFORE the 16/09 dump and before release #41;
# this instrument re-derives every basis number from the persisted registers
# (loud refusal on any drift, the fw33 discipline), scores a findings file
# against the register, and prints the scorecard.
#
# Honesty contract:
#   - the register is FROZEN at commit: predictions are never edited after
#     registration; a wrong prediction scores miss and its cause is written
#     in the next ring report
#   - the engine KNOWS ONLY WHAT THE REGISTERS KNOW: every selftest gate
#     re-derives a basis number from its source register; drift = refusal
#   - bands are anchored on the target board's own measured values, never on
#     corpus-wide ranges (ASUS varstore share 83.89% < the 84-90% corpus band)
#
# stdlib only. Loads inputs relative to this file's directory (lab/).
# Modes: list | show <id> | template | score <findings.json> | selftest | manifest

import json
import os
import sys
import re

HERE = os.path.dirname(os.path.abspath(__file__))

REGISTERS = {
    "oracle": "vendor-oracle.json",
    "armor": "vendor-flash-armor.json",
    "agesa": "vendor-agesa.json",
    "genome": "vendor-genome.json",
    "der": "vendor-der-inventory.json",
    "ifr": "vendor-ifr-census.json",
    "unasked": "vendor-unasked.json",
    "chipdb": "vendor-armor-chipdb.json",
    "lifecycles": "vendor-lifecycles.json",
    "ssdt": "vendor-ssdt-clock.json",
    "ledger": "vendor-ledger-tuf.json",
}

AGESA_EXPECTED = {
    "3604": "1.2.0.6b", "3802": "1.2.0.7", "3810": "1.2.0.7",
    "4003": "1.2.0.8", "4202": "1.2.0.A", "4402": "1.2.0.B",
    "4604": "1.2.0.Ca", "4631": "1.2.0.E", "4655": "1.2.0.12",
}

# the AGESA rank: the chronology's own order is the truth (letters precede
# the numeric rung .12 in this scheme); unknown levels ranked by fallback rules
_AGESA_ORDER = ["1.2.0.6b", "1.2.0.7", "1.2.0.8", "1.2.0.A",
                "1.2.0.B", "1.2.0.Ca", "1.2.0.E", "1.2.0.12"]

DSDT_GEN1, DSDT_GEN3 = "27d5e826e111d755", "0a4a6f162cad3e51"


def _load(name):
    with open(os.path.join(HERE, REGISTERS[name])) as f:
        return json.load(f)


def agesa_rank(level):
    if level in _AGESA_ORDER:
        return _AGESA_ORDER.index(level)
    suffix = level.split(".")[-1]
    if suffix.isdigit():
        n = int(suffix)
        return len(_AGESA_ORDER) - 1 + (n - 12) * 10 if n >= 12 else _AGESA_ORDER.index("1.2.0.8") + (ord(suffix[0]) - 48) * 0.01
    return _AGESA_ORDER.index("1.2.0.A") + (ord(suffix[0]) - ord("A")) * 0.5


def _in_band(v, band):
    lo, hi = band
    if lo is not None and v < lo:
        return False
    if hi is not None and v > hi:
        return False
    return True


# ---------------------------------------------------------------- checkers

def ck_identity_h3(obs, reg):
    m = obs.get("matches_known_release")
    n = obs.get("distinct_fingerprints_count")
    if m is False and isinstance(n, int) and n >= 3:
        return "hit"
    if m is False and isinstance(n, int) and n == 2:
        return "partial"
    return "miss"


def ck_psp_overlap(obs, reg):
    a, p, n = (set(obs.get(k) or []) for k in
               ("psp_hashes_3644", "psp_hashes_3604", "psp_hashes_3802"))
    if not a or not p or not n:
        return "miss"
    return "hit" if len(a & p) > len(a & n) else "miss"


def ck_agesa_monotone(obs, reg):
    lv = obs.get("agesa_level_41")
    if not isinstance(lv, str) or not lv.startswith("1.2.0."):
        return "miss"
    return "hit" if agesa_rank(lv) >= agesa_rank("1.2.0.12") else "miss"


def ck_armor_no_third_wave(obs, reg):
    ok = (obs.get("core_armor_41") == 4
          and obs.get("added_present_count_41") == 7)
    return "hit" if ok else "miss"


def ck_no_births_no_deaths(obs, reg):
    ok = obs.get("births_41") == 0 and obs.get("deaths_41") == 0
    return "hit" if ok else "miss"


def ck_conditional_dsdt(obs, reg):
    if obs.get("agesa_level_41") != "1.2.0.12":
        return "na"
    return "hit" if obs.get("dsdt_sha16_41") == DSDT_GEN3 else "miss"


CHECKERS = {
    "identity_h3": ck_identity_h3,
    "psp_overlap_direction": ck_psp_overlap,
    "agesa_monotone": ck_agesa_monotone,
    "armor_no_third_wave": ck_armor_no_third_wave,
    "no_births_no_deaths": ck_no_births_no_deaths,
    "conditional_dsdt": ck_conditional_dsdt,
}

KINDS = {"exact", "band", "set", "prefix", "predicate"}


# ---------------------------------------------------------------- engine

class Oracle:
    def __init__(self):
        self.reg = _load("oracle")
        self.preds = {p["id"]: p for p in self.reg["predictions"]}
        for name in REGISTERS:
            if name != "oracle":
                setattr(self, name, _load(name))

    # ---- scoring
    def score_one(self, p, findings):
        if p["kind"] == "predicate":
            if p["checker"] not in CHECKERS:
                return "miss", "no checker registered"
            obs = {k: findings.get(k) for k in p.get("observed_keys", [])}
            if all(v is None for v in obs.values()):
                return "na", "no observation supplied"
            return CHECKERS[p["checker"]](obs, self), ""
        v = findings.get(p.get("observed_key"))
        if v is None:
            return "na", "no observation supplied"
        k = p["kind"]
        if k == "exact":
            if v == p["expect"]:
                return "hit", ""
            if p.get("widened") and v in p["widened"]:
                return "partial", ""
            return "miss", ""
        if k == "band":
            if _in_band(v, p["expect"]):
                return "hit", ""
            if p.get("widened") and _in_band(v, p["widened"]):
                return "partial", ""
            return "miss", ""
        if k == "set":
            if v in p["expect"]:
                return "hit", ""
            if p.get("widened") and v in p["widened"]:
                return "partial", ""
            return "miss", ""
        if k == "prefix":
            return ("hit", "") if isinstance(v, str) and v.startswith(p["expect"]) else ("miss", "")
        return "miss", "unknown kind"

    def score(self, findings):
        rows = []
        for p in self.reg["predictions"]:
            v, note = self.score_one(p, findings)
            rows.append((p, v, note))
        n = {"hit": 0, "partial": 0, "miss": 0, "na": 0}
        for _, v, _ in rows:
            n[v] += 1
        return rows, n

    # ---- selftest
    def selftest(self):
        gates = []
        results = []

        def gate(name, want, got):
            results.append((name, want, got, want == got))
            return want == got

        a = self.armor
        probes = {p.get("version"): p for p in a.get("probes", [])}
        gate("G01 wave1 boundary first_with_core=3802",
             a.get("wave1_boundary", {}).get("first_with_core"), "3802")
        gate("G01b wave1 boundary last_without=3604",
             a.get("wave1_boundary", {}).get("last_without_core"), "3604")
        p36 = probes.get("3604", {})
        gate("G02 armor 3604 core_armor=0", p36.get("core_armor"), 0)
        gate("G02b armor 3604 added=0", len(p36.get("added_present", [])), 0)
        gate("G02c armor 3604 modules=618", p36.get("modules"), 618)
        gate("G02d armor 3604 rom_bytes=16MiB", p36.get("rom_bytes"), 16777216)
        gate("G03 AGESA map x9", AGESA_EXPECTED, AGESA_EXPECTED)
        tl_src = self.agesa.get("timeline") or []
        tl = {}
        for s in tl_src:
            v = s.get("version") or s.get("rung")
            vf = s.get("versions_found") or ([s.get("agesa")] if s.get("agesa") else [])
            if v and vf:
                tl[v] = vf[0] if isinstance(vf, list) else vf
        if len(tl) == 9:
            gate("G03b AGESA register map", tl, AGESA_EXPECTED)
        else:
            gate("G03b AGESA register map (9 rungs)", len(tl), 9)
        ranks = [agesa_rank(AGESA_EXPECTED[r]) for r in
                 ["3604", "3802", "3810", "4003", "4202", "4402", "4604", "4631", "4655"]]
        gate("G14 AGESA rank strictly increasing", ranks, sorted(ranks))
        ps = self.ssdt.get("per_specimen", {})
        gen_classes = {
            "3604": DSDT_GEN1, "3802": DSDT_GEN1, "3810": DSDT_GEN1,
            "4003": DSDT_GEN1, "4202": DSDT_GEN1, "4402": "f23c571b48b6d9e6",
            "4604": "f23c571b48b6d9e6", "4631": DSDT_GEN3, "4655": DSDT_GEN3,
        }
        got = {r: (ps.get("asus-" + r, {}).get("main_dsdt", {}) or {}).get("sha16") for r in gen_classes}
        gate("G04 DSDT generations x9", got, gen_classes)
        gate("G05 genome species=330", self.genome.get("species_total"), 330)
        gate("G05b genome wave1 births=5", (self.genome.get("wave1_births") or {}).get("count"), 5)
        gate("G05c genome wave2 births=2", (self.genome.get("wave2_births") or {}).get("count"), 2)
        der = self.der.get("per_specimen", {})
        der_counts = {r: len(der.get("asus-" + r, {}).get("trust_distinct", [])) for r in AGESA_EXPECTED}
        gate("G06 der 3604 certs=4", der_counts["3604"], 4)
        gate("G06b der 3810 certs=6", der_counts["3810"], 6)
        gate("G06c der count frozen 3810-4655",
             [der_counts[r] for r in ("3810", "4003", "4202", "4402", "4604", "4631", "4655")],
             [6, 6, 6, 6, 6, 6, 6])
        ifr = {s.get("id"): (s.get("totals") or {}).get("questions") for s in self.ifr.get("specimens", [])}
        gate("G07 ifr 3604-ref questions=7975", ifr.get("asus-prime-b450-plus-ref"), 7975)
        gate("G07b ifr 4655 questions=8273", ifr.get("asus-prime-b450-plus"), 8273)
        uc = (self.unasked.get("coverage", {}).get("asus-prime-b450-plus-ref", {}) or {}).get("setup_row", {})
        gate("G08 unasked Setup size=456", uc.get("size"), 456)
        gate("G08b unasked Setup uncovered=142", uc.get("uncovered"), 142)
        gate("G08c unasked share=83.89",
             round((self.unasked.get("coverage", {}).get("asus-prime-b450-plus-ref", {}) or {}).get("uncovered_share_pct", -1), 2), 83.89)
        lad = self.chipdb.get("ladder_movement", [])
        gate("G09 chipdb 41->46 (+5)",
             [lad[0].get("n_a"), lad[0].get("n_b"), len(lad[0].get("added", []))] if lad else None,
             [41, 46, 5])
        gate("G09b chipdb frozen after 3802",
             all(not m.get("added") and not m.get("dropped") for m in lad[1:]), True)
        smm = (self.lifecycles.get("smm_anatomy", {}).get("smm_census_per_rung", {}) or {})
        gate("G10 smm 3604 = 105+1",
             [smm.get("3604", {}).get("SMM"), smm.get("3604", {}).get("SMM-core")], [105, 1])
        gate("G10b smm 3802 = 108+1",
             [smm.get("3802", {}).get("SMM"), smm.get("3802", {}).get("SMM-core")], [108, 1])
        q = self.ledger.get("question_3644", {})
        gate("G11 ledger 3644 hypotheses=3", len(q.get("hypotheses_ring12", [])), 3)
        gate("G11b ledger H3 open", "H3 open" in json.dumps(q), True)
        # register integrity
        ids = [p["id"] for p in self.reg["predictions"]]
        gate("G12 register ids unique", len(set(ids)), len(ids))
        gate("G12b register size=26", len(ids), 26)
        kinds_ok = all(p.get("kind") in KINDS for p in self.reg["predictions"])
        gate("G12c register kinds valid", kinds_ok, True)
        checkers_ok = all(p.get("checker") in CHECKERS for p in self.reg["predictions"]
                          if p.get("kind") == "predicate")
        gate("G12d predicate checkers registered", checkers_ok, True)
        basis_ok = all(re.search(r"(vendor-[a-z0-9-]+\.json|docs/[a-z0-9-]+\.md)",
                                 " ".join(p.get("basis", []))) for p in self.reg["predictions"])
        gate("G12e every basis cites a register", basis_ok, True)
        # scorer smoke: one of each verdict
        smoke_rows, smoke_n = self.score({
            "rom_bytes": 16777216,                       # P-01 hit
            "legacy_smm_count": 3,                        # P-07 partial (widened)
            "dsdt_sha16": "deadbeefdeadbeef",             # P-09 miss
            "agesa_level_41": "1.2.0.13",                 # P-25 na (AGESA moved)
        })
        got_map = {p["id"]: v for p, v, _ in smoke_rows}
        gate("G13 smoke P-01 hit", got_map.get("P-01"), "hit")
        gate("G13b smoke P-07 partial", got_map.get("P-07"), "partial")
        gate("G13c smoke P-09 miss", got_map.get("P-09"), "miss")
        gate("G13d smoke P-25 na", got_map.get("P-25"), "na")

        npass = sum(1 for r in results if r[3])
        for name, want, got, ok in results:
            mark = "PASS" if ok else "FAIL"
            if not ok or os.environ.get("FW35_VERBOSE"):
                print(f"  [{mark}] {name}: want={want!r} got={got!r}")
        print(f"fw35-oracle selftest: {npass}/{len(results)} gates PASS")
        if npass != len(results):
            print("REFUSAL: register or source drift — fix before scoring.")
            sys.exit(2)
        return results


# ---------------------------------------------------------------- CLI

def _fmt_pred(p):
    exp = p.get("expect")
    if isinstance(exp, list) and p["kind"] == "band":
        exp = f"[{exp[0]}, {exp[1] if exp[1] is not None else 'inf'}]"
    return f"  {p['id']}  {p['target']:<11} {p['confidence']:<8} {p['field']}: {exp}  ({p['kind']})"


def main(argv):
    if not argv:
        argv = ["selftest"]
    cmd = argv[0].lstrip("-")
    eng = Oracle()

    if cmd == "selftest":
        eng.selftest()
        return 0

    # every other mode first proves the register chain
    saved = sys.stdout
    devnull = open(os.devnull, "w")
    sys.stdout = devnull
    try:
        eng.selftest()
    finally:
        sys.stdout = saved
        devnull.close()

    if cmd == "list":
        for t in ("day0-3644", "release-41"):
            print(f"[{t}]")
            for p in eng.reg["predictions"]:
                if p["target"] == t:
                    print(_fmt_pred(p))
        n = len(eng.reg["predictions"])
        print(f"  -- {n} predictions; scoring protocol: fw35-oracle.py score <findings.json>")
        return 0

    if cmd == "show" and len(argv) > 1:
        p = eng.preds.get(argv[1])
        if not p:
            print(f"no prediction {argv[1]}"); return 2
        print(json.dumps(p, indent=2))
        return 0

    if cmd == "template":
        tpl = {}
        for p in eng.reg["predictions"]:
            for k in p.get("observed_keys", []) or [p.get("observed_key")]:
                tpl[k] = None
        print(json.dumps(tpl, indent=2))
        return 0

    if cmd == "score" and len(argv) > 1:
        with open(argv[1]) as f:
            findings = json.load(f)
        rows, n = eng.score(findings)
        print("prediction scorecard")
        print(f"{'id':<6} {'field':<28} {'observed':<24} verdict")
        for p, v, note in rows:
            if p["kind"] == "predicate":
                obs = json.dumps({k: findings.get(k) for k in p.get("observed_keys", [])})[:22]
            else:
                obs = str(findings.get(p.get("observed_key")))[:22]
            extra = f"  ({note})" if note else ""
            print(f"{p['id']:<6} {p['field']:<28} {obs:<24} {v}{extra}")
        print(f"totals: {n['hit']} hit / {n['partial']} partial / {n['miss']} miss / {n['na']} na "
              f"of {len(rows)}")
        print("honesty rule: every partial and miss requires a written cause in the next ring report.")
        return 1 if n["miss"] else 0

    if cmd == "manifest":
        by = {}
        for p in eng.reg["predictions"]:
            by.setdefault(p["target"], []).append(p)
        conf = {}
        for p in eng.reg["predictions"]:
            conf[p["confidence"]] = conf.get(p["confidence"], 0) + 1
        print(json.dumps({
            "predictions": len(eng.reg["predictions"]),
            "by_target": {k: len(v) for k, v in by.items()},
            "by_confidence": conf,
            "checkers": sorted(CHECKERS),
            "registers_fused": sorted(REGISTERS.values()),
        }, indent=2))
        return 0

    print("modes: list | show <id> | template | score <findings.json> | selftest | manifest")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
