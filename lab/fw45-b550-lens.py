#!/usr/bin/env python3
"""fw45-b550-lens — the B550 lens layer (transfer calibration + anchored
proposals + the novelty-accounting reconciliation).

Ring 44 corrected the board (TUF GAMING B550-PLUS WIFI II) and read the
seven manual lens slots as loud-degraded nulls on the acquisitions, with
the honesty note attributing the nulls to calibration non-transfer.
Ring 45 MEASURES the attribution — and it was over-cautious: fw43's
proposers run on the B550 acquisitions UNCHANGED (7/7 slots proposed,
0 omitted, IFR exact-consumption validity 1.00). The ring-44 nulls were
the missing --lenses file, not an L3 refusal. What the corrected board
actually lacked was its own L2 basis: the B450 calibration rows say
nothing about B550. This instrument provides it.

    transfer calibration = the three vendor-verified acquisitions
    (b550w2-3644, b550w2-3645, b550-nw-3644) become the B550 anchor
    set; the transfer laws freeze as gates; propose re-derives every
    anchor before it proposes. A proposal that cannot re-derive the
    anchors is not proposed.

The ring-44 flagged novelty-accounting delta (summary 74 vs per-axis
walk 60) is reconciled here too — vendor-novelty-recon.json: the
serialized axes walk looked for `unregistered` keys, but fw41's
whitelist axis stores its unregistered count under `extra`; the 14
dropped rows are the B550 fan-control vocabulary (AUX0/1/2/4 Fan +
PWM-DC variants, Level 1..8) the structural extractor sweeps on the
corrected board. Zero new chip families: missing == 0, the 47-family
chip whitelist transfers whole.

Four laws (L2 re-derived for the transfer, L1/L3/L4 inherited):

  L1 PROPOSAL-NOT-MEASUREMENT   lens-shaped keys only (fw40.LENS_ONLY,
                   auto-derived); judge-owned slots NEVER proposed.
  L2-TRANSFER ANCHOR-BEFORE-PROPOSAL   propose refuses unless every
                   B550 anchor row re-derives exactly on the three
                   acquisitions (vendor-b550-lens.json). The B450
                   shared path must still reproduce the authorship
                   register — the method is one method.
  L3 LOUD DEGRADATION           an image a proposer cannot read yields
                   an omitted slot WITH the reason — never a guess.
  L4 ZERO WRITES                read-only on images; the only file
                   written is the --out document the operator asked
                   for.

Modes:
  propose <image> [--out proposals.json]   the B550-anchored day-0
                                           lens file + review table
  verify                                   re-derive every anchor row
  recon                                    the 74-vs-60 reconciliation,
                                           live on the corrected board
  selftest                                 two-tier gates (R + I live)
  manifest                                 registers + instruments
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, "/home/z/my-project/repo-bios/lib")

RING = 45
_M = {}


def _load_mod(name):
    key = f"_{name}"
    if key not in _M:
        import importlib.util
        path = os.path.join(HERE, name + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        _M[key] = m
    return _M[key]


def _mods():
    """(fw37, fw38, fw39, fw40, fw41, fw43) — the walk, the manual
    contract, the deep inventory, the weld, the corpus paths, the
    proposers whose method fw45 anchors for B550."""
    return (_load_mod("fw37-differ"), _load_mod("fw38-exam"),
            _load_mod("fw39-identity"), _load_mod("fw40-merge"),
            _load_mod("fw41-novelty"), _load_mod("fw43-proposal"))


class Refusal(Exception):
    """L1/L2/L3 refusal — loud, claimed, exit 2."""


# ---------------------------------------------------------------- registers

_LAB = HERE
_LENS_REG = os.path.join(_LAB, "vendor-b550-lens.json")
_RECON_REG = os.path.join(_LAB, "vendor-novelty-recon.json")


def _reg(path):
    if not os.path.exists(path):
        raise Refusal(f"missing register {os.path.basename(path)} — the "
                      "frozen surface is the only basis this instrument "
                      "accepts")
    with open(path) as f:
        return json.load(f)


def lens_register():
    return _reg(_LENS_REG)


def recon_register():
    return _reg(_RECON_REG)


# ---------------------------------------------------------------- anchors

ACQ = ("b550w2-3644", "b550w2-3645", "b550-nw-3644")


def acq_files():
    """image path per acquisition id, from the ring-44 register's
    acquisitions (the rom column), resolved against the corpus dir."""
    _f37, _f38, _f39, _f40, f41, _f43 = _mods()
    led = _reg(os.path.join(_LAB, "vendor-ledger-b550w2.json"))
    out = {}
    for a in led.get("acquisitions", []):
        rom = a.get("rom")
        if rom:
            out[a["rom"].replace(".rom", "")] = os.path.join(f41.CORPUS, rom)
    return out


def psp_anchor(path):
    """The PSP anchor row for one image (fw43's calibrated proposer)."""
    _f37, _f38, _f39, _f40, _f41, f43 = _mods()
    f37 = _mods()[0]
    got = f43.psp_bodies(f37.load(path))
    return {"dirs_found": got["dirs_found"],
            "dirs_valid": got["dirs_valid"],
            "by_magic": got["by_magic"],
            "blobs": got["blobs"],
            "skipped_entries": got["skipped_entries"],
            "hash_count": len(got["hashes"])}


def ifr_anchor(path):
    """The IFR + varstore-cross anchor rows for one image."""
    _f37, _f38, _f39, _f40, _f41, f43 = _mods()
    _census, totals, cross = f43.ifr_read(path)
    sr = cross.get("setup_row") or {}
    return {"totals": {k: totals[k] for k in
                       ("packages", "valid", "pages", "questions",
                        "options")},
            "cross": {k: cross[k] for k in
                      ("varstore_count", "varstore_bytes_total",
                       "varstore_bytes_covered", "uncovered_share_pct",
                       "zero_question_varstores")},
            "setup_row": {k: sr.get(k) for k in
                          ("name", "guid", "size", "covered",
                           "uncovered", "questions",
                           "offsets_beyond_size")}}


def rederive_anchors(_cache={}):
    """Every anchor row, live from the three acquisitions. Memoized per
    process (the fw39 _deep convention) — propose() and the selftest
    both call this; the walk is one walk."""
    if _cache:
        return _cache["v"]
    files = acq_files()
    missing = [k for k in ACQ if k not in files
               or not os.path.exists(files[k])]
    if missing:
        raise Refusal(f"acquisitions missing from the corpus: {missing} "
                      "(L3 loud — the anchor set cannot re-derive)")
    out = {k: {"psp": psp_anchor(files[k]), "ifr": ifr_anchor(files[k])}
           for k in ACQ}
    _cache["v"] = out
    return out


def psp_set_deltas():
    """The measured PSP body-hash set deltas (release vs board)."""
    _f37, _f38, _f39, _f40, _f41, f43 = _mods()
    f37 = _mods()[0]
    files = acq_files()
    sets = {k: set(f43.psp_bodies(f37.load(files[k]))["hashes"])
            for k in ACQ}
    a, b, c = sets["b550w2-3644"], sets["b550w2-3645"], sets["b550-nw-3644"]
    return {"release": {"w2_3644_minus_w2_3645": len(a - b),
                        "w2_3645_minus_w2_3644": len(b - a)},
            "board": {"w2_3644_minus_nw_3644": len(a - c),
                      "nw_3644_minus_w2_3644": len(c - a)}}


def cross_family_overlaps():
    """|B550 w2-3644 set ∩ B450 rung set| for the P-19 comparison rungs —
    the numbers the psp_overlap_direction checker consumes."""
    _f37, _f38, _f39, _f40, f41, f43 = _mods()
    f37 = _mods()[0]
    files = acq_files()
    sb = set(f43.psp_bodies(f37.load(files["b550w2-3644"]))["hashes"])
    out = {}
    for rung in ("3604", "3802"):
        p = os.path.join(f41.CORPUS, f41.RUNG_FILES[rung])
        out[rung] = len(sb & set(f43.psp_bodies(f37.load(p))["hashes"]))
    return out


# ---------------------------------------------------------------- propose

def propose(image, out=None):
    """The B550-anchored day-0 proposals. L2-transfer first: the three
    acquisitions must re-derive their anchors exactly, and the B450
    shared path must still reproduce the authorship register — then the
    image is proposed with the SAME method that carries both
    calibrations. The report carries the stock-3644 expectation so the
    operator's review moment can compare (the discriminator law: the
    PSP set separates 3644 from 3645; the IFR quartet cannot)."""
    _f37, _f38, _f39, f40, _f41, f43 = _mods()

    # --- L2-transfer: anchors re-derive, or nothing is proposed
    live = rederive_anchors()
    reg = lens_register()
    rows = _compare_rows(live, reg)
    bad = [r for r in rows if r["agree"] is False]
    if bad:
        raise Refusal(f"L2-transfer BROKEN: {len(bad)} anchor row(s) "
                      f"disagree ({bad[0]['image']} {bad[0]['group']}."
                      f"{bad[0]['field']} reg={bad[0]['registered']} "
                      f"got={bad[0]['reproduced']}) — nothing is "
                      "proposed on a broken basis")
    b450 = _b450_shared_path_rows()
    bad_b450 = [r for r in b450 if r["agree"] is False]
    if bad_b450:
        raise Refusal(f"L2-transfer BROKEN on the shared B450 path: "
                      f"{bad_b450[0]['field']} reg="
                      f"{bad_b450[0]['registered']} got="
                      f"{bad_b450[0]['reproduced']} — the method is one "
                      "method; if B450 drifts, B550 proposes nothing")

    # --- the proposals (fw43's proposers, fw45's basis)
    props, omitted, prov = {}, {}, {}
    got = f43.psp_bodies(_mods()[0].load(image))
    if got["dirs_valid"] == 0 or not got["hashes"]:
        omitted["psp_hashes_3644"] = ("no validated PSP directories in "
                                      "the image (L3 loud)")
    else:
        props["psp_hashes_3644"] = got["hashes"]
        prov["psp_hashes_3644"] = {
            "proposer": "psp", "method": "fw43 proposer (registered "
            "layout, fletcher32 dirs, one L2 hop, sha256_16 bodies)",
            "basis": ["vendor-psp.json layout_registered",
                      "vendor-psp-authorship.json per_specimen",
                      "vendor-b550-lens.json psp_anchors"],
            "dirs": got["dirs_valid"], "blobs": got["blobs"],
            "hash_count": len(got["hashes"])}
    for rung in ("3604", "3802"):
        key = f"psp_hashes_{rung}"
        fname = _mods()[4].RUNG_FILES.get(rung)
        path = (os.path.join(_mods()[4].CORPUS, fname)
                if fname else None)
        if not path or not os.path.exists(path):
            omitted[key] = (f"corpus rung {rung} missing ({path}) — "
                            "the comparison set needs the same method "
                            "on the real rung (L3 loud)")
            continue
        rgot = f43.psp_bodies(_mods()[0].load(path))
        if rgot["dirs_valid"] == 0 or not rgot["hashes"]:
            omitted[key] = f"no validated PSP directories on rung {rung}"
            continue
        props[key] = rgot["hashes"]
        prov[key] = {"proposer": "psp", "method": "fw43 proposer on "
                     f"corpus rung {rung}",
                     "basis": [f"corpus:{os.path.basename(path)}",
                               "vendor-psp-authorship.json per_specimen"],
                     "dirs": rgot["dirs_valid"], "blobs": rgot["blobs"]}

    _census, totals, cross = f43.ifr_read(image)
    if totals["packages"] == 0:
        omitted["ifr_questions_total"] = ("no IFR form packages found "
                                          "in the image (L3 loud)")
        omitted["ifr_valid_fraction"] = omitted["ifr_questions_total"]
    else:
        props["ifr_questions_total"] = totals["questions"]
        props["ifr_valid_fraction"] = round(
            totals["valid"] / totals["packages"], 6)
        prov["ifr_questions_total"] = {
            "proposer": "ifr", "method": "ring-6 exact-consumption walk "
            "over the fw39 deep walk (memoized)",
            "basis": ["vendor-ifr-census.json specimens",
                      "vendor-b550-lens.json ifr_anchors"],
            "totals": {k: totals[k] for k in
                       ("packages", "valid", "pages", "questions",
                        "options")}}
        prov["ifr_valid_fraction"] = {
            "proposer": "ifr", "method": "valid/packages",
            "basis": ["vendor-b550-lens.json ifr_anchors"]}
    sr = cross.get("setup_row")
    if sr is None:
        omitted["setup_uncovered_bytes"] = ("no Setup varstore row from "
                                            "the cross (L3 loud)")
    else:
        props["setup_uncovered_bytes"] = sr["uncovered"]
        prov["setup_uncovered_bytes"] = {
            "proposer": "cross", "method": "ring-20 width semantics "
            "verbatim (ONE_OF default-flag law, ring-43 re-derivation)",
            "basis": ["vendor-unasked.json coverage.setup_row",
                      "vendor-b550-lens.json cross_anchors"],
            "setup_row": {k: sr[k] for k in
                          ("size", "covered", "uncovered", "questions")}}
    if cross["varstore_bytes_total"] == 0:
        omitted["varstore_uncovered_share_pct"] = ("no sized varstores "
                                                   "from the cross")
    else:
        props["varstore_uncovered_share_pct"] = \
            cross["uncovered_share_pct"]
        prov["varstore_uncovered_share_pct"] = {
            "proposer": "cross", "method": "union coverage / size",
            "basis": ["vendor-b550-lens.json cross_anchors"],
            "share": cross["uncovered_share_pct"],
            "varstores": cross["varstore_count"]}

    f43._validate_lens_keys(props)
    bad_key = set(props) - set(f40.LENS_ONLY)
    if bad_key:
        raise Refusal(f"schema-lens: keys outside LENS_ONLY: {bad_key}")

    # --- the review table
    exp = reg.get("day0_lens_expectation", {}).get("stock_3644", {})
    print(f"propose {os.path.basename(image)}: {len(props)} slots "
          f"proposed, {len(omitted)} omitted  [fw45, L2-transfer "
          f"{len(rows)}/{len(rows)} anchors + {len(b450)}/"
          f"{len(b450)} B450 shared]")
    for k in sorted(props):
        v = props[k]
        shown = f43._fmt(v)
        marker = ""
        if k in exp and not isinstance(v, list):
            marker = ("  == stock-3644 anchor" if v == exp[k]
                      else f"  != stock-3644 anchor ({exp[k]})")
        elif k in exp and isinstance(v, list):
            marker = ("  == stock-3644 anchor"
                      if len(v) == exp[k]
                      else f"  != stock-3644 anchor "
                           f"(|set| {len(v)} vs {exp[k]})")
        print(f"  propose {k:<30} = {shown}{marker}")
    for k in sorted(omitted):
        print(f"  OMIT    {k:<30} {omitted[k]}")
    print(f"  judge-owned (fw39 fills these; NEVER proposed): "
          f"{sorted(f40.JUDGE_FILLS)}")
    print("  law L1: a proposal is not a measurement — review, then "
          "pass the file as --lenses (corrections beat proposals, "
          "always).")

    if out:
        with open(out, "w") as f:
            json.dump(props, f, indent=1, sort_keys=True)
        with open(out + ".report.json", "w") as f:
            json.dump({"instrument": "fw45-b550-lens", "ring": RING,
                       "image": os.path.abspath(image),
                       "law": "proposal is not a measurement — operator "
                              "confirms or corrects before the weld",
                       "calibration": {"transfer": "vendor-b550-lens.json",
                                       "shared": "fw43 B450 rows"},
                       "expectation": reg.get("day0_lens_expectation"),
                       "provenance": prov,
                       "omitted": omitted}, f, indent=1, sort_keys=True)
        print(f"  lens file: {out} (+ {out}.report.json)")
    return props, omitted, prov


# ---------------------------------------------------------------- verify

def _compare_rows(live, reg):
    """Anchor rows: registered vs re-derived, one row per field."""
    rows = []
    ra = reg.get("psp_anchors", {})
    ri = reg.get("ifr_anchors", {})
    rc = reg.get("cross_anchors", {})
    for img in ACQ:
        lp, la = (ra.get(img) or {}), (live.get(img, {}).get("psp") or {})
        for f in ("dirs_found", "dirs_valid", "blobs",
                  "skipped_entries", "hash_count"):
            rows.append({"image": img, "group": "psp", "field": f,
                         "registered": lp.get(f),
                         "reproduced": la.get(f),
                         "agree": lp.get(f) == la.get(f)})
        it, li = (ri.get(img) or {}), (live.get(img, {}).get("ifr") or {})
        for f in ("packages", "valid", "pages", "questions", "options"):
            rows.append({"image": img, "group": "ifr", "field": f,
                         "registered": (it.get(f)),
                         "reproduced": (li.get("totals") or {}).get(f),
                         "agree": it.get(f) ==
                         (li.get("totals") or {}).get(f)})
        cx, lc = (rc.get(img) or {}), (li.get("cross") or {})
        for f in ("varstore_count", "varstore_bytes_total",
                  "varstore_bytes_covered", "uncovered_share_pct",
                  "zero_question_varstores"):
            rows.append({"image": img, "group": "cross", "field": f,
                         "registered": cx.get(f),
                         "reproduced": lc.get(f),
                         "agree": cx.get(f) == lc.get(f)})
        sreg = (rc.get(img, {}) or {}).get("setup_row") or {}
        sgot = li.get("setup_row") or {}
        for f in ("size", "covered", "uncovered", "questions"):
            rows.append({"image": img, "group": "cross",
                         "field": f"setup.{f}",
                         "registered": sreg.get(f),
                         "reproduced": sgot.get(f),
                         "agree": sreg.get(f) == sgot.get(f)})
    return rows


def _b450_shared_path_rows():
    """The B450 authorship register still reproduces through the SAME
    proposer code (the shared-path law)."""
    _f37, _f38, _f39, _f40, f41, f43 = _mods()
    rows = []
    auth = f43.authorship_register().get("per_specimen", {})
    for rung in ("3604", "3802"):
        path = os.path.join(f41.CORPUS, f41.RUNG_FILES[rung])
        got = f43.psp_bodies(f37_load(path))
        a = auth.get(f"asus-{rung}") or {}
        for f in ("dirs_found", "dirs_valid", "blobs",
                  "skipped_entries"):
            rows.append({"rung": rung, "field": f,
                         "registered": a.get(f), "reproduced": got[f],
                         "agree": a.get(f) == got[f]})
        rows.append({"rung": rung, "field": "by_magic",
                     "registered": a.get("by_magic"),
                     "reproduced": got["by_magic"],
                     "agree": a.get("by_magic") == got["by_magic"]})
    return rows


def f37_load(path):
    return _mods()[0].load(path)


def verify():
    """Re-derive every anchor row and print the table; exit 2 on any
    disagreement (the register is the basis, drift is loud)."""
    live = rederive_anchors()
    reg = lens_register()
    rows = _compare_rows(live, reg)
    dl = reg.get("psp_set_deltas", {})
    got_dl = psp_set_deltas()
    for grp in ("release", "board"):
        for k, v in sorted((dl.get(grp) or {}).items()):
            g = (got_dl.get(grp) or {}).get(k)
            rows.append({"image": "deltas", "group": "psp",
                         "field": f"{grp}.{k}", "registered": v,
                         "reproduced": g, "agree": v == g})
    xf = reg.get("cross_family_overlap", {})
    got_xf = cross_family_overlaps()
    for k in ("3604", "3802"):
        rows.append({"image": "deltas", "group": "psp",
                     "field": f"cross_family.{k}",
                     "registered": (xf or {}).get(k),
                     "reproduced": got_xf.get(k),
                     "agree": (xf or {}).get(k) == got_xf.get(k)})
    b450 = _b450_shared_path_rows()
    print(f"verify-b550: {sum(1 for r in rows if r['agree'])}/"
          f"{sum(1 for r in rows if r['agree'] is not None)} anchor rows "
          f"agree; shared B450 path {sum(1 for r in b450 if r['agree'])}/"
          f"{len(b450)}")
    for r in rows:
        mark = {True: "ok  ", False: "DIFF", None: "note"}[r["agree"]]
        print(f"  {mark} {r['image']:<12} {r['group']:<5} "
              f"{r['field']:<28} reg={f43._fmt(r['registered'])} "
              f"got={f43._fmt(r['reproduced'])}")
    for r in b450:
        mark = {True: "ok  ", False: "DIFF", None: "note"}[r["agree"]]
        print(f"  {mark} b450-shared  {r['rung']:<12} {r['field']:<14} "
              f"reg={f43._fmt(r['registered'])} "
              f"got={f43._fmt(r['reproduced'])}")
    bad = [r for r in rows + b450 if r["agree"] is False]
    if bad:
        print(f"REFUSED: {len(bad)} anchor row(s) disagree — the "
              "register is the basis", file=sys.stderr)
        return 2
    return 0


# ---------------------------------------------------------------- recon

def recon():
    """The ring-44 flagged accounting delta, live: run fw41's novelty on
    the corrected board's 3644 acquisition and show BOTH accounting
    rules on the same result object — the serialized per-axis walk that
    reads only `unregistered` keys, and the summary's rule that also
    counts the whitelist axis's `extra` list. Register arithmetic is
    asserted; fw41 is unchanged (its summary was the full honest
    count)."""
    _f35, f37, _f38, _f39, f41, _f43 = _mods()
    reg = recon_register()
    files = acq_files()
    path = files.get("b550w2-3644")
    if not path or not os.path.exists(path):
        raise Refusal("b550w2-3644.rom missing from the corpus — the "
                      "reconciliation needs the corrected board's image")
    U = f41.build_universes()
    nov = f41.novelty(path, U)
    ax = nov["axes"] if "axes" in nov else nov
    summ = nov.get("summary") or ax.get("summary")
    # the two accounting rules on the SAME object
    walk_style = 0
    for name in f41.AXES:
        v = nov.get(name) or {}
        un = v.get("unregistered")
        walk_style += len(un) if isinstance(un, list) else 0
    extra = len(nov.get("whitelist", {}).get("extra") or [])
    agesa_un = (1 if (nov.get("agesa", {}).get("class")
                      == "unregistered") else 0)
    full = (len(nov.get("species", {}).get("unregistered") or [])
            + len(nov.get("certs", {}).get("unregistered") or [])
            + len(nov.get("dsdt", {}).get("unregistered") or [])
            + extra
            + len(nov.get("smm", {}).get("unregistered") or [])
            + agesa_un)
    names = sorted(nov.get("whitelist", {}).get("extra") or [])
    aux = [n for n in names if "AUX" in n or "fan" in n.lower()
           or "Fan" in n]
    lvl = [n for n in names if n.startswith("Level")]
    checks = [
        ("summary == registered 74",
         summ.get("unregistered_total") == 74),
        ("walk-style (unregistered keys only) == 60", walk_style == 60),
        ("full rule (incl. whitelist extra) == 74", full == 74),
        ("delta == 14 (the whitelist extra)", full - walk_style == 14
         and extra == 14),
        ("the 14 split 6 fan + 8 level",
         len(aux) == 6 and len(lvl) == 8 and len(names) == 14),
        ("missing == 0 (zero new chip families)",
         len(nov.get("whitelist", {}).get("missing") or []) == 0),
        ("register recon agrees",
         reg.get("resolution", {}).get("full_count") == 74
         and reg.get("resolution", {}).get("walk_count") == 60),
    ]
    ok = all(v for _k, v in checks)
    for k, v in checks:
        print(f"  {'PASS' if v else 'FAIL'}  recon {k}")
    print(f"fw45-b550-lens recon: {sum(1 for _k, v in checks if v)}/"
          f"{len(checks)} checks {'PASS' if ok else 'FAIL'} "
          f"(summary {summ.get('unregistered_total')}, walk "
          f"{walk_style}, extra {extra})")
    return 0 if ok else 2


# ---------------------------------------------------------------- manifest

def manifest():
    regs = ["vendor-b550-lens.json", "vendor-novelty-recon.json",
            "vendor-ledger-b550w2.json", "vendor-proposal-calibration.json",
            "vendor-psp.json", "vendor-psp-authorship.json",
            "vendor-ifr-census.json", "vendor-unasked.json"]
    print("fw45-b550-lens manifest — instrument (this file) + registers:")
    for r in regs:
        mark = "ok " if os.path.exists(os.path.join(_LAB, r)) else "MISS"
        print(f"  [{mark}] lab/{r}")
    _f37, _f38, _f39, f40, f41, f43 = _mods()
    print(f"  contract: fw40.LENS_ONLY = {sorted(f40.LENS_ONLY)}")
    print(f"  acquisitions: {ACQ}")
    print(f"  corpus:   {f41.CORPUS} "
          f"(present: {os.path.isdir(f41.CORPUS)})")
    return 0


# ---------------------------------------------------------------- selftest

def selftest():
    """Two tiers. R: the laws + KATs + register well-formedness (no
    corpus). I: live on the corpus — every anchor re-derives, the
    transfer laws hold on the acquisitions, the proposals land in the
    weld as lenses, the reconciliation reproduces live. Gates are loud:
    any FAIL = exit 1; any REFUSED = exit 2; corpus missing = tier I
    skipped loudly, exit reflects only what ran."""
    gates = []

    def gate(name, ok, detail=""):
        gates.append((name, bool(ok), detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}"
              + (f" — {detail}" if detail and not ok else ""))

    def refused(name, fn):
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — the gate reports it
            # the Refusal classes are PER-MODULE (fw43's is not fw45's
            # — the ring-42 boundary lesson); a refusal is a refusal
            if type(e).__name__ == "Refusal":
                gate(name, True)
                return e
            gate(name, False,
                 f"wrong exception {type(e).__name__}: {e}")
            return None
        gate(name, False, "no refusal raised")
        return None

    print("fw45-b550-lens selftest — the B550 lens layer")
    print("tier R — laws, KATs, register well-formedness (no corpus)")
    _f37, _f38, _f39, f40, f41, f43 = _mods()

    # R1 the contract is inherited, never re-transcribed
    gate("R1 LENS_ONLY contract 7 slots (auto-derived from fw40)",
         len(sorted(f40.LENS_ONLY)) == 7, f"got {sorted(f40.LENS_ONLY)}")

    # R2 schema refusals — judge-owned and foreign keys both bounce
    refused("R2 judge-owned key refused", lambda: f43._validate_lens_keys(
        {"matches_known_release": "x"}))
    refused("R2b foreign key refused", lambda: f43._validate_lens_keys(
        {"not_a_slot": 1}))

    # R3 the recon register's arithmetic
    try:
        rr = recon_register()
        res = rr.get("resolution", {})
        att = rr.get("attribution", {})
        gate("R3 recon arithmetic 74 == 48+0+4+14+8+0",
             res.get("full_count") == 74 and res.get("walk_count") == 60
             and res.get("delta") == 14
             and res.get("axis_counts") == {"species": 48, "certs": 0,
                                            "dsdt": 4, "whitelist": 14,
                                            "smm": 8, "agesa": 0},
             f"got {res}")
        gate("R3b the 14 split 6 fan + 8 level, named",
             att.get("fan_names_count") == 6 and
             att.get("level_names_count") == 8 and
             len(att.get("names") or []) == 14,
             f"got fan={att.get('fan_names_count')} "
             f"level={att.get('level_names_count')}")
        gate("R3c missing == 0 registered (zero new chip families)",
             att.get("missing") == 0, f"got {att.get('missing')}")
    except Refusal as e:
        gate("R3 recon register well-formed", False, str(e))

    # R4 the lens register carries the anchors and the transfer laws
    try:
        lr = lens_register()
        imgs = lr.get("images", {})
        xanch = lr.get("cross_anchors", {})
        gate("R4 lens register: 3 acquisitions with psp+ifr+cross anchors",
             sorted(imgs) == sorted(ACQ) and
             all(imgs[k].get("psp") and imgs[k].get("ifr")
                 for k in ACQ) and
             all(xanch.get(k) for k in ACQ),
             f"got images={sorted(imgs)} "
             f"cross={sorted(xanch)}")
        laws = lr.get("transfer_laws", {})
        gate("R4b transfer laws registered (identity/deltas/share/setup)",
             laws.get("release_ifr_identity") is True and
             laws.get("psp_release_delta") == 37 and
             laws.get("psp_board_delta") == 65 and
             laws.get("share_equal_across_three") == 85.73 and
             laws.get("setup_uncovered_equal") == 161,
             f"got {laws}")
        exp = lr.get("day0_lens_expectation", {}).get("stock_3644", {})
        gate("R4c day-0 expectation anchored (7 lens values)",
             exp.get("ifr_questions_total") == 14431 and
             exp.get("ifr_valid_fraction") == 1.0 and
             exp.get("setup_uncovered_bytes") == 161 and
             exp.get("varstore_uncovered_share_pct") == 85.73 and
             exp.get("psp_hash_count") == 203 and
             exp.get("psp_hashes_3604_count") == 194 and
             exp.get("psp_hashes_3802_count") == 193,
             f"got {exp}")
        sl = lr.get("lens_witnessed_scoreline", {})
        gate("R4d lens-witnessed scoreline 6/1/10/9, sets derived",
             sl.get("hit") == 6 and sl.get("partial") == 1 and
             sl.get("miss") == 10 and sl.get("na") == 9 and
             sorted(sl.get("hit_set") or []) ==
             ["P-03", "P-06", "P-08", "P-13", "P-16", "P-18"] and
             sorted(sl.get("partial_set") or []) == ["P-15"],
             f"got {sl}")
    except Refusal as e:
        gate("R4 lens register well-formed", False, str(e))

    # R5 fletcher32 KAT through the shared proposer (the PSP path is
    # the fw43-calibrated one — one method, two boards)
    body = b"B" * 32
    raw = bytearray(b"\x00" * 0x200)
    raw[0:4] = b"$PSP"
    raw[8:12] = (1).to_bytes(4, "little")
    raw[12:16] = (0).to_bytes(4, "little")
    e16 = bytes([1, 0]) + (0).to_bytes(2, "little") \
        + (32).to_bytes(4, "little") + (0x100).to_bytes(4, "little") \
        + b"\x00" * 4
    raw[16:32] = e16
    raw[0x100:0x120] = body
    chk = f43._fletcher32(bytes(raw[8:16 + 1 * 16]))
    raw[4:8] = chk.to_bytes(4, "little")
    got = f43.psp_bodies(bytes(raw))
    gate("R5 fletcher32 KAT via fw43.psp_bodies",
         got["dirs_valid"] == 1 and got["blobs"] == 1 and
         len(got["hashes"]) == 1,
         f"got dirs={got['dirs_valid']} blobs={got['blobs']}")

    # R6 the zero-writes law is structural: exactly two write sites in
    # the whole pre-selftest body, both inside propose()'s `if out:`
    # (the --out document the operator asked for — law L4)
    try:
        src = open(os.path.abspath(__file__)).read()
        body_src = src.split("def selftest", 1)[0]
        lines = body_src.splitlines()
        wsites = [i for i, ln in enumerate(lines)
                  if 'open(' in ln and '"w")' in ln]
        ok = (len(wsites) == 2 and
              all("json.dump" in lines[i + 1] for i in wsites) and
              all("if out:" in lines[i - 2] or
                  "with open(out" in lines[i] for i in wsites))
        gate("R6 zero writes outside the --out document (2 sites, both "
             "operator-requested)", ok,
             f"write sites={len(wsites)}")
    except Exception as e:  # noqa: BLE001
        gate("R6 zero writes", False, str(e))

    live = all(os.path.exists(os.path.join(f41.CORPUS, f))
               for f in ("b550w2-3644.rom", "b550w2-3645.rom",
                         "b550-nw-3644.rom")) \
        and os.path.isdir(f41.CORPUS) \
        and os.path.exists(os.path.join(
            f41.CORPUS, f41.RUNG_FILES["3604"]))

    if live:
        print("tier I — live transfer calibration (the corpus answers)")
        files = acq_files()

        # I1-I3 the anchors re-derive on the three acquisitions
        try:
            live_anch = rederive_anchors()
            reg = lens_register()
            rows = _compare_rows(live_anch, reg)
            bad = [r for r in rows if r["agree"] is False]
            gate("I1 anchors re-derive on b550w2-3644",
                 not [r for r in bad if r["image"] == "b550w2-3644"],
                 f"{len([r for r in bad if r['image'] == 'b550w2-3644'])}"
                 " rows disagree")
            gate("I2 anchors re-derive on b550w2-3645",
                 not [r for r in bad if r["image"] == "b550w2-3645"],
                 f"{len([r for r in bad if r['image'] == 'b550w2-3645'])}"
                 " rows disagree")
            gate("I3 anchors re-derive on b550-nw-3644",
                 not [r for r in bad if r["image"] == "b550-nw-3644"],
                 f"{len([r for r in bad if r['image'] == 'b550-nw-3644'])}"
                 " rows disagree")
        except Refusal as e:
            gate("I1-I3 anchors re-derive", False, str(e))

        # I4 the set-delta laws (release 37, board 65)
        try:
            reg = lens_register()
            dl = reg.get("psp_set_deltas", {})
            got_dl = psp_set_deltas()
            gate("I4 PSP release delta 37/37 (3644 vs 3645)",
                 (dl.get("release", {}).get("w2_3644_minus_w2_3645") == 37
                  and dl.get("release", {}).get("w2_3645_minus_w2_3644")
                  == 37
                  and got_dl["release"]["w2_3644_minus_w2_3645"] == 37
                  and got_dl["release"]["w2_3645_minus_w2_3644"] == 37),
                 f"reg={dl.get('release')} got={got_dl['release']}")
            gate("I4b PSP board delta 65/65 (w2-3644 vs nw-3644)",
                 (dl.get("board", {}).get("w2_3644_minus_nw_3644") == 65
                  and dl.get("board", {}).get("nw_3644_minus_w2_3644")
                  == 65
                  and got_dl["board"]["w2_3644_minus_nw_3644"] == 65
                  and got_dl["board"]["nw_3644_minus_w2_3644"] == 65),
                 f"reg={dl.get('board')} got={got_dl['board']}")
        except Refusal as e:
            gate("I4 PSP set-delta laws", False, str(e))

        # I5 the cross-family overlap (P-19's checker inputs) — 40 == 40
        try:
            reg = lens_register()
            xf = reg.get("cross_family_overlap", {})
            got_xf = cross_family_overlaps()
            gate("I5 cross-family PSP overlap 40 (3604) / 40 (3802)",
                 xf.get("3604") == 40 and xf.get("3802") == 40 and
                 got_xf.get("3604") == 40 and got_xf.get("3802") == 40,
                 f"reg={xf} got={got_xf}")
        except Refusal as e:
            gate("I5 cross-family overlap", False, str(e))

        # I6 the shared B450 path still reproduces the authorship rows
        try:
            b450 = _b450_shared_path_rows()
            badb = [r for r in b450 if r["agree"] is False]
            gate("I6 shared B450 path == authorship register (2 rungs)",
                 not badb, f"{badb[:1]}")
        except Refusal as e:
            gate("I6 shared B450 path", False, str(e))

        # I7 propose on the corrected board: 7 slots, anchor-conformant,
        # and the weld consumes them (fw43's I6 discipline, B550 basis)
        try:
            props, omitted, _prov = propose(
                files["b550w2-3644"], out=None)
            gate("I7 propose emits exactly LENS_ONLY keys (7 slots)",
                 set(props) == set(f40.LENS_ONLY) and not omitted,
                 f"props={sorted(props)} omitted={sorted(omitted)}")
            reg = lens_register()
            exp = reg.get("day0_lens_expectation", {}) \
                     .get("stock_3644", {})
            gate("I7b proposals == stock-3644 anchors",
                 props.get("ifr_questions_total")
                 == exp.get("ifr_questions_total") and
                 props.get("ifr_valid_fraction")
                 == exp.get("ifr_valid_fraction") and
                 props.get("setup_uncovered_bytes")
                 == exp.get("setup_uncovered_bytes") and
                 props.get("varstore_uncovered_share_pct")
                 == exp.get("varstore_uncovered_share_pct") and
                 len(props.get("psp_hashes_3644") or [])
                 == exp.get("psp_hash_count"),
                 "lens values off the anchors")
            _eo, draft = _mods()[1].exam(files["b550w2-3644"],
                                         target="day0-3644",
                                         geometry=False)
            merged, rep = f40.weld(draft, None, lenses=props,
                                   target="day0")
            landed = [k for k in props if merged.get(k) == props[k]]
            gate("I7c every proposal survives the weld unchanged",
                 len(landed) == len(props),
                 f"landed {len(landed)}/{len(props)}")
            prov_ok = all(str(rep.get("provenance", {}).get(k, ""))
                          .startswith("lens") for k in props)
            gate("I7d the weld journals them as lenses (L1)",
                 prov_ok, str({k: rep.get("provenance", {}).get(k)
                               for k in sorted(props)}))
        except Refusal as e:
            gate("I7 propose+weld on B550", False, str(e))

        # I8-I9 the reconciliation, live on the corrected board
        try:
            U = f41.build_universes()
            nov = f41.novelty(files["b550w2-3644"], U)
            summ = nov.get("summary") or {}
            walk_style = 0
            for name in f41.AXES:
                v = nov.get(name) or {}
                un = v.get("unregistered")
                walk_style += len(un) if isinstance(un, list) else 0
            extra = len(nov.get("whitelist", {}).get("extra") or [])
            gate("I8 live novelty summary == 74 (fw41 unchanged)",
                 summ.get("unregistered_total") == 74,
                 f"got {summ.get('unregistered_total')}")
            gate("I8b walk-style (unregistered keys) == 60, extra == 14",
                 walk_style == 60 and extra == 14,
                 f"walk={walk_style} extra={extra}")
            names = sorted(nov.get("whitelist", {}).get("extra") or [])
            aux = [n for n in names if "aux" in n.lower()]
            lvl = [n for n in names if n.startswith("Level")]
            gate("I9 the 14 = 6 AUX-fan + 8 Level names (B550 only)",
                 len(aux) == 6 and len(lvl) == 8 and len(names) == 14,
                 f"aux={len(aux)} level={len(lvl)} total={len(names)}")
            gate("I9b missing == 0 (the 47 chip families transfer whole)",
                 len(nov.get("whitelist", {}).get("missing") or []) == 0,
                 f"missing={nov.get('whitelist', {}).get('missing')}")
            ref = os.path.join(f41.CORPUS, f41.RUNG_FILES["3604"])
            refnames = f41._armor_names(f41._deep(ref)["blobs"])
            ref_aux = [n for n in refnames
                       if "aux" in n.lower() or n.startswith("Level")]
            gate("I9c the B450 ref extraction carries ZERO AUX/Level",
                 not ref_aux, f"got {ref_aux[:4]}")
        except Refusal as e:
            gate("I8-I9 reconciliation live", False, str(e))
    else:
        print("tier I — SKIPPED (acquisitions or corpus absent; the R "
              "tier still binds)")

    n_pass = sum(1 for _, ok, _ in gates if ok)
    n_all = len(gates)
    print(f"fw45-b550-lens selftest: {n_pass}/{n_all} gates PASS"
          + (" (tier I live)" if live
             else " (tier R only — corpus absent)"))
    if n_pass != n_all:
        return 1
    return 0


# ---------------------------------------------------------------- main

def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    mode = argv[1]
    if mode == "selftest":
        return selftest()
    if mode == "manifest":
        return manifest()
    if mode == "verify":
        try:
            return verify()
        except Refusal as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 2
    if mode == "recon":
        try:
            return recon()
        except Refusal as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 2
    if mode == "propose":
        if len(argv) < 3:
            print("usage: propose <image> [--out proposals.json]")
            return 2
        image = argv[2]
        out = None
        if "--out" in argv:
            out = argv[argv.index("--out") + 1]
        try:
            propose(image, out=out)
            return 0
        except Refusal as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 2
    print(f"unknown mode {mode!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
