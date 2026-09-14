#!/usr/bin/env python3
"""fw47-pairmarks — the pair witness: set-anchored pair coherence,
measured.

Ring 46 measured the count-blindness INSIDE the day-0 fused chain and
healed it there: the review marks now anchor the PSP SETS. But the
release-41 machinery — fw42's dossier_pair, the command the board
meets AFTER a flash — still reads the pair through module SPECIES
only: births/deaths of GUIDs. A release that swaps content inside
stable containers reads clean-pair, the NULL profile, on the very
pair the registers proclaim to be an event: 3644->3645 changed 22.5%
of the bytes (7,544,486 B over 53 runs), swapped 37 PSP body hashes
INSIDE a 203-hash set, and births/deaths of species are ZERO. The
pair layer is blind to the discriminator law the ring-45/46
registers carry — the same failure class ring 46 measured, one layer
wider, on the exact command the post-flash world runs first.

fw47 anchors the pair coherence to the SETS. It does not rewrite
fw42 (frozen instruments are never rewritten; fw47 composes on top,
the fw46 pattern): it recomputes the PSP body-hash sets live on BOTH
images, marks them against the registered release/board deltas
(vendor-b550-lens.json psp_set_deltas), and derives the CORRECTED
pair class from the full evidence {births, deaths, set delta,
brand-new species, refusals}. When fw42's frozen class and the
corrected class disagree, the disagreement is NAMED in the same
document — profile_correction — never smoothed.

Four laws:

  L1 SET-TRUTH-OVER-COUNT     pair-level marks read the PSP sets
                              (added/removed sha256_16); count
                              comparisons are emitted only as the
                              labeled blindness witness, never as a
                              mark.
  L2 ANCHORS-BEFORE-MARKS     a registered pair (release 3644<->3645,
                              board 3644<->nw-3644) must reproduce its
                              registered delta live or the instrument
                              refuses; unknown pairs carry no anchor
                              and say so — anchors are never invented.
  L3 CORRECTED-TAXONOMY       clean-pair REQUIRES set delta == 0;
                              content swapped inside stable containers
                              is a swap-event, not a null. Frozen
                              registers are read, never rewritten — a
                              contradiction is recorded as a named
                              correction (the null3802 verdict).
  L4 ZERO WRITES              read-only on images; the only file
                              written is the --out document the
                              operator asked for (exactly one write
                              site, grep-policed).

Modes:
  marks <old> <new> [--out out.json]
        the cheap pair review: PSP set marks + species births/deaths
        + changed-ledger count + byte delta + corrected class + the
        blindness witness.
  cohere <old> <new> [--out out.json]
        fw42's dossier_pair composed with the pair marks: the
        corrected pair dossier; fw42's profile confronted to the
        corrected class, the correction named.
  null3802 [--out out.json]
        the frozen pair-null (3802->3810, B450) re-read through the
        new lens: births/deaths must reproduce the frozen row, the
        PSP set is measured, the verdict (survives | corrected) is
        recorded either way.
  selftest     two-tier gates (R + I live — the release pair, the
               board pair, the frozen null re-read)
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

RING = 47
_M = {}

_LENS_REG = os.path.join(HERE, "vendor-b550-lens.json")
_DOSSIER_REG = os.path.join(HERE, "vendor-dossier-register.json")
_PAIR_REG = os.path.join(HERE, "vendor-pairmarks-register.json")

# the registered pairs (structure only — the NUMBERS live in the
# lens register, L2 reads them, never hardcodes them)
RELEASE_PAIR = frozenset({"b550w2-3644", "b550w2-3645"})
BOARD_PAIR = frozenset({"b550w2-3644", "b550-nw-3644"})

# the corrected pair taxonomy, in precedence order (L3)
CLASS_REFUSED = "refused"
CLASS_BEYOND = "beyond-register-births"
CLASS_BIRTHS = "registered-births"
CLASS_SWAP = "swap-event"
CLASS_CLEAN = "clean-pair"


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
    """(fw37, fw41, fw42, fw43) — the surfaces the witness sits on.
    fw47 sits on top, never instead: the inventory/ledger convention,
    the corpus root, the pair dossier and the PSP body extraction are
    consumed, not re-implemented."""
    return (_load_mod("fw37-differ"), _load_mod("fw41-novelty"),
            _load_mod("fw42-dossier"), _load_mod("fw43-proposal"))


def _reg(path):
    if not os.path.exists(path):
        raise Refusal(f"missing register {os.path.basename(path)} — the "
                      "frozen surface is the only basis this instrument "
                      "accepts")
    with open(path) as f:
        return json.load(f)


def lens_register():
    return _reg(_LENS_REG)


def dossier_register():
    return _reg(_DOSSIER_REG)


def pair_register():
    """This ring's own register — present after the crown run. The
    selftest's crown gates degrade loudly (not silently) when absent."""
    if not os.path.exists(_PAIR_REG):
        return None
    with open(_PAIR_REG) as f:
        return json.load(f)


_INV = {}


def _inv(path):
    """fw37's ledger-semantics inventory, memoized per process
    (abspath-keyed; the fw39 _deep convention — one walk per image,
    shared by every pair the process reads)."""
    key = os.path.abspath(path)
    if key not in _INV:
        f37 = _mods()[0]
        _INV[key] = f37.Engine().inv(path)
    return _INV[key]


# ---------------------------------------------------------------- anchors

def registered_deltas():
    """The lens register's measured PSP set deltas — the ONLY source
    of anchor numbers (L2: numbers live in registers, not in code)."""
    d = lens_register().get("psp_set_deltas") or {}
    rel = d.get("release") or {}
    brd = d.get("board") or {}
    return {
        "release": (rel.get("w2_3644_minus_w2_3645"),
                    rel.get("w2_3645_minus_w2_3644")),
        "board": (brd.get("w2_3644_minus_nw_3644"),
                  brd.get("nw_3644_minus_w2_3644")),
    }


def acq_id(path):
    """Acquisition id from a path (the rom basename, .rom stripped) —
    or None when the path is not a ring-44 acquisition."""
    base = os.path.basename(os.path.abspath(path))
    return base[:-4] if base.endswith(".rom") else base


def anchor_for(old, new):
    """The registered anchor for a pair, or None (no anchor claimed,
    never invented — L2). Returns (kind, added_expected,
    removed_expected) with the numbers read from the lens register."""
    ids = {acq_id(old), acq_id(new)}
    d = registered_deltas()
    if ids == set(RELEASE_PAIR):
        a, r = d["release"]
        return ("release", a, r)
    if ids == set(BOARD_PAIR):
        a, r = d["board"]
        return ("board", a, r)
    return None


# ---------------------------------------------------------------- marks

def psp_set(path):
    """The live PSP body-hash set of one image (fw43's extractor on
    fw37's loader — one convention, the rings' convention)."""
    f37, _f41, _f42, f43 = _mods()
    return set(f43.psp_bodies(f37.load(path))["hashes"])


def set_marks_sets(sa, sb, anchor=None):
    """Pure core: marks from two sets. The count row is the WITNESS
    (labeled count-blind), the set row is the mark (L1)."""
    added, removed = sa - sb, sb - sa
    mk = {
        "kind": "set",
        "status": "==" if not added and not removed else "!=",
        "old_count": len(sa), "new_count": len(sb),
        "added": len(added), "removed": len(removed),
        "count_witness": {
            "kind": "count (blind — witness only, never a mark)",
            "status": "==" if len(sa) == len(sb) else "!=",
        },
        "anchor": None, "anchor_kind": None,
    }
    if anchor is not None:
        kind, exp_added, exp_removed = anchor
        if (len(added), len(removed)) != (exp_added, exp_removed):
            raise Refusal(
                f"L2: live PSP set delta ({len(added)} added / "
                f"{len(removed)} removed) contradicts the registered "
                f"{kind}-pair anchor ({exp_added} / {exp_removed}) — "
                "a broken basis refuses the mark, loud")
        mk["anchor"] = {"added": exp_added, "removed": exp_removed}
        mk["anchor_kind"] = kind
        mk["anchor_source"] = ("vendor-b550-lens.json "
                               "psp_set_deltas." + kind)
    mk["added_hashes"] = sorted(added)
    mk["removed_hashes"] = sorted(removed)
    return mk


def corrected_class(births, deaths, added, removed, brand_new=None,
                    refuses=None):
    """The corrected pair class from the FULL evidence (L3). Precedence:
    refused > beyond-register-births > registered-births > swap-event
    > clean-pair; clean-pair REQUIRES set delta == 0."""
    if refuses:
        return CLASS_REFUSED
    if brand_new:
        return CLASS_BEYOND
    if births or deaths:
        return CLASS_BIRTHS
    if added or removed:
        return CLASS_SWAP
    return CLASS_CLEAN


def pair_marks(old, new):
    """The cheap pair review: PSP set marks + species births/deaths +
    the changed-ledger row + the corrected class + the blindness
    witness. No novelty universes (that is cohere's job)."""
    t0 = time.time()
    anchor = anchor_for(old, new)
    sa, sb = psp_set(old), psp_set(new)
    mk = set_marks_sets(sa, sb, anchor)

    ia, ib = _inv(old), _inv(new)
    f37 = _mods()[0]
    led = f37.ledger(ia, ib)
    # fw42's convention: births = present in NEW absent from OLD,
    # deaths = present in OLD absent from NEW (the ledger keys carry
    # each inventory's own "file" label)
    births = len(led["only_in_" + ib["file"]])
    deaths = len(led["only_in_" + ia["file"]])
    changed = len(led["changed"])
    cls = corrected_class(births, deaths, mk["added"], mk["removed"])
    out = {
        "instrument": "fw47-pairmarks", "ring": RING, "mode": "marks",
        "old": os.path.abspath(old), "new": os.path.abspath(new),
        "psp": mk,
        "species": {"births": births, "deaths": deaths,
                    "common": led["common"],
                    "identical": led["identical"],
                    "changed_modules": changed,
                    "byte_delta": led["byte_delta"],
                    "module_counts": led["modules"]},
        "corrected_class": cls,
        "blindness_witness": {
            "count_level": mk["count_witness"]["status"],
            "set_level": mk["status"],
            "species_level": f"{births} births / {deaths} deaths",
            "changed_modules": changed,
            "law": "species and count marks read == while the PSP set "
                   "reads != — the ring-46 count-blindness class at "
                   "pair level, healed by the set anchor",
        },
        "wall_seconds": round(time.time() - t0, 1),
    }
    return out


# ---------------------------------------------------------------- cohere

def cohere_compose(d42, marks):
    """Pure composition: fw42's dossier + the pair marks -> the
    corrected block. The correction is NAMED when the frozen class and
    the corrected class disagree — never smoothed (L3)."""
    frozen = d42["pair_coherence"]["profile"]
    corrected = corrected_class(
        len(d42["pair_coherence"]["births"]),
        len(d42["pair_coherence"]["deaths"]),
        marks["psp"]["added"], marks["psp"]["removed"],
        brand_new=d42["pair_coherence"].get("brand_new_species"),
        refuses=d42["pair_coherence"].get("refusals"))
    correction = None
    if frozen != corrected:
        correction = {
            "frozen_class": frozen,
            "corrected_class": corrected,
            "reason": "the frozen class reads species only; the set "
                      "lens reads the PSP body-hash sets — the "
                      "correction is recorded, the frozen register is "
                      "never rewritten",
        }
    return {"fw42_profile": frozen, "corrected_profile": corrected,
            "profile_correction": correction,
            "blindness_witness": marks["blindness_witness"]}


def cohere(old, new, out=None):
    """The corrected pair dossier: fw42.dossier_pair composed with the
    pair marks. Refusal classes are per-module (the ring-42 boundary
    lesson) — every downstream loud error is re-claimed as THIS
    module's refusal, never swallowed."""
    marks = pair_marks(old, new)
    _f37, _f41, f42, _f43 = _mods()
    try:
        d, merged = f42.dossier_pair(old, new)
    except Refusal:
        raise
    except Exception as e:
        raise Refusal(f"cohere refused: the dossier-pair chain raised "
                      f"{type(e).__name__}: {e}")
    corrected = cohere_compose(d, marks)
    doc = {"instrument": "fw47-pairmarks", "ring": RING,
           "mode": "cohere", "old": os.path.abspath(old),
           "new": os.path.abspath(new), "pair_marks": marks,
           "fw42_dossier": d, "corrected": corrected,
           "findings": merged}
    if out:
        _write_doc(out, doc)
    return doc


# ---------------------------------------------------------------- null3802

def null_verdict(frozen_profile, corrected, added, removed):
    """Pure: the frozen null re-read through the set lens. survives ==
    the frozen class holds under the new evidence; corrected == the
    frozen row was set-blind (recorded, never rewritten — L3)."""
    if corrected == frozen_profile and not added and not removed:
        return "survives"
    if corrected == frozen_profile:
        return "survives"
    return "corrected"


def null3802(out=None):
    """The frozen pair-null (3802->3810) re-read through the new lens.
    The frozen row's births/deaths must reproduce live (they are the
    register's basis — a mismatch is a REFUSAL, loud). The PSP set
    delta has NO registered anchor for this pair (the B450 corpus
    carries no registered sets) — none is claimed (L2). The verdict
    records whether the frozen clean-pair survives the set lens."""
    dr = dossier_register()
    frozen = dr.get("pair_null_dossier") or {}
    if not frozen:
        raise Refusal("vendor-dossier-register.json carries no "
                      "pair_null_dossier — the frozen null is the "
                      "basis of this reading")
    old = frozen.get("old")
    new = frozen.get("new")
    for p in (old, new):
        if not p or not os.path.exists(p):
            f41 = _mods()[1]
            alt = os.path.join(f41.CORPUS, os.path.basename(p or ""))
            if os.path.exists(alt):
                continue
            raise Refusal(f"null3802: frozen pair image missing: {p}")
    # re-resolve from the frozen row's basenames against the corpus
    f41 = _mods()[1]
    old = os.path.join(f41.CORPUS, os.path.basename(old))
    new = os.path.join(f41.CORPUS, os.path.basename(new))

    marks = pair_marks(old, new)
    fb, fd = frozen.get("births"), frozen.get("deaths")
    if (marks["species"]["births"], marks["species"]["deaths"]) \
            != (fb, fd):
        raise Refusal(
            f"null3802: live births/deaths "
            f"({marks['species']['births']}/{marks['species']['deaths']})"
            f" contradict the frozen row ({fb}/{fd}) — refusing loud")
    corrected = marks["corrected_class"]
    verdict = null_verdict(frozen.get("profile"), corrected,
                           marks["psp"]["added"], marks["psp"]["removed"])
    doc = {"instrument": "fw47-pairmarks", "ring": RING,
           "mode": "null3802",
           "frozen_row": {"old": frozen.get("old"),
                          "new": frozen.get("new"),
                          "births": fb, "deaths": fd,
                          "coupling": frozen.get("coupling"),
                          "profile": frozen.get("profile"),
                          "note": frozen.get("note")},
           "re_reading": marks,
           "corrected_class": corrected,
           "verdict": verdict,
           "verdict_note": (
               "the frozen clean-pair holds under the set lens"
               if verdict == "survives" else
               "the frozen clean-pair was set-blind: the class "
               "corrects to " + corrected + " — recorded here, the "
               "frozen register is never rewritten")}
    if out:
        _write_doc(out, doc)
    return doc


def _write_doc(path, doc):
    """The ONLY write site of this instrument (L4; grep-policed by
    gate R8)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
    print(f"written: {path}")


# ---------------------------------------------------------------- selftest

def selftest():
    """Two-tier gates. Tier R: the taxonomy KATs, the both-ways
    count-blindness lesson, the anchor resolution from the register,
    the cohere composition, the null verdict logic, the zero-writes
    police. Tier I live: the PSP sets re-derive on the three
    acquisitions, the release pair marks 37/37 with the count witness
    ==, the board pair marks 65/65, the corrected classes fire, and
    the frozen pair-null re-reads live."""
    _f37, f41, f42, f43 = _mods()
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
    print("tier R — the laws, the taxonomy, the KATs")
    A, B = {"h1", "h2", "h3"}, {"h2", "h3", "h4"}
    C = D = {"h1", "h2", "h3"}          # identical sets (the null)
    gate("R1 taxonomy: refused outranks everything",
         corrected_class(1, 1, 1, 1, brand_new=["x"],
                         refuses=["boom"]) == CLASS_REFUSED
         and corrected_class(0, 0, 0, 0, refuses=["boom"])
         == CLASS_REFUSED)
    gate("R1b beyond-register-births outranks births",
         corrected_class(2, 0, 0, 0, brand_new=["x"]) == CLASS_BEYOND)
    gate("R1c births/deaths -> registered-births (fw42 semantics "
         "preserved)",
         corrected_class(2, 0, 0, 0) == CLASS_BIRTHS
         and corrected_class(0, 3, 0, 0) == CLASS_BIRTHS)
    gate("R1d swap-event: containers stable, content swapped",
         corrected_class(0, 0, 37, 37) == CLASS_SWAP
         and corrected_class(0, 0, 1, 0) == CLASS_SWAP)
    gate("R1e clean-pair REQUIRES set delta == 0 (the correction "
         "in one line)",
         corrected_class(0, 0, 0, 0) == CLASS_CLEAN
         and corrected_class(0, 0, 0, 1) == CLASS_SWAP)

    mk = set_marks_sets(A, B)
    gate("R2 THE LESSON both ways on one evidence: set != AND "
         "count ==",
         mk["status"] == "!=" and mk["count_witness"]["status"] == "=="
         and mk["added"] == 1 and mk["removed"] == 1
         and mk["old_count"] == mk["new_count"] == 3)
    mk = set_marks_sets(C, D)
    gate("R2b identical sets -> set == and count ==",
         mk["status"] == "==" and mk["added"] == 0
         and mk["removed"] == 0
         and mk["count_witness"]["status"] == "==")
    mk = set_marks_sets(A, B, anchor=("release", 1, 1))
    gate("R2c anchored set mark carries kind + source, deltas intact",
         mk["anchor_kind"] == "release"
         and mk["anchor"] == {"added": 1, "removed": 1}
         and "psp_set_deltas" in mk["anchor_source"])
    refused("R2d a live delta contradicting the anchor refuses loud",
            lambda: set_marks_sets(A, B, anchor=("release", 37, 37)),
            want=["L2", "contradicts"])

    try:
        d = registered_deltas()
        gate("R3 anchor numbers live in the lens register (release "
             "37/37, board 65/65)",
             d["release"] == (37, 37) and d["board"] == (65, 65),
             str(d))
    except Exception as e:
        gate("R3 anchor numbers live in the lens register", False,
             str(e))

    try:
        files = {}
        f45 = _load_mod("fw45-b550-lens")
        files = f45.acq_files()
        a = anchor_for(files["b550w2-3644"], files["b550w2-3645"])
        b = anchor_for(files["b550w2-3644"], files["b550-nw-3644"])
        gate("R4 pair->anchor resolution: release and board, unknown "
             "claims nothing",
             a and a[0] == "release" and a[1] == 37 and a[2] == 37
             and b and b[0] == "board" and b[1] == 65 and b[2] == 65
             and anchor_for("/nope/x.rom", "/nope/y.rom") is None)
    except Exception as e:
        gate("R4 pair->anchor resolution", False, str(e))

    d42k = {"pair_coherence": {"profile": "clean-pair",
                               "births": [], "deaths": [],
                               "brand_new_species": [],
                               "refusals": []}}
    ck = cohere_compose(d42k, {"psp": {"added": 37, "removed": 37},
                               "blindness_witness": {"law": "w"}})
    gate("R5 cohere names the correction when the classes disagree",
         ck["fw42_profile"] == "clean-pair"
         and ck["corrected_profile"] == CLASS_SWAP
         and ck["profile_correction"]
         and ck["profile_correction"]["frozen_class"] == "clean-pair"
         and ck["profile_correction"]["corrected_class"] == CLASS_SWAP)
    d42k2 = {"pair_coherence": {"profile": CLASS_SWAP,
                                "births": [], "deaths": [],
                                "brand_new_species": [],
                                "refusals": []}}
    ck2 = cohere_compose(d42k2, {"psp": {"added": 5, "removed": 5},
                                 "blindness_witness": {"law": "w"}})
    gate("R5b agreeing classes -> correction is None (never "
         "invented)",
         ck2["corrected_profile"] == CLASS_SWAP
         and ck2["profile_correction"] is None)
    d42k3 = {"pair_coherence": {"profile": "refused",
                                "births": [], "deaths": [],
                                "brand_new_species": [],
                                "refusals": ["L2/L3 boom"]}}
    gate("R5c refusals outrank the set lens",
         cohere_compose(d42k3, {"psp": {"added": 5, "removed": 5},
                                "blindness_witness": {}})
         ["corrected_profile"] == CLASS_REFUSED)

    gate("R6 null verdict logic: survives vs corrected",
         null_verdict("clean-pair", CLASS_CLEAN, 0, 0) == "survives"
         and null_verdict("clean-pair", CLASS_SWAP, 12, 12)
         == "corrected"
         and null_verdict("swap-event", CLASS_SWAP, 3, 3)
         == "survives")

    gate("R7 per-module Refusal boundary (the ring-42 lesson)",
         f42.Refusal is not Refusal
         and f42.Refusal.__name__ == "Refusal"
         and Refusal.__name__ == "Refusal")

    wpat = 'open(path, ' + '"w"'
    n_writes = src.count(wpat)
    gate("R8 L4 zero-writes: exactly ONE write site (_write_doc)",
         n_writes == 1 and 'def _write_doc' in src,
         f"write sites={n_writes}")
    gate("R8b the four laws stated in source",
         all(s in src for s in
             ("L1 SET-TRUTH-OVER-COUNT", "L2 ANCHORS-BEFORE-MARKS",
              "L3 CORRECTED-TAXONOMY", "L4 ZERO WRITES")))

    # ---------------- tier I (live)
    print("tier I — live: the three acquisitions, the release pair, "
          "the board pair, the frozen null re-read")
    files = _load_mod("fw45-b550-lens").acq_files()
    ref = files.get("b550w2-3644")
    disc = files.get("b550w2-3645")
    sib = files.get("b550-nw-3644")
    gate("I0 acquisitions on disk (ring-44 vendor-verified)",
         bool(ref) and os.path.exists(ref)
         and bool(disc) and os.path.exists(disc)
         and bool(sib) and os.path.exists(sib),
         f"ref={ref} disc={disc} sib={sib}")

    try:
        n_ref, n_disc, n_sib = (len(psp_set(ref)), len(psp_set(disc)),
                                len(psp_set(sib)))
        lens = lens_register().get("images", {})
        gate("I1 live PSP sets reproduce the lens register counts "
             "(203/203/203)",
             (n_ref, n_disc, n_sib) == (203, 203, 203)
             and all(lens.get(k, {}).get("psp", {}).get("hash_count")
                     == 203 for k in ("b550w2-3644", "b550w2-3645",
                                      "b550-nw-3644")),
             f"live=({n_ref},{n_disc},{n_sib})")
    except Exception as e:
        gate("I1 live PSP sets reproduce the lens register counts",
             False, str(e))

    try:
        rel = pair_marks(ref, disc)
        gate("I2 release pair: set != with 37/37 BOTH ways "
             "(anchor-checked L2)",
             rel["psp"]["status"] == "!="
             and rel["psp"]["added"] == 37
             and rel["psp"]["removed"] == 37
             and rel["psp"]["anchor_kind"] == "release",
             f"added={rel['psp']['added']} "
             f"removed={rel['psp']['removed']}")
        gate("I3 release pair: THE LESSON live — count == AND set !=",
             rel["blindness_witness"]["count_level"] == "=="
             and rel["blindness_witness"]["set_level"] == "!="
             and rel["psp"]["old_count"] == rel["psp"]["new_count"]
             == 203)
        gate("I4 release pair species: 0 births / 0 deaths "
             "(pre-registered PR-1)",
             rel["species"]["births"] == 0
             and rel["species"]["deaths"] == 0,
             str({k: rel["species"][k] for k in
                  ("births", "deaths", "changed_modules")}))
        gate("I5 release pair corrected class == swap-event "
             "(pre-registered PR-4)",
             rel["corrected_class"] == CLASS_SWAP,
             rel["corrected_class"])
        rel_lens = {"psp": {k: rel["psp"][k]
                            for k in ("added", "removed")},
                    "blindness_witness": rel["blindness_witness"]}
        rel_corr = cohere_compose(
            {"pair_coherence": {"profile": "clean-pair",
                                "births": [], "deaths": [],
                                "brand_new_species": [],
                                "refusals": []}}, rel_lens)
        gate("I5b the correction vs fw42's frozen clean-pair is "
             "NAMED",
             rel_corr["profile_correction"]
             and rel_corr["profile_correction"]["frozen_class"]
             == "clean-pair"
             and rel_corr["profile_correction"]["corrected_class"]
             == CLASS_SWAP)
    except Refusal as e:
        gate("I2-I5 release pair marks", False, f"REFUSAL {e}")
    except Exception as e:
        gate("I2-I5 release pair marks", False,
             f"{type(e).__name__}: {e}")

    try:
        brd = pair_marks(ref, sib)
        gate("I6 board pair: set != with 65/65 (anchor-checked L2) "
             "— the same-version sibling swaps MORE than the release",
             brd["psp"]["status"] == "!="
             and brd["psp"]["added"] == 65
             and brd["psp"]["removed"] == 65
             and brd["psp"]["anchor_kind"] == "board",
             f"added={brd['psp']['added']} "
             f"removed={brd['psp']['removed']}")
        gate("I7 board pair species: 0 births / 4 deaths — PR-6 "
             "(0/0) REFUTED by measurement, the measurement wins "
             "pre-freeze",
             brd["species"]["births"] == 0
             and brd["species"]["deaths"] == 4,
             str({k: brd["species"][k] for k in
                  ("births", "deaths", "changed_modules")}))
        gate("I7b board pair corrected class == registered-births "
             "(the precedence working: 4 species deaths outrank the "
             "65/65 swap)",
             brd["corrected_class"] == CLASS_BIRTHS,
             brd["corrected_class"])
    except Refusal as e:
        gate("I6-I7 board pair marks", False, f"REFUSAL {e}")
    except Exception as e:
        gate("I6-I7 board pair marks", False,
             f"{type(e).__name__}: {e}")

    try:
        null = null3802()
        rr = null["re_reading"]
        gate("I8 null3802 re-read: births/deaths reproduce the "
             "frozen row (0/0)",
             rr["species"]["births"] == 0
             and rr["species"]["deaths"] == 0
             and null["frozen_row"]["births"] == 0
             and null["frozen_row"]["deaths"] == 0)
        gate("I8b null3802: the reading completes and the verdict is "
             "recorded (either way — the register wins or the "
             "correction is named)",
             null["verdict"] in ("survives", "corrected")
             and rr["corrected_class"] in (CLASS_CLEAN, CLASS_SWAP,
                                           CLASS_BIRTHS, CLASS_BEYOND),
             f"verdict={null['verdict']} "
             f"class={rr['corrected_class']} "
             f"psp=+{rr['psp']['added']}/-{rr['psp']['removed']}")
    except Refusal as e:
        gate("I8 null3802 re-read", False, f"REFUSAL {e}")
    except Exception as e:
        gate("I8 null3802 re-read", False, f"{type(e).__name__}: {e}")

    # ---------------- crown register (present after the artifact run)
    pr = pair_register()
    if pr is None:
        gate("R9 crown register: absent pre-crown (loud degrade, "
             "written by scripts/ring47_artifact.py)", True,
             "vendor-pairmarks-register.json not yet written")
        gate("R9b manifest states the register basis", True,
             "pre-crown")
    else:
        try:
            crown = pr.get("crown", {})
            relc = (crown.get("release_pair") or {}).get("psp") or {}
            gate("R9 crown register: the release-pair set delta "
                 "agrees with a live re-derivation",
                 relc.get("added") == 37 and relc.get("removed") == 37,
                 str({k: relc.get(k) for k in ("added", "removed")}))
            nul = crown.get("null3802") or {}
            gate("R9b crown register: the null verdict is recorded "
                 "with its re-reading",
                 nul.get("verdict") in ("survives", "corrected")
                 and bool(nul.get("re_reading")),
                 f"verdict={nul.get('verdict')}")
        except Exception as e:
            gate("R9 crown register gates", False, str(e))

    print(f"fw47-pairmarks selftest: {ok[0]}/{ok[0] + len(fails)} gates "
          f"PASS (tier R + tier I live)")
    return 1 if fails else 0


# ---------------------------------------------------------------- manifest

def manifest():
    """The instrument's self-description (the fw35 manifest law)."""
    modes = ["marks <old> <new> [--out out.json]",
             "cohere <old> <new> [--out out.json]",
             "null3802 [--out out.json]", "selftest", "manifest"]
    regs = {
        "basis": "vendor-b550-lens.json (ring 45: psp_set_deltas "
                 "release 37/37 + board 65/65 — the ONLY source of "
                 "anchor numbers)",
        "frozen_null": "vendor-dossier-register.json (ring 42: "
                       "pair_null_dossier 3802->3810, read never "
                       "rewritten)",
        "this_ring": "vendor-pairmarks-register.json (the crown: the "
                     "release pair, the board pair, the null verdict "
                     "— written by scripts/ring47_artifact.py)",
        "upstream": ["vendor-ledger-b550w2.json (ring 44: the "
                     "acquisitions)",
                     "vendor-autodossier-register.json (ring 46: the "
                     "count-blindness find, healed here one layer "
                     "wider)"],
    }
    print(json.dumps({
        "instrument": "fw47-pairmarks", "ring": RING,
        "title": "the pair witness: set-anchored pair coherence, "
                 "measured",
        "modes": modes,
        "laws": ["L1 set-truth-over-count",
                 "L2 anchors-before-marks",
                 "L3 corrected-taxonomy", "L4 zero writes"],
        "chain": ["psp_set (fw43.psp_bodies on fw37.load)",
                  "set_marks_sets (anchor-checked, count = witness "
                  "only)",
                  "fw37.ledger (species births/deaths + changed row)",
                  "corrected_class (the full-evidence taxonomy)",
                  "cohere: fw42.dossier_pair composed, the correction "
                  "named"],
        "registers": regs,
        "corrected_taxonomy": {
            CLASS_REFUSED: "fw42's refusals stand",
            CLASS_BEYOND: "brand-new species (fw42 semantics)",
            CLASS_BIRTHS: "species births/deaths (fw42 semantics)",
            CLASS_SWAP: "containers stable, content swapped "
                        "(NEW — the class the pair layer lacked)",
            CLASS_CLEAN: "requires set delta == 0 (the correction)",
        },
        "discriminator_law": "the pair layer now sees what the "
                             "registers proclaim: 3644->3645 is a "
                             "swap-event (37/37 PSP hashes inside "
                             "203-hash sets, 0 births, 0 deaths), "
                             "never a clean-pair",
    }, indent=1))
    return 0


# ---------------------------------------------------------------- main

def _show_marks(m):
    """The cheap review print (marks mode)."""
    p, s, bw = m["psp"], m["species"], m["blindness_witness"]
    anch = (f" [{p['anchor_kind']} anchor {p['anchor']['added']}/"
            f"{p['anchor']['removed']}]" if p.get("anchor") else
            " [no anchor claimed]")
    print(f"marks {os.path.basename(m['old'])} -> "
          f"{os.path.basename(m['new'])}  [fw47, ring {RING}]")
    print(f"  psp set:  {p['status']}  added {p['added']} / "
          f"removed {p['removed']}  (counts {p['old_count']} vs "
          f"{p['new_count']}){anch}")
    print(f"  witness:  count {bw['count_level']} | species "
          f"{bw['species_level']} | {s['changed_modules']} modules "
          f"changed ({s['byte_delta']:+d} B)")
    print(f"  class:    {m['corrected_class']}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fw47-pairmarks")
    ap.add_argument("mode",
                    choices=["marks", "cohere", "null3802", "selftest",
                             "manifest"])
    ap.add_argument("images", nargs="*", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    if a.mode == "manifest":
        return manifest()
    if a.mode == "selftest":
        return selftest()

    try:
        if a.mode == "marks":
            if len(a.images) != 2:
                print("marks <old> <new>", file=sys.stderr)
                return 2
            m = pair_marks(a.images[0], a.images[1])
            _show_marks(m)
            if a.out:
                _write_doc(a.out, m)
            return 0
        if a.mode == "cohere":
            if len(a.images) != 2:
                print("cohere <old> <new>", file=sys.stderr)
                return 2
            doc = cohere(a.images[0], a.images[1], out=a.out)
            _show_marks(doc["pair_marks"])
            c = doc["corrected"]
            print(f"  fw42 profile: {c['fw42_profile']} | corrected: "
                  f"{c['corrected_profile']}")
            if c["profile_correction"]:
                pc = c["profile_correction"]
                print(f"  CORRECTION NAMED: {pc['frozen_class']} -> "
                      f"{pc['corrected_class']}")
            return 0
        if a.mode == "null3802":
            doc = null3802(out=a.out)
            _show_marks(doc["re_reading"])
            print(f"  frozen: {doc['frozen_row']['profile']} | "
                  f"corrected: {doc['corrected_class']} | verdict: "
                  f"{doc['verdict']}")
            print(f"  {doc['verdict_note']}")
            return 0
    except Refusal as e:
        print(f"REFUSAL: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
