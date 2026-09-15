#!/usr/bin/env python3
"""fw48-pairaxes — the full-axis pair witness: the set lens on every
axis, measured.

Ring 47 anchored the pair coherence to the PSP sets: 3644->3645 is a
swap-event (37/37 body hashes inside 203-hash sets, 0 births, 0
deaths), and the same-version sibling is a registered-births event
(65/65, 0 births / 4 deaths). But the PSP axis is ONE axis of the
novelty walk. The release's other content axes — the DER trust set,
the DSDT lineage, the whitelist chip families and fan vocabulary, the
SMM GUID set, the AGESA level — are pair-blind today: no instrument
reads their set deltas across a pair. "Improve system compatibility"
changed 22.5% of the bytes with zero form grammar (ring 45) and zero
species events (ring 47); whether it touched ANY non-PSP axis is an
open, measurable, pre-registerable question — and the answer decides
what the 16/09 dump and the post-flash world can claim.

fw48 extends the set lens to ALL axes. It composes on fw47 (frozen,
never rewritten — the fw46/47 pattern): fw47.pair_marks still owns
the PSP set marks and the species ledger row; fw48 adds the five
non-PSP content axes, classifies every axis (axis-clean / axis-swap),
and derives the PAIR SIGNATURE from the full evidence — the
sharpened taxonomy the PSP-only witness could not name:

  psp-localized-swap   the PSP axis swapped, every other content
                       axis identical (the pre-registered release-
                       pair claim — the sharpened form of the
                       ring-47 swap-event)
  multi-axis-swap      more than the PSP axis moved — a release or
                       board event the PSP-only witness misreads as
                       a mere swap, or misses entirely when the PSP
                       axis is clean

Four laws (inherited, extended):

  L1 SET-TRUTH-OVER-COUNT     every axis marks on its set; counts
                              are witnesses, never marks.
  L2 ANCHORS-BEFORE-MARKS     the PSP anchors live in the ring-45
                              lens register (fw47 enforces them); the
                              non-PSP anchors live in THIS ring's
                              crown register once it exists — a
                              registered pair+axis must reproduce its
                              registered delta or the instrument
                              refuses loud; unknown pairs and the
                              exploratory null row claim no anchor,
                              never invented.
  L3 CORRECTED-TAXONOMY       the signature is derived from the FULL
                              evidence {axis deltas, species
                              births/deaths}; a container event
                              outranks axis swaps; contradictions
                              are named, never smoothed; frozen
                              registers are read, never rewritten.
  L4 ZERO WRITES              read-only on images; the only file
                              written is the --out document the
                              operator asked for (exactly one write
                              site, grep-policed).

Modes:
  axes <image> [--out out.json]
        the live axis sets of ONE image (counts + items, per axis).
  marks <old> <new> [--out out.json]
        the full-axis pair witness: fw47's PSP+species marks composed
        with the five non-PSP axis marks, per-axis classes, the pair
        signature, the multi-axis blindness witness.
  null3802 [--out out.json]
        the B450 count-blind founder pair (3802->3810) re-read on ALL
        axes — exploratory, no anchor (the row becomes an anchor only
        if a later ring pre-registers it); the frozen births/deaths
        must reproduce or the instrument refuses.
  selftest     two-tier gates (R + I live), the PR ledger frozen in
               the gate names
  manifest     registers + instruments
"""

import argparse
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, "/home/z/my-project/repo-bios/lib")

RING = 48
_M = {}

_PAIRAXES_REG = os.path.join(HERE, "vendor-pairaxes-register.json")

# the non-PSP content axes (psp stays fw47's — composed, not duplicated)
AXES = ("certs", "dsdt", "whitelist", "smm", "agesa")

# the pair signature taxonomy (L3, full evidence)
SIG_BIRTHS = "registered-births"
SIG_PSP_LOCAL = "psp-localized-swap"
SIG_MULTI = "multi-axis-swap"
SIG_CLEAN = "clean-pair"

AXIS_CLEAN = "axis-clean"
AXIS_SWAP = "axis-swap"

# ------------------------------------------------------------- pre-reg
# THE PRE-REGISTRATION LEDGER — frozen in source BEFORE the crown
# measurement (the ring-45/47 mechanic). The crown writer computes
# each outcome from the measurement; refuted PRs stay visible.
PRE_REG = {
    "PR-1": {"pair": "release", "axis": "dsdt",
             "claim": "release pair dsdt set delta == 0 — the P-25 "
                      "analog on B550: AGESA unchanged (1.2.0.12 both) "
                      "so 'improve system compatibility' leaves the "
                      "ACPI lineage untouched"},
    "PR-2": {"pair": "release", "axis": "certs",
             "claim": "release pair certs set delta == 0 — the DER "
                      "trust set (6 certs, the corpus's 3810 freeze "
                      "level) is release-stable"},
    "PR-3": {"pair": "release", "axis": "whitelist",
             "claim": "release pair whitelist set delta == 0 — chip "
                      "families AND the AUX/Level fan vocabulary are "
                      "board hardware, not release content"},
    "PR-4": {"pair": "release", "axis": "smm",
             "claim": "release pair smm set delta == 0 — law "
                      "corollary: species births/deaths == 0 (ring 47) "
                      "implies every GUID subset is stable; a "
                      "refutation indicts the stack above the SMM "
                      "extractor"},
    "PR-5": {"pair": "release", "axis": "agesa",
             "claim": "release pair agesa set delta == 0 — 1.2.0.12 "
                      "on both images (ring 44's machine extraction)"},
    "PR-6": {"pair": "board", "axis": "dsdt",
             "claim": "board pair dsdt set delta != 0 — the "
                      "version-number trap reaches the DSDT axis: a "
                      "different board carries its own ACPI lineage "
                      "even under the same version number"},
    "PR-7": {"pair": "board", "axis": "whitelist",
             "claim": "board pair whitelist set delta != 0 — the "
                      "sibling's fan-header vocabulary differs from "
                      "the WIFI II's (at least one AUX/Level string "
                      "absent on nw, or new on nw)"},
    "PR-8": {"pair": "release", "axis": "signature",
             "claim": "release pair signature == psp-localized-swap — "
                      "PSP delta > 0 while ALL five non-PSP axes are "
                      "delta == 0 (the swap is PSP-localized)"},
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
    """(fw37, fw38, fw39, fw41, fw45, fw47) — the surfaces the witness
    sits on. fw48 sits on top, never instead: the loader, the lenses,
    the trust census, the deep walk + whitelist extractor, the
    acquisition resolution and the PSP pair witness are consumed,
    not re-implemented."""
    return tuple(_load_mod(n) for n in
                 ("fw37-differ", "fw38-exam", "fw39-identity",
                  "fw41-novelty", "fw45-b550-lens", "fw47-pairmarks"))


def _reg(path):
    if not os.path.exists(path):
        raise Refusal(f"missing register {os.path.basename(path)} — the "
                      "frozen surface is the only basis this instrument "
                      "accepts")
    with open(path) as f:
        return json.load(f)


def pairaxes_register():
    """This ring's own register — present after the crown run. The
    crown gates degrade loudly (not silently) when absent."""
    if not os.path.exists(_PAIRAXES_REG):
        return None
    with open(_PAIRAXES_REG) as f:
        return json.load(f)


# ---------------------------------------------------------------- axes

_AXIS_CACHE = {}


def _agesa_set(lvl):
    """Pure: the AGESA axis set from an x_agesa agesa_level payload —
    the picked level plus any multiple (set semantics make a
    multi-level release just another axis delta)."""
    picked = (lvl.get("picked") if isinstance(lvl, dict) else lvl)
    multi = (lvl.get("multiple") if isinstance(lvl, dict) else None) or []
    out = {str(picked)} if picked is not None else set()
    out |= {str(x) for x in multi}
    return out


def axis_sets(path):
    """The live axis sets of ONE image (memoized per abspath per
    process). Every axis is EXTRACTED from the bytes through the
    rings' own extractors — one convention, the fw41 walk: certs via
    fw39.trust_census, dsdt via fw38.x_acpi (checksum-valid DSDT
    sha16s), whitelist via fw41._armor_names, smm via the SMM-typed
    GUIDs of fw41's deep walk, agesa via fw38.x_agesa."""
    key = os.path.abspath(path)
    if key in _AXIS_CACHE:
        return _AXIS_CACHE[key]
    f37, f38, f39, f41, _f45, _f47 = _mods()
    raw = f37.load(path)
    inv = f41._deep(path)
    blobs = inv["blobs"]

    tc = f39.trust_census(raw)
    certs = set(tc)

    dsdt = {}
    for blob in blobs:
        w = f38.x_acpi(blob)
        for t in w["tables"].get("DSDT", []):
            if t.get("checksum_ok") and t.get("sha16"):
                dsdt[t["sha16"]] = dsdt.get(t["sha16"], 0) + 1
    dsdt_primary = (max(dsdt, key=lambda k: dsdt[k]) if dsdt else None)

    whitelist = set(f41._armor_names(blobs))

    smm = {g.upper() for g, m in inv["modules"].items()
           if m["ftype_name"] in f41.SMM_FTYPE_NAMES}

    ag = f38.x_agesa(haystacks=blobs)
    lvl = ag.get("agesa_level")
    agesa = _agesa_set(lvl)

    out = {
        "rom": {"bytes": len(raw), "sha_full": f39._sha16(raw)},
        "certs": {"set": frozenset(certs),
                  "meta": {"sightings": sum(len(v) for v in tc.values())}},
        "dsdt": {"set": frozenset(dsdt),
                 "meta": {"instances": dsdt, "primary": dsdt_primary}},
        "whitelist": {"set": frozenset(whitelist),
                      "meta": {"extracted": len(whitelist)}},
        "smm": {"set": frozenset(smm),
                "meta": {}},
        "agesa": {"set": frozenset(agesa),
                  "meta": {"picked": (lvl.get("picked")
                                      if isinstance(lvl, dict) else lvl),
                           "combo": ag.get("agesa_string")}},
    }
    _AXIS_CACHE[key] = out
    return out


def acq_id(path):
    """Acquisition id from a path (fw47's convention)."""
    _f37, _f38, _f39, _f41, _f45, f47 = _mods()
    return f47.acq_id(path)


# ---------------------------------------------------------------- anchors

def axis_anchors_from(reg, old, new):
    """Pure: the registered non-PSP anchors for a pair from a register
    payload. Only rows with anchor: true and matching pair ids anchor
    (L2: unknown pairs and the exploratory null row claim nothing,
    never invented). Returns {axis: (kind, added, removed)}."""
    if not reg:
        return {}
    ids = {acq_id(old), acq_id(new)}
    out = {}
    for kind, row in (reg.get("pair_axes") or {}).items():
        if not row or not row.get("anchor"):
            continue
        if set(row.get("pair_ids") or []) != ids:
            continue
        for ax, d in (row.get("axes") or {}).items():
            out[ax] = (kind, d[0], d[1])
    return out


def axis_anchors_for(old, new):
    """The registered anchors for this pair (the register-backed
    wrapper of axis_anchors_from)."""
    return axis_anchors_from(pairaxes_register(), old, new)


# ---------------------------------------------------------------- marks

def axis_mark(sa, sb, anchor=None, axis="?"):
    """Pure core: one axis's marks from two sets. The count row is the
    WITNESS (labeled count-blind), the set row is the mark (L1). The
    items are carried whole — the vocabulary IS the evidence."""
    added, removed = sa - sb, sb - sa
    mk = {
        "kind": "set", "axis": axis,
        "status": "==" if not added and not removed else "!=",
        "old_count": len(sa), "new_count": len(sb),
        "added": len(added), "removed": len(removed),
        "added_items": sorted(added), "removed_items": sorted(removed),
        "count_witness": {
            "kind": "count (blind — witness only, never a mark)",
            "status": "==" if len(sa) == len(sb) else "!=",
        },
        "anchor": None, "anchor_kind": None, "anchor_source": None,
    }
    if anchor is not None:
        kind, exp_a, exp_r = anchor
        if (len(added), len(removed)) != (exp_a, exp_r):
            raise Refusal(
                f"L2: live {axis} set delta ({len(added)} added / "
                f"{len(removed)} removed) contradicts the registered "
                f"{kind}-pair anchor ({exp_a} / {exp_r}) — a broken "
                "basis refuses the mark, loud")
        mk["anchor"] = {"added": exp_a, "removed": exp_r}
        mk["anchor_kind"] = kind
        mk["anchor_source"] = ("vendor-pairaxes-register.json "
                               f"pair_axes.{kind}.axes.{axis}")
    return mk


def axis_class(mk):
    """The per-axis class (L3): axis-clean requires set delta == 0."""
    return AXIS_CLEAN if mk["status"] == "==" else AXIS_SWAP


def classify_signature(axis_deltas, births, deaths):
    """Pure: the pair signature from the FULL evidence (L3).
    axis_deltas: {axis: (added, removed)} INCLUDING psp. Precedence:
    a container event (species births/deaths) outranks axis swaps;
    psp-localized-swap REQUIRES the PSP axis to be the only mover;
    every other non-empty move set is multi-axis-swap."""
    movers = {k for k, v in axis_deltas.items() if v[0] or v[1]}
    if births or deaths:
        return SIG_BIRTHS
    if not movers:
        return SIG_CLEAN
    if movers == {"psp"}:
        return SIG_PSP_LOCAL
    return SIG_MULTI


def _compose(m47, ax_old, ax_new, anchors, old, new, t0, mode):
    """The document assembly shared by marks and null3802 (one
    convention): fw47's marks verbatim + the five axis marks + the
    signature + the multi-axis blindness witness."""
    marks = {}
    for ax in AXES:
        marks[ax] = axis_mark(ax_old[ax]["set"], ax_new[ax]["set"],
                              anchor=anchors.get(ax), axis=ax)
    axis_deltas = {"psp": (m47["psp"]["added"], m47["psp"]["removed"])}
    axis_deltas.update({ax: (marks[ax]["added"], marks[ax]["removed"])
                        for ax in AXES})
    births = m47["species"]["births"]
    deaths = m47["species"]["deaths"]
    sig = classify_signature(axis_deltas, births, deaths)
    blind = {ax: {"count_level": marks[ax]["count_witness"]["status"],
                  "set_level": marks[ax]["status"]}
             for ax in AXES
             if marks[ax]["count_witness"]["status"] == "=="
             and marks[ax]["status"] == "!="}
    doc = {
        "instrument": "fw48-pairaxes", "ring": RING, "mode": mode,
        "old": os.path.abspath(old), "new": os.path.abspath(new),
        "fw47_marks": m47,
        "fw47_class_note": "fw47's corrected_class is the PSP-level "
                           "class (swap-event / registered-births / "
                           "clean-pair); fw48's signature is the "
                           "full-axis refinement — when they disagree, "
                           "both stand, the refinement is named "
                           "(L3: named, never smoothed)",
        "axes": {ax: {"mark": marks[ax],
                      "old_meta": ax_old[ax]["meta"],
                      "new_meta": ax_new[ax]["meta"]}
                 for ax in AXES},
        "axis_deltas": axis_deltas,
        "per_axis_classes": {"psp": m47["psp"]["status"],
                             **{ax: axis_class(marks[ax])
                                for ax in AXES}},
        "container": {"births": births, "deaths": deaths,
                      "changed_modules": m47["species"]["changed_modules"],
                      "byte_delta": m47["species"]["byte_delta"]},
        "signature": sig,
        "signature_law": "the signature reads the FULL evidence: a "
                         "container event outranks axis swaps; "
                         "psp-localized-swap REQUIRES every non-PSP "
                         "axis identical",
        "multi_axis_blindness": {
            "axes_swap_in_stable_counts": blind,
            "law": "an axis whose COUNTS read == while its SET reads "
                   "!= is a swap inside stable containers — the "
                   "ring-46 blindness class, per axis",
        },
        "wall_seconds": round(time.time() - t0, 1),
    }
    return doc


def full_marks(old, new, out=None):
    """The full-axis pair witness. fw47.pair_marks owns PSP + species
    (composed, never re-implemented); its refusals are re-claimed
    with THIS module's name (the ring-42 boundary lesson)."""
    t0 = time.time()
    _f37, _f38, _f39, _f41, _f45, f47 = _mods()
    try:
        m47 = f47.pair_marks(old, new)
    except f47.Refusal as e:
        raise Refusal(f"fw48-pairaxes.marks: the fw47 PSP witness "
                      f"refused ({e}) — re-claimed, never swallowed")
    ax_old, ax_new = axis_sets(old), axis_sets(new)
    anchors = axis_anchors_for(old, new)
    doc = _compose(m47, ax_old, ax_new, anchors, old, new, t0, "marks")
    if out:
        _write_doc(out, doc)
    return doc


# ---------------------------------------------------------------- null3802

def null3802_axes(out=None):
    """The B450 count-blind founder pair (3802->3810) re-read on ALL
    axes. fw47.null3802 first: the frozen births/deaths must reproduce
    or the chain refuses; the PSP verdict is theirs. The non-PSP rows
    are EXPLORATORY — no anchor is claimed (L2); the row becomes an
    anchor only if a later ring pre-registers it."""
    t0 = time.time()
    _f37, _f38, _f39, f41, _f45, f47 = _mods()
    try:
        n47 = f47.null3802()
    except f47.Refusal as e:
        raise Refusal(f"fw48-pairaxes.null3802: fw47 refused ({e}) — "
                      "re-claimed, never swallowed")
    frozen = (f47.dossier_register().get("pair_null_dossier") or {})
    old = os.path.join(f41.CORPUS, os.path.basename(frozen.get("old") or ""))
    new = os.path.join(f41.CORPUS, os.path.basename(frozen.get("new") or ""))
    ax_old, ax_new = axis_sets(old), axis_sets(new)
    doc = _compose(n47["re_reading"], ax_old, ax_new, {}, old, new, t0,
                   "null3802")
    doc["frozen_row"] = n47["frozen_row"]
    doc["fw47_verdict"] = n47["verdict"]
    doc["anchor_policy"] = ("exploratory — no anchor claimed for the "
                            "non-PSP axes (L2); the row becomes an "
                            "anchor only if a later ring pre-registers "
                            "it")
    if out:
        _write_doc(out, doc)
    return doc


# ---------------------------------------------------------------- axes doc

def axes_doc(path, out=None):
    """The live axis sets of ONE image — the cheap per-image reading
    the pair marks are built from."""
    ax = axis_sets(path)
    doc = {
        "instrument": "fw48-pairaxes", "ring": RING, "mode": "axes",
        "image": os.path.abspath(path),
        "rom_bytes": ax["rom"]["bytes"],
        "rom_sha_full": ax["rom"]["sha_full"],
        "axes": {name: {"count": len(ax[name]["set"]),
                        "items": sorted(ax[name]["set"]),
                        "meta": ax[name]["meta"]}
                 for name in AXES},
    }
    if out:
        _write_doc(out, doc)
    return doc


def _write_doc(path, doc):
    """The ONLY write site of this instrument (L4; grep-policed by
    gate R6)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
    print(f"written: {path}")


# ---------------------------------------------------------------- selftest

def selftest():
    """Two-tier gates. Tier R: the signature taxonomy KATs, the
    per-axis blindness lesson, the anchor mechanics, the PRE_REG
    ledger, the laws police. Tier I live: the axis sets re-derive on
    the acquisitions, the release and board pairs mark full-axis, the
    null re-reads, and the crown register (when present) agrees with
    a live re-derivation — the PR outcomes confronted to the
    measurement."""
    _f37, _f38, _f39, f41, f45, f47 = _mods()
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
    print("tier R — the laws, the signature taxonomy, the KATs")
    A, B = {"h1", "h2", "h3"}, {"h2", "h3", "h4"}
    C = D = {"h1", "h2", "h3"}
    gate("R1 signature: a container event outranks axis swaps",
         classify_signature({"psp": (37, 37), "certs": (2, 2)},
                            1, 0) == SIG_BIRTHS
         and classify_signature({"psp": (0, 0)}, 0, 3) == SIG_BIRTHS)
    gate("R1b psp-only move -> psp-localized-swap",
         classify_signature({"psp": (37, 37), "certs": (0, 0),
                             "dsdt": (0, 0), "whitelist": (0, 0),
                             "smm": (0, 0), "agesa": (0, 0)},
                            0, 0) == SIG_PSP_LOCAL)
    gate("R1c psp AND another axis -> multi-axis-swap",
         classify_signature({"psp": (37, 37), "certs": (0, 1)},
                            0, 0) == SIG_MULTI)
    gate("R1d a NON-PSP move alone -> multi-axis-swap (the event the "
         "PSP-only witness cannot see)",
         classify_signature({"psp": (0, 0), "certs": (2, 2)},
                            0, 0) == SIG_MULTI)
    gate("R1e all axes zero -> clean-pair",
         classify_signature({"psp": (0, 0), "certs": (0, 0),
                             "dsdt": (0, 0), "whitelist": (0, 0),
                             "smm": (0, 0), "agesa": (0, 0)},
                            0, 0) == SIG_CLEAN)

    mk = axis_mark(A, B, axis="certs")
    gate("R2 per-axis THE LESSON: set != AND count == (and the "
         "inherited fw47 orientation: added = old-only)",
         mk["status"] == "!=" and mk["count_witness"]["status"] == "=="
         and mk["added"] == 1 and mk["removed"] == 1
         and mk["old_count"] == mk["new_count"] == 3
         and mk["added_items"] == ["h1"]
         and mk["removed_items"] == ["h4"]
         and mk["axis"] == "certs")
    mk = axis_mark(C, D, axis="dsdt")
    gate("R2b identical sets -> set == and count ==",
         mk["status"] == "==" and mk["added"] == 0
         and mk["removed"] == 0
         and mk["count_witness"]["status"] == "==")
    mk = axis_mark(A, B, anchor=("release", 1, 1), axis="whitelist")
    gate("R2c anchored axis mark carries kind + source, deltas intact",
         mk["anchor_kind"] == "release"
         and mk["anchor"] == {"added": 1, "removed": 1}
         and "pair_axes.release" in mk["anchor_source"])
    refused("R2d a live axis delta contradicting its anchor refuses "
            "loud, naming the AXIS",
            lambda: axis_mark(A, B, anchor=("release", 37, 37),
                              axis="certs"),
            want=["L2", "certs", "contradicts"])

    gate("R3 PRE_REG ledger: 8 PRs, every pair/axis inside the "
         "universe, claims stated",
         len(PRE_REG) == 8
         and all(p["pair"] in ("release", "board")
                 and (p["axis"] in AXES or p["axis"] == "signature")
                 and p["claim"] for p in PRE_REG.values())
         and PRE_REG["PR-8"]["axis"] == "signature"
         and PRE_REG["PR-1"]["axis"] == "dsdt")

    reg_k = {"pair_axes": {
        "release": {"anchor": True, "pair_ids": ["b550w2-3644",
                                                 "b550w2-3645"],
                    "axes": {"certs": [0, 0], "dsdt": [1, 1]}},
        "board": {"anchor": True, "pair_ids": ["b550w2-3644",
                                               "b550-nw-3644"],
                  "axes": {"dsdt": [2, 2]}},
        "null3802": {"anchor": False, "pair_ids": ["x-3802", "x-3810"],
                     "axes": {"certs": [9, 9]}},
    }}
    got = axis_anchors_from(reg_k, "/p/b550w2-3644.rom",
                            "/p/b550w2-3645.rom")
    gate("R4 anchors resolve per pair+axis from the register",
         got.get("certs") == ("release", 0, 0)
         and got.get("dsdt") == ("release", 1, 1)
         and "smm" not in got)
    got = axis_anchors_from(reg_k, "/p/b550w2-3644.rom",
                            "/p/b550-nw-3644.rom")
    gate("R4b the board pair anchors only its own rows",
         got.get("dsdt") == ("board", 2, 2) and "certs" not in got)
    gate("R4c the exploratory null row anchors NOTHING and unknown "
         "pairs claim nothing",
         axis_anchors_from(reg_k, "/p/x-3802.rom", "/p/x-3810.rom") == {}
         and axis_anchors_from(reg_k, "/p/a.rom", "/p/b.rom") == {}
         and axis_anchors_from(None, "/p/a.rom", "/p/b.rom") == {})

    gate("R5 agesa set semantics: picked singleton, multiple joins "
         "the set",
         _agesa_set({"picked": "1.2.0.12", "multiple": None})
         == {"1.2.0.12"}
         and _agesa_set({"picked": "1.2.0.12",
                         "multiple": ["1.2.0.6c"]})
         == {"1.2.0.12", "1.2.0.6c"}
         and _agesa_set({"picked": None, "multiple": None}) == set())

    gate("R6 per-module Refusal boundary (the ring-42 lesson)",
         f47.Refusal is not Refusal
         and Refusal.__name__ == "Refusal"
         and f47.Refusal.__name__ == "Refusal")

    wpat = 'open(path, ' + '"w"'
    n_writes = src.count(wpat)
    gate("R7 L4 zero-writes: exactly ONE write site (_write_doc)",
         n_writes == 1 and 'def _write_doc' in src,
         f"write sites={n_writes}")
    gate("R7b the four laws stated in source",
         all(s in src for s in
             ("L1 SET-TRUTH-OVER-COUNT", "L2 ANCHORS-BEFORE-MARKS",
              "L3 CORRECTED-TAXONOMY", "L4 ZERO WRITES")))

    gate("R8 acq_id convention (fw47's, consumed)",
         acq_id("/p/b550w2-3644.rom") == "b550w2-3644"
         and acq_id("/p/noext") == "noext")

    # ---------------- tier I (live)
    print("tier I — live: the acquisitions, the release pair, the "
          "board pair, the null re-read, the crown")
    files = f45.acq_files()
    ref = files.get("b550w2-3644")
    disc = files.get("b550w2-3645")
    sib = files.get("b550-nw-3644")
    dr = f47.dossier_register()
    frozen = (dr.get("pair_null_dossier") or {})
    nold = os.path.join(f41.CORPUS,
                        os.path.basename(frozen.get("old") or ""))
    nnew = os.path.join(f41.CORPUS,
                        os.path.basename(frozen.get("new") or ""))
    gate("I0 acquisitions + null images on disk (ring-44 "
         "vendor-verified / the B450 corpus)",
         bool(ref) and os.path.exists(ref)
         and bool(disc) and os.path.exists(disc)
         and bool(sib) and os.path.exists(sib)
         and os.path.exists(nold) and os.path.exists(nnew),
         f"ref={ref} disc={disc} sib={sib} null={nold}/{nnew}")

    try:
        axr = axis_sets(ref)
        gate("I1 the axes re-derive on the reference image (certs 6, "
             "dsdt present, whitelist >= 41, smm present, agesa "
             "1.2.0.12)",
             len(axr["certs"]["set"]) == 6
             and len(axr["dsdt"]["set"]) >= 1
             and len(axr["whitelist"]["set"]) >= 41
             and len(axr["smm"]["set"]) >= 1
             and axr["agesa"]["set"] == {"1.2.0.12"},
             f"certs={len(axr['certs']['set'])} "
             f"dsdt={len(axr['dsdt']['set'])} "
             f"wl={len(axr['whitelist']['set'])} "
             f"smm={len(axr['smm']['set'])} agesa={sorted(axr['agesa']['set'])}")
    except Exception as e:
        gate("I1 the axes re-derive on the reference image", False,
             f"{type(e).__name__}: {e}")

    rel = brd = nul = None
    try:
        rel = full_marks(ref, disc)
        gate("I2 release pair: psp 37/37 anchor-checked (fw47 "
             "enforces, L2)",
             rel["fw47_marks"]["psp"]["status"] == "!="
             and rel["fw47_marks"]["psp"]["added"] == 37
             and rel["fw47_marks"]["psp"]["removed"] == 37
             and rel["fw47_marks"]["psp"]["anchor_kind"] == "release")
        gate("I2b release pair: the five axis marks are present and "
             "classified",
             all(rel["axes"][ax]["mark"]["status"] in ("==", "!=")
                 for ax in AXES)
             and all(rel["per_axis_classes"][ax] in (AXIS_CLEAN,
                                                     AXIS_SWAP)
                     for ax in AXES)
             and rel["per_axis_classes"]["psp"] == "!=")
        gate("I2c release pair: container 0/0 (fw47's measured row, "
             "reproduced)",
             rel["container"]["births"] == 0
             and rel["container"]["deaths"] == 0)
        gate("I2d the corollary law live: species 0/0 implies the "
             "smm axis reads ==",
             (rel["container"]["births"] or rel["container"]["deaths"])
             or rel["axes"]["smm"]["mark"]["status"] == "==")
        gate("I2e release pair: signature derived and recorded",
             rel["signature"] in (SIG_BIRTHS, SIG_PSP_LOCAL,
                                  SIG_MULTI, SIG_CLEAN),
             rel["signature"])
    except Refusal as e:
        gate("I2 release pair marks", False, f"REFUSAL {e}")
    except Exception as e:
        gate("I2 release pair marks", False, f"{type(e).__name__}: {e}")

    try:
        brd = full_marks(ref, sib)
        gate("I3 board pair: psp 65/65 anchor-checked, container "
             "0/4 (fw47's measured rows, reproduced)",
             brd["fw47_marks"]["psp"]["added"] == 65
             and brd["fw47_marks"]["psp"]["removed"] == 65
             and brd["container"]["births"] == 0
             and brd["container"]["deaths"] == 4)
        gate("I3b board pair signature == registered-births (the "
             "container event outranks every axis swap)",
             brd["signature"] == SIG_BIRTHS, brd["signature"])
    except Refusal as e:
        gate("I3 board pair marks", False, f"REFUSAL {e}")
    except Exception as e:
        gate("I3 board pair marks", False, f"{type(e).__name__}: {e}")

    try:
        nul = null3802_axes()
        gate("I4 null3802 full-axis: fw47's verdict reproduced "
             "(either way) and the exploratory policy stated",
             nul["fw47_verdict"] in ("survives", "corrected")
             and nul["frozen_row"]["births"] == 0
             and nul["frozen_row"]["deaths"] == 0
             and "no anchor" in nul["anchor_policy"])
        gate("I4b null3802: the five axis marks completed (no "
             "anchor claimed on any of them)",
             all(nul["axes"][ax]["mark"]["anchor"] is None
                 for ax in AXES))
    except Refusal as e:
        gate("I4 null3802 full-axis", False, f"REFUSAL {e}")
    except Exception as e:
        gate("I4 null3802 full-axis", False, f"{type(e).__name__}: {e}")

    # ---------------- crown register (present after the artifact run)
    pr = pairaxes_register()
    if pr is None:
        gate("R9 crown register: absent pre-crown (loud degrade, "
             "written by scripts/ring48_register.py)", True,
             "vendor-pairaxes-register.json not yet written")
    elif rel is None:
        gate("R9 crown register gates", False,
             "crown present but the live release marks failed — "
             "nothing to confront")
    else:
        try:
            crown = pr.get("crown", {})
            reg_rel = ((crown.get("release_pair") or {})
                       .get("axis_deltas") or {})
            gate("R9 crown release row vs live: every axis delta "
                 "re-derives",
                 all(tuple(reg_rel.get(ax) or ())
                     == tuple(rel["axis_deltas"].get(ax) or ())
                     for ax in (["psp"] + list(AXES))),
                 f"reg={reg_rel} live={rel['axis_deltas']}")
            preg = pr.get("pre_registrations") or {}
            gate("R9b the PR ledger is complete and confronted: 8 "
                 "outcomes recorded, each with measured numbers",
                 len(preg) == 8
                 and all(k in preg for k in PRE_REG)
                 and all(v.get("outcome") in ("hit", "refuted")
                         and "measured" in v for v in preg.values()))
            sig8 = preg.get("PR-8", {}).get("measured", {})
            gate("R9c PR-8's registered signature agrees with the "
                 "live release signature",
                 sig8.get("signature") == rel["signature"],
                 f"reg={sig8.get('signature')} "
                 f"live={rel['signature']}")
        except Exception as e:
            gate("R9 crown register gates", False, str(e))

    print(f"fw48-pairaxes selftest: {ok[0]}/{ok[0] + len(fails)} gates "
          f"PASS (tier R + tier I live)")
    return 1 if fails else 0


# ---------------------------------------------------------------- manifest

def manifest():
    """The instrument's self-description (the fw35 manifest law)."""
    modes = ["axes <image> [--out out.json]",
             "marks <old> <new> [--out out.json]",
             "null3802 [--out out.json]", "selftest", "manifest"]
    regs = {
        "basis": "vendor-b550-lens.json (ring 45, via fw47: the PSP "
                 "set anchors release 37/37 + board 65/65)",
        "frozen_null": "vendor-dossier-register.json (ring 42: "
                       "pair_null_dossier 3802->3810, read never "
                       "rewritten)",
        "this_ring": "vendor-pairaxes-register.json (the crown: the "
                     "full-axis rows for the release pair, the board "
                     "pair, the exploratory null — written by "
                     "scripts/ring48_register.py)",
        "upstream": ["vendor-pairmarks-register.json (ring 47: the "
                     "PSP pair witness fw48 composes on)",
                     "vendor-ledger-b550w2.json (ring 44: the "
                     "acquisitions)"],
    }
    print(json.dumps({
        "instrument": "fw48-pairaxes", "ring": RING,
        "title": "the full-axis pair witness: the set lens on every "
                 "axis, measured",
        "modes": modes,
        "axes": list(AXES) + ["psp (fw47's, composed)"],
        "laws": ["L1 set-truth-over-count",
                 "L2 anchors-before-marks",
                 "L3 corrected-taxonomy", "L4 zero writes"],
        "chain": ["axis_sets (fw39.trust_census / fw38.x_acpi / "
                  "fw41._armor_names / SMM GUIDs / fw38.x_agesa)",
                  "axis_mark (anchor-checked, count = witness only)",
                  "fw47.pair_marks (PSP + species, composed)",
                  "classify_signature (the full-evidence taxonomy)",
                  "null3802_axes: the B450 founder pair re-read, "
                  "exploratory"],
        "registers": regs,
        "signature_taxonomy": {
            SIG_BIRTHS: "species births/deaths (a container event "
                        "outranks every axis swap)",
            SIG_PSP_LOCAL: "the PSP axis moved, ALL other content "
                           "axes identical (the sharpened swap-event)",
            SIG_MULTI: "more than the PSP axis moved (or the PSP "
                       "axis clean while another moved)",
            SIG_CLEAN: "every axis delta == 0 and no container event",
        },
        "pre_registrations": {k: v["claim"] for k, v in
                              PRE_REG.items()},
    }, indent=1))
    return 0


# ---------------------------------------------------------------- main

def _show(doc):
    """The cheap review print (marks / null3802)."""
    ax = doc["axis_deltas"]
    pcs = doc["per_axis_classes"]
    print(f"{doc['mode']} {os.path.basename(doc['old'])} -> "
          f"{os.path.basename(doc['new'])}  [fw48, ring {RING}]")
    print(f"  psp:       {doc['fw47_marks']['psp']['status']}  "
          f"+{ax['psp'][0]}/-{ax['psp'][1]}  | container "
          f"{doc['container']['births']}/{doc['container']['deaths']} "
          f"({doc['container']['changed_modules']} modules changed, "
          f"{doc['container']['byte_delta']:+d} B)")
    for name in AXES:
        m = doc["axes"][name]["mark"]
        anch = (f" [{m['anchor_kind']} anchor]" if m.get("anchor")
                else "")
        print(f"  {name:<9} {m['status']}  +{m['added']}/-"
              f"{m['removed']}  (counts {m['old_count']} vs "
              f"{m['new_count']}){anch}")
    print(f"  fw47 class: {doc['fw47_marks']['corrected_class']} | "
          f"signature: {doc['signature']}")
    blind = doc["multi_axis_blindness"]["axes_swap_in_stable_counts"]
    if blind:
        print(f"  BLINDNESS: {', '.join(sorted(blind))} swapped "
              "inside stable counts")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fw48-pairaxes")
    ap.add_argument("mode",
                    choices=["axes", "marks", "null3802", "selftest",
                             "manifest"])
    ap.add_argument("images", nargs="*", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    if a.mode == "manifest":
        return manifest()
    if a.mode == "selftest":
        return selftest()

    try:
        if a.mode == "axes":
            if len(a.images) != 1:
                print("axes <image>", file=sys.stderr)
                return 2
            doc = axes_doc(a.images[0], out=a.out)
            print(f"axes {os.path.basename(doc['image'])}  "
                  f"[fw48, ring {RING}]")
            for name in AXES:
                row = doc["axes"][name]
                print(f"  {name:<9} {row['count']}")
            return 0
        if a.mode == "marks":
            if len(a.images) != 2:
                print("marks <old> <new>", file=sys.stderr)
                return 2
            doc = full_marks(a.images[0], a.images[1], out=a.out)
            _show(doc)
            return 0
        if a.mode == "null3802":
            doc = null3802_axes(out=a.out)
            _show(doc)
            print(f"  fw47 verdict: {doc['fw47_verdict']} | "
                  f"{doc['anchor_policy']}")
            return 0
    except Refusal as e:
        print(f"REFUSAL: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
