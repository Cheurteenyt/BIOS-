#!/usr/bin/env python3
# lab/fw38-exam.py — ring 38 « l'examen blanc » (the conductor + the dress rehearsal)
#
# Precedent: fw33 (triage engine), fw35 (oracle), fw36 (atlas), fw37 (differ).
# The day-0 arsenal existed but FRAGMENTED: identification (33), comparison
# (34), cartography (36), walking (37) and scoring (35) were four separate
# commands with human interpretation between each. Ring 38 closes the loop:
#
#   exam <image>        — ONE command runs the full measurable chain on any
#                         image (rom/pierce → inventory → vars → AGESA ladder
#                         → armor names → SMM census → ACPI walk → PSP scan →
#                         whitelist match) and assembles the fw35 findings
#                         draft, auto-filling every field the registers prove
#                         automatable (11 of 20 day-0 fields), then scores it.
#                         Manual lenses stay null and are LABELED, never
#                         invented.
#   exam-pair <old> <new> — the release-41 lens: same extractors on both
#                         images + the fw37 ledger (births/deaths at species
#                         level) → fills 6 of the 8 release-41 fields.
#   mock                — THE EXAMEN BLANC: the full exam chain + pair run
#                         against the surviving OVMF stand-in corpus, with
#                         the discrimination invariant asserted: on a
#                         non-target image the oracle may hit ONLY the
#                         absence-predictions (P-04/P-05); any band/presence
#                         hit on the wrong board is an over-broad oracle and
#                         the mock FAILS loudly. Proven before a board sits
#                         on the table.
#   selftest            — two-tier (fw36/fw37 discipline): tier R re-derives
#                         every anchor from the persisted registers; tier I
#                         runs the full mock LIVE on the OVMF corpus (loud
#                         skip when absent).
#   manifest            — provenance + oracle linkage.
#
# stdlib-only, read-only, no new JSON artifacts (the registers ARE the
# artifacts; the mock transcript is ephemeral; exam --out writes ONLY where
# the operator asks). Hypens in sibling names require importlib-by-path.

import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


fw37 = _mod("fw37-differ")
fw36 = _mod("fw36-atlas")
fw35 = _mod("fw35-oracle")

_sha16 = fw37.sha256_16


def _reg(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- registers
# Every register is loaded lazily; tier R re-derives the anchors from the
# SAME files, so any drift in the chain is refused before any exam runs.

_C = {}


def reg_agesa():
    if "agesa" not in _C:
        _C["agesa"] = _reg("vendor-agesa.json")
    return _C["agesa"]


def reg_flash_armor():
    if "flash" not in _C:
        _C["flash"] = _reg("vendor-flash-armor.json")
    return _C["flash"]


def reg_genome():
    if "genome" not in _C:
        _C["genome"] = _reg("vendor-genome.json")
    return _C["genome"]


def reg_acpi():
    if "acpi" not in _C:
        _C["acpi"] = _reg("vendor-acpi.json")
    return _C["acpi"]


def reg_psp():
    if "psp" not in _C:
        _C["psp"] = _reg("vendor-psp.json")
    return _C["psp"]


def reg_chipdb():
    if "chipdb" not in _C:
        _C["chipdb"] = _reg("vendor-armor-chipdb.json")
    return _C["chipdb"]


def reg_lifecycles():
    if "lifecycles" not in _C:
        _C["lifecycles"] = _reg("vendor-lifecycles.json")
    return _C["lifecycles"]


def oracle():
    if "oracle" not in _C:
        _C["oracle"] = fw35.Oracle()
    return _C["oracle"]


def template_keys():
    eng = oracle()
    keys = []
    for p in eng.reg["predictions"]:
        for k in p.get("observed_keys", []) or [p.get("observed_key")]:
            keys.append(k)
    return keys


# ---------------------------------------------------------------- helpers

def quartet_names():
    """The core-armor quartet: the NAMED members of the added_watchlist.
    Register rule: watchlist values without 'unnamed' — must be exactly
    four and must contain SbRomArmorSmm (P-05's subject)."""
    wl = reg_flash_armor()["added_watchlist"]
    named = sorted(n for n in wl.values() if "unnamed" not in n)
    return named


def watchlist_prefixes():
    """GUID prefixes (8 hex chars) of the added watchlist — the added-species
    identity used by exam-pair for added_present_count."""
    out = []
    for k in reg_flash_armor()["added_watchlist"]:
        p = k.replace("…", "").strip()
        if len(p) >= 8:
            out.append(p[:8].upper())
    return out


def legacy_dead_guids():
    """The legacy-SMM species: genome species whose dead_at transition
    lands on 4202/4402 (the register's labels are transition strings —
    P-07's basis: deaths are EXACTLY the two legacy retirements)."""
    out = []
    for s in reg_genome()["species"]:
        d = s.get("dead_at")
        if isinstance(d, str):
            tail = d.split("->")[-1]      # transition labels carry the
            if tail.endswith(("4202", "4402")):   # vendor prefix (asus-)
                out.append(s["guid"])
    return sorted(out)


def agesa_ladder():
    """[(agesa, version, date)] from the timeline — the domestic rungs."""
    out = []
    for t in reg_agesa()["timeline"]:
        if t.get("agesa"):
            out.append((t["agesa"], t["version"], t.get("date")))
    return out


AGESA_RE = re.compile(rb"1\.2\.0\.[0-9A-Za-z]{1,3}")
COMBO_RE = re.compile(rb"Combo[A-Za-z0-9]{0,6}PI")


def x_agesa(haystacks):
    """AGESA lens: version tokens NEAR the AGESA/Combo markers first; the
    combo prefix literal for P-03. Never guesses: no marker → null."""
    near, combo_hits = {}, []
    for hay in haystacks:
        for m in re.finditer(rb"AGESA|Combo[A-Za-z0-9]{0,6}PI", hay):
            lo, hi = max(0, m.start() - 96), min(len(hay), m.end() + 96)
            for t in AGESA_RE.findall(hay[lo:hi]):
                near[t.decode()] = near.get(t.decode(), 0) + 1
        for m in COMBO_RE.finditer(hay):
            s = m.group().decode()
            if s not in combo_hits:
                combo_hits.append(s)
    level = None
    if near:
        top = sorted(near.items(), key=lambda kv: -kv[1])
        level = top[0][0]
        if len(top) > 1:            # several version-like tokens: the draft
            level = {"__multi__": [k for k, _ in top],  # stays null, the
                     "picked": top[0][0]}               # human decides
    combo = None
    for c in combo_hits:
        if c == "ComboAM4v2PI":
            combo = c
            break
    if combo is None and combo_hits:
        combo = combo_hits[0]
    ladder_pos = None
    lv = (level or {}).get("picked") if isinstance(level, dict) else level
    if lv:
        for i, (a, v, d) in enumerate(agesa_ladder()):
            if a == lv:
                ladder_pos = {"rung": v, "date": d, "index": i,
                              "rungs": len(agesa_ladder())}
                break
    return {"agesa_level": lv if not isinstance(level, dict) else
            {"multiple": level["__multi__"], "picked": level["picked"]},
            "agesa_string": combo, "tokens_near_marker": near,
            "ladder_position": ladder_pos}


def x_armor(inv):
    """Armor lens: quartet + SbRomArmorSmm by NAME presence; added-species
    count by watchlist GUID prefix presence (the stronger identity)."""
    names = {m.get("name") for m in inv["modules"].values()
             if m.get("name")}
    guids = {g.upper() for g in inv["modules"]}
    q = quartet_names()
    present = [n for n in q if n in names]
    prefixes = watchlist_prefixes()
    found = [p for p in prefixes
             if any(g.startswith(p) or g.replace("-", "").startswith(p)
                    for g in guids)]
    return {"armor_quartet_present": len(present) == len(q) and bool(q),
            "sbrom_armorsmm_present": "SbRomArmorSmm" in names,
            "quartet_present_names": present,
            "core_armor_count": len(present),
            "added_present_count": len(found),
            "watchlist_size": len(prefixes)}


def x_smm_census(inv):
    """Census buckets EXACTLY as the lifecycles register convention:
    SMM / SMM-DXE / SMM-core from the FV file types (0x0A/0x0C/0x0D)."""
    bt = inv["by_type"]
    census = {"SMM": bt.get("smm", 0),
              "SMM-DXE": bt.get("combined_smm_dxe", 0),
              "SMM-core": bt.get("smm_core", 0)}
    return {"buckets": census, "smm_census_total": sum(census.values())}


def x_legacy_smm(inv):
    """P-07 lens: how many of the two registered legacy-SMM species (dead at
    4202/4402) are present in this image."""
    dead = legacy_dead_guids()
    guids = {g.upper() for g in inv["modules"]}
    found = [d for d in dead
             if any(g.replace("-", "").startswith(
                 d.replace("-", "").upper()) for g in guids)]
    return {"legacy_smm_count": len(found), "species": len(dead)}


# ---------------------------------------------------------------- ACPI walk

def _table_at(body, off, sigs=None):
    """Parse an ACPI table header at off; return dict or None. Checksum is
    REPORTED, never faked: a bad-checksum table is carried with
    checksum_ok=false so the human sees it."""
    if off < 0 or off + 36 > len(body):
        return None
    sig = body[off:off + 4]
    if sigs is not None and sig not in sigs:
        return None
    length = int.from_bytes(body[off + 4:off + 8], "little")
    if length < 36 or off + length > len(body):
        return None
    rev = body[off + 8]
    csum_ok = (sum(body[off:off + length]) & 0xFF) == 0
    return {"sig": sig.decode("latin-1"), "off": off, "length": length,
            "revision": rev, "checksum_ok": csum_ok,
            "oem_table_id": body[off + 10:off + 18].decode("latin-1",
                                                           "replace"),
            "sha16": _sha16(body[off:off + length])}


def x_acpi(body):
    """The ACPI walk on ONE pierced payload (or raw): RSDP pointer-walk
    first (20-byte checksum validated), then a checksum-validated sig-scan
    fallback for DSDT/SSDT — the ring-36-era footprint heuristic validated
    only by length plausibility; this walk SUPERSEDES it with real
    checksums and reports every verdict. Never raises."""
    out = {"rsdp": [], "tables": {}, "rejected": [], "dsdt": None,
           "ssdts": [], "aod_ssdt_revision": None, "walk": []}
    if len(body) < 64:
        return out
    # --- RSDP candidates
    pos = 0
    roots = []
    while True:
        off = body.find(b"RSD PTR ", pos)
        if off < 0:
            break
        pos = off + 8
        ok = (off + 20 <= len(body)
              and sum(body[off:off + 20]) & 0xFF == 0)
        out["rsdp"].append({"off": off, "checksum20_ok": ok})
        if ok:
            roots.append(off)
    # --- pointer walk from every valid RSDP
    parsed = {}
    for r in roots:
        rev = body[r + 15]
        try:
            if rev >= 2:
                root_off = int.from_bytes(body[r + 24:r + 32], "little")
            else:
                root_off = int.from_bytes(body[r + 16:r + 20], "little")
        except Exception:
            continue
        if root_off <= 0 or root_off + 36 > len(body):
            continue
        root = _table_at(body, root_off)
        if not root or root["sig"] not in ("XSDT", "RSDT"):
            continue
        out["walk"].append(f"root {root['sig']} @0x{root_off:x} "
                           f"({root['length']} B, csum={root['checksum_ok']})")
        esize = 8 if root["sig"] == "XSDT" else 4
        for e in range(36, root["length"] - esize + 1, esize):
            addr = int.from_bytes(
                body[root_off + e:root_off + e + esize], "little")
            if addr <= 0 or addr + 36 > len(body):
                continue
            t = _table_at(body, addr)
            if t:
                parsed[t["off"]] = t
                if t["sig"] == "FACP":
                    dsdt_addr = 0
                    if t["length"] >= 44:
                        dsdt_addr = int.from_bytes(
                            body[addr + 40:addr + 44], "little")
                    if t["length"] >= 148 and dsdt_addr == 0:
                        dsdt_addr = int.from_bytes(
                            body[addr + 140:addr + 148], "little")
                    d = _table_at(body, dsdt_addr, sigs=(b"DSDT",))
                    if d:
                        parsed[d["off"]] = d
    # --- checksum-validated sig-scan fallback (union; the OVMF pierced RSDP
    # may itself be checksum-broken per the ring-36 register)
    for sig in (b"DSDT", b"SSDT"):
        pos = 0
        while True:
            off = body.find(sig, pos)
            if off < 0:
                break
            pos = off + 4
            if off not in parsed:
                t = _table_at(body, off, sigs=(sig,))
                if t:
                    parsed[t["off"]] = t
                else:
                    ln = int.from_bytes(body[off + 4:off + 8], "little") \
                        if off + 8 <= len(body) else None
                    out["rejected"].append(
                        {"sig": sig.decode("latin-1"), "off": off,
                         "length": ln,
                         "reason": "bad length or checksum"})
    # --- classify: ONLY checksum-valid tables are admitted; every failed
    # candidate (including the ring-36 false positive) is carried in
    # rejected with its reason — refusal is auditable, never silent
    tabs = sorted(parsed.values(), key=lambda t: t["off"])
    for t in tabs:
        if not t["checksum_ok"]:
            out["rejected"].append(
                {"sig": t["sig"], "off": t["off"], "length": t["length"],
                 "reason": "checksum failed",
                 "oem_table_id": t["oem_table_id"]})
            continue
        out["tables"].setdefault(t["sig"], []).append(t)
    ds = out["tables"].get("DSDT", [])
    out["dsdt"] = ds[0] if ds else None
    for s in out["tables"].get("SSDT", []):
        out["ssdts"].append(s)
        if "AOD" in (s["oem_table_id"] or ""):
            out["aod_ssdt_revision"] = s["revision"]
    return out


def x_acpi_all(payloads):
    """Walk every pierced payload; keep the checksum-pref DSDT across
    payloads. One entry per payload in the report."""
    merged = {"payloads": [], "dsdt_sha16": None,
              "aod_ssdt_revision": None, "dsdt_ok": False,
              "dsdt_rejected": []}
    best = None
    for i, p in enumerate(payloads):
        w = x_acpi(p)
        merged["dsdt_rejected"].extend(
            r["off"] for r in w["rejected"] if r["sig"] == "DSDT")
        row = {"payload": i,
               "rsdp_valid": sum(1 for r in w["rsdp"] if r["checksum20_ok"]),
               "rsdp_seen": len(w["rsdp"]),
               "walk": w["walk"],
               "sigs": {k: [t["off"] for t in v]
                        for k, v in w["tables"].items()},
               "dsdt": w["dsdt"], "ssdt_count": len(w["ssdts"]),
               "aod_ssdt_revision": w["aod_ssdt_revision"]}
        merged["payloads"].append(row)
        if w["dsdt"]:
            cand = w["dsdt"]
            if best is None or (cand["checksum_ok"]
                                and not best["checksum_ok"]):
                best = cand
    if best:
        merged["dsdt_sha16"] = best["sha16"]
        merged["dsdt_ok"] = best["checksum_ok"]
        merged["dsdt"] = best
    for row in merged["payloads"]:
        if row["aod_ssdt_revision"] is not None:
            merged["aod_ssdt_revision"] = row["aod_ssdt_revision"]
    return merged


def x_psp(raw):
    """PSP directory candidates — REPORT-ONLY (the layout_registered
    convention: 16 B header cookie/checksum/count/additional_info, 16 B
    entries). No verdict is invented: candidates carry header fields,
    entry-type sample, span and region sha16; the day-0 operator matches
    them against vendor-psp specimens (fw33 place_body) per §1.2."""
    cands = []
    for magic in (b"$PSP", b"$PL2", b"$BHD", b"$BL2"):
        pos = 0
        while True:
            off = raw.find(magic, pos)
            if off < 0:
                break
            pos = off + 4
            if off + 16 > len(raw):
                continue
            count = int.from_bytes(raw[off + 8:off + 12], "little")
            addinfo = int.from_bytes(raw[off + 12:off + 16], "little")
            end = off + 16 + count * 16
            if count == 0 or count > 512 or end > len(raw):
                continue
            types = [raw[off + 16 + i * 16] for i in range(min(count, 24))]
            cands.append({"magic": magic.decode(), "offset": f"0x{off:x}",
                          "count": count,
                          "additional_info": f"0x{addinfo:x}",
                          "address_mode_bits": (addinfo >> 30) & 3,
                          "types_sample": types, "span": end - off,
                          "region_sha16": _sha16(raw[off:end])})
    return cands


def x_whitelist(haystacks, families):
    """Whitelist lens: how many of the REGISTERED family strings are present
    in the image (utf-8 and utf-16-le tried). Under-reports if the board
    carries unregistered families — the honesty note travels with the
    finding."""
    found, missing = [], []
    for fam in families:
        b8 = fam.encode("utf-8", "replace")
        b16 = fam.encode("utf-16-le", "replace")
        if any(b8 in h or b16 in h for h in haystacks):
            found.append(fam)
        else:
            missing.append(fam)
    return {"families_total": len(families), "families_found": len(found),
            "families_missing": len(missing), "found": found}


# ---------------------------------------------------------------- conductor

MANUAL_DAY0 = {
    "trust_cert_distinct": "DER lens (§2): distinct DER blob count — "
                           "manual, matched against vendor-der-inventory",
    "ifr_questions_total": "IFR grammar lens (§3) — manual",
    "ifr_valid_fraction": "IFR grammar lens (§3) — manual",
    "setup_uncovered_bytes": "IFR×varstore cross (§3/§4) — manual",
    "varstore_uncovered_share_pct": "IFR×varstore cross (§3/§4) — manual; "
                                    "P-16 band 83.0-86.0 (board-anchored)",
    "matches_known_release": "composite H3 judgement (§1) — manual, "
                             "P-18 requires >=3 independent fingerprints",
    "distinct_fingerprints_count": "counted from the §1-§3 tables — manual",
    "psp_hashes_3644": "PSP entry hashes (§1.2) — manual; candidates are "
                       "listed by the psp lens (region sha16)",
    "psp_hashes_3604": "manual — compare candidates to vendor-psp specimen",
    "psp_hashes_3802": "manual — compare candidates to vendor-psp specimen",
}


def chip_families_for(target):
    """day0-3644 lens = the 3604 table set (41, P-06 basis); release-41 lens
    = the frozen 46-family state (P-26 basis — frozen from 3802)."""
    per = reg_chipdb()["per_specimen"]
    if target == "day0-3644":
        return per["asus-3604"]["table_sets"][0]
    # release-41: the first specimen with 46 families in ASUS order
    for k in ("asus-3802", "asus-3810", "asus-4003", "asus-4655"):
        s = per[k]["table_sets"][0]
        if len(s) == 46:
            return s
    return per["asus-4655"]["table_sets"][0]


def exam(image, target="day0-3644", geometry=True):
    """The full measurable chain on ONE image → exam dict + findings draft."""
    raw = fw37.load(image)
    payloads, notes = fw37.pierce_all(raw)
    names_fb = fw37.Engine().census_names()
    inv = fw37.inventory(image, names_fallback=names_fb)
    hay = [raw] + payloads

    agesa = x_agesa(haystacks=hay)
    armor = x_armor(inv)
    smm = x_smm_census(inv)
    legacy = x_legacy_smm(inv)
    acpi = x_acpi_all(payloads if payloads else [raw])
    psp = x_psp(raw)
    wl = x_whitelist(hay, chip_families_for(target))
    vars_ = fw37.walk_vars(raw)
    setup_size = None
    for r in vars_.get("latest", []):
        if r.get("name") == "Setup" and r.get("state_name") == "live":
            setup_size = r.get("size")
            break

    geo = None
    if geometry:
        try:
            geo = fw36.atlas(image)
        except Exception as e:                       # atlas is optional
            geo = {"error": f"atlas lens unavailable: {e}"}

    draft = {k: None for k in template_keys()}
    multi = isinstance(agesa["agesa_level"], dict)
    draft.update({
        "rom_bytes": len(raw),
        "agesa_level": None if multi else agesa["agesa_level"],
        "agesa_string": agesa["agesa_string"],
        "armor_quartet_present": armor["armor_quartet_present"],
        "sbrom_armorsmm_present": armor["sbrom_armorsmm_present"],
        "chip_whitelist_families": wl["families_found"],
        "legacy_smm_count": legacy["legacy_smm_count"],
        "module_count": inv["module_count"],
        "dsdt_sha16": acpi["dsdt_sha16"],
        "aod_ssdt_revision": acpi["aod_ssdt_revision"],
        "setup_varstore_size": setup_size,
        "smm_census_total": smm["smm_census_total"],
    })

    examout = {
        "instrument": "fw38-exam", "ring": 38, "image": image,
        "target": target,
        "rom": {"bytes": len(raw), "sha256_16": _sha16(raw)},
        "geometry": geo,
        "inventory": {"module_count": inv["module_count"],
                      "by_type": inv["by_type"],
                      "acpi_modules": [m.get("name") for m in
                                       inv["modules"].values()
                                       if m.get("name") and "cpi" in
                                       m["name"].lower()],
                      "pierced_payloads": len(payloads),
                      "pierced_notes": notes},
        "agesa": agesa,
        "armor": armor,
        "smm_census": smm,
        "legacy_smm": legacy,
        "acpi": {k: v for k, v in acpi.items() if k != "dsdt"},
        "psp_candidates": psp,
        "whitelist": {k: v for k, v in wl.items() if k != "found"},
        "vars": {"records": vars_.get("records"),
                 "live": vars_.get("live_variables"),
                 "distinct": vars_.get("distinct_variables"),
                 "setup_varstore_size": setup_size},
        "findings_draft": draft,
        "manual_lenses": MANUAL_DAY0,
    }
    return examout, draft


def exam_pair(old, new):
    """The release-41 lens: extractors on both images + the fw37 ledger for
    the species-level births/deaths (the genome convention)."""
    da = exam(old, target="release-41", geometry=False)[1]
    eb, db = exam(new, target="release-41", geometry=False)
    led = fw37.ledger(fw37.Engine().inv(old), fw37.Engine().inv(new))
    # species-level births/deaths: GUID truth from the ledger-semantics
    # inventories (the fw37 gate numbers prove these match the wall)
    ma = fw37.Engine().inv(old)["modules"]
    mb = fw37.Engine().inv(new)["modules"]
    births = len(set(mb) - set(ma))
    deaths = len(set(ma) - set(mb))
    # the release-41 draft carries ONLY the _41 keys — the day-0 keys of
    # the old image must NOT leak (they would re-score against day-0
    # expectations and pollute the release-41 verdicts)
    draft = {k: None for k in template_keys()}
    draft.update({
        "agesa_level_41": (db["agesa_level"] if not isinstance(
            db["agesa_level"], dict) else None),
        "core_armor_41": eb["armor"]["core_armor_count"],
        "added_present_count_41": eb["armor"]["added_present_count"],
        "births_41": births,
        "deaths_41": deaths,
        "dsdt_sha16_41": db["dsdt_sha16"],
        "chip_whitelist_families_41": db["chip_whitelist_families"],
    })
    out = {"instrument": "fw38-exam-pair", "ring": 38, "old": old,
           "new": new, "ledger": {k: v for k, v in led.items()
                                  if not k.startswith("only_in_")},
           "births_41": births, "deaths_41": deaths,
           "findings_draft": draft}
    return out, draft


# ---------------------------------------------------------------- mock

def _score_draft(draft):
    rows, n = oracle().score(draft)
    verdicts = {p["id"]: (v, note) for p, v, note in rows}
    return rows, n, verdicts


ABSENCE_PREDICTIONS = {"P-04", "P-05"}


def mock(quiet=False):
    """THE EXAMEN BLANC. Full chain + pair on the OVMF stand-in corpus with
    the discrimination invariant asserted. Returns the transcript dict;
    raises SystemExit(1) on any breach."""
    eng = fw37.Engine()
    if not eng.corpus_ok():
        raise SystemExit("MOCK SKIP (loud): OVMF corpus absent at "
                         f"{eng.corpus} — tier I cannot run")
    plain = eng.corpus_path("OVMF_CODE_4M.fd")
    secboot = eng.corpus_path("OVMF_CODE_4M.secboot.fd")
    if not os.path.exists(secboot):
        secboot = eng.corpus_path("OVMF_CODE_4M.snakeoil.fd")

    t = {}
    e1, d1 = exam(plain, target="day0-3644")
    e2, d2 = exam(secboot, target="day0-3644")
    ep, dp = exam_pair(plain, secboot)
    rows1, n1, v1 = _score_draft(d1)
    rows2, n2, v2 = _score_draft(d2)
    rowsp, np_, vp = _score_draft(dp)

    # ---- the invariants
    def hits(v):
        return {k for k, (ver, _n) in v.items() if ver == "hit"}

    h1, hp = hits(v1), hits(vp)
    t["day0_hits"] = sorted(h1)
    t["release41_hits"] = sorted(hp)
    t["assert_absence_only_day0"] = h1 <= ABSENCE_PREDICTIONS
    t["assert_no_hits_release41"] = hp == set()
    t["P-01_verdict"] = v1["P-01"][0]
    t["assert_P01_miss_on_ovmf"] = v1["P-01"][0] == "miss"
    t["P-09_verdict"] = v1["P-09"][0]
    t["assert_P09_never_hits"] = v1["P-09"][0] != "hit"
    # the runtime-ACPI corpus has NO static DSDT — the honest expectation
    # is None (refused candidates in the report), never an invented hash
    t["assert_dsdt_honest_none"] = (e1["acpi"]["dsdt_sha16"] is None
                                    and len(e1["acpi"]["dsdt_rejected"]) > 0)
    t["dsdt_deterministic"] = (e1["acpi"]["dsdt_sha16"]
                               == exam(plain, geometry=False)[0]
                               ["acpi"]["dsdt_sha16"])
    t["births_41"] = ep["births_41"]
    t["deaths_41"] = ep["deaths_41"]
    t["assert_wall_18_9"] = (ep["births_41"] == 18 and ep["deaths_41"] == 9)
    t["assert_score_roundtrip"] = (n1["na"] + n1["hit"] + n1["partial"]
                                   + n1["miss"] == 26
                                   and np_["na"] + np_["hit"]
                                   + np_["partial"] + np_["miss"] == 26)

    transcript = {
        "instrument": "fw38-exam mock", "ring": 38,
        "stand_in": {"plain": plain, "secboot": secboot},
        "day0_profile": {"totals": n1, "hits": sorted(h1)},
        "release41_profile": {"totals": np_, "hits": sorted(hp)},
        "pair": {"births_41": ep["births_41"], "deaths_41": ep["deaths_41"],
                 "byte_delta": ep["ledger"].get("byte_delta")},
        "invariants": {k: v for k, v in t.items()},
        "mock_findings_day0": d1,
        "mock_findings_release41": dp,
    }
    if not all(v for k, v in t.items() if k.startswith("assert_")):
        bad = [k for k, v in t.items()
               if k.startswith("assert_") and not v]
        if not quiet:
            print(json.dumps(transcript, indent=2))
        raise SystemExit(f"MOCK FAILED — discrimination breached: {bad}")
    return transcript


# ---------------------------------------------------------------- selftest

def selftest():
    gates = []

    def gate(name, ok, detail=""):
        gates.append((name, bool(ok), detail))

    # ---- tier R: register re-derivation (ALWAYS)
    tk = template_keys()
    used = {"rom_bytes", "agesa_level", "agesa_string",
            "armor_quartet_present", "sbrom_armorsmm_present",
            "chip_whitelist_families", "legacy_smm_count", "module_count",
            "dsdt_sha16", "aod_ssdt_revision", "setup_varstore_size",
            "smm_census_total", "agesa_level_41", "core_armor_41",
            "added_present_count_41", "births_41", "deaths_41",
            "dsdt_sha16_41", "chip_whitelist_families_41"}
    gate("R1 template 31 unique keys, every conductor field covered",
         len(set(tk)) == 31 and used <= set(tk),
         f"{len(set(tk))} unique of {len(tk)} (shared keys expected)")
    q = quartet_names()
    gate("R2 quartet = 4 named, SbRomArmorSmm in",
         len(q) == 4 and "SbRomArmorSmm" in q, ",".join(q))
    wb = reg_genome()["wave1_births"]
    prefixes = {p[:8] for p in watchlist_prefixes()}
    gate("R3 wave1_births == 5, prefixes in watchlist",
         wb["count"] == 5 and all(g[:8].upper() in prefixes
                                  for g in wb["guids"]),
         f"{wb['count']} births")
    dead = legacy_dead_guids()
    gate("R4 legacy dead species == 2 (transitions ->4202/->4402)",
         len(dead) == 2, ",".join(g[:8] for g in dead))
    ac = reg_acpi()
    found_anchor = "27d5e826e111d755" in json.dumps(ac)
    p09 = oracle().preds["P-09"]
    gate("R5 acpi anchor == oracle P-09 expect",
         found_anchor and p09.get("expect") == "27d5e826e111d755",
         f"anchor={found_anchor} expect={p09.get('expect')}")
    lad = agesa_ladder()
    gate("R6 AGESA ladder >= 9 rungs, 3644 = 1.2.0.6b",
         len(lad) >= 9 and any(a == "1.2.0.6b" and v == "3604"
                               for a, v, _d in lad),
         f"{len(lad)} rungs")
    per = reg_chipdb()["per_specimen"]
    fams46 = [k for k, v in per.items() if len(v["table_sets"][0]) == 46]
    gate("R7 chipdb 3604 == 41 families; a 46-family ASUS set exists",
         len(per["asus-3604"]["table_sets"][0]) == 41 and fams46,
         f"41@3604, 46@{fams46[:2]}")
    smm3604 = reg_lifecycles()["smm_anatomy"]["smm_census_per_rung"]["3604"]
    gate("R8 lifecycles SMM census 3604 == 105/0/1",
         smm3604 == {"SMM": 105, "SMM-DXE": 0, "SMM-core": 1},
         json.dumps(smm3604))
    lay = reg_psp()["layout_registered"]
    gate("R9 psp layout documents 16B header + 16B entry",
         "16 B" in lay.get("header", "")
         and "16 B" in lay.get("psp_entry", ""), "layout_registered")
    saved = sys.stdout
    devnull = open(os.devnull, "w")
    sys.stdout = devnull
    try:
        oracle().selftest()
        r10 = True
    except Exception:
        r10 = False
    finally:
        sys.stdout = saved
        devnull.close()
    gate("R10 oracle chain selftest passes (36/36)", r10, "fw35 invoked")
    bt = fw37.FILE_TYPES
    gate("R11 census buckets resolve in fw37 FILE_TYPES",
         bt.get(0x0A) == "smm" and bt.get(0x0D) == "smm_core"
         and bt.get(0x0C) == "combined_smm_dxe", "0x0A/0x0C/0x0D")

    # ---- tier I: LIVE on the OVMF stand-in (loud skip when absent)
    eng = fw37.Engine()
    if not eng.corpus_ok():
        print("fw38-exam selftest: %d/%d gates PASS — tier I SKIPPED "
              "(corpus absent: %s)" % (len([g for g in gates if g[1]]),
                                       len(gates), eng.corpus))
        return 0 if all(g[1] for g in gates) else 1
    plain = eng.corpus_path("OVMF_CODE_4M.fd")
    e1, d1 = exam(plain, geometry=False)
    gate("I1 exam(plain) completes, rom+modules measured",
         d1["rom_bytes"] > 0 and d1["module_count"] > 0,
         f"{d1['rom_bytes']} B / {d1['module_count']} modules")
    e2, _d2 = exam(plain, geometry=False)
    rej = e1["acpi"]["dsdt_rejected"]
    gate("I2 ACPI walk honest + deterministic on runtime-ACPI corpus",
         e1["acpi"]["dsdt_sha16"] is None and e1["acpi"] == e2["acpi"]
         and 2259668 in rej,
         f"dsdt=None, ring-36 false positive rejected @2259668: "
         f"{2259668 in rej}, {len(rej)} DSDT sig hits refused")
    gate("I2b runtime-ACPI marker present (QemuFwCfgAcpiPlatform)",
         "QemuFwCfgAcpiPlatform" in (e1["inventory"]["acpi_modules"] or []),
         str(e1["inventory"]["acpi_modules"]))
    rows1, n1, v1 = _score_draft(d1)
    h1 = {k for k, (ver, _n) in v1.items() if ver == "hit"}
    gate("I3 P-01 miss on OVMF (4M != 16M)", v1["P-01"][0] == "miss",
         f"obs={d1['rom_bytes']}")
    gate("I4 P-09 never hits on OVMF (no static DSDT: na)",
         v1["P-09"][0] != "hit", f"verdict={v1['P-09'][0]}")
    gate("I5 day0 hit-set ⊆ {P-04,P-05} (discrimination)",
         h1 <= ABSENCE_PREDICTIONS, f"hits={sorted(h1)}")
    secboot = eng.corpus_path("OVMF_CODE_4M.secboot.fd")
    if not os.path.exists(secboot):
        secboot = eng.corpus_path("OVMF_CODE_4M.snakeoil.fd")
    ep, dp = exam_pair(plain, secboot)
    gate("I6 pair wall 18 births / 9 deaths (genome level)",
         ep["births_41"] == 18 and ep["deaths_41"] == 9,
         f"{ep['births_41']}/{ep['deaths_41']}")
    rowsp, np_, vp = _score_draft(dp)
    hp = {k for k, (ver, _n) in vp.items() if ver == "hit"}
    gate("I7 release-41 hit-set empty on OVMF pair", hp == set(),
         f"hits={sorted(hp)}")
    gate("I8 fw35 score roundtrip both drafts (26 rows each)",
         len(rows1) == 26 and len(rowsp) == 26,
         f"{len(rows1)}/{len(rowsp)} rows")

    npass = sum(1 for g in gates if g[1])
    for name, ok, detail in gates:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}"
              + (f"  [{detail}]" if detail else ""))
    print(f"fw38-exam selftest: {npass}/{len(gates)} gates PASS "
          f"(tier I live)")
    return 0 if npass == len(gates) else 1


# ---------------------------------------------------------------- main

def main(argv):
    if not argv:
        argv = ["selftest"]
    cmd = argv[0].lstrip("-")

    if cmd == "selftest":
        return selftest()

    if cmd == "manifest":
        print(json.dumps({
            "instrument": "fw38-exam", "ring": 38,
            "provenance": "the conductor + the dress rehearsal: the "
                          "fragmented day-0 chain (33/34/36/37 + 35) becomes "
                          "ONE command, with the measurable fields auto-"
                          "filled and the manual lenses labeled; the mock "
                          "proves discrimination on the OVMF stand-in "
                          "before a board exists",
            "modes": ["exam <image> [--out findings.json] [--no-geometry]",
                      "exam-pair <old> <new>",
                      "mock", "selftest", "manifest"],
            "auto_day0_fields": ["rom_bytes", "agesa_level", "agesa_string",
                                 "armor_quartet_present",
                                 "sbrom_armorsmm_present",
                                 "chip_whitelist_families",
                                 "legacy_smm_count", "module_count",
                                 "dsdt_sha16", "aod_ssdt_revision",
                                 "setup_varstore_size", "smm_census_total"],
            "auto_release41_fields": ["agesa_level_41", "core_armor_41",
                                      "added_present_count_41", "births_41",
                                      "deaths_41", "dsdt_sha16_41",
                                      "chip_whitelist_families_41"],
            "manual_lenses": MANUAL_DAY0,
            "registers_fused": ["vendor-agesa", "vendor-flash-armor",
                                "vendor-genome", "vendor-acpi", "vendor-psp",
                                "vendor-armor-chipdb", "vendor-lifecycles",
                                "vendor-oracle (via fw35)"],
            "oracle_linkage": "exam → findings draft → fw35 Oracle.score; "
                              "mock asserts hit-set ⊆ {P-04,P-05} on the "
                              "stand-in (absence-predictions only) and an "
                              "empty hit-set for release-41",
            "new_in_ring38": "checksum-validated ACPI walk (supersedes the "
                             "ring-36 length-plausibility heuristic), "
                             "register-anchored legacy-SMM lens (dead at "
                             "4202/4402), report-only PSP header lens from "
                             "layout_registered",
        }, indent=2))
        return 0

    if cmd == "exam" and len(argv) > 1:
        args = argv[1:]
        image = args[0]
        out = None
        if "--out" in args:
            out = args[args.index("--out") + 1]
        e, d = exam(image, geometry="--no-geometry" not in args)
        if out:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)
            e["findings_written_to"] = out
        print(json.dumps(e, indent=2))
        rows, n, _v = _score_draft(d)
        print(f"[exam verdict draft] {n['hit']} hit / {n['partial']} partial "
              f"/ {n['miss']} miss / {n['na']} na — manual lenses "
              f"{len(MANUAL_DAY0)} remain (fill, then fw35-oracle.py score)",
              file=sys.stderr)
        return 0

    if cmd == "exam-pair" and len(argv) > 2:
        e, d = exam_pair(argv[1], argv[2])
        if "--out" in argv:
            out = argv[argv.index("--out") + 1]
            with open(out, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)
            e["findings_written_to"] = out
        print(json.dumps(e, indent=2))
        return 0

    if cmd == "mock":
        t = mock()
        print(json.dumps(t, indent=2))
        inv = t["invariants"]
        print("[examen blanc] invariants hold: "
              + ", ".join(k for k in inv if k.startswith("assert_")),
              file=sys.stderr)
        return 0

    print("modes: exam <image> [--out f.json] [--no-geometry] | "
          "exam-pair <old> <new> [--out f.json] | mock | selftest | manifest")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
