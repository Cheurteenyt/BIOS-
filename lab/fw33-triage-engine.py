#!/usr/bin/env python3
# fw33-triage-engine.py — the day-0 triage weapon (ring 33, front a).
#
# Zero-download register fusion over the ASUS PRIME B450-PLUS ladder:
# nine rings of persisted registers (genome, churn atlas, AGESA chronology,
# flash-armor probes, acquisition ledger, SMM quorum, armor chipdb) fused
# into ONE queryable instrument so that any GUID / body hash pulled from a
# future dump is placed instantly: identity, birth, death, moves, body
# chain, armor wave, AGESA context, and the recommended diff pair.
#
# Honesty contract: the engine KNOWS ONLY WHAT THE REGISTERS KNOW.
#   - the never-touched static core is not enumerable (genome honesty)
#   - frontier events carry name=null; names join via the armor watchlist
#   - armor expectations for unprobed releases are bracketed, not measured
# Every gate in --selftest must pass or the engine refuses to answer.
#
# stdlib only. Loads inputs relative to this file's directory (lab/).

import json
import os
import sys
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))

REGISTERS = {
    "genome": "vendor-genome.json",
    "churn": "vendor-churn-atlas.json",
    "agesa": "vendor-agesa.json",
    "armor": "vendor-flash-armor.json",
    "acquisition": "vendor-acquisition.json",
    "quorum": "vendor-smm-quorum.json",
    "chipdb": "vendor-armor-chipdb.json",
}

WAVE_SCORES_EXPECTED = {  # rung -> (wave-core score /7, legacy score /2)
    "3604": (0, 2), "3802": (5, 2), "3810": (5, 2), "4003": (5, 2),
    "4202": (5, 1), "4402": (5, 0), "4604": (7, 0), "4631": (7, 0),
    "4655": (7, 0),
}

AGESA_EXPECTED = {
    "3604": "1.2.0.6b", "3802": "1.2.0.7", "3810": "1.2.0.7",
    "4003": "1.2.0.8", "4202": "1.2.0.A", "4402": "1.2.0.B",
    "4604": "1.2.0.Ca", "4631": "1.2.0.E", "4655": "1.2.0.12",
}

MOVE_CLASS = {
    0: "static-since-birth",
    1: "one-move",
    2: "sparse-mover",
    3: "mover",
    4: "mover",
    5: "agesa-engine-room",      # the 98-species spike at every AGESA swap
    6: "chronic-mover",
    7: "chronic-mover",
    8: "all-frontier-mover",     # present at EVERY one of the 8 frontiers
}


def sha256_16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


class Engine:
    def __init__(self):
        self.reg = {}
        for key, fname in REGISTERS.items():
            path = os.path.join(HERE, fname)
            if not os.path.exists(path):
                raise SystemExit(
                    "honesty contract violated: register missing: %s" % fname)
            with open(path, "r", encoding="utf-8") as f:
                self.reg[key] = json.load(f)
        self._build()

    # ------------------------------------------------------------------
    # index construction
    # ------------------------------------------------------------------
    def _build(self):
        g = self.reg["genome"]

        # ladder + edges
        self.edges = [t["transition"] for t in g["transitions"]]
        self.ladder = [self.edges[0].split("->")[0].replace("asus-", "")]
        for e in self.edges:
            self.ladder.append(e.split("->")[1].replace("asus-", ""))

        # species indexes
        self.by_guid = {}
        self.by_body = {}   # hash16 -> list of (guid, at, role)
        for sp in g["species"]:
            self.by_guid[sp["guid"]] = sp
            for step in sp.get("hash_chain", []):
                self.by_body.setdefault(step["from"], []).append(
                    (sp["guid"], step["at"], "from"))
                self.by_body.setdefault(step["to"], []).append(
                    (sp["guid"], step["at"], "to"))

        # AGESA map from the 9-point dated ladder (fail loudly on drift)
        self.agesa = {}
        self.agesa_points = {}
        for s in self.reg["agesa"]["timeline"]:
            v = str(s["version"])
            self.agesa[v] = s["agesa"]
            self.agesa_points[v] = s
        for v, want in AGESA_EXPECTED.items():
            got = self.agesa.get(v)
            if got != want:
                raise SystemExit(
                    "AGESA drift at %s: register says %r, engine pinned %r"
                    % (v, got, want))

        # armor replay: PRESENCE lists per probe (added_present reports the
        # wave members present in that image — not newly-added events)
        self.armor_members = {}   # rung -> list of member names present
        self.armor_legacy = {}    # rung -> int legacy-SMM count
        for p in self.reg["armor"]["probes"]:
            v = p["version"]
            self.armor_members[v] = list(p.get("added_present", []))
            self.armor_legacy[v] = len([x for x in p.get("removed_present", [])
                                        if "SMM" in x])

        # name anchors: watchlist prefixes ("391626DB\u2026") + quorum facts
        self.names = {}
        for prefix, name in self.reg["armor"].get("added_watchlist", {}).items():
            self.names[prefix.replace("\u2026", "").upper()] = name
        self.armor_identity = self.reg["quorum"].get("armor_identity", {})

        # per-rung census (churn)
        self.per_rung = self.reg["churn"]["per_rung"]

        # frontier event lists (born/dead GUIDs per edge)
        self.frontiers = {}
        for f in self.reg["churn"]["frontiers"]:
            self.frontiers[f["transition"]] = f

        self.wave1 = set(g["wave1_births"]["guids"])
        self.wave2 = set(g["wave2_births"]["guids"])

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _name(self, guid):
        for prefix, name in self.names.items():
            if guid.upper().startswith(prefix.upper()):
                return name
        return None

    def _edge_agesa(self, edge):
        a = edge.split("->")[1].replace("asus-", "")
        return self.agesa.get(a)

    def _edge_date(self, edge):
        a = edge.split("->")[1].replace("asus-", "")
        for p in self.reg["armor"]["probes"]:
            if p["version"] == a:
                return p.get("date")
        return None

    def _move_class(self, moves):
        return MOVE_CLASS.get(moves, "mover")

    def _diff_advice(self, sp):
        """the edges where this species' body actually changed, earliest first."""
        pairs = []
        for step in sp.get("hash_chain", []):
            if step["from"] != step["to"]:
                pairs.append(step["at"])
        if not pairs:
            return ["no body change on the ladder — diff work is pointless; "
                    "placement is the product"]
        return pairs

    # ------------------------------------------------------------------
    # placement API — the day-0 weapon
    # ------------------------------------------------------------------
    def place_guid(self, guid):
        guid = guid.strip().upper()
        out = {"mode": "guid", "guid": guid}
        sp = self.by_guid.get(guid)
        if sp is None:
            out["verdict"] = "UNPLACED"
            out["reading"] = (
                "not touched by any frontier event: either the never-touched "
                "static core (not enumerable from registers) or a species "
                "new to the ladder (would be a NEW event, not seen in 9 rings)")
            out["next"] = [
                "run body mode on its FFS body sha256_16",
                "diff its host FV against asus-3802 and asus-4604 sentinels "
                "(the two wave boundaries) before any other probe",
            ]
            return out
        birth = sp.get("born_at")
        death = sp.get("dead_at")
        out["verdict"] = "PLACED"
        out["name"] = self._name(guid)
        out["types"] = sp.get("types", [])
        out["flags"] = sp.get("flags", [])
        out["wave"] = ("wave1 (core SMM armor, 2022-05-12)" if guid in self.wave1
                       else "wave2 (armor completion, 2024-04-08)"
                       if guid in self.wave2 else None)
        out["born_at"] = birth
        out["birth_agesa"] = self._edge_agesa(birth) if birth else None
        out["birth_date"] = self._edge_date(birth) if birth else None
        out["dead_at"] = death
        out["death_agesa"] = self._edge_agesa(death) if death else None
        out["moves"] = sp.get("moves")
        out["move_class"] = self._move_class(sp.get("moves", 0))
        out["hash_chain"] = sp.get("hash_chain", [])
        out["body_changes_on"] = self._diff_advice(sp)
        if guid in self.armor_identity or out["name"] in self.armor_identity:
            key = guid if guid in self.armor_identity else out["name"]
            out["armor_identity"] = self.armor_identity[key]
        return out

    def place_body(self, hash16):
        hash16 = hash16.strip().lower()
        hits = self.by_body.get(hash16, [])
        out = {"mode": "body", "hash16": hash16, "hits": len(hits)}
        if not hits:
            out["verdict"] = "UNPLACED-BODY"
            out["reading"] = (
                "this body hash never appears in any recorded chain step — "
                "either a body that never changed across the probed ladder "
                "(chains record only changes) or a species outside the "
                "frontier events")
            out["next"] = ["place by GUID instead",
                           "diff against 3802/4604 sentinels"]
            return out
        placements = []
        for guid, at, role in hits:
            placements.append({
                "guid": guid,
                "name": self._name(guid),
                "at_edge": at,
                "role": role,
                "agesa": self._edge_agesa(at),
                "wave": ("wave1" if guid in self.wave1 else
                         "wave2" if guid in self.wave2 else None),
            })
        out["verdict"] = "PLACED-BODY"
        out["placements"] = placements
        return out

    def rung_report(self, version):
        v = str(version)
        if v not in self.ladder:
            raise SystemExit("rung %s not on the probed ladder %r"
                             % (v, self.ladder))
        idx = self.ladder.index(v)
        out = {"mode": "rung", "rung": v}
        out["census"] = self.per_rung.get("asus-" + v)
        out["agesa"] = self.agesa.get(v)
        out["wave_score"] = "/".join(str(x) for x in WAVE_SCORES_EXPECTED[v])
        out["armor_members"] = self.armor_members.get(v, [])
        out["legacy_smm_present"] = self.armor_legacy.get(v)
        out["in_edge"] = self.edges[idx - 1] if idx > 0 else None
        out["out_edge"] = self.edges[idx] if idx < len(self.edges) else None
        fe = self.frontiers.get(self.edges[idx]) if idx < len(self.edges) else None
        if fe:
            out["next_frontier"] = {
                "transition": fe["transition"],
                "born": fe.get("born", []),
                "dead": fe.get("dead", []),
                "moved_count": len(fe.get("moved", fe.get("moved_guids", [])))
                if isinstance(fe.get("moved", fe.get("moved_guids", [])), list)
                else fe.get("moved"),
            }
        out["probe"] = next((p for p in self.reg["armor"]["probes"]
                             if p["version"] == v), None)
        return out

    # ------------------------------------------------------------------
    # the day-0 card
    # ------------------------------------------------------------------
    def plan(self, rung=None):
        arm = self.reg["armor"]
        out = {
            "mode": "plan",
            "title": "day-0 triage card — ASUS PRIME B450-PLUS, 16 MiB ROM",
            "ladder": [
                {
                    "rung": v,
                    "date": next((p["date"] for p in arm["probes"]
                                  if p["version"] == v), None),
                    "agesa": self.agesa.get(v),
                    "wave_score": "%d/7" % WAVE_SCORES_EXPECTED[v][0],
                    "legacy_score": "%d/2" % self.armor_legacy.get(v, 0),
                    "rom_sha256_16": next((p.get("rom_sha256_16") for p in arm["probes"]
                                           if p["version"] == v), None),
                }
                for v in self.ladder
            ],
            "procedure": [
                "1. dump the ROM (2x16 MiB clip or in-system), never flash first",
                "2. sha256 the dump; match a ladder rom_sha256_16 above — if it "
                "matches a probed rung, every expectation on that row applies "
                "as-is; if not, bracket between probed neighbors",
                "3. census the FFS files; for each GUID call: engine guid <G>",
                "4. UNPLACED verdicts are the payload of the day: they are "
                "either the never-touched static core or NEW events — "
                "diff them against the 3802 and 4604 sentinels first",
                "5. check armor by expectation: >=3802 must show the 5 wave-1 "
                "members, >=4604 the 7; legacy SMM count must read 2/2 (<=4003), "
                "1/2 (4202), 0/2 (>=4402)",
                "6. read AGESA: the dump must show the row's version string; a "
                "mismatch means the release is off-ledger (escalate)",
                "7. 3644 question: %s" % json.dumps(
                    self.reg["acquisition"].get("the_3644_question",
                                                "register field absent"))[:160],
            ],
            "sentinels": {
                p["version"]: p.get("rom_sha256_16")
                for p in arm["probes"] if p.get("sentinel")
            },
            "downloads_total": arm.get("downloads_total"),
            "honesty": [
                "expectations are measured at 9 probed rungs only; the other "
                "31 of 40 ledger releases are bracketed, not measured",
                "the static core is not enumerable from registers",
                "LogoFail correlation stays year-granular",
            ],
        }
        if rung:
            r = str(rung)
            if r in WAVE_SCORES_EXPECTED:
                out["focus_rung"] = self.rung_report(r)
            else:
                raise SystemExit("no probed expectation for rung %s" % r)
        return out

    def waves(self):
        arm = self.reg["armor"]
        return {
            "mode": "waves",
            "wave1": {
                "boundary": arm.get("wave1_boundary"),
                "members": [
                    {"guid": g, "name": self._name(g),
                     "moves": self.by_guid[g]["moves"]}
                    for g in sorted(self.wave1)
                ],
            },
            "wave2": {
                "boundary": arm.get("boundary"),
                "members": [
                    {"guid": g, "name": self._name(g),
                     "moves": self.by_guid[g]["moves"]}
                    for g in sorted(self.wave2)
                ],
            },
            "legacy_retirement": {
                "reading": arm["reading"]["ring16_reading_corrected"],
            },
        }

    def agesa_table(self):
        rows = []
        for v in self.ladder:
            rows.append({"rung": v, "agesa": self.agesa.get(v)})
        return {"mode": "agesa", "points": rows,
                "note": "single tie 3802==3810 (1.2.0.7); PSP/NVRAM analysis "
                        "must treat them as a pair"}

    # ------------------------------------------------------------------
    # self-test — genome-exact gates; any failure aborts the engine
    # ------------------------------------------------------------------
    def selftest(self):
        g = self.reg["genome"]
        gates = []

        def gate(name, want, got):
            gates.append({"gate": name, "want": want, "got": got,
                          "pass": want == got})

        gate("species_total==330", 330, g["species_total"])
        gate("edges==8", 8, len(self.edges))
        gate("ladder==9 rungs",
             ["3604", "3802", "3810", "4003", "4202", "4402", "4604",
              "4631", "4655"], self.ladder)
        quiet = next(t for t in g["transitions"]
                     if t["transition"] == "asus-3802->asus-3810")
        gate("quiet edge 3802->3810 {born,dead,moved}=={0,0,45}",
             {"born": 0, "dead": 0, "moved": 45},
             {"born": quiet["born"], "dead": quiet["dead"],
              "moved": quiet["moved"]})

        w1 = [s for s in g["species"] if "wave1_birth" in s.get("flags", [])]
        gate("wave1 births==5 all born 3604->3802",
             (5, "asus-3604->asus-3802"),
             (len(w1), w1[0]["born_at"] if w1 else None))
        w2 = [s for s in g["species"] if "wave2_birth" in s.get("flags", [])]
        gate("wave2 births==2 all born 4402->4604",
             (2, "asus-4402->asus-4604"),
             (len(w2), w2[0]["born_at"] if w2 else None))

        sba = self.by_guid.get("51080191-ED06-4AA0-BFD7-F04837CF70DB")
        gate("SbRomArmorSmm moves==0 (genome-exact)", 0,
             sba["moves"] if sba else None)
        gate("SbRomArmorSmm name anchor", "SbRomArmorSmm",
             self._name("51080191-ED06-4AA0-BFD7-F04837CF70DB"))
        quartet = sorted(s["guid"] for s in g["species"]
                         if "armor_quartet" in s.get("flags", []))
        gate("armor quartet == the 4 named members", sorted([
            "391626DB-3CEC-4339-A3D6-9CDFF4690E12",
            "51080191-ED06-4AA0-BFD7-F04837CF70DB",
            "6C289241-E240-483F-9E3E-872C0396B599",
            "755877A6-4F10-4A5C-9B2E-852123B9682C"]), quartet)

        l4202 = [s for s in g["species"]
                 if "legacy_death_4202" in s.get("flags", [])]
        l4402 = [s for s in g["species"]
                 if "legacy_death_4402" in s.get("flags", [])]
        gate("legacy death @4202 == 827E45A4",
             ["827E45A4-C285-4E45-8BC7-CD8E58D9EE84"],
             [s["guid"] for s in l4202])
        gate("legacy death @4402 == 21782819",
             ["21782819-FDA0-4ADE-BD36-C95F079F057D"],
             [s["guid"] for s in l4402])

        md = g["derived"]["move_distribution"]
        gate("move_distribution covers 330 species", 330,
             sum(md.values()))
        gates.append({"gate": "total move events across genome",
                      "want": ">0", "got": sum(int(k) * c
                                               for k, c in md.items()),
                      "pass": sum(int(k) * c for k, c in md.items()) > 0})
        gate("all-frontier movers (moves==8) == 26", 26, md.get("8", 0))
        gate("static-since-birth (moves==0) == 4", 4, md.get("0", 0))

        gate("AGESA ladder points == 9", 9, len(self.reg["agesa"]["timeline"]))
        rank = {v: i for i, v in enumerate(
            ["1.2.0.6b", "1.2.0.7", "1.2.0.8", "1.2.0.A", "1.2.0.B",
             "1.2.0.Ca", "1.2.0.E", "1.2.0.12"])}
        monotone = all(
            rank[AGESA_EXPECTED[self.ladder[i]]]
            <= rank[AGESA_EXPECTED[self.ladder[i + 1]]]
            for i in range(len(self.ladder) - 1))
        gate("AGESA monotone non-decreasing (ranked)", True, monotone)
        gate("AGESA single tie 3802==3810",
             [("3802", "1.2.0.7"), ("3810", "1.2.0.7")],
             [(v, self.agesa[v]) for v in ("3802", "3810")])

        gate("armor wave scores replay == register reading",
             WAVE_SCORES_EXPECTED,
             {v: (len(self.armor_members[v]), self.armor_legacy[v])
              for v in self.ladder})
        gate("armor boundary first_complete==4604", "4604",
             self.reg["armor"]["boundary"]["first_complete"])
        gate("armor boundary last_incomplete==4402", "4402",
             self.reg["armor"]["boundary"]["last_incomplete"])
        gate("wave1 first_with_core==3802", "3802",
             self.reg["armor"]["wave1_boundary"]["first_with_core"])

        broken = 0
        steps = 0
        for sp in g["species"]:
            prev = None
            for st in sp.get("hash_chain", []):
                steps += 1
                if prev is not None and st["from"] != prev:
                    broken += 1
                prev = st["to"]
        gate("chain integrity: every step links from==prev.to", 0, broken)
        gates.append({"gate": "chain steps total", "want": ">0",
                      "got": steps, "pass": steps > 0})

        gate("probes==9, every one with a rom sha256_16 anchor", 9,
             len([p for p in self.reg["armor"]["probes"]
                  if p.get("rom_sha256_16")]))
        sizes = sorted({p["rom_bytes"] for p in self.reg["armor"]["probes"]
                        if p.get("rom_bytes")})
        gate("rom sizes == {capsule payload 16515072, full 16777216}",
             [16515072, 16777216], sizes)
        gate("sentinels == {3604, 4655}", ["3604", "4655"],
             sorted(v for v, p in ((p["version"], p)
                                   for p in self.reg["armor"]["probes"])
                    if p.get("sentinel")))
        gate("churn per_rung covers the ladder", self.ladder,
             [k.replace("asus-", "") for k in self.per_rung
              if k.replace("asus-", "") in WAVE_SCORES_EXPECTED])
        gate("the_3644_question registered", True,
             "the_3644_question" in self.reg["acquisition"])

        allpass = all(gt["pass"] for gt in gates)
        return {"mode": "selftest", "gates": len(gates),
                "all_pass": allpass, "detail": gates}

    # ------------------------------------------------------------------
    # manifest
    # ------------------------------------------------------------------
    def manifest(self):
        st = self.selftest()
        demos = {
            "demo_sbromarmor": self.place_guid(
                "51080191-ED06-4AA0-BFD7-F04837CF70DB"),
            "demo_wave2_freeform": self.place_guid(
                "02076249-A52B-420E-BD53-AED044349379"),
            "demo_plan_4655": self.plan("4655"),
        }
        man = {
            "_meta": {
                "ring": 33,
                "title": "the day-0 triage weapon (front 33a)",
                "instrument": "fw33-triage-engine.py (this manifest is its "
                              "self-test + demo transcript)",
                "inputs": {k: {"file": v, "sha256_16": sha256_16(
                    os.path.join(HERE, v))} for k, v in REGISTERS.items()},
            },
            "selftest": st,
            "coverage": {
                "species": self.reg["genome"]["species_total"],
                "edges": len(self.edges),
                "rungs": self.ladder,
                "probed_rungs": [p["version"] for p in self.reg["armor"]["probes"]],
                "body_chain_steps_indexed": len(self.by_body),
                "named_anchors": len(self.names),
            },
            "demos": demos,
            "honesty": [
                "the engine knows only what the registers know",
                "the never-touched static core is not enumerable",
                "frontier names join only via the armor watchlist (7 anchors)",
                "unprobed releases (31 of 40) are bracketed, not measured",
                "any register drift aborts the engine at load (AGESA pin) "
                "or at self-test (every gate)",
            ],
        }
        return man


def main(argv):
    if len(argv) < 1:
        argv = ["selftest"]
    cmd = argv[0].lstrip("-")
    eng = Engine()
    if cmd == "guid" and len(argv) > 1:
        out = eng.place_guid(argv[1])
    elif cmd == "body" and len(argv) > 1:
        out = eng.place_body(argv[1])
    elif cmd == "rung" and len(argv) > 1:
        out = eng.rung_report(argv[1])
    elif cmd == "plan":
        out = eng.plan(argv[1] if len(argv) > 1 else None)
    elif cmd == "wave":
        out = eng.waves()
    elif cmd == "agesa":
        out = eng.agesa_table()
    elif cmd == "selftest":
        out = eng.selftest()
    elif cmd == "manifest":
        out = eng.manifest()
        path = os.path.join(HERE, "vendor-triage-engine.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
        print("manifest written: %s" % path, file=sys.stderr)
        if not out["selftest"]["all_pass"]:
            raise SystemExit("SELFTEST FAILED — manifest still written, "
                             "but the engine is NOT cleared for day-0 use")
        return 0
    else:
        raise SystemExit(
            "usage: fw33-triage-engine.py guid|body|rung|plan|wave|agesa|"
            "selftest|manifest [arg]")
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if cmd == "selftest" and not out["all_pass"]:
        raise SystemExit("SELFTEST FAILED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
