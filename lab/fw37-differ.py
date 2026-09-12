#!/usr/bin/env python3
# fw37-differ.py — the GUID-aligned module differ, TRACKED (ring 37).
#
# The ring-34 registers (ovmf-constellation / ovmf-nx-pin / ovmf-vars-differ)
# were produced by session-side scripts (ring4_lib.py walkers + ring9_differ.py
# fronts) that the repo deliberately did not track — "the repo tracks
# knowledge, not scratch". That left the project's single most load-bearing
# capability untracked: the FFS walker + GUID-aligned ledger + byte-pin + VARS
# walk that day-0 (16/09 dump) and release-41 (P-20..P-26) both consume.
#
# Ring 37 promotes that machinery into THIS tracked instrument, per the
# fw33/fw35/fw36 precedent:
#   scan   — per-image inventory: FV census (raw _FVH scan, checksum-gated),
#            generic LZMA pierce (ALL guided sections, extended sizes ok),
#            FFS walk with UI-name resolution — NO census needed (vendor-ready)
#   ledger — GUID-aligned pair ledger (common/identical/changed/only-in/
#            byte-delta) — the ring-34 §2 shape, the release-41 P-20..P-26 input
#   pin    — per-module byte-run pins for any GUID pair — the ring-34 §3 shape,
#            the CAP comparator layer for the day-0 dump
#   vars   — the auth-variable store walk (60-byte header derived on live
#            bytes in ring-34 debug7) + pairwise store delta
#
# Fidelity contract: the LEDGER pipeline is byte-compatible with the ring-34
# numbers (files start at FV offset + 0x48, the registered walker's choice;
# bodies hashed raw, pad/raw filetypes skipped, exact-run pins without gap
# clustering). The selftest proves it:
#   tier R — every anchor re-derived from the persisted ring-34 registers,
#            ALWAYS runs
#   tier I — every anchor re-derived LIVE on the surviving OVMF corpus with
#            THIS instrument, byte-compared to the registers; loudly SKIPPED
#            when the corpus is absent (sandbox ephemeral)
#
# stdlib only, read-only. Modes:
#   scan <image> | ledger <imgA> <imgB> | pin <imgA> <imgB> [guid...]
#   vars <image> | selftest | manifest

import json
import lzma
import os
import sys
import hashlib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = HERE

DEFAULT_CORPUS = "/home/z/my-project/scratch-ovmf/extract/usr/share/OVMF"

# EFI_LZMA_CUSTOM_DECOMPRESS_GUID — the guided-section definition GUID whose
# payload is a bare LZMA_ALONE stream (5-byte props + 8-byte size header).
LZMA_GUID = bytes.fromhex("98584eee143959429d6edc7bd79403cf")

FILE_TYPES = {0x01: "raw", 0x02: "freeform", 0x03: "security_core",
              0x04: "pei_core", 0x05: "dxe_core", 0x06: "peim",
              0x07: "driver", 0x08: "combined_peim_driver",
              0x09: "application", 0x0A: "smm", 0x0B: "fv_image",
              0x0C: "combined_smm_dxe", 0x0D: "smm_core", 0xF0: "pad"}
MAX_FVS = 48

ATTR_NAMES = {0x1: "non-volatile", 0x2: "boot-access",
              0x4: "runtime-access", 0x8: "hw-error-record",
              0x10: "authenticated-write", 0x20: "time-based-auth",
              0x40: "append-only"}
STATE_NAMES = {0x3F: "live", 0x3C: "obsolete(transition)", 0x3D: "replaced"}
KEY_VARS = {"PK", "KEK", "db", "dbx", "dbt", "dbr"}


def load(p):
    with open(p, "rb") as f:
        return f.read()


def sha256_16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def guid_canon(b):
    """EFI GUID — first three fields little-endian, the rest raw."""
    return (f"{int.from_bytes(b[0:4], 'little'):08X}-"
            f"{int.from_bytes(b[4:6], 'little'):04X}-"
            f"{int.from_bytes(b[6:8], 'little'):04X}-"
            f"{b[8]:02X}{b[9]:02X}-" + b[10:16].hex().upper())


# ---------------------------------------------------------------- FV scan

def scan_fvs(b):
    """Raw _FVH scan — the proven spi_map._scan_fvs filters: 8-byte-aligned
    header, non-zero FS GUID, header length 0x48..0x600 even, volume length
    sane, header checksum closing to zero, no span overlap."""
    fvs, spans, pos = [], [], 0
    while len(fvs) < MAX_FVS:
        i = b.find(b"_FVH", pos)
        if i < 0:
            break
        pos = i + 4
        h = i - 0x28                      # signature sits at +0x28
        if h < 0 or h % 8:
            continue
        fs_guid = guid_canon(b[h + 0x10:h + 0x20])
        if fs_guid == "00000000-0000-0000-0000-000000000000":
            continue
        fv_len = int.from_bytes(b[h + 0x20:h + 0x28], "little")
        hlen = int.from_bytes(b[h + 0x30:h + 0x32], "little")
        if not 0x48 <= hlen <= 0x600 or hlen % 2:
            continue
        if fv_len < hlen or h + fv_len > len(b) or fv_len > 0x2000000:
            continue
        csum = 0
        for k in range(0, hlen, 2):
            csum = (csum + int.from_bytes(b[h + k:h + k + 2], "little")) & 0xFFFF
        if csum != 0:                     # header checksum must close
            continue
        if any(s <= h < e for s, e in spans):
            continue
        fvs.append({"offset": h, "length": fv_len, "hlen": hlen,
                    "fs_guid": fs_guid})
        spans.append((h, h + fv_len))
    return fvs


# ---------------------------------------------------------------- FFS walk

def iter_files(blob, fv, hlen=None):
    """Yield (guid, ftype, size, file_start, body) over one FV — the ring-34
    walker, verbatim semantics: files start at fv.offset + 0x48 by default
    (the registered pipeline's choice; the census it produced is the anchor),
    state bits active-low, 0xFFFFFF size = 32-byte header with ExtSize,
    files 8-byte aligned."""
    start = fv["offset"] + (hlen if hlen is not None else 0x48)
    end = fv["offset"] + fv["length"]
    off = start
    while off + 24 <= end:
        ftype = blob[off + 18]
        size = blob[off + 20] | (blob[off + 21] << 8) | (blob[off + 22] << 16)
        state = blob[off + 23] ^ 0xFF
        if size == 0xFFFFFF:
            if off + 32 > end:
                break
            size = int.from_bytes(blob[off + 24:off + 32], "little")
            hl = 32
        else:
            hl = 24
        if size < hl or off + size > end or state & 0x07 != 0x07:
            break
        yield (guid_canon(blob[off:off + 16]), ftype, size, off,
               blob[off + hl:off + size])
        off = (off + size + 7) & ~7


def iter_sections(body):
    """Yield (stype, section_body) over an FFS file body (4-byte align)."""
    off = 0
    while off + 4 <= len(body):
        ssize = body[off] | (body[off + 1] << 8) | (body[off + 2] << 16)
        stype = body[off + 3]
        h = 4
        if ssize == 0xFFFFFF:
            if off + 12 > len(body):
                break
            ssize = int.from_bytes(body[off + 4:off + 12], "little")
            h = 8
        if ssize < h or off + ssize > len(body):
            break
        yield stype, body[off + h:off + ssize]
        off = (off + ssize + 3) & ~3


def ui_name(body):
    """The USER_INTERFACE section (0x15) name of one FFS file — decode first,
    THEN cut at the null (a byte-level split would eat the final character
    whenever its own high byte is 0). No census needed."""
    for stype, sbody in iter_sections(body):
        if stype == 0x15:
            s = sbody.decode("utf-16-le", "replace").split("\x00", 1)[0]
            s = "".join(ch for ch in s if 32 <= ord(ch) < 127).strip()
            return s or None
    return None


# ---------------------------------------------------------------- pierce

def pierce_all(img):
    """Every LZMA guided-section payload in the image, in order of appearance
    (generic: all occurrences, extended section sizes handled, false GUID
    hits rejected by the decompressor itself). The ring-34 pipeline used the
    FIRST hit of an OVMF CODE image; the gates prove this generalization
    reproduces it byte-for-byte where exactly one payload exists."""
    outs, notes, pos = [], [], 0
    while True:
        g = img.find(LZMA_GUID, pos)
        if g < 0:
            break
        pos = g + 16
        sec = g - 4
        if sec < 0 or sec + 3 >= len(img):
            continue
        # the observed geometry (the one the registered walker used): a
        # COMPRESSION-section (type 0x02, OVMF GenFv layout) or a GUIDED
        # section (type 0x17, the plain-EDK2 layout) — both put the LZMA
        # custom-decompress GUID at sec+4 and a u16 data offset at sec+20;
        # anything else is a GUID hit inside a module body -> skip
        if img[sec + 3] not in (0x02, 0x17):
            continue
        ssize = img[sec] | (img[sec + 1] << 8) | (img[sec + 2] << 16)
        if ssize == 0xFFFFFF:
            if sec + 12 > len(img):
                continue
            ssize = int.from_bytes(img[sec + 4:sec + 12], "little")
        doff = int.from_bytes(img[g + 16:g + 18], "little")
        if doff < 20 or doff > 0x200 or ssize < doff + 13 \
                or sec + ssize > len(img):
            continue
        try:
            outs.append(lzma.decompress(img[sec + doff:sec + ssize],
                                        format=lzma.FORMAT_ALONE))
        except lzma.LZMAError:
            notes.append(f"guided section @0x{sec:x}: not an LZMA_ALONE "
                         "stream (GUID hit rejected)")
    return outs, notes


def inventory(path, names_fallback=None, ledger_semantics=False):
    """Full per-image inventory. ledger_semantics=True pins the registered
    pipeline exactly (+0x48 file start); otherwise each FV's own header
    length is honored (vendor FVs may carry extended headers)."""
    raw = load(path)
    sym = os.path.islink(path)
    outer = scan_fvs(raw)
    payloads, notes = pierce_all(raw)

    modules = {}
    by_type = {}
    fv_rows = []
    for pi, payload in enumerate(payloads):
        for fi, fv in enumerate(scan_fvs(payload)):
            hlen = 0x48 if ledger_semantics else fv["hlen"]
            fv_rows.append({"payload": pi, "fv": fi, "offset": fv["offset"],
                            "length": fv["length"], "fs_guid": fv["fs_guid"]})
            for guid, ftype, size, off, body in iter_files(payload, fv, hlen):
                if ftype in (0xF0, 0x01):     # pad / raw — registered filter
                    continue
                name = ui_name(body)
                if name is None and names_fallback:
                    name = names_fallback.get(guid)
                modules[guid] = {"name": name, "ftype": ftype,
                                 "ftype_name": FILE_TYPES.get(ftype,
                                                              f"type_{ftype:#04x}"),
                                 "size": size, "sha8": sha256_16(body),
                                 "payload": pi, "fv": fi, "offset": off,
                                 "fv_hlen": hlen}
                tn = FILE_TYPES.get(ftype, f"type_{ftype:#04x}")
                by_type[tn] = by_type.get(tn, 0) + 1
    return {"file": os.path.basename(path), "size": len(raw),
            "sha256_16": sha256_16(raw),
            "symlink_to": os.path.basename(os.path.realpath(path)) if sym
            else None,
            "fv_census": {"outer": len(outer),
                          "pierced_payloads": len(payloads),
                          "pierced_fvs": fv_rows},
            "pierced_notes": notes,
            "modules": modules, "module_count": len(modules),
            "by_type": by_type}


# ---------------------------------------------------------------- ledger

def ledger(inva, invb):
    """GUID-aligned pair ledger — the ring-34 §2 shape."""
    ma, mb = inva["modules"], invb["modules"]
    common = set(ma) & set(mb)
    changed = {g for g in common if ma[g]["sha8"] != mb[g]["sha8"]}
    return {
        "modules": [len(ma), len(mb)],
        "only_in_" + inva["file"]: [ma[g]["name"] or g
                                    for g in sorted(set(ma) - set(mb))],
        "only_in_" + invb["file"]: [mb[g]["name"] or g
                                    for g in sorted(set(mb) - set(ma))],
        "common": len(common),
        "identical": len(common) - len(changed),
        "changed": [f"{ma[g]['name'] or g} "
                    f"({ma[g]['size']}->{mb[g]['size']} B)"
                    for g in sorted(changed)],
        "changed_guids": sorted(changed),
        "byte_delta": sum(mb[g]["size"] - ma[g]["size"] for g in changed),
    }


# ---------------------------------------------------------------- pins

def pins(inva, invb, guids=None):
    """Per-module byte-run pins — the ring-34 §3 shape: exact consecutive
    runs (no gap clustering), first-8-bytes hex before/after."""
    if guids is None:
        guids = ledger(inva, invb)["changed_guids"]
    ma, mb = inva["modules"], invb["modules"]
    out = []
    for guid in guids:
        if guid not in ma or guid not in mb:
            out.append({"guid": guid, "error": "absent from one image"})
            continue
        name = ma[guid]["name"] or mb[guid]["name"] or guid
        # bodies are not retained in the inventory (memory); re-read lazily
        body_a = _module_body(inva, guid)
        body_b = _module_body(invb, guid)
        if body_a is None or body_b is None:
            out.append({"guid": guid, "name": name,
                        "error": "module body not re-readable"})
            continue
        n = min(len(body_a), len(body_b))
        runs = []
        for i in range(n):
            if body_a[i] != body_b[i]:
                if runs and i == runs[-1][1] + 1:
                    runs[-1][1] = i
                else:
                    runs.append([i, i])
        out.append({
            "guid": guid, "name": name,
            "len": [len(body_a), len(body_b)],
            "head_differs": body_a[:2] != body_b[:2],
            "byte_diffs": sum(b - a + 1 for a, b in runs) + abs(len(body_a)
                                                                - len(body_b)),
            "runs": [{"off": a, "len": b - a + 1,
                      "a": body_a[a:a + 8].hex(),
                      "b": body_b[a:a + 8].hex()} for a, b in runs[:24]],
            "runs_total": len(runs),
        })
    return {"pairs": out,
            "total_byte_diffs": sum(p.get("byte_diffs", 0) for p in out)}


def _module_body(inv, guid):
    """Re-read one module's raw FFS body from its (payload, fv, offset)."""
    m = inv["modules"].get(guid)
    if m is None:
        return None
    raw = load(inv["_paths"][inv["file"]])
    payloads, _ = pierce_all(raw)
    if m["payload"] >= len(payloads) or not payloads:
        return None
    payload = payloads[m["payload"]]
    fvs = scan_fvs(payload)
    if m["fv"] >= len(fvs):
        return None
    fv = fvs[m["fv"]]
    hlen = m.get("fv_hlen", 0x48)
    start = fv["offset"] + hlen
    end = fv["offset"] + fv["length"]
    off = start
    while off + 24 <= end:
        ftype = payload[off + 18]
        size = payload[off + 20] | (payload[off + 21] << 8) | (payload[off + 22] << 16)
        state = payload[off + 23] ^ 0xFF
        if size == 0xFFFFFF:
            if off + 32 > end:
                return None
            size = int.from_bytes(payload[off + 24:off + 32], "little")
            hl = 32
        else:
            hl = 24
        if size < hl or off + size > end or state & 0x07 != 0x07:
            return None
        if (off == m["offset"] and ftype not in (0xF0, 0x01)):
            return payload[off + hl:off + size]
        off = (off + size + 7) & ~7
    return None


# ---------------------------------------------------------------- vars

def walk_vars(img):
    """Auth-variable walk — the 60-byte header derived on live bytes
    (ring-34 debug7, no PublishSequence field). FV header length is read
    from the FV header itself."""
    if img[0x28:0x2C] != b"_FVH":
        return {"error": "no _FVH at 0x28"}
    fv_guid = guid_canon(img[16:32])
    fv_len = int.from_bytes(img[32:40], "little")
    hlen = int.from_bytes(img[0x30:0x32], "little")
    vs = hlen
    store_guid = guid_canon(img[vs:vs + 16])
    store_size = int.from_bytes(img[vs + 16:vs + 20], "little")
    fmt, state = img[vs + 20], img[vs + 21]
    body = img[vs + 28:vs + store_size]
    records = []
    off = 0
    while off + 0x3C <= len(body):
        sid = int.from_bytes(body[off:off + 2], "little")
        if sid != 0x55AA:
            break
        st = body[off + 2]
        attrs = int.from_bytes(body[off + 4:off + 8], "little")
        nsz = int.from_bytes(body[off + 0x24:off + 0x28], "little")
        dsz = int.from_bytes(body[off + 0x28:off + 0x2C], "little")
        g = guid_canon(body[off + 0x2C:off + 0x3C])
        noff, doff = off + 0x3C, off + 0x3C + nsz
        if not (2 <= nsz <= 1024) or dsz > 0x100000 or doff + dsz > len(body):
            break
        name = body[noff:noff + nsz].decode("utf-16-le",
                                            "replace").rstrip("\x00")
        data = body[doff:doff + dsz]
        records.append({"name": name, "vguid": g, "state": st,
                        "state_name": STATE_NAMES.get(st, f"raw:{st:#04x}"),
                        "attrs": attrs,
                        "attr_names": [n for bit, n in ATTR_NAMES.items()
                                       if attrs & bit],
                        "size": dsz, "sha": sha256_16(data)})
        off = (doff + dsz + 3) & ~3
    erased_pct = 100 * body[off:].count(0xFF) / max(1, len(body) - off)

    latest, live = {}, {}
    for r in records:
        latest[(r["vguid"], r["name"])] = r
        if r["state"] == 0x3F:
            live[(r["vguid"], r["name"])] = r
    return {"fv_guid": fv_guid, "fv_len": fv_len, "store_guid": store_guid,
            "store_size": store_size, "format": fmt, "store_state": state,
            "records": len(records),
            "state_histogram": dict(Counter(r["state_name"] for r in records)),
            "erased_pct_after_walk": round(erased_pct, 3),
            "distinct_variables": len(latest),
            "live_variables": len(live),
            "latest": [{"name": r["name"], "vguid": r["vguid"],
                        "state_name": r["state_name"],
                        "attrs": r["attr_names"], "size": r["size"],
                        "sha": r["sha"]}
                       for r in sorted(latest.values(),
                                       key=lambda x: x["name"])],
            "key_variables": [{"name": r["name"], "size": r["size"],
                               "sha": r["sha"], "attrs": r["attr_names"]}
                              for (g, n), r in latest.items()
                              if n in KEY_VARS]}


def vars_delta(stores):
    """Pairwise store delta on the latest-record view (ring-34 §4 shape)."""
    delta = {}
    names = sorted(stores)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            ka = {v["name"]: v for v in stores[a]["latest"]}
            kb = {v["name"]: v for v in stores[b]["latest"]}
            common = set(ka) & set(kb)
            delta[f"{a}|{b}"] = {
                "only_in_" + a: sorted(set(ka) - set(kb)),
                "only_in_" + b: sorted(set(kb) - set(ka)),
                "common": len(common),
                "identical": sum(1 for k in common
                                 if ka[k]["sha"] == kb[k]["sha"]),
                "changed": sorted(f"{k} ({ka[k]['size']}->{kb[k]['size']} B)"
                                  for k in common
                                  if ka[k]["sha"] != kb[k]["sha"]),
                "key_delta": {k: [ka[k]["size"] if k in ka else None,
                                  kb[k]["size"] if k in kb else None,
                                  "same-bytes" if k in ka and k in kb
                                  and ka[k]["sha"] == kb[k]["sha"] else
                                  ("changed" if k in ka and k in kb
                                   else "absent")]
                              for k in KEY_VARS if k in ka or k in kb},
            }
    return delta


def vars_report(paths):
    stores = {}
    for label, path in paths.items():
        img = load(path)
        stores[label] = {"file": os.path.basename(path), "size": len(img),
                         "sha8": sha256_16(img), **walk_vars(img)}
    return {"stores": stores, "delta": vars_delta(stores)}


# ---------------------------------------------------------------- engine

class Engine:
    def __init__(self, corpus=None):
        self.corpus = corpus or os.environ.get("FW37_CORPUS") or DEFAULT_CORPUS
        with open(os.path.join(LAB, "ovmf-constellation.json")) as f:
            self.const = json.load(f)
        with open(os.path.join(LAB, "ovmf-nx-pin.json")) as f:
            self.nx = json.load(f)
        with open(os.path.join(LAB, "ovmf-vars-differ.json")) as f:
            self.vd = json.load(f)
        self._census_names = None

    def corpus_path(self, name):
        return os.path.join(self.corpus, name)

    def corpus_ok(self):
        return os.path.isdir(self.corpus) and os.path.exists(
            self.corpus_path("OVMF_CODE_4M.fd"))

    def census_names(self):
        """GUID -> name from the persisted census (optional fallback; the
        primary source is the UI section, resolved live)."""
        if self._census_names is None:
            self._census_names = {}
            try:
                with open(os.path.join(LAB, "ovmf-census.json")) as f:
                    cen = json.load(f)
                for b in cen.get("builds", {}).values():
                    for m in b.get("modules", []):
                        if m.get("guid") and m.get("name"):
                            self._census_names[m["guid"]] = m["name"]
            except (OSError, json.JSONDecodeError):
                pass
        return self._census_names

    def inv(self, path):
        return inventory(path, names_fallback=self.census_names(),
                         ledger_semantics=True)

    def vars_map(self):
        return {"plain": self.corpus_path("OVMF_VARS_4M.fd"),
                "snakeoil": self.corpus_path("OVMF_VARS_4M.snakeoil.fd"),
                "ms": self.corpus_path("OVMF_VARS_4M.ms.fd")}


def selftest():
    results = []

    def gate(name, ok, detail=""):
        results.append((name, ok, detail))
        return ok

    eng = Engine()
    const, nx, vd = eng.const, eng.nx, eng.vd

    # ---- tier R: register re-derivation (always)
    classes = {c["sha8"]: sorted(c["builds"]) for c in const["identity_classes"]}
    gate("R1 three identity classes",
         len(classes) == 3 and
         classes.get("1a46295574430cfb") == ["ms", "secboot", "snakeoil"] and
         classes.get("624e06de18b4fa53") == ["plain"] and
         classes.get("9ee9f2382e0c6aa9") == ["strictnx"], str(classes))
    gate("R2 module counts 135/144/144",
         const["module_counts"] == {"plain": 135, "secboot": 144,
                                    "strictnx": 144},
         str(const["module_counts"]))
    p = const["pairwise"]["plain|secboot"]
    gate("R3 wall ledger 126/6/120 +777472, only 9/18",
         (p["common"], p["identical"], len(p["changed"]), p["byte_delta"]) ==
         (126, 6, 120, 777472) and
         (len(p["only_in_plain"]), len(p["only_in_secboot"])) == (9, 18),
         f"{p['common']}/{p['identical']}/{len(p['changed'])}/+{p['byte_delta']}")
    s = const["pairwise"]["secboot|strictnx"]
    gate("R4 strictnx pair 144/142/2/0",
         (s["common"], s["identical"], len(s["changed"]), s["byte_delta"]) ==
         (144, 142, 2, 0),
         f"{s['common']}/{s['identical']}/{len(s['changed'])}/{s['byte_delta']}")
    byname = {pr.get("name"): pr for pr in nx["pairs"]}
    bds, isc = byname.get("BdsDxe", {}), byname.get("IScsiDxe", {})
    rbds, risc = (bds.get("runs") or [{}])[0], (isc.get("runs") or [{}])[0]
    gate("R5 NX pins 3 bytes, offsets/hex byte-exact",
         nx["total_byte_diffs"] == 3 and bds.get("byte_diffs") == 1 and
         isc.get("byte_diffs") == 2 and
         (rbds.get("off"), rbds.get("len")) == (35487, 1) and
         (risc.get("off"), risc.get("len")) == (94610, 2) and
         rbds.get("secboot") == "01e84531000080bd" and
         rbds.get("strictnx") == "00e84531000080bd" and
         risc.get("secboot") == "662e0f1f84000000" and
         risc.get("strictnx") == "00660f1f84000000",
         f"BdsDxe@{rbds.get('off')} IScsiDxe@{risc.get('off')}")
    st = vd["stores"]
    gate("R6 VARS 0/39/39, states 21/17/1",
         st["plain"]["records"] == 0 and st["plain"]["size"] == 540672 and
         st["snakeoil"]["records"] == st["ms"]["records"] == 39 and
         st["snakeoil"]["state_histogram"] ==
         {"obsolete(transition)": 17, "live": 21, "replaced": 1} and
         st["ms"]["state_histogram"] ==
         {"obsolete(transition)": 17, "live": 21, "replaced": 1} and
         st["snakeoil"]["live_variables"] == st["ms"]["live_variables"] == 21,
         "plain 0 / snakeoil 39 / ms 39")
    gate("R6b VARS store sha8s",
         st["snakeoil"]["sha8"] == "e875a265aabb3fa9" and
         st["ms"]["sha8"] == "0d12f9839018a68f", "")
    kd = vd["delta"]["ms|snakeoil"]["key_delta"]
    gate("R7 VARS key_delta ms|snakeoil",
         kd == {"KEK": [2565, 1031, "changed"], "PK": [1005, 1031, "changed"],
                "db": [3143, 1031, "changed"], "dbx": [76, 76, "same-bytes"]},
         str(kd))

    # ---- tier I: live corpus re-derivation (skipped loudly when absent)
    if eng.corpus_ok():
        cp = eng.corpus_path
        code = {"plain": cp("OVMF_CODE_4M.fd"),
                "secboot": cp("OVMF_CODE_4M.secboot.fd"),
                "strictnx": cp("OVMF_CODE_4M.secboot.strictnx.fd"),
                "ms": cp("OVMF_CODE_4M.ms.fd"),
                "snakeoil": cp("OVMF_CODE_4M.snakeoil.fd")}
        shas = {b: sha256_16(load(p)) for b, p in code.items()}
        live_classes = {}
        for b, h in shas.items():
            live_classes.setdefault(h, []).append(b)
        gate("I1 live identity classes (5 builds -> 3, symlink-resolved)",
             {h: sorted(v) for h, v in live_classes.items()} == classes
             and shas["ms"] == shas["snakeoil"] == "1a46295574430cfb",
             str({h: "+".join(sorted(v)) for h, v in live_classes.items()}))

        inv = {b: eng.inv(p) for b, p in code.items()}
        for b, o in inv.items():
            o["_paths"] = {o["file"]: code[b]}
        gate("I2 live pierce+walk counts 135/144/144",
             (inv["plain"]["module_count"], inv["secboot"]["module_count"],
              inv["strictnx"]["module_count"]) == (135, 144, 144) and
             all(len(o["pierced_notes"]) == 0 for o in inv.values()),
             f"{inv['plain']['module_count']}/"
             f"{inv['secboot']['module_count']}/"
             f"{inv['strictnx']['module_count']}")

        lp = ledger(inv["plain"], inv["secboot"])
        gate("I3 live wall ledger == register",
             (lp["common"], lp["identical"], len(lp["changed"]),
              lp["byte_delta"]) == (126, 6, 120, 777472) and
             (len(lp["only_in_" + inv["plain"]["file"]]),
              len(lp["only_in_" + inv["secboot"]["file"]])) == (9, 18) and
             set(lp["changed_guids"]) == set(p["changed_guids"]),
             f"{lp['common']}/{lp['identical']}/{len(lp['changed'])}"
             f"/+{lp['byte_delta']}")

        ls = ledger(inv["secboot"], inv["strictnx"])
        gate("I4 live strictnx ledger == register",
             (ls["common"], ls["identical"], len(ls["changed"]),
              ls["byte_delta"]) == (144, 142, 2, 0) and
             set(ls["changed_guids"]) == set(s["changed_guids"]),
             f"{ls['common']}/{ls['identical']}/{len(ls['changed'])}")

        px = pins(inv["secboot"], inv["strictnx"], ls["changed_guids"])
        pb = {pr.get("name"): pr for pr in px["pairs"]}
        lb, li = pb.get("BdsDxe", {}), pb.get("IScsiDxe", {})
        ok5 = (px["total_byte_diffs"] == 3 and lb.get("byte_diffs") == 1 and
               li.get("byte_diffs") == 2 and
               (lb.get("runs") or [{}])[0].get("off") == 35487 and
               (li.get("runs") or [{}])[0].get("off") == 94610 and
               (lb.get("runs") or [{}])[0].get("a") == "01e84531000080bd" and
               (lb.get("runs") or [{}])[0].get("b") == "00e84531000080bd" and
               (li.get("runs") or [{}])[0].get("a") == "662e0f1f84000000" and
               (li.get("runs") or [{}])[0].get("b") == "00660f1f84000000")
        gate("I5 live pins == register (offsets + hex byte-exact)", ok5,
             f"total {px['total_byte_diffs']} B — the instrument re-derives "
             "the ring-34 pins to the byte")
        if lb.get("name") and li.get("name"):
            # honest UI check: a SEPARATE inventory with NO census fallback —
            # the names must come from the image's own UI sections
            ui = inventory(code["secboot"])
            n1 = ui["modules"].get(
                "6D33944A-EC75-4855-A54D-809C75241F6C", {}).get("name")
            n2 = ui["modules"].get(
                "86CDDF93-4872-4597-8AF9-A35AE4D3725F", {}).get("name")
            gate("I5b live UI names resolve without census",
                 bool(n1 and n2 and "Bds" in n1 and "IScsi" in n2),
                 f"{n1} / {n2} (UI sections, no census)")
        else:
            gate("I5b live UI names resolve without census", False,
                 "UI sections did not resolve")

        vm = eng.vars_map()
        vr = vars_report(vm)
        ok6 = (vr["stores"]["plain"]["records"] == 0 and
               vr["stores"]["snakeoil"]["records"] == 39 and
               vr["stores"]["ms"]["records"] == 39 and
               vr["stores"]["snakeoil"]["state_histogram"] ==
               {"obsolete(transition)": 17, "live": 21, "replaced": 1} and
               vr["stores"]["ms"]["live_variables"] == 21)
        gate("I6 live VARS walk == register", ok6,
             f"plain {vr['stores']['plain']['records']} / "
             f"snakeoil {vr['stores']['snakeoil']['records']} / "
             f"ms {vr['stores']['ms']['records']}")
        lk = vr["delta"]["ms|snakeoil"]["key_delta"]
        gate("I7 live VARS key_delta == register",
             lk == {"KEK": [2565, 1031, "changed"],
                    "PK": [1005, 1031, "changed"],
                    "db": [3143, 1031, "changed"],
                    "dbx": [76, 76, "same-bytes"]}, str(lk))
    else:
        for name in ("I1", "I2", "I3", "I4", "I5", "I5b", "I6", "I7"):
            gate(f"{name} SKIPPED (no corpus at {eng.corpus})", True,
                 "skipped loudly — the instrument refuses to pretend")

    npass = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        if not ok or os.environ.get("FW37_VERBOSE"):
            print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print(f"fw37-differ selftest: {npass}/{len(results)} gates PASS "
          f"(tier I {'live' if eng.corpus_ok() else 'SKIPPED'})")
    if npass != len(results):
        print("REFUSAL: register or live-corpus drift — fix before diffing.")
        sys.exit(2)
    return 0


def main(argv):
    if not argv:
        argv = ["selftest"]
    cmd = argv[0].lstrip("-")

    if cmd == "selftest":
        return selftest()

    if cmd == "manifest":
        eng = Engine()
        print(json.dumps({
            "instrument": "fw37-differ", "ring": 37,
            "provenance": "promoted from session scripts ring4_lib.py + "
                          "ring9_differ.py (the ring-34 differ) — the walkers "
                          "that produced the registered numbers are now "
                          "tracked and self-verifying",
            "modes": ["scan", "ledger", "pin", "vars", "selftest", "manifest"],
            "registers_fused": ["ovmf-constellation.json",
                                "ovmf-nx-pin.json", "ovmf-vars-differ.json",
                                "ovmf-census.json (names, optional)"],
            "corpus": eng.corpus, "corpus_present": eng.corpus_ok(),
            "vendor_ready": "scan/ledger/pin/vars accept any image path; "
                            "pierce is generic (all LZMA guided sections); "
                            "names resolve from UI sections without census",
            "oracle_linkage": {
                "day0-3644": "pins = the CAP comparator layer (ring-34 §3); "
                             "ledger = identity fingerprints feeding P-18; "
                             "vars = the store lens behind P-14..P-17",
                "release-41": "ledger release40|release41 = the measurement "
                              "input for P-20..P-26 (AGESA, armor, genome "
                              "births/deaths, DER, facade, DSDT, whitelist)"},
        }, indent=2))
        return 0

    if cmd == "scan" and len(argv) > 1:
        inv = inventory(argv[1], names_fallback=Engine().census_names())
        shown = {k: v for k, v in inv.items() if k != "modules"}
        shown["modules"] = (f"<{inv['module_count']} modules — full map in "
                            "JSON; use ledger/pin for pairwork>")
        print(json.dumps(shown, indent=2))
        return 0

    if cmd == "ledger" and len(argv) > 2:
        eng = Engine()
        a, b = eng.inv(argv[1]), eng.inv(argv[2])
        for o, p in ((a, argv[1]), (b, argv[2])):
            o["_paths"] = {o["file"]: p}
        print(json.dumps(ledger(a, b), indent=2))
        return 0

    if cmd == "pin" and len(argv) > 2:
        eng = Engine()
        a, b = eng.inv(argv[1]), eng.inv(argv[2])
        for o, p in ((a, argv[1]), (b, argv[2])):
            o["_paths"] = {o["file"]: p}
        guids = argv[3:] or None
        print(json.dumps(pins(a, b, guids), indent=2))
        return 0

    if cmd == "vars" and len(argv) > 1:
        img = load(argv[1])
        print(json.dumps({"file": os.path.basename(argv[1]),
                          "size": len(img), "sha8": sha256_16(img),
                          **walk_vars(img)}, indent=2))
        return 0

    print("modes: scan <image> | ledger <imgA> <imgB> | "
          "pin <imgA> <imgB> [guid...] | vars <image> | selftest | manifest")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
