#!/usr/bin/env python3
"""fw39-identity — the identity engine (le moteur d'identité), ring 39.

The H3 machine. Ring 38 rehearsed the exam; this ring answers the question
the 16/09 dump will actually pose: IS THIS IMAGE ONE OF THE KNOWN RELEASES,
or is it a published-but-unlisted build (H3, P-18)? Every earlier instrument
MEASURES; this one JUDGES IDENTITY — by counting independent fingerprint
differences against every registered rung of the ASUS PRIME B450-PLUS
chronology, with each axis grounded in its own register and each convention
measured live on the surviving corpus before freezing.

Fingerprint axes (each = one independent identity feature, obs vs anchor):
  rom_sha        DECISIVE — whole-file sha256[:16] AND body sha256[:16]
                 (rom[0x40000:], the CAP-strip convention). Measured live:
                 3604/4655 anchors are FULL-file (rom_bytes 16777216);
                 3802..4631 anchors are BODY (rom_bytes 16515072). Both
                 forms are always computed from the dump; an anchor matches
                 under ITS registered convention.
  agesa_level    top near-marker token (fw38 x_agesa); na when ambiguous
  dsdt_sha16_set all checksum-valid DSDTs across pierced payloads
  smm_census     the lifecycles 3-bucket dict (SMM / SMM-DXE / SMM-core)
  trust_certs    NEW lens born this ring: raw-plane DER census. Validated
                 on 3604: 12 sightings / 4 distinct / each cert exactly x3
                 (PK/KEK/db), set == vendor-der-inventory EXACTLY.
  armor_core     the four core-armor module names present (fw38 x_armor)
  armor_added    watchlist-prefix GUIDs present (fw38 x_armor)
  genome_profile (wave1_present, wave2_present, legacy_present) — the
                 registered birth/death species, counted from inventory GUIDs

Report-only (measured, never scored — each for a named reason):
  module_count   THREE-WAY semantics mismatch measured live this ring:
                 fw37 walk 580 vs probes 618 vs genome 608 @3604 — the
                 axis is identity-deaf until the walks are reconciled
  whitelist_str  the family STRING pool (may be rung-invariant; the live
                 self-ID decides — if constant across rungs it carries no
                 identity signal)
  genome_full_set full GUID-set intersection stats (580 vs 608 walk gap)
  psp            report-only per the ring-38 honesty ledger (no verdict
                 invented without specimen-validated reimplementation)

Verdict semantics (feeds fw35 P-18 / ck_identity_h3 directly):
  sha-hit            matches_known_release=True  (byte-identical to a rung)
  no-match, min>=3   matches_known_release=False, count=min  -> H3-eligible
  no-match, min 1-2  matches_known_release=False, count=min  -> below floor
  na axes never count; every draft names its nearest neighbour and the
  per-rung diff axes, so a human can audit any verdict in one read.

Modes: lens | fingerprint | anchors | identify | matrix | selftest | manifest
stdlib-only, read-only, docs-side. Two-tier selftest (fw36/37/38 discipline):
tier R re-derives every anchor and convention from the registers; tier I
runs the chain live on the surviving corpus.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RING = 39
RUNGS = ["3604", "3802", "3810", "4003", "4202", "4402", "4604", "4631",
         "4655"]
ROM_FULL = 16777216
BODY_OFF = 0x40000            # the CAP-strip convention: cap[0x40800:] == rom[0x40000:]

SCORE_AXES = ["rom_sha", "agesa_level", "dsdt_sha16_set", "smm_census",
              "trust_certs", "armor_core", "armor_added", "genome_profile"]
REPORT_ONLY = ["module_count", "whitelist_str", "genome_full_set", "psp"]


def _sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def _load_mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


fw35 = fw36 = fw37 = fw38 = None


def _mods():
    global fw35, fw36, fw37, fw38
    if fw38 is None:
        fw35 = _load_mod("fw35-oracle")
        fw36 = _load_mod("fw36-atlas")
        fw37 = _load_mod("fw37-differ")
        fw38 = _load_mod("fw38-exam")
    return fw35, fw36, fw37, fw38


def _reg(name):
    with open(os.path.join(HERE, f"{name}.json")) as f:
        return json.load(f)


def reg_agesa():
    return _reg("vendor-agesa")


def reg_armor():
    return _reg("vendor-flash-armor")


def reg_genome():
    return _reg("vendor-genome")


def reg_acpi():
    return _reg("vendor-acpi")


def reg_chipdb():
    return _reg("vendor-armor-chipdb")


def reg_lifecycles():
    return _reg("vendor-lifecycles")


def reg_der():
    return _reg("vendor-der-inventory")


# --------------------------------------------------------------- trust lens
# (NEW this ring; conventions measured live on asus-prime-b450-plus-ref.rom)

def _dlen(b, o):
    """DER TLV length for a SEQUENCE at o (short / 0x81 / 0x82 forms)."""
    if o + 2 > len(b) or b[o] != 0x30:
        return None
    if b[o + 1] == 0x82:
        if o + 4 > len(b):
            return None
        return struct.unpack(">H", b[o + 2:o + 4])[0] + 4
    if b[o + 1] == 0x81:
        if o + 3 > len(b):
            return None
        return b[o + 2] + 3
    if b[o + 1] < 0x80:
        return b[o + 1] + 2
    return None


def is_der_cert(b, o):
    """X.509 Certificate ::= SEQ { tbs SEQ, sigAlg SEQ, sig BIT STRING }.
    Structural validation only — no subject parsing (the ring-22 register
    already carries subjects; this lens only needs identity + count)."""
    ln = _dlen(b, o)
    if not ln or ln < 64 or o + ln > len(b):
        return False
    body = b[o:o + ln]
    if body[4] != 0x30:
        return False
    tb = _dlen(body, 4)
    if not tb or 4 + tb >= ln:
        return False
    o2 = 4 + tb
    if body[o2] != 0x30:
        return False
    sa = _dlen(body, o2)
    if not sa:
        return False
    o3 = o2 + sa
    if o3 >= ln or body[o3] != 0x03:
        return False
    return True


def cert_census(buf):
    """Distinct DER certs in one buffer: {sha16: [offsets]}."""
    out, o = {}, 0
    while True:
        o = buf.find(b"\x30\x82", o)
        if o < 0:
            break
        if is_der_cert(buf, o):
            ln = _dlen(buf, o)
            sha = _sha16(buf[o:o + ln])
            out.setdefault(sha, []).append(o)
        o += 1
    return out


def trust_census(raw):
    """The trust-material census: RAW PLANE only (the PK/KEK/db default
    stores live in the NVRAM region, outside FVMAIN). Returns
    {sha16: [offsets]} — sightings are the offsets, distinct is the keys."""
    return cert_census(raw)


# ------------------------------------------------------ genome derivations

def _t_bside(label):
    """'asus-4003->asus-4202' -> '4202' (the rung the change LANDED at)."""
    return label.split("->")[1].replace("asus-", "")


def genome_species():
    return reg_genome()["species"]


def genome_present_at(rung):
    """Species GUIDs present at rung R: born at B(born_at)<=R; dead at
    B(dead_at)>R; born_at None means present since the genome base (3604)."""
    ri = RUNGS.index(rung)
    out = []
    for s in genome_species():
        b = s.get("born_at")
        d = s.get("dead_at")
        if b and RUNGS.index(_t_bside(b)) > ri:
            continue
        if d and RUNGS.index(_t_bside(d)) <= ri:
            continue
        out.append(s["guid"].upper())
    return set(out)


def quartet_guids():
    """The four core-armor species, by the registered genome flag
    'armor_quartet' (names travel in the register too: PrepareWhiteListSmm,
    SbRomArmorSmm, FlashSmiSmm, FlashSmiDxe)."""
    return {s["guid"].upper() for s in genome_species()
            if "armor_quartet" in (s.get("flags") or [])}


def sbrom_guid():
    """The SbRomArmorSmm species GUID, by the registered names list."""
    for s in genome_species():
        if "SbRomArmorSmm" in (s.get("names") or []):
            return s["guid"].upper()
    return None


def genome_flags():
    """The registered birth/death species sets the profile axis counts."""
    w1, w2, legacy = set(), set(), set()
    for s in genome_species():
        b, d = s.get("born_at"), s.get("dead_at")
        fl = s.get("flags") or []
        if b and _t_bside(b) == "3802":
            w1.add(s["guid"].upper())
        if b and _t_bside(b) == "4604":
            w2.add(s["guid"].upper())
        if d:
            legacy.add(s["guid"].upper())
        if "legacy_death_4402" in fl:
            legacy.add(s["guid"].upper())
    return w1, w2, legacy


def genome_profile_anchor(rung):
    """(wave1_present, wave2_present, legacy_present) expected at rung."""
    w1, w2, legacy = genome_flags()
    pres = genome_present_at(rung)
    return (len(w1 & pres), len(w2 & pres), len(legacy & pres))


# ----------------------------------------------------------- anchor vectors

def _agesa_anchor():
    out = {}
    for e in reg_agesa()["timeline"]:
        v = e.get("version")
        if v in RUNGS and e.get("agesa"):
            out[v] = e["agesa"]
    return out


def _acpi_anchor():
    out = {}
    sp = reg_acpi()["specimens"]
    for r in RUNGS:
        if r not in sp:
            continue
        shas = set()
        for t in sp[r].get("shipped", []):
            if t.get("sig") == "DSDT" and t.get("sha16"):
                shas.add(t["sha16"])
        if shas:
            out[r] = shas
    return out


def _smm_anchor():
    per = reg_lifecycles()["smm_anatomy"]["smm_census_per_rung"]
    return {r: {"SMM": per[r]["SMM"], "SMM-DXE": per[r]["SMM-DXE"],
                "SMM-core": per[r]["SMM-core"]}
            for r in RUNGS if r in per}


def _cert_anchor():
    per = reg_der()["per_specimen"]
    return {r: set(per.get("asus-" + r, {}).get("trust_distinct") or [])
            for r in RUNGS if per.get("asus-" + r)}


def _probes_anchor():
    out = {}
    for p in reg_armor()["probes"]:
        v = p.get("version")
        if v in RUNGS:
            out[v] = p
    return out


def _chip_anchor():
    per = reg_chipdb()["per_specimen"]
    out = {}
    for r in RUNGS:
        e = per.get("asus-" + r)
        if e:
            fams = set()
            for ts in e.get("table_sets", []):
                fams |= set(ts)
            out[r] = fams
    return out


def _whitelist_union():
    u = set()
    for fams in _chip_anchor().values():
        u |= fams
    return sorted(u)


def anchors():
    """The registered half of every axis, per rung. sha convention follows
    each probe's rom_bytes (16777216=FULL file, 16515072=BODY rom[0x40000:])."""
    probes = _probes_anchor()
    out = {}
    for r in RUNGS:
        p = probes[r]
        rb = p.get("rom_bytes")
        sha = p.get("rom_sha256_16")
        out[r] = {
            "rom_bytes": rb,
            "rom_sha": sha,
            "sha_convention": ("FULL" if rb == ROM_FULL else
                               "BODY0x40000" if rb == ROM_FULL - BODY_OFF
                               else f"UNKNOWN({rb})"),
            "agesa_level": _agesa_anchor().get(r),
            "dsdt_sha16_set": sorted(_acpi_anchor().get(r) or []),
            "smm_census": _smm_anchor().get(r),
            "trust_certs": sorted(_cert_anchor().get(r) or []),
            "armor_core": p.get("core_armor"),
            "armor_added": len(p.get("added_present") or []),
            "genome_profile": list(genome_profile_anchor(r)),
            "files": reg_genome()["per_rung_file_counts"].get(
                "asus-" + r, {}).get("files"),
            "probe_modules": p.get("modules"),
        }
    return out


# ---------------------------------------------------------- byte fingerprints

def _deep_inventory(image):
    """The identity lens's walk: fw37 primitives, DEEPER piercing.

    Why this exists (measured live, ring 39): fw37.inventory pierces ONE
    level (FVMAIN_COMPACT -> payload). On ASUS vendor builds the flash-
    armor wave (the five wave-1 species incl. 89BE47F4-80CE-4B87-ABD1-
    D279AB6A16AE and the named quartet) lives inside a NESTED guided
    LZMA section that the level-1 pierce does not reach — the shallow
    walk sees 583 files vs the genome's 608 and misses exactly the armor
    species (their only raw-plane occurrence is an HII string reference,
    not a file). Under-reporting here would INFLATE the diff count of a
    day-0 dump against its true sibling rung (sha + armor + wave1 = 3
    artificial diffs on a mere repack) — a manufactured H3. The lens
    therefore pierces recursively (depth cap 3) and walks every FV of
    every level with the fw37 iter_files semantics verbatim.
    """
    fw35, fw36, fw37, fw38 = _mods()
    raw = fw37.load(image)
    names_fb = fw37.Engine().census_names()
    modules, by_type, fv_rows = {}, {}, []

    seen, frontier, level = [], [raw], 0
    while frontier and level < 3:
        nxt = []
        for blob in frontier:
            outs, _notes = fw37.pierce_all(blob)
            for o in outs:
                if o not in seen:
                    seen.append(o)
                    nxt.append(o)
        frontier = nxt
        level += 1

    blobs = [raw] + seen
    for bi, blob in enumerate(blobs):
        for fi, fv in enumerate(fw37.scan_fvs(blob)):
            hlen = fv["hlen"]
            fv_rows.append({"blob": bi, "fv": fi, "offset": fv["offset"],
                            "length": fv["length"],
                            "fs_guid": fv["fs_guid"]})
            for guid, ftype, size, off, body in fw37.iter_files(
                    blob, fv, hlen):
                if ftype in (0xF0, 0x01):
                    continue
                name = fw37.ui_name(body)
                if name is None and names_fb:
                    name = names_fb.get(guid)
                modules[guid] = {"name": name, "ftype": ftype,
                                 "ftype_name": fw37.FILE_TYPES.get(
                                     ftype, f"type_{ftype:#04x}"),
                                 "size": size, "sha8": fw37.sha256_16(body),
                                 "blob": bi, "fv": fi, "offset": off}
                tn = fw37.FILE_TYPES.get(ftype, f"type_{ftype:#04x}")
                by_type[tn] = by_type.get(tn, 0) + 1
    return {"modules": modules, "by_type": by_type,
            "blobs": blobs,
            "fv_census": {"blobs": len(blobs), "fvs": fv_rows},
            "module_count": len(modules),
            "pierce_depth": level}


def fingerprint(image, deep=True):
    """The observed half of every axis, from bytes alone. deep=False keeps
    the cheap raw-plane lenses (sha, certs) and skips the FVMAIN chain."""
    fw35, fw36, fw37, fw38 = _mods()
    raw = fw37.load(image)
    obs = {
        "instrument": "fw39-identity", "ring": RING, "image": image,
        "rom_bytes": len(raw),
        "rom_sha_full": _sha16(raw),
        "rom_sha_body": _sha16(raw[BODY_OFF:]) if len(raw) >= ROM_FULL else None,
        "trust_sightings": 0, "trust_certs": [], "trust_offsets": {},
    }
    tc = trust_census(raw)
    obs["trust_certs"] = sorted(tc.keys())
    obs["trust_sightings"] = sum(len(v) for v in tc.values())
    obs["trust_offsets"] = {k: v for k, v in tc.items()}

    if not deep:
        return obs

    payloads, notes = fw37.pierce_all(raw)
    inv = _deep_inventory(image)
    hay = inv["blobs"]

    ag = fw38.x_agesa(haystacks=hay)
    lvl = ag["agesa_level"]
    obs["agesa_level"] = (lvl.get("picked") if isinstance(lvl, dict) else lvl)
    obs["agesa_multi"] = (lvl.get("multiple") if isinstance(lvl, dict) else None)
    obs["agesa_string"] = ag["agesa_string"]

    # the ACPI register convention: every checksum-valid DSDT instance
    # counts; the variants ship 1-2x each (the occ-2 variant is the clock
    # anchor). Collect across ALL deep blobs, keep per-sha instance counts.
    dsdt_seen = {}
    for blob in hay:
        w = fw38.x_acpi(blob)
        for t in w["tables"].get("DSDT", []):
            if t.get("checksum_ok") and t.get("sha16"):
                dsdt_seen[t["sha16"]] = dsdt_seen.get(t["sha16"], 0) + 1
    obs["dsdt_sha16_set"] = sorted(dsdt_seen)
    obs["dsdt_instances"] = dsdt_seen
    obs["dsdt_primary"] = (max(dsdt_seen, key=lambda k: dsdt_seen[k])
                           if dsdt_seen else None)

    obs["smm_census"] = fw38.x_smm_census(inv)["buckets"]

    guids = {g.upper() for g in inv["modules"]}
    q = quartet_guids()
    obs["armor_core"] = len(q & guids)
    obs["armor_quartet_present"] = obs["armor_core"] == 4
    sg = sbrom_guid()
    obs["sbrom_armorsmm_present"] = (sg in guids) if sg else None
    obs["quartet_present_guids"] = sorted(q & guids)
    wl7 = fw38.watchlist_prefixes()
    obs["armor_added"] = len([p for p in wl7
                              if any(g.startswith(p)
                                     or g.replace("-", "").startswith(p)
                                     for g in guids)])

    wl = fw38.x_whitelist(hay, _whitelist_union())
    obs["whitelist_str"] = sorted(wl["found"])
    day0_41 = fw38.chip_families_for("day0-3644")
    wld0 = fw38.x_whitelist(hay, day0_41)
    obs["chip_whitelist_families"] = wld0["families_found"]

    w1, w2, legacy = genome_flags()
    obs["genome_profile"] = [len(w1 & guids), len(w2 & guids),
                             len(legacy & guids)]
    obs["genome_full_set"] = {
        "observed": len(guids),
        "report": "deep walk (recursive pierce, raw-plane FVs included); "
                  "module_count stays report-only — the residual gap vs "
                  "the genome counts is itself measured",
    }
    obs["module_count"] = inv["module_count"]
    obs["pierce_depth"] = inv["pierce_depth"]
    obs["blobs_walked"] = inv["fv_census"]["blobs"]

    lg = fw38.legacy_dead_guids()
    obs["legacy_smm_count"] = len([
        d for d in lg
        if any(g.replace("-", "").startswith(d.replace("-", "").upper())
               for g in guids)])

    # PSP candidates: report-only (ring-38 honesty ledger)
    pspr = fw38.x_psp(raw)
    obs["psp_candidates"] = len(pspr if isinstance(pspr, list)
                                else pspr.get("candidates", []))
    return obs


# ---------------------------------------------------------------- comparison

def _axis_comparable(name, obs, anc):
    o = obs.get(name)
    a = anc.get(name)
    if o is None or a is None:
        return False
    if name == "rom_sha":
        # obs carries both forms; anc is the registered sha16 under its
        # own convention — comparable iff either form matches it OR the
        # convention is resolvable (both forms computed)
        return True
    if isinstance(a, (list, set)):
        return isinstance(o, (list, set))
    if isinstance(a, dict):
        return isinstance(o, dict)
    return True


def _axis_equal(name, obs, anc, rung=None):
    o, a = obs.get(name), anc.get(name)
    if name == "rom_sha":
        o = obs.get("rom_sha_full")
        conv = (anc.get("sha_convention") if isinstance(anc, dict)
                else None)
        if conv == "FULL":
            return o == a
        if conv == "BODY0x40000":
            body = obs.get("rom_sha_body")
            return body == a if body else o == a
        # unknown convention: match if EITHER form agrees (honest union)
        return (o == a) or (obs.get("rom_sha_body") == a)
    if isinstance(a, (list, set)) and isinstance(o, (list, set)):
        return set(o) == set(a)
    if isinstance(a, dict) and isinstance(o, dict):
        return {k: v for k, v in o.items()} == {k: v for k, v in a.items()}
    return o == a


def identify(image, deep=True):
    """Judge identity against every rung. Returns the per-rung diff table
    (comparable axes only), the verdict, and the fw35-ready keys."""
    obs = fingerprint(image, deep=deep)
    anc = anchors()
    per_rung, for_report = {}, {}
    for r in RUNGS:
        a = anc[r]
        diffs, axes, na_axes = 0, [], []
        for ax in SCORE_AXES:
            av = a.get(ax)
            if ax == "rom_sha":
                cmp_ok = True
            else:
                cmp_ok = _axis_comparable(
                    ax, {k: obs.get(k) for k in SCORE_AXES},
                    {ax: av}) and not (ax == "agesa_level"
                                       and obs.get("agesa_multi"))
            if not cmp_ok:
                na_axes.append(ax)
                continue
            if not _axis_equal(ax, obs, {"rom_sha": a["rom_sha"],
                                         "sha_convention": a["sha_convention"],
                                         ax: av}, rung=r):
                diffs += 1
                axes.append(ax)
        per_rung[r] = {"diffs": diffs, "diff_axes": axes,
                       "na_axes": na_axes,
                       "sha_hit": _axis_equal(
                           "rom_sha", obs,
                           {"rom_sha": a["rom_sha"],
                            "sha_convention": a["sha_convention"]},
                           rung=r)}
    sha_rungs = [r for r in RUNGS if per_rung[r]["sha_hit"]]
    if sha_rungs:
        verdict = {
            "verdict": "known-release",
            "matches_known_release": True,
            "distinct_fingerprints_count": 0,
            "matched_release": sha_rungs[0] if len(sha_rungs) == 1
            else sha_rungs,
            "note": "byte-identity under the registered sha convention",
        }
    else:
        best = min(RUNGS, key=lambda r: (per_rung[r]["diffs"], r))
        n = per_rung[best]["diffs"]
        if n >= 3:
            v, note = "no-match-h3-eligible", (
                "differs from EVERY registered release by >=3 independent "
                "fingerprints — the P-18 H3 shape")
        else:
            v, note = "no-match-below-floor", (
                "closest rung separates by <3 axes — a repack or a "
                "neighbour build, NOT H3-eligible as counted")
        verdict = {"verdict": v,
                   "matches_known_release": False,
                   "distinct_fingerprints_count": n,
                   "nearest_release": best,
                   "nearest_diff_axes": per_rung[best]["diff_axes"],
                   "note": note}
    return {"image": image, "observed": obs, "per_rung": per_rung,
            "verdict": verdict}


# ------------------------------------------------------------------- matrix

def matrix():
    """Anchor-vs-anchor separation across all 45 rung pairs, full axes and
    semantic-only (rom_sha excluded — every distinct build trivially
    differs in bytes; the SEMANTIC floor calibrates the H3 threshold)."""
    anc = anchors()
    pairs, full_floor, sem_floor = [], None, None
    for i, a in enumerate(RUNGS):
        for b in RUNGS[i + 1:]:
            full, sem = 0, 0
            for ax in SCORE_AXES:
                av, bv = anc[a][ax], anc[b][ax]
                if ax == "rom_sha":
                    if av != bv:
                        full += 1
                    continue
                if av is None or bv is None:
                    continue
                if isinstance(av, (list, set)):
                    if set(av) != set(bv):
                        full += 1
                        sem += 1
                elif isinstance(av, dict):
                    if av != bv:
                        full += 1
                        sem += 1
                else:
                    if av != bv:
                        full += 1
                        sem += 1
            pairs.append({"pair": f"{a}|{b}", "full": full, "semantic": sem})
            full_floor = full if full_floor is None else min(full_floor, full)
            sem_floor = sem if sem_floor is None else min(sem_floor, sem)
    return {"pairs": pairs, "floor_full": full_floor,
            "floor_semantic": sem_floor,
            "n_pairs": len(pairs)}


# ----------------------------------------------------------------- selftest

def selftest(all_rungs=False):
    fw35, fw36, fw37, fw38 = _mods()
    g, fails = [], []

    def gate(name, ok, detail=""):
        g.append((name, ok, detail))
        if not ok:
            fails.append(name)

    # ---- tier R: registers only -------------------------------------
    R = anchors()

    # R1 genome presence-set deltas == transition born/dead
    trans = {t["transition"]: t for t in reg_genome()["transitions"]}
    prev = genome_present_at("3604")
    ok = len(reg_genome()["species"]) == 330
    gate("R1a species_total=330", ok, f"n={len(reg_genome()['species'])}")
    for r in RUNGS[1:]:
        cur = genome_present_at(r)
        born = len(cur - prev)
        dead = len(prev - cur)
        t = trans.get(f"asus-{RUNGS[RUNGS.index(r)-1]}->asus-{r}", {})
        gate(f"R1b delta@{r}", born == t.get("born", -1)
             and dead == t.get("dead", -1),
             f"born {born}/{t.get('born')} dead {dead}/{t.get('dead')}")
        prev = cur

    # R2 profile anchors: 3604 = (0,0,2)
    gate("R2 profile@3604=(0,0,2)", R["3604"]["genome_profile"] == [0, 0, 2],
         str(R["3604"]["genome_profile"]))
    gate("R2b profile@4655 legacy=0",
         R["4655"]["genome_profile"][2] == 0, str(R["4655"]["genome_profile"]))

    # R3 cert anchors: 4@3604, 6@3810+
    ca = _cert_anchor()
    gate("R3a |certs@3604|=4", len(ca.get("3604", set())) == 4,
         str(len(ca.get("3604", set()))))
    gate("R3b |certs@3810|=6", len(ca.get("3810", set())) == 6,
         str(len(ca.get("3810", set()))))
    gate("R3c certs 3810..4655 all 6",
         all(len(ca.get(r, set())) == 6 for r in
             ["3810", "4003", "4202", "4402", "4604", "4631", "4655"]))

    # R4 AGESA ladder monotone + bracket
    aa = _agesa_anchor()
    ok = all(r in aa for r in RUNGS)
    gate("R4a agesa 9/9", ok, str(sorted(aa)))
    if ok:
        rank = fw35.agesa_rank
        mono = all(rank(aa[RUNGS[i]]) <= rank(aa[RUNGS[i + 1]])
                   for i in range(len(RUNGS) - 1))
        gate("R4b monotone", mono)
        gate("R4c 3604=1.2.0.6b", aa["3604"] == "1.2.0.6b", aa["3604"])

    # R5 DSDT anchors everywhere
    da = _acpi_anchor()
    gate("R5 dsdt 9/9 nonempty", all(da.get(r) for r in RUNGS),
         str({r: len(da.get(r) or []) for r in RUNGS}))

    # R6 SMM census anchor
    sa = _smm_anchor()
    gate("R6 smm@3604=105/0/1",
         sa.get("3604") == {"SMM": 105, "SMM-DXE": 0, "SMM-core": 1},
         str(sa.get("3604")))

    # R7 probes ladder: distinct shas, core 0/4, added 0/5x5/7x3
    pa = _probes_anchor()
    shas = [pa[r].get("rom_sha256_16") for r in RUNGS]
    gate("R7a probe shas distinct", len(set(shas)) == 9)
    gate("R7b core_armor 0@3604, 4@rest",
         pa["3604"].get("core_armor") == 0
         and all(pa[r].get("core_armor") == 4 for r in RUNGS[1:]))
    adds = [len(pa[r].get("added_present") or []) for r in RUNGS]
    gate("R7c added ladder 0/5/5/5/5/5/7/7/7",
         adds == [0, 5, 5, 5, 5, 5, 7, 7, 7], str(adds))

    # R8 sha conventions from rom_bytes
    conv = {r: R[r]["sha_convention"] for r in RUNGS}
    gate("R8a 3604/4655 FULL",
         conv["3604"] == "FULL" and conv["4655"] == "FULL", str(conv))
    gate("R8b 3802..4631 BODY0x40000",
         all(conv[r] == "BODY0x40000" for r in RUNGS[1:8]), str(conv))

    # R9 chipdb law
    chi = _chip_anchor()
    gate("R9a 41@3604", len(chi["3604"]) == 41, str(len(chi["3604"])))
    gate("R9b 46@3802+",
         all(len(chi[r]) == 46 for r in RUNGS[1:8]))

    # R10 oracle chain selftest (the 36-gate score card stays green)
    try:
        rc = fw35.main(["selftest"])
        ok = rc == 0
    except Exception:
        buf = __import__("io").StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = fw35.main(["selftest"])
        finally:
            sys.stdout = old
        ok = rc == 0
    gate("R10 fw35 oracle selftest", ok, f"rc={rc}")

    # R11 module_count honesty note stays registered
    gate("R11 module_count report-only",
         "module_count" in REPORT_ONLY and "module_count" not in SCORE_AXES)

    # ---- tier I: live corpus ----------------------------------------
    V = "/tmp/my-project/scratch-vendor"
    IMG = {
        "3604": f"{V}/asus-prime-b450-plus-ref.rom",
        "3810": f"{V}/asus-prime-b450-plus-3810.rom",
        "3802": f"{V}/asus-prime-b450-plus-3802.rom",
        "4655": f"{V}/asus-prime-b450-plus.rom",
        "tuf": f"{V}/asus/TUF-B450-PLUS-GAMING-ASUS-4645.rom",
    }
    have = {k: v for k, v in IMG.items() if os.path.exists(v)}
    corpus_absent = not any(os.path.exists(v) for v in IMG.values())
    if corpus_absent:
        print(f"fw39-identity selftest: {sum(1 for _, ok2, _ in g if ok2)}"
              f"/{len(g)} gates PASS (tier R) — tier I SKIPPED (no corpus)")
        return 0 if not fails else 1

    # I1 trust lens @3604 — the ring-22 register re-derived live
    t3604 = trust_census(fw37.load(have["3604"]))
    gate("I1a sightings=12", sum(len(v) for v in t3604.values()) == 12,
         str(sum(len(v) for v in t3604.values())))
    gate("I1b distinct set == register",
         set(t3604) == ca["3604"])
    gate("I1c each cert x3", all(len(v) == 3 for v in t3604.values()))

    # I2 trust lens @3810 + the deep semantic axes on a mid-rung
    if "3810" in have:
        t3810 = trust_census(fw37.load(have["3810"]))
        gate("I2 3810 set == register (6)",
             set(t3810) == ca["3810"], f"{len(t3810)} distinct")
        id3810 = identify(have["3810"])
        o8 = id3810["observed"]
        gate("I2b armor (4,5) @3810",
             o8.get("armor_core") == 4 and o8.get("armor_added") == 5,
             f"({o8.get('armor_core')},{o8.get('armor_added')})")
        gate("I2c sbrom present @3810",
             o8.get("sbrom_armorsmm_present") is True)
        gate("I2d self SEMANTIC diffs == 0 @3810",
             id3810["per_rung"]["3810"]["diffs"] == 0,
             str(id3810["per_rung"]["3810"]["diff_axes"]))

    # I3 the lens generalizes ACROSS boards: TUF (same vendor) carries its
    # own registered trust set (6, sharing the Microsoft material with
    # PRIME); MSI/Gigabyte factory stores are empty (the ring-22
    # cross_vendor_trust_zero gate was about OTHER vendors, not TUF).
    if "tuf" in have:
        ttuf = trust_census(fw37.load(have["tuf"]))
        treg = set(reg_der()["per_specimen"]["tuf-4645"]["trust_distinct"])
        gate("I3 TUF trust set == register (6)",
             set(ttuf) == treg, f"distinct={len(ttuf)} shared-PRIME="
             f"{len(set(ttuf) & ca['3810'])}")

    # I4/I5 fingerprint + self-identify on the anchor release
    id3604 = identify(have["3604"])
    o = id3604["observed"]
    gate("I4a sha FULL == anchor",
         o["rom_sha_full"] == pa["3604"]["rom_sha256_16"], o["rom_sha_full"])
    gate("I4b agesa 1.2.0.6b", o.get("agesa_level") == "1.2.0.6b",
         str(o.get("agesa_level")))
    gate("I4c smm 105/0/1",
         o.get("smm_census") == {"SMM": 105, "SMM-DXE": 0, "SMM-core": 1},
         str(o.get("smm_census")))
    gate("I4d certs 4", len(o.get("trust_certs") or []) == 4)
    gate("I4e armor (0,0)",
         o.get("armor_core") == 0 and o.get("armor_added") == 0,
         f"({o.get('armor_core')},{o.get('armor_added')})")
    gate("I4f profile (0,0,2)",
         list(o.get("genome_profile") or []) == [0, 0, 2],
         str(o.get("genome_profile")))
    gate("I4g dsdt set == anchor (4 variants)",
         o.get("dsdt_sha16_set") == R["3604"]["dsdt_sha16_set"],
         str(o.get("dsdt_sha16_set")))
    gate("I4h whitelist41 == 41",
         o.get("chip_whitelist_families") == 41,
         str(o.get("chip_whitelist_families")))
    gate("I4i legacy 2 @3604", o.get("legacy_smm_count") == 2,
         str(o.get("legacy_smm_count")))
    v = id3604["verdict"]
    gate("I5 self-match 3604, 0 diffs",
         v["matches_known_release"] is True
         and v.get("matched_release") == "3604"
         and v["distinct_fingerprints_count"] == 0,
         json.dumps(v)[:120])
    gate("I5b self SEMANTIC diffs == 0 @3604",
         id3604["per_rung"]["3604"]["diffs"] == 0,
         str(id3604["per_rung"]["3604"]["diff_axes"]))

    # I6 matrix shape + floor
    m = matrix()
    gate("I6a 36 pairs (C(9,2))", m["n_pairs"] == 36, str(m["n_pairs"]))
    gate("I6b floor_full >= 2", (m["floor_full"] or 0) >= 2,
         str(m["floor_full"]))
    gate("I6c floor_semantic >= 1", (m["floor_semantic"] or 0) >= 1,
         str(m["floor_semantic"]))

    # I7/I8 discrimination controls: TUF + OVMF must not self-match
    for key, name in (("tuf", "I7 TUF"),):
        if key in have:
            vid = identify(have[key])
            gate(f"{name} no-match",
                 vid["verdict"]["matches_known_release"] is False,
                 vid["verdict"]["verdict"])
    ovmf = "/tmp/my-project/scratch-ovmf/OVMF-4M-pure.fd"
    if not os.path.exists(ovmf):
        for cand in ("/tmp/my-project/scratch-ring28/OVMF_VARS_4M.fd",):
            if os.path.exists(cand):
                ovmf = cand
                break
    ovmf_ok = None
    if os.path.exists(ovmf):
        vid = identify(ovmf, deep=False)   # raw-plane only: sha+certs
        ovmf_ok = vid["verdict"]["matches_known_release"] is False
        gate("I8 OVMF no-match (raw plane)", ovmf_ok,
             vid["verdict"]["verdict"])
    else:
        gate("I8 OVMF no-match (skipped, no image)", True, "absent")

    # I9 fw35 roundtrip: the verdict keys drive P-18 as registered
    draft = {k: None for k in fw38.template_keys()}
    draft["matches_known_release"] = v["matches_known_release"]
    draft["distinct_fingerprints_count"] = v["distinct_fingerprints_count"]
    rows, _n = fw35.Oracle().score(draft)
    p18v = next(verdict for p, verdict, _note in rows if p["id"] == "P-18")
    gate("I9a self-match -> P-18 miss", p18v == "miss", p18v)
    draft2 = dict(draft)
    draft2["matches_known_release"] = False
    draft2["distinct_fingerprints_count"] = 3
    rows2, _n2 = fw35.Oracle().score(draft2)
    p18b = next(verdict for p, verdict, _note in rows2
                if p["id"] == "P-18")
    gate("I9b no-match/3 -> P-18 hit", p18b == "hit", p18b)

    n_pass = sum(1 for _, ok2, _ in g if ok2)
    for name, ok2, detail in g:
        print(f"  {'PASS' if ok2 else 'FAIL'}  {name}  {detail}")
    print(f"fw39-identity selftest: {n_pass}/{len(g)} gates PASS "
          f"({'tier I live' if not corpus_absent else 'tier R only'})")
    if all_rungs:
        print("[--all-rungs] live self-identification of every rung:")
        for r in RUNGS:
            if r in have:
                vid = identify(have[r])
                vv = vid["verdict"]
                print(f"  {r}: {vv['verdict']} "
                      f"nearest={vv.get('nearest_release', vv.get('matched_release'))} "
                      f"count={vv['distinct_fingerprints_count']}")
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fw39-identity")
    ap.add_argument("mode", choices=["lens", "fingerprint", "anchors",
                                     "identify", "matrix", "selftest",
                                     "manifest"])
    ap.add_argument("image", nargs="?", default=None)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--all-rungs", action="store_true")
    args = ap.parse_args(argv)

    if args.mode == "selftest":
        return selftest(all_rungs=args.all_rungs)
    if args.mode == "anchors":
        print(json.dumps(anchors(), indent=1, sort_keys=True))
        return 0
    if args.mode == "matrix":
        print(json.dumps(matrix(), indent=1, sort_keys=True))
        return 0
    if args.mode == "manifest":
        print(json.dumps({
            "instrument": "fw39-identity", "ring": RING,
            "title": "the identity engine — the H3 machine",
            "axes_scored": SCORE_AXES, "axes_report_only": REPORT_ONLY,
            "rungs": RUNGS,
            "modes": ["lens", "fingerprint", "anchors", "identify",
                      "matrix", "selftest", "manifest"],
        }, indent=1))
        return 0
    if not args.image:
        ap.error(f"{args.mode} requires an image path")
    if args.mode == "lens":
        fw37 = _mods()[2]
        raw = fw37.load(args.image)
        tc = trust_census(raw)
        out = {"image": args.image, "lens": "trust-certs (raw plane)",
               "sightings": sum(len(v) for v in tc.values()),
               "distinct": sorted(tc.keys()),
               "offsets": {k: v for k, v in tc.items()}}
        print(json.dumps(out, indent=1))
        return 0
    if args.mode == "fingerprint":
        print(json.dumps(fingerprint(args.image, deep=not args.fast),
                         indent=1, sort_keys=True))
        return 0
    if args.mode == "identify":
        print(json.dumps(identify(args.image, deep=not args.fast),
                         indent=1, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
