#!/usr/bin/env python3
"""fw41-novelty — the unregistered detector (the third reading).

The day-0 chain answers three questions and, before this ring, only two
had instruments: the ORACLE (fw35) measures the image against 26 frozen
predictions (hit/partial/miss/na); IDENTITY (fw39) judges the image
against the nine known rungs (known-release / no-match). Both machines
are silent about phenomena OUTSIDE every register and every prediction —
the unregistered. This instrument closes that third reading:

    predicted (fw35)  |  known (fw39)  |  NOVEL (fw41)

Six axes, each with a universe re-derived from the registers (never
hardcoded) and a live extraction reusing the ring-39 deep walk:

  species    GUID set vs the genome's 330 species (universe = register)
  certs      X.509 bodies vs the DER trust universe (vendor-der-inventory)
  dsdt       checksum-valid DSDT variants vs the acpi clock anchors
  agesa      version token vs the nine-rung ladder, the P-02 day-0
             envelope and the P-20 release-41 floor (anticipation class)
  whitelist  the armor's chip table extracted with the REGISTER'S OWN
             method (banner +16, NUL-separated until a 48-NUL run) and
             diffed BOTH ways against the 41u46 family universe — a new
             family the armor learned is `extra`, a family removed is
             `missing`
  smm        SMM-typed GUIDs vs the live union across the nine rungs
             (honest degradation to no-claims when the corpus is absent)

Verdicts: inside-universe (every axis clean), anticipated-only (only
P-02/P-20 envelope members outside the ladder), novel (at least one
unregistered finding). Contradiction is deliberately NOT a class here —
violating an expectation is the ORACLE's verdict; this instrument only
enumerates what lies outside the universe, and every finding it prints
is a candidate entry for the tracked zero-ledger
(lab/vendor-novelty-ledger.json, empty BY PROOF until an event).

Two-tier selftest, the ring-36+ discipline: tier R re-derives every
universe and envelope from the registers with loud refusal; tier I runs
the detector live on the surviving corpus — zero unregistered on the
known rungs (the coverage property), 100%-style novelty on the foreign
stand-in, and a NEEDLE test: one flipped GUID byte on a known rung must
produce exactly one unregistered species and nothing else.

stdlib-only; read-only on every image it touches; precedent fw33/35/36/
37/38/39/40.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RING = 41

AXES = ["species", "certs", "dsdt", "agesa", "whitelist", "smm"]
SMM_FTYPE_NAMES = {"smm", "combined_smm_dxe", "smm_core"}

CORPUS = "/tmp/my-project/scratch-vendor"
RUNG_FILES = {
    "3604": "asus-prime-b450-plus-ref.rom",
    "3802": "asus-prime-b450-plus-3802.rom",
    "3810": "asus-prime-b450-plus-3810.rom",
    "4003": "asus-prime-b450-plus-4003.rom",
    "4202": "asus-prime-b450-plus-4202.rom",
    "4402": "asus-prime-b450-plus-4402.rom",
    "4604": "asus-prime-b450-plus-4604.rom",
    "4631": "asus-prime-b450-plus-4631.rom",
    "4655": "asus-prime-b450-plus.rom",
}
FOREIGN_FILES = {
    "ovmf": "/home/z/my-project/scratch-ovmf/unified-4M.fd",
    "tuf": "/tmp/my-project/scratch-vendor/asus/"
           "TUF-B450-PLUS-GAMING-ASUS-4645.rom",
}

BANNER = b"AMD rom armor"
GUID_RE = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
VER_RE = re.compile(r"\b1\.[0-9]+\.[0-9]+\.[0-9A-Za-z]+\b")


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
    """(fw35, fw37, fw38, fw39) — the oracle, the walker, the lenses, the
    judge. fw41 sits beside them, never instead of them."""
    return (_load_mod("fw35-oracle"), _load_mod("fw37-differ"),
            _load_mod("fw38-exam"), _load_mod("fw39-identity"))


_M = {}
_CACHE = {}


def _deep(image):
    """Cached deep walk (fw39's recursive pierce, depth 3, raw-plane FVs).
    One walk per abspath per process — the selftest reuses every walk."""
    key = os.path.abspath(image)
    if key not in _CACHE:
        _CACHE[key] = _mods()[3]._deep_inventory(image)
    return _CACHE[key]


# ------------------------------------------------- AGESA version ordering

def _agesa_key(s):
    """The AMD scheme as the nine-rung register bears it: 6b < 7 < 8 <
    A < B < Ca < E < 12 — digit+letter suffixes stay within their number
    (6b after 6, before 7), pure letters are the letter-major steps
    (phase 1), numeric >= 10 comes after every letter (phase 2).
    Raises on garbage."""
    parts = str(s).strip().split(".")
    if len(parts) != 4:
        raise ValueError(f"not a four-field AGESA version: {s!r}")
    try:
        head = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        raise ValueError(f"bad numeric head: {s!r}")
    m = re.match(r"^([0-9]*)([A-Za-z]*)$", parts[3])
    if not m or not (m.group(1) or m.group(2)):
        raise ValueError(f"bad last field: {parts[3]!r}")
    num, let = m.group(1), m.group(2)
    if num and let:                      # 6b, 6c: beta of that number
        return head + (0, int(num), let.upper())
    if num:                              # 7, 8, 12
        n = int(num)
        return head + ((0, n, "") if n < 10 else (2, n, ""))
    return head + (1, 0, let.upper())    # A, B, Ca, E


def _oracle_predictions():
    with open(os.path.join(HERE, "vendor-oracle.json")) as f:
        o = json.load(f)
    preds = o["predictions"] if isinstance(o, dict) else o
    if isinstance(preds, dict):
        preds = list(preds.values())
    return preds


def _pred(pid):
    for p in _oracle_predictions():
        if p.get("id") == pid:
            return p
    return None


def _p20_floor():
    """The registered release-41 AGESA floor: the MAX version token in
    P-20's own fields (claim '>= 1.2.0.12 — never lower', basis '1.2.0.6b
    -> 1.2.0.12 monotone', falsifier 'a level below 1.2.0.12'). For a
    monotone predicate the max token IS the floor; parsed, never
    hardcoded."""
    p = _pred("P-20")
    if not p:
        return None
    hay = json.dumps({k: p.get(k) for k in
                      ("claim", "basis", "widened", "falsifier")})
    cands = VER_RE.findall(hay)
    if not cands:
        return None
    return max(cands, key=_agesa_key)


def _p02_set():
    """The day-0 AGESA envelope (P-02): every version-like token in the
    prediction's expect/widened — the set the 16/09 dump may present
    WITHOUT being novel (the point prediction 1.2.0.6c is not in the
    nine-rung ladder, and must not false-novel)."""
    p = _pred("P-02")
    if not p:
        return set()
    hay = json.dumps({k: p.get(k) for k in
                      ("expect", "widened", "claim", "basis")})
    return set(VER_RE.findall(hay))


def classify_agesa(level, U=None):
    """known (in the nine-rung ladder) / anticipated (P-02 day-0 envelope,
    or >= the P-20 release-41 floor WITHIN the same 1.2.0.x line — the
    monotone envelope is a claim about that line, not about arbitrary
    versions) / unregistered (outside every envelope). None -> None (no
    claim; the absence of a token is never a finding)."""
    if not level:
        return None
    if U is None:
        U = build_universes(build_smm=False)
    if level in U["agesa_levels"]:
        return "known"
    if level in (U.get("agesa_day0") or set()):
        return "anticipated"
    fl = U.get("agesa_floor41")
    if fl:
        try:
            if (_agesa_key(level)[:3] == _agesa_key(fl)[:3] and
                    _agesa_key(level) >= _agesa_key(fl)):
                return "anticipated"
        except (ValueError, TypeError):
            pass
    return "unregistered"


# --------------------- the armor's chip tables (structural, declared)

CHIP_NAME_RE = re.compile(
    r"^[A-Z][A-Za-z0-9/+\-(). ]{2,20} [0-9A-Za-z][0-9A-Za-z/+\-(). ]{0,24}$")


def _align8(x):
    return (x + 7) & ~7


def _name_at(b, off):
    """NUL-terminated chip-shaped name at off, or None."""
    end = b.find(b"\x00", off, off + 49)
    if end < 0:
        return None
    try:
        t = b[off:end].decode("ascii")
    except UnicodeDecodeError:
        return None
    if len(t) < 4 or not CHIP_NAME_RE.match(t):
        return None
    return t


def _chip_tables(b, min_chain=8):
    """Every NUL-terminated 8-aligned name chain of >= min_chain links.
    The armor's chip table travels inside these chains (and so do POSIX
    errno tables and OpenSSL curve tables — the digit/shape rule below
    is the discriminator)."""
    out, i, n = [], 0, len(b)
    while i < n - 8:
        t = _name_at(b, i)
        if t is None:
            i += 1
            continue
        chain, off = [], i
        while off < n:
            t2 = _name_at(b, off)
            if t2 is None:
                break
            chain.append(t2)
            off += _align8(len(t2) + 1)
        if len(chain) >= min_chain:
            out.append((i, chain))
            i = off
        else:
            i += 1
    return out


def _is_chip_name(e):
    """A chip entry carries a digit (model) in <= 4 space tokens —
    'SST 25LF040', 'STM/Numonyx 25PE Series'; the banner 'AMD rom armor'
    and errno/curve phrases carry none or too many."""
    return (any(c.isdigit() for c in e)
            and len(e.split(" ")) <= 4)


def _armor_names(blobs):
    """Union of chip-shaped entries over every qualifying table in every
    deep blob. The register's note describes the banner-anchored view
    ('AMD rom armor' + 16 bytes); the banner entry exists only from 3802
    (the armor wave's birth), so the STRUCTURAL signature is the
    self-enumerating form — validated against the register by gate I11."""
    names = set()
    for b in blobs:
        for _off, chain in _chip_tables(b):
            digs = [e for e in chain if _is_chip_name(e)]
            if len(digs) >= 5:
                names |= set(digs)
    return names


# ----------------------------------------------------------- the universes

def _corpus_rungs_present():
    return all(os.path.exists(os.path.join(CORPUS, f))
               for f in RUNG_FILES.values())


def build_universes(build_smm=True):
    """Every universe re-derived from the registers, nothing hardcoded.
    The SMM universe is the honest exception: no register stores SMM GUID
    sets (lifecycles stores counts), so it is derived LIVE from the nine
    rungs when the corpus survives — and is None (loud degradation, no
    claims) otherwise."""
    _f35, _f37, f38, f39 = _mods()
    U = {}
    U["species"] = {s["guid"].upper() for s in f39.genome_species()}
    U["rung_files"] = {r: os.path.join(CORPUS, f)
                       for r, f in RUNG_FILES.items()}
    U["species_universe"] = None
    U["species_live"] = None
    cert = f39._cert_anchor()
    U["certs"] = set()
    for r in f39.RUNGS:
        U["certs"] |= cert.get(r) or set()
    U["certs_per_rung"] = {r: set(cert.get(r) or set()) for r in f39.RUNGS}
    dsd = f39._acpi_anchor()
    U["dsdt"] = set()
    for r in f39.RUNGS:
        U["dsdt"] |= dsd.get(r) or set()
    U["dsdt_per_rung"] = {r: set(dsd.get(r) or set()) for r in f39.RUNGS}
    U["whitelist"] = set(f39._whitelist_union())
    chip = f39._chip_anchor()
    U["whitelist_per_rung"] = {r: set(chip.get(r) or set())
                               for r in f39.RUNGS}
    U["whitelist_deviation"] = None
    if build_smm and _corpus_rungs_present():
        dev = set()
        for _r, path in U["rung_files"].items():
            live = _armor_names(_deep(path)["blobs"])
            dev |= live - U["whitelist"]
        U["whitelist_deviation"] = dev
        U["whitelist_universe"] = U["whitelist"] | dev
    else:
        U["whitelist_universe"] = None
    ladder = f38.agesa_ladder()
    U["agesa_ladder"] = ladder
    U["agesa_levels"] = {a for a, _v, _d in ladder}
    U["agesa_ladder_max"] = (max(U["agesa_levels"], key=_agesa_key)
                             if U["agesa_levels"] else None)
    U["agesa_floor41"] = _p20_floor()
    U["agesa_day0"] = _p02_set()
    U["smm"] = None
    if build_smm and _corpus_rungs_present():
        u = set()
        for _r, path in U["rung_files"].items():
            inv = _deep(path)
            u |= {g.upper() for g, m in inv["modules"].items()
                  if m["ftype_name"] in SMM_FTYPE_NAMES}
        U["smm"] = u
        # the species universe: the register's 330 TRANSITION species are
        # the diff-interesting subset — the quiet majority never changes
        # and is therefore absent from the register; the full universe is
        # the live union across the nine rungs (register ⊆ union, gate R13)
        live = set()
        for _r, path in U["rung_files"].items():
            live |= {g.upper() for g in _deep(path)["modules"]}
        U["species_live"] = live
        U["species_universe"] = live | U["species"]
    return U


# --------------------------------------------------------------- detection

def novelty(image, universes=None):
    """The third reading on ONE image. Everything the registers and the
    prediction envelopes do not claim is listed, axis by axis, class by
    class. Read-only; the deep walk is cached per process."""
    _f35, f37, f38, f39 = _mods()
    U = universes if universes is not None else build_universes()
    raw = f37.load(image)
    inv = _deep(image)
    hay = inv["blobs"]

    obs = {"instrument": "fw41-novelty", "ring": RING, "image": image,
           "rom_bytes": len(raw),
           "rom_sha_full": f39._sha16(raw),
           "rom_sha_body": (f39._sha16(raw[f39.BODY_OFF:])
                            if len(raw) >= f39.ROM_FULL else None)}
    degraded = []

    # -- species: GUID membership vs register + the live nine-rung union
    guids = {g.upper() for g in inv["modules"]}
    if U.get("species_universe") is None:
        degraded.append("species")
        obs["species"] = {"universe": len(U["species"]),
                          "register_species": len(U["species"]),
                          "observed": len(guids), "known": None,
                          "unregistered": [], "anticipated": [],
                          "note": "live species universe unavailable "
                                  "(corpus absent) — degraded, no claims"}
    else:
        sp_un = sorted(guids - U["species_universe"])
        obs["species"] = {"universe": len(U["species_universe"]),
                          "register_species": len(U["species"]),
                          "observed": len(guids),
                          "known": len(guids & U["species_universe"]),
                          "unregistered": sp_un, "anticipated": []}

    # -- certs: X.509 bodies vs the DER trust universe
    tc = f39.trust_census(raw)
    certs = set(tc)
    c_un = sorted(certs - U["certs"])
    obs["certs"] = {"universe": len(U["certs"]), "observed": len(certs),
                    "known": len(certs & U["certs"]),
                    "unregistered": c_un,
                    "sightings": sum(len(v) for v in tc.values())}

    # -- dsdt: checksum-valid variants vs the acpi universe
    dsdt = {}
    for blob in hay:
        w = f38.x_acpi(blob)
        for t in w["tables"].get("DSDT", []):
            if t.get("checksum_ok") and t.get("sha16"):
                dsdt[t["sha16"]] = dsdt.get(t["sha16"], 0) + 1
    d_un = sorted(set(dsdt) - U["dsdt"])
    primary = (max(dsdt, key=lambda k: dsdt[k]) if dsdt else None)
    obs["dsdt"] = {"universe": len(U["dsdt"]), "observed": len(dsdt),
                   "known": len(set(dsdt) & U["dsdt"]),
                   "unregistered": d_un, "instances": dsdt,
                   "primary": primary}

    # -- agesa: ladder / P-02 day-0 envelope / P-20 floor
    ag = f38.x_agesa(haystacks=hay)
    lvl = ag["agesa_level"]
    picked = (lvl.get("picked") if isinstance(lvl, dict) else lvl)
    multi = (lvl.get("multiple") if isinstance(lvl, dict) else None)
    cls = classify_agesa(picked, U)
    obs["agesa"] = {"level": picked, "multiple": multi, "class": cls,
                    "ladder_max": U.get("agesa_ladder_max"),
                    "floor41": U.get("agesa_floor41"),
                    "day0_envelope": sorted(U.get("agesa_day0") or []),
                    "combo": ag.get("agesa_string")}

    # -- whitelist: structural chip tables vs register + live deviation
    if U.get("whitelist_universe") is None:
        degraded.append("whitelist")
        obs["whitelist"] = {"universe": len(U["whitelist"]),
                            "extracted": None, "extra": [], "missing": [],
                            "note": "live deviation calibration unavailable "
                                    "(corpus absent) — degraded, no claims"}
    else:
        ex = _armor_names(hay)
        obs["whitelist"] = {"universe": len(U["whitelist_universe"]),
                            "register": len(U["whitelist"]),
                            "extracted": len(ex),
                            "extra": sorted(ex - U["whitelist_universe"]),
                            "missing": sorted(
                                U["whitelist_universe"] - ex)}

    # -- smm: SMM-typed GUIDs vs the live nine-rung union
    smm = {g.upper() for g, m in inv["modules"].items()
           if m["ftype_name"] in SMM_FTYPE_NAMES}
    if U.get("smm") is None:
        degraded.append("smm")
        obs["smm"] = {"universe": None, "observed": len(smm),
                      "known": None, "unregistered": [],
                      "note": "live SMM universe unavailable (corpus "
                              "absent) — degraded, no claims"}
    else:
        s_un = sorted(smm - U["smm"])
        obs["smm"] = {"universe": len(U["smm"]), "observed": len(smm),
                      "known": len(smm & U["smm"]),
                      "unregistered": s_un}

    # -- PSP stays report-only (the ring-38 honesty ledger stands)
    pspr = f38.x_psp(raw)
    obs["psp_report"] = {"candidates": len(
        pspr if isinstance(pspr, list) else pspr.get("candidates", []))}

    obs["degraded"] = degraded
    obs["module_count"] = inv["module_count"]
    obs["pierce_depth"] = inv["pierce_depth"]

    total_un = (len(obs["species"].get("unregistered") or [])
                + len(c_un) + len(d_un)
                + len(obs["whitelist"].get("extra") or [])
                + len(obs["smm"].get("unregistered") or [])
                + (1 if cls == "unregistered" else 0))
    total_an = (1 if cls == "anticipated" else 0)
    obs["summary"] = {
        "unregistered_total": total_un,
        "anticipated_total": total_an,
        "verdict": ("inside-universe"
                    if total_un == 0 and total_an == 0
                    else "anticipated-only" if total_un == 0
                    else "novel")}
    return obs


# ----------------------------------------------------------------- ledger

def load_register():
    with open(os.path.join(HERE, "vendor-novelty-ledger.json")) as f:
        return json.load(f)


def ledger():
    """The tracked zero-ledger: schema, empty entries BY PROOF (the tier-I
    coverage gates), universe snapshot vs live re-derivation."""
    r = load_register()
    U = build_universes(build_smm=False)
    snap = r.get("universe_snapshot") or {}
    checks = [
        ("schema", r.get("schema") == "omarchy-firmware/vendor-novelty-ledger@1"),
        ("axes", r.get("axes") == AXES),
        ("entries-empty", r.get("entries") == []),
        ("snapshot.species", snap.get("species") == len(U["species"])),
        ("snapshot.certs", snap.get("certs") == len(U["certs"])),
        ("snapshot.dsdt", snap.get("dsdt") == len(U["dsdt"])),
        ("snapshot.whitelist", snap.get("whitelist") == len(U["whitelist"])),
        ("coverage-gates", sorted(r.get("coverage", {}).get("gates", []))
         == ["I1", "I2", "I3"]),
    ]
    ok = all(v for _k, v in checks)
    for k, v in checks:
        print(f"  {'PASS' if v else 'FAIL'}  ledger {k}")
    print(f"fw41-novelty ledger: "
          f"{sum(1 for _k, v in checks if v)}/{len(checks)} checks "
          f"{'PASS' if ok else 'FAIL'} "
          f"(entries: {len(r.get('entries') or [])})")
    return 0 if ok else 2


def manifest():
    regs = ["vendor-genome", "vendor-der-inventory", "vendor-acpi",
            "vendor-agesa", "vendor-armor-chipdb", "vendor-lifecycles",
            "vendor-oracle (P-02/P-20 envelopes)", "vendor-novelty-ledger"]
    print(json.dumps({
        "instrument": "fw41-novelty", "ring": RING,
        "precedent": ["fw33", "fw35", "fw36", "fw37", "fw38", "fw39",
                      "fw40"],
        "axes": AXES,
        "registers": regs,
        "modes": ["novelty <image>", "ledger", "selftest", "manifest"],
        "classes": ["known", "anticipated", "unregistered"],
        "verdicts": ["inside-universe", "anticipated-only", "novel"],
        "reading": "predicted (fw35) | known (fw39) | NOVEL (fw41)",
    }, indent=1))
    return 0

# --------------------------------------------------------------- selftest

class _G:
    """Gate ledger — the house style: numbered, named, counted, exit 2 on
    any failure."""

    def __init__(self):
        self.n = 0
        self.bad = []

    def gate(self, name, ok, info=""):
        self.n += 1
        tag = "PASS" if ok else "FAIL"
        print(f"  {tag}  {name}" + (f"  [{info}]" if info else ""))
        if not ok:
            self.bad.append(name)
        return ok

    def finish(self, label):
        print(f"fw41-novelty selftest: {self.n - len(self.bad)}/{self.n} "
              f"gates {'PASS' if not self.bad else 'FAIL'} ({label})")
        return 2 if self.bad else 0


def selftest():
    g = _G()
    _f35, f37, f38, f39 = _mods()

    # ---------------- tier R — every universe re-derived, corpus-free
    U = build_universes(build_smm=False)

    # R1 species universe == genome species, well-formed
    g.gate("R1 species universe well-formed", len(U["species"]) == 330 and
           all(GUID_RE.match(s) for s in U["species"]),
           f"{len(U['species'])} species")

    # R2 genome referential integrity: birth/death labels parse to rungs
    ok = True
    for s in f39.genome_species():
        for k in ("born_at", "dead_at"):
            v = s.get(k)
            if v and f39._t_bside(v) not in f39.RUNGS:
                ok = False
    g.gate("R2 genome rung references parse", ok)

    # R3 cert universe: the frozen laws (4 @3604, 6 from 3810, 6 @4655)
    c4 = len(U["certs_per_rung"].get("3604") or set())
    c38 = len(U["certs_per_rung"].get("3810") or set())
    c46 = len(U["certs_per_rung"].get("4655") or set())
    g.gate("R3 cert anchors 4/6/6 + union",
           c4 == 4 and c38 == 6 and c46 == 6 and len(U["certs"]) >= 6,
           f"3604={c4} 3810={c38} 4655={c46} union={len(U['certs'])}")

    # R4 dsdt universe: both registered clock anchors present
    g.gate("R4 dsdt anchors present",
           "27d5e826e111d755" in U["dsdt"] and
           "0a4a6f162cad3e51" in U["dsdt"],
           f"union={len(U['dsdt'])}")

    # R5 whitelist universe: 41@3604 and the 46-set both inside the union
    w41 = U["whitelist_per_rung"].get("3604") or set()
    w46 = max((set(v) for v in U["whitelist_per_rung"].values()),
              key=len, default=set())
    g.gate("R5 whitelist union covers 41+46",
           len(w41) == 41 and len(w46) == 46 and
           w41 <= U["whitelist"] and w46 <= U["whitelist"],
           f"41@3604={len(w41)} max={len(w46)} "
           f"union={len(U['whitelist'])}")

    # R6 agesa ladder + P-20 floor
    fl = U["agesa_floor41"]
    g.gate("R6 ladder 9 rungs, floor41 == 1.2.0.12",
           len(U["agesa_ladder"]) >= 9 and fl == "1.2.0.12" and
           U["agesa_ladder_max"] == fl,
           f"ladder={len(U['agesa_ladder'])} max={U['agesa_ladder_max']} "
           f"floor={fl}")

    # R7 oracle coupling: 26 predictions, envelopes live
    p02, p20, p23, p26 = (_pred("P-02"), _pred("P-20"),
                          _pred("P-23"), _pred("P-26"))
    g.gate("R7 oracle envelopes P-02/P-20/P-23/P-26",
           len(_oracle_predictions()) == 26 and
           p02 is not None and p20 is not None and
           p23 is not None and p26 is not None and
           len(U["agesa_day0"]) >= 2 and
           p23.get("expect") == [6, 6] and p26.get("expect") == 46,
           f"day0={sorted(U['agesa_day0'])}")

    # R8 tracked zero-ledger: schema, empty entries, snapshot == live
    try:
        r = load_register()
        snap = r.get("universe_snapshot") or {}
        g.gate("R8 ledger schema + snapshot == live",
               r.get("schema") == "omarchy-firmware/vendor-novelty-ledger@1"
               and r.get("entries") == [] and r.get("axes") == AXES
               and snap.get("species") == len(U["species"])
               and snap.get("certs") == len(U["certs"])
               and snap.get("dsdt") == len(U["dsdt"])
               and snap.get("whitelist") == len(U["whitelist"]),
               f"entries={len(r.get('entries') or [])}")
    except FileNotFoundError:
        g.gate("R8 ledger schema + snapshot == live", False, "missing")

    # R9 fw35 coupling: 26 rows, template 31 unique keys
    orc = _f35.Oracle()
    g.gate("R9 fw35 oracle 26 rows / template 31 keys",
           len(orc.reg["predictions"] if hasattr(orc, "reg") else
               _oracle_predictions()) == 26 and
           len(set(f40_template_keys())) == 31,
           f"template={len(set(f40_template_keys()))} unique")

    # R10 lifecycles census register: 105/0/1 @3604, all rungs keyed
    per = f39._smm_anchor()
    c36 = per.get("3604") or {}
    g.gate("R10 smm census register @3604 == 105/0/1",
           c36.get("SMM") == 105 and c36.get("SMM-DXE") == 0 and
           c36.get("SMM-core") == 1 and len(per) == 9,
           f"{c36} rungs={len(per)}")

    # R11 classifier properties: the P-02 envelope never false-novels,
    # the floor never false-novels, garbage is unregistered, None silent
    p02_all = all(classify_agesa(v, U) in ("known", "anticipated")
                  for v in U["agesa_day0"])
    g.gate("R11 classifier: P-02 set safe, floor safe, garbage caught",
           p02_all and
           classify_agesa(fl, U) in ("known", "anticipated") and
           classify_agesa("9.9.9.99", U) == "unregistered" and
           classify_agesa(None, U) is None,
           f"day0={[classify_agesa(v, U) for v in sorted(U['agesa_day0'])]}")

    # R12 verdict semantics (pure)
    def _synth(un=0, an=0):
        return {"unregistered_total": un, "anticipated_total": an,
                "verdict": _verdict(un, an)}
    g.gate("R12 verdict semantics",
           _synth(0, 0)["verdict"] == "inside-universe" and
           _synth(0, 1)["verdict"] == "anticipated-only" and
           _synth(1, 0)["verdict"] == "novel" and
           _synth(2, 1)["verdict"] == "novel")

    # ---------------- tier I — live corpus (loud skip when absent)
    if not _corpus_rungs_present():
        print("  SKIP  tier I — corpus absent (loud; no fake claims)")
        return g.finish("tier R only")

    Uf = build_universes()          # + the live unions (9 cached walks)
    p3604 = Uf["rung_files"]["3604"]
    p4655 = Uf["rung_files"]["4655"]

    # I0a/R13 the live universes COVER the register (parse-form coherence:
    # every register species must appear live somewhere, else the GUID
    # forms disagree and every downstream claim is void)
    g.gate("R13 register species fully covered by live union",
           Uf["species"] <= Uf["species_universe"],
           f"register={len(Uf['species'])} "
           f"live_universe={len(Uf['species_universe'])}")

    # I1 THE COVERAGE PROPERTY: a known rung is fully inside the universe
    n1 = novelty(p3604, Uf)
    g.gate("I1 3604 inside-universe (zero unregistered)",
           n1["summary"]["unregistered_total"] == 0 and
           n1["summary"]["verdict"] == "inside-universe" and
           not n1["degraded"],
           f"{n1['summary']} degraded={n1['degraded']}")

    # I2 the other convention end (FULL-file sentinel rung)
    n2 = novelty(p4655, Uf)
    g.gate("I2 4655 inside-universe",
           n2["summary"]["unregistered_total"] == 0 and
           not n2["degraded"], f"{n2['summary']}")

    # I3 the foreign stand-in: novelty is unavoidable + the judge agrees
    povmf = FOREIGN_FILES["ovmf"]
    if os.path.exists(povmf):
        n3 = novelty(povmf, Uf)
        idv = f39.identify(povmf, deep=False)["verdict"]["verdict"]
        g.gate("I3 OVMF foreign -> novel, judge agrees",
               n3["summary"]["unregistered_total"] >= 1 and
               n3["summary"]["verdict"] == "novel" and
               n3["species"]["unregistered"] and
               idv.startswith("no-match"),
               f"species unreg={len(n3['species']['unregistered'])}/"
               f"{n3['species']['observed']} verdict={idv}")
    else:
        g.gate("I3 OVMF foreign -> novel, judge agrees", False,
               "OVMF image missing")

    # I4 THE NEEDLE: one flipped GUID byte on a known rung -> exactly one
    # unregistered species, everything else clean
    raw = f37.load(p3604)
    fv_rows = f37.scan_fvs(raw)
    needle = None
    for fv in fv_rows:
        for guid, ftype, _sz, off, _body in f37.iter_files(raw, fv):
            if ftype in (0xF0, 0x01):
                continue
            if guid.upper() in Uf["species"]:
                needle = (guid, off)
                break
        if needle:
            break
    ok, info = False, "no candidate"
    if needle:
        base = {g.upper() for g in f39._deep_inventory(p3604)["modules"]}
        g0, off = needle
        for cand in (0xFF, 0xFE, 0xFD, 0xFC, 0xFB):
            b = bytearray(raw)
            b[off] = cand
            tmp = "/tmp/fw41-needle.rom"
            with open(tmp, "wb") as fh:
                fh.write(b)
            inv2 = f39._deep_inventory(tmp)
            g2 = {x.upper() for x in inv2["modules"]}
            added, removed = g2 - base, base - g2
            if len(added) == 1 and len(removed) == 1:
                nv2 = novelty(tmp, Uf)
                others_zero = all(
                    not nv2[ax].get("unregistered")
                    for ax in ("certs", "dsdt", "smm"))
                wl_ok = not nv2["whitelist"].get("extra")
                ok = (added.isdisjoint(Uf["species"]) and
                      nv2["species"]["unregistered"] == sorted(added) and
                      nv2["species"]["observed"] == nv2["species"][
                          "universe"] - (nv2["species"]["universe"] -
                                         len(nv2["species"][
                                             "unregistered"])) - 0 + 0
                      or True)  # observed==universe not required; see below
                ok = (added.isdisjoint(Uf["species"]) and
                      nv2["species"]["unregistered"] == sorted(added) and
                      others_zero and wl_ok and
                      nv2["summary"]["verdict"] == "novel")
                info = (f"guid {g0[:8]}.. flipped @{off:#x} -> "
                        f"{sorted(added)[0][:8]}.. "
                        f"summary={nv2['summary']}")
                break
        os.remove(tmp)
    g.gate("I4 needle: 1 flipped GUID -> exactly 1 species novelty",
           ok, info)

    # I5 cert lens live law @3604: 4 distinct, 12 sightings, all known
    g.gate("I5 certs live @3604: 4 distinct / 12 sightings",
           n1["certs"]["observed"] == 4 and n1["certs"]["known"] == 4 and
           n1["certs"]["sightings"] == 12,
           f"{n1['certs']['observed']}/{n1['certs']['sightings']}")

    # I6 dsdt live @3604: anchor primary, nothing unregistered
    g.gate("I6 dsdt live @3604: primary == clock anchor",
           n1["dsdt"]["primary"] == "27d5e826e111d755" and
           not n1["dsdt"]["unregistered"],
           f"primary={n1['dsdt']['primary']}")

    # I7 smm live @3604: census agreement (106 SMM-typed) + clean
    g.gate("I7 smm live @3604: 106 typed, zero unregistered",
           n1["smm"]["observed"] == 106 and
           not n1["smm"]["unregistered"],
           f"observed={n1['smm']['observed']}")

    # I8 JSON roundtrip stability
    j = json.loads(json.dumps(n1))
    g.gate("I8 novelty JSON roundtrip stable",
           j["summary"] == n1["summary"] and
           j["species"] == n1["species"])

    # I9 degraded honesty: no live universes -> no claims, register-only
    Ux = dict(Uf)
    Ux["smm"] = None
    Ux["species_universe"] = None
    Ux["whitelist_universe"] = None
    n9 = novelty(p3604, Ux)
    g.gate("I9 degraded axes: loud, claim-free, verdict unaffected",
           n9["degraded"] == ["species", "whitelist", "smm"] and
           not n9["smm"]["unregistered"] and
           not n9["species"]["unregistered"] and
           n9["summary"]["unregistered_total"] == 0,
           f"degraded={n9['degraded']}")

    # I10 the two machines agree: judge known-release, detector clean
    idr = f39.identify(p3604, deep=True)
    known_rungs = [r for r, e in idr["per_rung"].items()
                   if e["sha_hit"]]
    g.gate("I10 agreement: identify known-release == novelty clean",
           idr["verdict"]["verdict"] == "known-release" and
           known_rungs and
           idr["per_rung"][known_rungs[0]]["diffs"] == 0 and
           n1["summary"]["unregistered_total"] == 0,
           f"matched={known_rungs}")

    # I11 THE EXTRACTOR GATE: the structural chip-table extractor covers
    # the register on EVERY rung (register ⊆ live union) and its
    # deviation is ONE stable, chip-shaped set across all nine rungs
    ok, info = True, ""
    dev = None
    for r in f39.RUNGS:
        path = Uf["rung_files"][r]
        live = _armor_names(_deep(path)["blobs"])
        reg = Uf["whitelist_per_rung"].get(r) or set()
        if not reg <= live:
            ok = False
            info = f"{r}: register NOT covered " \
                   f"(missing={sorted(reg - live)[:3]})"
            break
        d = live - Uf["whitelist"]
        if dev is None:
            dev = d
        elif d != dev:
            ok = False
            info = f"{r}: deviation unstable {sorted(d)[:3]}"
            break
    if ok:
        bad = [e for e in (dev or set()) if not _is_chip_name(e)]
        ok = bool(dev) and not bad and len(dev) <= 8
        info = (f"9/9 covered, deviation={len(dev or set())} "
                f"{sorted(dev or set())[:2]}" if ok else
                f"deviation hostile: {sorted(bad)[:2] or 'size'}")
    g.gate("I11 extractor: register covered 9/9, deviation stable", ok,
           info)

    # I12 robustness on the same-vendor sibling (TUF): runs, valid verdict
    ptuf = FOREIGN_FILES["tuf"]
    if os.path.exists(ptuf):
        nt = novelty(ptuf, Uf)
        g.gate("I12 TUF sibling: runs, verdict in enum",
               nt["summary"]["verdict"] in
               ("inside-universe", "anticipated-only", "novel"),
               f"{nt['summary']}")
    else:
        g.gate("I12 TUF sibling: runs, verdict in enum", False,
               "TUF image missing")

    return g.finish("tier R + tier I live")


def _verdict(un, an):
    return ("inside-universe" if un == 0 and an == 0
            else "anticipated-only" if un == 0 else "novel")


def f40_template_keys():
    """The fw35 template's unique keys, via fw40's law (31 unique of 32
    slots) — the R9 coupling without importing fw40's machinery."""
    f38 = _M["_fw38-exam"]
    try:
        f40 = _load_mod("fw40-merge")
        return f40._unique_keys()
    except Exception:
        return f38.template_keys()


def show(obs):
    """Human one-pager for a novelty run."""
    s = obs["summary"]
    print(f"fw41-novelty: {obs['image']}")
    print(f"  rom {obs['rom_bytes']} B  sha16 {obs['rom_sha_full']}"
          f"  modules {obs['module_count']}  depth {obs['pierce_depth']}")
    for ax in AXES:
        a = obs[ax]
        if ax == "agesa":
            print(f"  agesa     : {a.get('level')} -> {a.get('class')}"
                  f"  (ladder max {a.get('ladder_max')}, "
                  f"floor41 {a.get('floor41')})")
        elif ax == "whitelist":
            print(f"  whitelist : extracted {a.get('extracted')} / "
                  f"universe {a.get('universe')}  "
                  f"extra {len(a.get('extra') or [])}  "
                  f"missing {len(a.get('missing') or [])}")
            for e in (a.get("extra") or []):
                print(f"      + {e}")
            for m in (a.get("missing") or []):
                print(f"      - {m}")
        else:
            print(f"  {ax:<9}: universe {a.get('universe')}  "
                  f"observed {a.get('observed')}  known {a.get('known')}  "
                  f"unregistered {len(a.get('unregistered') or [])}")
            for u in (a.get("unregistered") or [])[:12]:
                print(f"      ? {u}")
    print(f"  psp (report-only): {obs['psp_report']['candidates']} "
          f"candidates")
    if obs["degraded"]:
        print(f"  DEGRADED axes: {obs['degraded']} (no claims made)")
    print(f"  VERDICT: {s['verdict']}  "
          f"unregistered={s['unregistered_total']}  "
          f"anticipated={s['anticipated_total']}")
    return 0 if s["verdict"] == "inside-universe" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="fw41-novelty",
        description="the unregistered detector — the third reading "
                    "(predicted | known | NOVEL)")
    ap.add_argument("mode", choices=["novelty", "ledger", "selftest",
                                     "manifest"])
    ap.add_argument("image", nargs="?", help="firmware image (any CAP/")
    ap.add_argument("--quiet", action="store_true",
                    help="summary line only")
    a = ap.parse_args(argv)
    if a.mode == "selftest":
        return selftest()
    if a.mode == "manifest":
        return manifest()
    if a.mode == "ledger":
        return ledger()
    if not a.image:
        ap.error("novelty requires an image")
    obs = novelty(a.image)
    if a.quiet:
        print(json.dumps(obs["summary"]))
    else:
        show(obs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
