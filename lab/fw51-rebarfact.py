#!/usr/bin/env python3
"""fw51-rebarfact — the factory law of the ReBAR chain: what the vendor
actually SHIPS, where the Auto heuristic starts.

Ring 49 measured the ReBAR AXIS (the option, its SUPPRESS_IF/GRAY_OUT
wrappers, the pair law); ring 50 measured the LANGUAGE (the labels: the
option says {0x00: Disabled, 0x01: Auto}, no Enabled — the founder's
"c'est en auto" byte-true, and the Auto heuristic is the ONLY path).
Ring 51 measures the FACTORY LAW: the two independent sources that say
what a shipped board holds before anyone touches it —

  SOURCE N (NVRAM): the AMI NVAR store's StdDefaults variable (GUID
    4599D26F-1A11-49B8-B91F-858745CFF824) carries a NESTED NVAR store
    whose inner "Setup" variable (GUID EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9,
    515 B on the WIFI II) IS the factory canon — byte-addressable at the
    very voffs the name table gave rings 49/50. The ring-14 grammar reads
    it verbatim; the B550 acquisitions had never been parsed before this
    ring (ring 14's specimens were the six B450 boards).
  SOURCE I (IFR): the Setup module's own constructs — the ONE_OF option
    flags (EFI_IFR_FLAG_DEFAULT 0x10) and the DEFAULT statements (op
    0x5B, the "ami value ops" ring 49 kept raw) — the form-side claim of
    what the defaults are.

The cross of the two sources over the five gates (MmioAddrLimit,
Above4gDecode, ResizeBarSupport, SriovSupport, CsmSupport) is THE factory
law — and the founder's symptom court: if the factory canon says Auto and
the IFR defaults say Disabled, the shipped NVRAM outranks the form (the
AMI factory law, byte-proven); if the canon says Disabled, the founder's
board carries NVRAM drift and "c'est en auto" is a written state, not the
factory state. Either verdict is decisive for "il détecte mal alors que
c'est en auto", and the 16/09 dump inherits a five-gate byte court.

MODES
  fact <image>        both sources for one acquisition + the cross
  pair <old> <new>    the factory pair law (blob identity, diff spans,
                      gate-byte equality)
  null450 <image>     the generational null: the same factory read on a
                      B450 acquisition (board-relative name-table voffs;
                      unreliable 0x0 metas reported, never claimed)
  day0                the pre-registered dump card: five-gate byte court
                      + live-minus-factory protocol (ring-14 delta) +
                      the failure lexicon
  selftest            two-tier gates (R: laws + synthetic KATs,
                      I: live corpus + crown bridge)
  manifest            the ring's tracked surface

LAWS
  L1 BYTES-OVER-GUESSES  a default is claimed only from measured bytes
                         (NVRAM canon or a resolved IFR construct);
                         unresolved ops stay raw, never invented.
  L2 ANCHORS-BEFORE-MARKS  every store/entry/voff/qid/tok is extracted
                         live; the five gates must reproduce the ring-49
                         crown (and the stores the probe-measured shape)
                         or the instrument refuses loud.
  L3 ZERO WRITES         this instrument reads; the crown register is
                         written once by scripts/ring51_register.py.
  L4 COMPOSE-ON-FROZEN   fw49 imported (and through it fw37/fw43), never
                         rewritten; the NVAR grammar is the ring-14
                         walker carried VERBATIM (its /tmp home is
                         volatile, so the copy lives here, pinned by
                         ring-14 KATs and the ring-14 register).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import importlib.util

REPO = os.environ.get("OMARCHY_FW_REPO", "/home/z/my-project/repo-bios")
CORPUS = os.environ.get("OMARCHY_FW_CORPUS", "/tmp/my-project/scratch-vendor")
ACQ = ("b550w2-3644", "b550w2-3645", "b550-nw-3644")

# ---------------------------------------------------------------- imports


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


F49 = _load("f49", os.path.join(REPO, "lab", "fw49-rebar.py"))

# fw49 pulled fw37/fw43 through its own module level; the names stay
# reachable for anchor checks without a second load.
F43 = F49.F43

# ---------------------------------------------------------------- constants

# The five gates. voff/qid/tok are the ring-49 crown values (its
# "questions" rows, including the two rows ring 49 recorded without
# labels); the instrument re-derives all of them live (L2).
GATES = ("MmioAddrLimit", "Above4gDecode", "ResizeBarSupport",
         "SriovSupport", "CsmSupport")
CROWN = {
    "MmioAddrLimit": {"voff": 0x1B6, "qid": 0x310, "tok": 694},
    "Above4gDecode": {"voff": 0x1BA, "qid": 0x20E, "tok": 1281},
    "ResizeBarSupport": {"voff": 0x1BB, "qid": 0x20F, "tok": 1403},
    "SriovSupport": {"voff": 0x1BC, "qid": 0x210, "tok": 1283},
    "CsmSupport": {"voff": 0x1F2, "qid": 0x2900, "tok": 1602},
}
# ring-50 language anchors (the vocabulary the labels resolve through)
LANG_TOKS = {"Enabled": 3, "Disabled": 4, "Auto": 5}
LABEL_OF_VALUE = {
    "Above4gDecode": {0x00: "Disabled", 0x01: "Enabled"},
    "ResizeBarSupport": {0x00: "Disabled", 0x01: "Auto"},
    "SriovSupport": {0x00: "Disabled", 0x01: "Enabled"},
    "CsmSupport": {0x00: "Disabled", 0x01: "Enabled"},
}

SETUP_GUID = "EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9"
STDDEFAULTS_GUID = "4599D26F-1A11-49B8-B91F-858745CFF824"
SYSTEMACCESS_GUID = "E770BB69-BCB4-4D04-9E97-23FF9456FEAC"

# ---------------------------------------------------------------- the
# pre-registration ledger, frozen in the source BEFORE the crown
# measurement. Probes touched STRUCTURE only (store anchors, entry
# inventory, blob sizes, blob identity shas, name-table voffs); the five
# gate-byte VALUES and the IFR default semantics were never read when
# these claims were written.
PRE_REG = {
    "PR-1": {
        "claim": "the factory canon says Auto: StdDefaults Setup"
                 "[0x1BB] (ResizeBarSupport) == 0x01 on b550w2-3644 — "
                 "the founder's board reports 'c'est en auto' without "
                 "intervention",
        "basis": "founder-anchored (ring 49/50: the word, byte-true)",
    },
    "PR-2": {
        "claim": "the factory canon says Enabled: StdDefaults Setup"
                 "[0x1BA] (Above4gDecode) == 0x01 — else the ReBAR "
                 "question would be SUPPRESSED on a factory-fresh "
                 "board and the shipped chain dead-on-arrival",
        "basis": "structure-anchored (SUPPRESS_IF, ring 49)",
    },
    "PR-3": {
        "claim": "the factory canon says CSM off: StdDefaults Setup"
                 "[0x1F2] (CsmSupport) == 0x00 — the vendor help's own "
                 "chain requires it and the B550 generation boots "
                 "UEFI-only",
        "basis": "help-anchored (tok 1404, ring 49)",
    },
    "PR-4": {
        "claim": "the two sources AGREE on every gate: the IFR default "
                 "(resolved under the coherent layout) equals the "
                 "factory NVRAM byte; the informative-miss alternative "
                 "is pre-named — 'the shipped StdDefaults outrank the "
                 "IFR defaults' (the AMI factory law)",
        "basis": "two-source law (this ring's cross)",
    },
    "PR-5": {
        "claim": "release law: the factory StdDefaults blob is "
                 "byte-identical 3644 -> 3645 (sha16 equal, both "
                 "windows), gate bytes included — the cert-only "
                 "release of rings 47-50 cannot move the factory "
                 "canon",
        "basis": "pair law (rings 47/48/49/50 invariance chain)",
    },
    "PR-6": {
        "claim": "board law: the sibling's factory gate bytes equal "
                 "the WIFI II's on all five gates; the measured 1-B "
                 "blob delta (6,823 vs 6,822; Setup 515 vs 514) sits "
                 "OUTSIDE the gate offsets",
        "basis": "pair law (ring 49/50 axis+language invariance "
                 "modulo the grayout qid)",
    },
    "PR-7": {
        "claim": "absence law: SystemAccess (1 B, GUID E770BB69-…) "
                 "ships in NO StdDefaults on any acquisition — the "
                 "grayout gate is factory-open (absence reads as "
                 "unrestricted); measured, not decoded",
        "basis": "structure (ring 50 varstore census + the nested "
                 "store's entry list)",
    },
    "PR-8": {
        "claim": "factory-store shape: each B550 CAP's outer NVAR "
                 "store carries EXACTLY ONE variable (StdDefaults) — "
                 "no live Setup in the factory image; the live "
                 "variables materialize on the board, so the dump's "
                 "outer store will differ and the ring-14 "
                 "live-minus-factory delta lands on this contrast",
        "basis": "probe-measured shape (this ring, structure only)",
    },
    "PR-9": {
        "claim": "generational null: the B450 3604 factory chain "
                 "reads (Above4gDecode == 0x00, ResizeBarSupport == "
                 "0x00) — dead-on-arrival, the generational opposite "
                 "of the B550; CsmSupport on B450 stays UNMEASURED "
                 "(its name-table meta reads 0x0 — reported, never "
                 "claimed)",
        "basis": "the 2022 CSM-era defaults vs the 2026 UEFI-only "
                 "board",
    },
}

# probe-measured store shape (b550w2-3644/3645, b550-nw-3644) — L2 anchors
STORE_ANCHORS = ("0x40078", "0x1040078")   # both SPI windows, 32-MiB images
STDDEF_DATA = {"b550w2-3644": 6823, "b550w2-3645": 6823,
               "b550-nw-3644": 6822}
STDDEF_ENTRIES = 17
STDDEF_SHA = {"b550w2-3644": "c127f5cb3e69cbb5",
              "b550w2-3645": "c127f5cb3e69cbb5",
              "b550-nw-3644": "0f8adf40e172b2c1"}
SETUP_DATA = {"b550w2-3644": 515, "b550w2-3645": 515, "b550-nw-3644": 514}

REFUSALS = []


class Refusal(Exception):
    pass


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


# ---------------------------------------------------------------- NVAR
# grammar: UEFITool new_engine ami_nvar (Kaitai + nvram.h + nvramparser.cpp,
# BSD-2, Nikolaj Schlej / LongSoft), imported VERBATIM from the ring-14
# probe scripts/ring14_nvar.py (fetched 2026-09-11; every rule cites its
# source there). The copy is pinned by the R-tier KATs and by the live
# anchors above; semantics were never re-derived from memory.

# NVRAM_NVAR_STORE_FILE_GUID CEF5B9A3-476D-497F-9FDC-E98143E0422C
NVAR_FILE_GUID_LE = bytes.fromhex("A3B9F5CE6D477F499FDCE98143E0422C")

ATTR_BITS = [(0x01, "runtime"), (0x02, "ascii_name"), (0x04, "local_guid"),
             (0x08, "data_only"), (0x10, "ext_header"),
             (0x20, "hw_error_record"), (0x40, "auth_write"), (0x80, "valid")]
EXT_CHECKSUM, EXT_AUTH_WRITE, EXT_TIME_BASED = 0x01, 0x10, 0x20

PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")


def attrs_text(a: int):
    names = [n for bit, n in ATTR_BITS if a & bit]
    return "+".join(names) if names else f"{a:#04x}"


def guid_str(raw: bytes) -> str:
    d1 = int.from_bytes(raw[0:4], "little")
    d2 = int.from_bytes(raw[4:6], "little")
    d3 = int.from_bytes(raw[6:8], "little")
    return f"{d1:08X}-{d2:04X}-{d3:04X}-{raw[8:10].hex().upper()}-{raw[10:16].hex().upper()}"


def u16(b, o):
    return int.from_bytes(b[o:o + 2], "little")


def parse_entry(blob: bytes, off: int, body_end: int):
    """One NVAR entry, per ksy_ami_nvar.ksy nvar_entry. Returns dict;
    raises ValueError on structural violation."""
    if blob[off] != 0x4E:
        return {"offset": off, "terminator": True,
                "first_bytes": blob[off:off + 8].hex()}
    if blob[off:off + 4] != b"NVAR":
        raise ValueError(f"signature_rest != VAR at {off:#x}")
    size = u16(blob, off + 4)
    if size <= 10:
        raise ValueError(f"size {size} <= 10 at {off:#x}")
    if off + size > body_end:
        raise ValueError(f"entry {off:#x} size {size} crosses body end")
    nxt = int.from_bytes(blob[off + 6:off + 9], "little")
    attrs = blob[off + 9]
    valid = bool(attrs & 0x80)
    data_only = bool(attrs & 0x08)
    local_guid = bool(attrs & 0x04)
    ascii_name = bool(attrs & 0x02)
    ext_flag = bool(attrs & 0x10)

    cur = off + 10
    guid, guid_index, name = None, None, None
    if valid and not data_only:
        if local_guid:
            guid = guid_str(blob[cur:cur + 16])
            cur += 16
        else:
            guid_index = blob[cur]
            cur += 1
        if ascii_name:
            end = blob.find(b"\x00", cur, off + size)
            if end < 0:
                raise ValueError(f"unterminated ascii name at {off:#x}")
            name = blob[cur:end].decode("ascii", "replace")
            cur = end + 1
        else:
            chars = []
            p = cur
            while p + 2 <= off + size:
                ch = u16(blob, p)
                p += 2
                if ch == 0:
                    break
                chars.append(ch)
            else:
                raise ValueError(f"unterminated ucs2 name at {off:#x}")
            name = "".join(chr(c) for c in chars)
            cur = p

    ext_size, ext_attrs, ext_checksum_ok, ext_ts, ext_hash = \
        0, None, None, None, None
    if valid and ext_flag and size > 12:
        field = u16(blob, off + size - 2)
        ext_size = field if field >= 3 else 0
        if ext_size:
            ea = blob[off + size - 2 - ext_size]
            ext_attrs = ea
            if (ea & EXT_TIME_BASED) and ext_size >= 11:
                ext_ts = int.from_bytes(
                    blob[off + size - 2 - ext_size + 1:
                         off + size - 2 - ext_size + 9], "little")
            if (ea & EXT_TIME_BASED) and ext_size >= 43 and not data_only:
                ext_hash = blob[off + size - 2 - ext_size + 9:
                                off + size - 2 - ext_size + 41].hex()
            if (ea & EXT_CHECKSUM) and ext_size >= 4:
                total = (sum(blob[off + 10:off + size]) +
                         sum(u16(blob, off + 4).to_bytes(2, "little")) +
                         attrs) & 0xFF
                ext_checksum_ok = (total == 0)

    data_start = cur
    data_end = off + size - ext_size
    if data_end < data_start:
        raise ValueError(f"negative data region at {off:#x}")
    data = blob[data_start:data_end]

    return {"offset": off, "size": size, "next": nxt,
            "next_hex": hex(nxt), "attrs": attrs,
            "attrs_text": attrs_text(attrs), "valid": valid,
            "data_only": data_only, "guid": guid,
            "guid_index": guid_index, "name": name,
            "ext_size": ext_size, "ext_attrs": ext_attrs,
            "ext_checksum_ok": ext_checksum_ok,
            "ext_timestamp": ext_ts, "ext_hash": ext_hash,
            "data_start": data_start, "data_size": len(data),
            "nested": data[:4] == b"NVAR"}


def resolve_owner(entry, entries_by_off, seen=None):
    """data_only ownership: backward link search, nvramparser.cpp 143-177."""
    seen = seen or set()
    for prev_off in sorted(entries_by_off, reverse=True):
        if prev_off >= entry["offset"] or prev_off in seen:
            continue
        prev = entries_by_off[prev_off]
        if prev.get("terminator"):
            continue
        if prev["next"] != 0xFFFFFF and \
                prev["offset"] + prev["next"] == entry["offset"]:
            if prev["name"] is not None:
                return prev
            seen.add(prev_off)
            return resolve_owner(prev, entries_by_off, seen)
    return None


def walk_store(blob: bytes, region_start: int, region_end: int):
    """Linear walk per ksy seq: repeat until signature_first != 0x4e."""
    entries, errors = [], []
    off = region_start
    while off < region_end:
        try:
            e = parse_entry(blob, off, region_end)
        except ValueError as ex:
            errors.append(f"{ex}")
            break
        if e.get("terminator"):
            entries.append(e)
            break
        entries.append(e)
        off += e["size"]
    return entries, errors


def walk_region(blob: bytes, region_start: int, region_end: int, depth: int):
    """Store-level logic over one region (FFS body or nested data)."""
    if depth > 3:
        return {"depth_cap": True}
    entries, errors = walk_store(blob, region_start, region_end)
    term = next((e for e in entries if e.get("terminator")), None)
    real = [e for e in entries if not e.get("terminator")]
    offs = {e["offset"] for e in real}

    idx_max = max([e["guid_index"] for e in real
                   if e["guid_index"] is not None], default=-1)
    guid_area_n = idx_max + 1
    guid_area = []
    guid_resolved = 0
    if guid_area_n and region_end - 16 * guid_area_n >= region_start:
        for i in range(guid_area_n):
            g = blob[region_end - 16 * (i + 1):region_end - 16 * i]
            guid_area.append(guid_str(g))
        guid_resolved = sum(1 for e in real
                            if e["guid_index"] is not None
                            and e["guid_index"] < guid_area_n)

    links = [e for e in real if e["next"] != 0xFFFFFF]
    resolved = sum(1 for e in links if e["offset"] + e["next"] in offs)
    targets = {e["offset"] + e["next"] for e in links}
    roots = sorted(o for o in offs if o not in targets)

    by_off = {e["offset"]: e for e in real}
    variables, data_only_rec = [], []
    for e in real:
        if e.get("terminator"):
            continue
        data = blob[e["data_start"]:e["data_start"] + e["data_size"]]
        rec = {"offset": hex(e["offset"]), "name": e["name"],
               "guid": e["guid"] or (guid_area[e["guid_index"]]
                                     if e["guid_index"] is not None and
                                     e["guid_index"] < len(guid_area)
                                     else "UNRESOLVED_INDEX"),
               "attrs": e["attrs_text"], "size": e["size"],
               "data_size": e["data_size"],
               "sha256_16": hashlib.sha256(data).hexdigest()[:16]}
        if e["data_only"]:
            owner = resolve_owner(e, by_off)
            rec["owner"] = owner["name"] if owner and owner["name"] else \
                (hex(owner["offset"]) if owner else None)
            data_only_rec.append(rec)
        else:
            pr = PRINTABLE.findall(data[:128])
            if pr:
                rec["head"] = sorted(set(x.decode() for x in pr))[:6]
            variables.append(rec)

    free_uniform = None
    if term:
        pad_start = term["offset"] + 1
        pad_end = region_end - 16 * guid_area_n if guid_area_n else region_end
        if pad_end > pad_start:
            pad = blob[pad_start:pad_end]
            free_uniform = (len(set(pad)) == 1)

    nested_stores = []
    if depth < 3:
        for e in real:
            if e["nested"] and e["data_size"] >= 10:
                inner = walk_region(blob, e["data_start"],
                                    e["data_start"] + e["data_size"],
                                    depth + 1)
                nested_stores.append({
                    "container_offset": hex(e["offset"]),
                    "container_name": e["name"],
                    "region": [hex(e["data_start"]),
                               hex(e["data_start"] + e["data_size"])],
                    "inner": inner})

    store = {"region": [hex(region_start), hex(region_end)],
             "depth": depth,
             "entries_total": len(real),
             "nested_stores": nested_stores,
             "walk_errors": errors,
             "terminator": {"offset": hex(term["offset"]),
                            "first_bytes": term["first_bytes"]} if term
             else None,
             "guid_area": {"count": guid_area_n,
                           "guids": guid_area,
                           "indexed_refs_resolved": guid_resolved},
             "links": {"declared": len(links), "resolved": resolved,
                       "broken": len(links) - resolved},
             "chain_roots": len(roots),
             "free_space_uniform_ff": free_uniform,
             "data_only_entries": data_only_rec,
             "variables": sorted(variables, key=lambda v: v["offset"])}
    return store


def parse_nvar_store(blob: bytes, ffs_off: int):
    """FFS-anchored NVAR store: validate the raw-file header, then
    walk_region over its body."""
    ffs_size = int.from_bytes(blob[ffs_off + 20:ffs_off + 23], "little")
    ffs_type = blob[ffs_off + 18]
    ffs_state = blob[ffs_off + 23]
    body_start = ffs_off + 24
    body_end = min(ffs_off + ffs_size, len(blob))
    if ffs_type != 0x01 or ffs_size < 48 or body_end > len(blob):
        return {"ffs_offset": hex(ffs_off), "verdict":
                f"not a raw FFS file (type={ffs_type:#x} size={ffs_size})"}
    st = walk_region(blob, body_start, body_end, 0)
    st["ffs_offset"] = hex(ffs_off)
    st["ffs_type"] = hex(ffs_type)
    st["ffs_state"] = hex(ffs_state)
    st["ffs_size"] = ffs_size
    return st


def iter_all_variables(store, path=()):
    """Yield (path, variable) across a store and every nested store."""
    if "variables" not in store:
        return
    for v in store["variables"]:
        yield path, v
    for ns in store.get("nested_stores", []):
        yield from iter_all_variables(
            ns["inner"], path + (ns["container_name"],))


# ---------------------------------------------------------------- NVAR
# factory side

def nvar_stores(image_path: str) -> list[dict]:
    """Every NVAR store of one image, ring-14 grammar."""
    blob = open(image_path, "rb").read()
    hits = []
    i = blob.find(NVAR_FILE_GUID_LE)
    while i != -1:
        hits.append(i)
        i = blob.find(NVAR_FILE_GUID_LE, i + 1)
    if not hits:
        raise Refusal("no NVAR FFS anchor in " + image_path)
    stores = []
    for h in hits:
        st = parse_nvar_store(blob, h)
        if "entries_total" not in st:
            raise Refusal(f"NVAR anchor {hex(h)}: {st.get('verdict')}")
        if st["walk_errors"]:
            raise Refusal(f"NVAR store {hex(h)} walk errors: "
                          f"{st['walk_errors']}")
        if st["links"]["broken"]:
            raise Refusal(f"NVAR store {hex(h)}: "
                          f"{st['links']['broken']} broken links")
        stores.append(st)
    return stores


def stddefaults_blob(image_path: str) -> dict:
    """The factory canon: StdDefaults' nested Setup blob (+ census)."""
    stores = nvar_stores(image_path)
    windows = []
    for st in stores:
        outer = st["variables"]
        sd = next((v for v in outer
                   if v["guid"] == STDDEFAULTS_GUID
                   and v["name"] == "StdDefaults"), None)
        if sd is None:
            raise Refusal("no StdDefaults variable in store "
                          + st["ffs_offset"])
        nested = next((ns["inner"] for ns in st["nested_stores"]
                       if ns["container_name"] == "StdDefaults"), None)
        if nested is None:
            raise Refusal("StdDefaults carries no nested store in "
                          + st["ffs_offset"])
        inner_setup = next((v for v in nested["variables"]
                            if v["name"] == "Setup"
                            and v["guid"] == SETUP_GUID), None)
        if inner_setup is None:
            raise Refusal("no inner Setup variable in the nested store")
        blob = open(image_path, "rb").read()
        # the variable's offset is absolute in the image; parse its entry
        # again to slice the data region exactly (variables carry sizes,
        # not bytes)
        off = int(inner_setup["offset"], 16)
        # parse the entry again to slice the data exactly
        e = parse_entry(blob, off, int(nested["region"][1], 16))
        data = blob[e["data_start"]:e["data_start"] + e["data_size"]]
        windows.append({
            "store": st["ffs_offset"],
            "outer_variables": [v["name"] for v in outer],
            "nested_entries": nested["entries_total"],
            "nested_names": [v["name"] for v in nested["variables"]],
            "stddef_data_size": sd["data_size"],
            "stddef_sha16": sd["sha256_16"],
            "setup_data_size": len(data),
            "setup_sha16": sha16(data),
            "setup_bytes": data,
            "inventory": {v["name"]: {"size": v["data_size"],
                                      "sha16": v["sha256_16"],
                                      "guid": v["guid"]}
                          for v in nested["variables"]},
        })
    for w in windows[1:]:
        if w["setup_bytes"] != windows[0]["setup_bytes"]:
            raise Refusal("the SPI windows disagree on the factory Setup "
                          "blob — refusing to pick one")
    system_access = []
    blob = open(image_path, "rb").read()
    for st in stores:
        for path, v in iter_all_variables(st):
            if v["name"] == "SystemAccess":
                system_access.append(path)
    return {"windows": windows, "setup_blob": windows[0]["setup_bytes"],
            "both_windows_identical": True,
            "systemaccess_paths": system_access}


def factory_gate_bytes(image_path: str, voffs: dict[str, int]) -> dict:
    """The five gate bytes out of the factory canon, board-relative."""
    fct = stddefaults_blob(image_path)
    blob = fct["setup_blob"]
    gates = {}
    for nm, voff in voffs.items():
        if nm not in GATES:
            continue
        if voff <= 0 or voff >= len(blob):
            gates[nm] = {"voff": voff, "verdict": "unreliable-voff"}
            continue
        gates[nm] = {"voff": voff, "byte": blob[voff],
                     "hex": f"0x{blob[voff]:02x}"}
    return gates, fct


# ---------------------------------------------------------------- IFR
# form-side defaults

OP_DEFAULT = 0x5B
FLAG_DEFAULT = 0x10


def ifr_gate_constructs(image_path: str,
                        gates: tuple[str, ...] = GATES,
                        crown_check: bool = True) -> dict[str, dict]:
    """The gates' live IFR constructs: options (with flags), raw 0x5B
    ops. L2 (crown_check, B550 scope): every qid/tok/voff must
    reproduce the ring-49 crown. `gates` scopes the demand (the B450
    null claims only what its name table names reliably, under its OWN
    board-relative constructs — no crown comparison)."""
    name, pe = F49.setup_pe(image_path)
    ntf = F49.name_table_fields(image_path)
    voff_map = {v: n for n, v in ntf.items() if n in gates and v > 0}
    found: dict[str, dict] = {}
    for d in F43.direct_forms(pe):
        body = pe[d["offset"] + 4:d["offset"] + d["size"]]
        for q in F49.questions_at(body, voff_map):
            nm = voff_map.get(q["voff"])
            if nm and nm not in found:
                q["body"] = body
                found[nm] = q
    missing = [n for n in gates if n not in found]
    if missing:
        raise Refusal(f"IFR gate questions missing: {missing}")
    out = {}
    for nm, q in found.items():
        if crown_check:
            if q["qid"] != CROWN[nm]["qid"] or q["prompt"] != CROWN[nm]["tok"]:
                raise Refusal(f"L2 {nm}: live qid {q['qid']:#x}/tok "
                              f"{q['prompt']} != crown "
                              f"{CROWN[nm]['qid']:#x}/{CROWN[nm]['tok']}")
            if q["voff"] != CROWN[nm]["voff"]:
                raise Refusal(f"L2 {nm}: live voff {q['voff']:#x} != crown "
                              f"{CROWN[nm]['voff']:#x}")
        opts, vals = F49.one_of_scope(q["body"], q["off"])
        out[nm] = {
            "qid": hex(q["qid"]), "tok": q["prompt"],
            "voff": hex(q["voff"]),
            "options": [{"tok": o["tok"], "flags": o["flags"],
                         "type": o["type"], "value": o["value"]}
                        for o in opts],
            "raw_default_ops": list(vals),
            "flag_default_values": [o["value"] for o in opts
                                    if o["flags"] & FLAG_DEFAULT],
        }
    return out


def parse_default_op(raw_hex: str, layout: str) -> dict | None:
    """One 0x5B-06 op under a candidate layout. 'A' = the standard
    EFI_IFR_DEFAULT (DefaultId u16, Type u8, Value u8); 'B' = the
    value-first alternative. Returns None when the op is too long for
    the layout's u8 tail (longer values are legal IFR, just not u8)."""
    raw = bytes.fromhex(raw_hex)
    if len(raw) < 4:
        return None
    if layout == "A":
        return {"default_id": int.from_bytes(raw[0:2], "little"),
                "type": raw[2], "value": raw[3],
                "value_hex": f"0x{raw[3]:02x}"}
    if layout == "B":
        return {"default_id": int.from_bytes(raw[2:4], "little"),
                "type": raw[1], "value": raw[0],
                "value_hex": f"0x{raw[0]:02x}"}
    return None


def _hex2(v) -> str:
    """Normalize a value to two lowercase hex digits (option values are
    raw-byte hex without the 0x prefix; parsed defaults carry ints)."""
    if isinstance(v, int):
        return f"{v:02x}"
    return v.lower().removeprefix("0x").zfill(2)


def choose_layout(raw_ops: list[str], option_values: list[str]) -> str:
    """The coherent layout, derived — never assumed: a layout is
    coherent for one question when its parsed defaults carry UNIQUE
    default_ids (one default per store per question) and every value is
    one of the question's own option values. Both coherent => ambiguous
    (the honest answer); both incoherent => 'raw-only' (the ops stay
    raw, nothing is claimed)."""
    opt_set = {_hex2(v) for v in option_values}
    verdicts = {}
    for layout in ("A", "B"):
        parsed = [parse_default_op(r, layout) for r in raw_ops]
        parsed = [p for p in parsed if p is not None]
        ids = [p["default_id"] for p in parsed]
        vals = [_hex2(p["value"]) for p in parsed]
        ok = (len(parsed) > 0
              and len(set(ids)) == len(ids)
              and (not opt_set or all(v in opt_set for v in vals)))
        verdicts[layout] = ok
    if verdicts["A"] and not verdicts["B"]:
        return "A"
    if verdicts["B"] and not verdicts["A"]:
        return "B"
    if not verdicts["A"] and not verdicts["B"]:
        return "raw-only"
    return "ambiguous"


def ifr_gate_defaults(image_path: str,
                      gates: tuple[str, ...] = GATES,
                      crown_check: bool = True) -> dict:
    """The form-side default claims, layout resolved per gate."""
    constructs = ifr_gate_constructs(image_path, gates, crown_check)
    out = {}
    for nm, c in constructs.items():
        opt_vals = [o["value"] for o in c["options"]]
        layout = "none"
        defaults = []
        if c["raw_default_ops"]:
            layout = choose_layout(c["raw_default_ops"], opt_vals)
            if layout in ("A", "B"):
                defaults = [parse_default_op(r, layout)
                            for r in c["raw_default_ops"]]
                defaults = [d for d in defaults if d is not None]
        out[nm] = dict(c)
        out[nm]["default_layout"] = layout
        out[nm]["default_statements"] = defaults
    return out


# ---------------------------------------------------------------- modes

def name_table_crownsafe(image_path: str) -> dict[str, int]:
    """The image's own name-table voffs, L2-checked against the crown
    where the crown has the field (the B550 acquisitions)."""
    ntf = F49.name_table_fields(image_path)
    for nm, c in CROWN.items():
        if nm in ntf and ntf[nm] == c["voff"]:
            continue
        if nm in ntf and ntf[nm] != c["voff"]:
            # a board-relative table may legitimately move a field —
            # but the B550 crowns pinned these five; a move is loud.
            raise Refusal(f"L2 name-table {nm}: {ntf[nm]:#x} != crown "
                          f"{c['voff']:#x}")
    return ntf


def fact(acq: str) -> dict:
    """Both sources + the cross, for one acquisition."""
    path = os.path.join(CORPUS, acq + ".rom")
    if not os.path.exists(path):
        raise Refusal(f"{path} missing from the corpus")
    ntf = name_table_crownsafe(path)
    gates, fct = factory_gate_bytes(path, ntf)
    ifr = ifr_gate_defaults(path)
    w = fct["windows"][0]
    cross = {}
    for nm in GATES:
        g, i = gates.get(nm), ifr[nm]
        row = {"gate": nm, "voff": hex(CROWN[nm]["voff"]),
               "factory": g, "ifr_options": i["options"],
               "ifr_layout": i["default_layout"],
               "ifr_defaults": i["default_statements"],
               "ifr_flag_defaults": i["flag_default_values"]}
        if g and "byte" in g and i["default_statements"]:
            ids = {d["default_id"]: d["value"] for d in
                   i["default_statements"]}
            form_default = ids.get(0, ids.get(min(ids)))
            row["ifr_std_default"] = f"0x{form_default:02x}"
            row["verdict"] = ("agree" if form_default == g["byte"]
                              else "diverge-nvram-outranks-ifr")
        elif g and "byte" in g and i["flag_default_values"]:
            row["verdict"] = ("agree" if
                              int(i["flag_default_values"][0], 16)
                              == g["byte"]
                              else "diverge-nvram-outranks-ifr")
        elif g and "byte" in g:
            row["verdict"] = "no-ifr-default"
        else:
            row["verdict"] = "unmeasurable"
        cross[nm] = row
    return {
        "acq": acq,
        "name_table": {k: hex(v) for k, v in sorted(ntf.items(),
                                                    key=lambda kv: kv[1])},
        "stores": [w0["store"] for w0 in fct["windows"]],
        "both_windows_identical": fct["both_windows_identical"],
        "outer_variables": w["outer_variables"],
        "nested_entries": w["nested_entries"],
        "nested_names": w["nested_names"],
        "stddef": {"data_size": w["stddef_data_size"],
                   "sha16": w["stddef_sha16"]},
        "setup_blob": {"data_size": w["setup_data_size"],
                       "sha16": w["setup_sha16"]},
        "systemaccess_paths": fct["systemaccess_paths"],
        "inventory": w["inventory"],
        "gates": cross,
    }


def diff_spans(a: bytes, b: bytes) -> list[list[int]]:
    """Inclusive byte spans where two blobs differ (common prefix/suffix
    trimmed); returns [] when equal."""
    if a == b:
        return []
    n = min(len(a), len(b))
    lo = next((i for i in range(n) if a[i] != b[i]), n)
    hi = next((i for i in range(1, n - lo + 1)
               if a[len(a) - i] != b[len(b) - i]), 0)
    return [[lo, max(len(a), len(b)) - hi - 1]]


def pair(old: str, new: str) -> dict:
    """The factory pair law: blob identity, diff spans, gate bytes."""
    fo = fact(old)
    fn = fact(new)
    so, sn = fo["setup_blob"], fn["setup_blob"]
    blob_o = stddefaults_blob(os.path.join(CORPUS, old + ".rom"))["setup_blob"]
    blob_n = stddefaults_blob(os.path.join(CORPUS, new + ".rom"))["setup_blob"]
    spans = diff_spans(blob_o, blob_n)
    gate_hits = []
    for nm in GATES:
        voff = CROWN[nm]["voff"]
        if any(lo <= voff <= hi for lo, hi in spans):
            gate_hits.append(nm)
    gates_equal = all(
        fo["gates"][nm]["factory"].get("hex")
        == fn["gates"][nm]["factory"].get("hex")
        for nm in GATES
        if "hex" in fo["gates"][nm].get("factory", {}))
    if fo["stddef"]["sha16"] == fn["stddef"]["sha16"]:
        verdict = "factory-invariant"
    elif gates_equal and not gate_hits:
        verdict = "factory-invariant-modulo-non-gate-bytes"
    else:
        verdict = "factory-divergent"
    return {"pair": f"{old}->{new}",
            "stddef": [fo["stddef"], fn["stddef"]],
            "setup_blob": [so, sn],
            "diff_spans": spans,
            "gates_in_diff": gate_hits,
            "gate_bytes_equal": gates_equal,
            "verdict": verdict}


def null450(acq: str) -> dict:
    """The generational null: the same factory read on a B450 image.
    Board-relative name table; 0x0 metas reported, never claimed."""
    path = os.path.join(CORPUS, acq + ".rom")
    if not os.path.exists(path):
        raise Refusal(f"{path} missing from the corpus")
    ntf = F49.name_table_fields(path)
    reliable = {n: v for n, v in ntf.items() if v > 0 and n in GATES}
    unreliable = sorted(n for n, v in ntf.items() if v <= 0)
    gates, fct = factory_gate_bytes(path, reliable)
    ifr = ifr_gate_defaults(path, tuple(reliable), crown_check=False)
    cross = {}
    for nm, g in gates.items():
        i = ifr.get(nm)
        row = {"gate": nm, "voff": hex(g["voff"]),
               "factory": g, "ifr_layout": i["default_layout"],
               "ifr_defaults": i["default_statements"],
               "ifr_options": i["options"]}
        if "byte" in g and i["default_statements"]:
            ids = {d["default_id"]: d["value"] for d in
                   i["default_statements"]}
            form_default = ids.get(0, ids.get(min(ids)))
            row["ifr_std_default"] = f"0x{form_default:02x}"
            row["verdict"] = ("agree" if form_default == g["byte"]
                              else "diverge-nvram-outranks-ifr")
        elif "byte" in g:
            row["verdict"] = "no-ifr-default"
        else:
            row["verdict"] = "unmeasurable"
        cross[nm] = row
    return {"acq": acq, "kind": "b450-null",
            "name_table": {k: hex(v) for k, v in sorted(ntf.items(),
                                                        key=lambda kv: kv[1])},
            "unreliable_metas": unreliable,
            "stddef": fct["windows"][0]["stddef_data_size"],
            "setup_blob": {"data_size": fct["windows"][0]["setup_data_size"],
                           "sha16": fct["windows"][0]["setup_sha16"]},
            "systemaccess_paths": fct["systemaccess_paths"],
            "gates": cross}


FAILURE_LEXICON = {
    "Above4gDecode": "byte 0x00 hides the ReBAR question entirely "
                     "(SUPPRESS_IF) — Auto can never engage",
    "ResizeBarSupport": "byte 0x00 is ReBAR off — the option may SAY "
                        "Auto on the form only while the shipped canon "
                        "still holds 0x01; a 0x00 here IS the drift",
    "SriovSupport": "byte 0x00 disables SR-IOV — not a ReBAR gate, "
                    "recorded as the neighbor control",
    "CsmSupport": "byte 0x01 keeps CSM alive — the vendor help's own "
                  "NOTE makes the chain dead while it is on",
    "MmioAddrLimit": "the decode window ceiling — context for Above 4G, "
                     "not a gate itself",
}


def day0() -> dict:
    """The pre-registered dump card: the five-gate byte court."""
    return {
        "card": "16/09 dump — the five-gate byte court (pre-registered "
                "by ring 51, executed by the day-0 protocol)",
        "step_1_factory_identity": {
            "expect": "the dump's StdDefaults blob reproduces the "
                      "stock-3644 factory sha16 "
                      "(see crown: factory.stddef_3644_sha16); a "
                      "different sha is a flash-history marker, "
                      "read with fw48's marks before anything else",
            "windows": STORE_ANCHORS,
        },
        "step_2_live_minus_factory": {
            "protocol": "the ring-14 delta, gate-scoped: parse the "
                        "dump's outer NVAR store (the CAP ships ONE "
                        "variable, StdDefaults; a real board carries "
                        "live variables written by its boots), read "
                        "the live Setup blob at the five gate voffs, "
                        "delta against the factory canon per gate",
            "expect_live_setup_present": True,
            "systemaccess": "read the live SystemAccess variable "
                            "(1 B, GUID " + SYSTEMACCESS_GUID + "); the "
                            "factory ships none (absence = the grayout "
                            "gate open); a live 0x01 grays the option",
        },
        "step_3_lexicon": FAILURE_LEXICON,
        "step_4_os_half": [
            "omarchy-firmware diag-gpu -> gpu-bar1-small if BAR1 "
            "<= 256 MiB (ReBAR off)",
            "sudo lspci -vv -s <gpu> | grep -A4 'Physical Resizable BAR'",
            "dmesg | grep -iE 'rebar|resizable'",
            "/proc/iomem -> GPU BARs above the 4 GB line",
        ],
        "verdicts": {
            "all-five-faithful": "the firmware chain is exactly as "
                                 "shipped — the symptom lives in the OS "
                                 "half or in the Auto heuristic itself "
                                 "(vendor code, the named open question)",
            "above4g-drift": "the chain is broken at gate 1 — the "
                             "ReBAR question is HIDDEN on the board",
            "rebar-drift": "the option lies: the form shows Auto, the "
                           "NVRAM holds Disabled — the drift IS the "
                           "symptom, re-engage via the BIOS default",
            "csm-drift": "the chain is broken at the CSM gate",
            "systemaccess-live-1": "the option is GRAYED on the board — "
                                   "a restricted-session story, not a "
                                   "detection story",
        },
    }


# ---------------------------------------------------------------- selftest

def selftest() -> list[str]:
    checks = []

    def gate(name, ok):
        checks.append(f"{name}={'PASS' if ok else 'FAIL'}")

    # --- tier R: laws + synthetic KATs
    # KAT: a synthetic NVAR store parses and yields a gate byte
    payload = bytes(0x00 for _ in range(0x1BA)) + bytes([0x01]) \
        + bytes([0x01]) + bytes(0x00 for _ in range(24))
    # payload[0x1BA]=0x01, payload[0x1BB]=0x01
    name_bytes = b"Setup\x00"
    guid = bytes.fromhex("43D687ECA4EBB54BA1E53F3E36B20DA9")
    hdr = b"NVAR" + (len(payload) + len(name_bytes) + 16 + 10).to_bytes(
        2, "little") + b"\xff\xff\xff" + bytes([0x86])
    entry = hdr + guid + name_bytes + payload
    inner = entry + b"\x00"  # terminator
    st = walk_region(inner, 0, len(inner), 0)
    ok_parse = (len(st["walk_errors"]) == 0
                and len(st["variables"]) == 1
                and st["variables"][0]["name"] == "Setup")
    data = b"\x00"
    if ok_parse:
        e = parse_entry(inner, 0, len(inner))  # the store's one entry
        data = inner[e["data_start"]:e["data_start"] + e["data_size"]]
    gate("R1-nvar-kat", ok_parse and data[0x1BA] == 0x01
         and data[0x1BB] == 0x01)

    # KAT: the layout chooser — the measured real-data shape (two ops,
    # ids {0,1} under A; duplicated id 0 under B) must resolve to A
    raw = ["00000000", "01000000"]
    opts = ["00", "01"]
    gate("R2-layout-real-shape", choose_layout(raw, opts) == "A")
    # ambiguous case: one op, both layouts coherent
    gate("R3-layout-ambiguous", choose_layout(["00000000"], opts)
         == "ambiguous")
    # incoherent case: the value byte reads outside the option set
    # under BOTH layouts (A reads raw[3]=0x04, B reads raw[0]=0x04)
    # => the ops stay raw, nothing is claimed
    gate("R4-layout-raw-only", choose_layout(["04000004"], opts)
         == "raw-only")
    # KAT: parse_default_op under A reads the standard layout
    d = parse_default_op("01000000", "A")
    gate("R5-default-op-A", d["default_id"] == 1 and d["value"] == 0)

    # --- tier I: live corpus
    try:
        f = fact("b550w2-3644")
        gate("I1-store-shape", f["stores"] == list(STORE_ANCHORS)
             and f["nested_entries"] == STDDEF_ENTRIES
             and f["setup_blob"]["data_size"] == SETUP_DATA["b550w2-3644"]
             and f["stddef"]["data_size"] == STDDEF_DATA["b550w2-3644"])
        gate("I2-windows-identical", f["both_windows_identical"])
        gate("I3-outer-only-stddefaults",
             f["outer_variables"] == ["StdDefaults"])
        gate("I4-systemaccess-absent", f["systemaccess_paths"] == [])
        gate("I5-gates-live",
             all(f["gates"][nm]["factory"].get("hex")
                 for nm in GATES))
        p = pair("b550w2-3644", "b550w2-3645")
        gate("I6-release-factory-law",
             p["verdict"] in ("factory-invariant",
                              "factory-invariant-modulo-non-gate-bytes"))
        n = null450("asus-prime-b450-plus-ref")
        gate("I7-null450-shape",
             n["setup_blob"]["data_size"] == 456
             and "CsmSupport" in n["unreliable_metas"])
        reg_path = os.path.join(REPO, "lab",
                                "vendor-rebarfact-register.json")
        if os.path.exists(reg_path):
            reg = json.load(open(reg_path))
            gate("I8-crown-bridge",
                 f["gates"]["ResizeBarSupport"]["factory"]["hex"]
                 == reg["factory"]["b550w2-3644"]["gates"]
                 ["ResizeBarSupport"]["factory"]["hex"]
                 and f["setup_blob"]["sha16"]
                 == reg["factory"]["b550w2-3644"]["setup_blob"]["sha16"])
        else:
            raise Refusal("crown-not-written")
    except Refusal as exc:
        checks.append(f"I-live=REFUSED({exc})")
    return checks


def manifest() -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    tracked = sorted(f for f in os.listdir(here)
                     if f.endswith((".py", ".json", ".md")))
    return {"ring": 51, "instrument": "lab/fw51-rebarfact.py",
            "lab_surface": tracked,
            "register": "lab/vendor-rebarfact-register.json",
            "corpus": CORPUS, "acquisitions": list(ACQ),
            "nvar_grammar": "ring-14 walker verbatim (UEFITool ami_nvar, "
                            "BSD-2); authority recorded in "
                            "lab/vendor-nvram.json"}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    mode, *rest = argv
    try:
        if mode == "fact" and rest:
            print(json.dumps(fact(rest[0]), indent=1, ensure_ascii=False))
        elif mode == "pair" and len(rest) == 2:
            print(json.dumps(pair(rest[0], rest[1]), indent=1,
                             ensure_ascii=False))
        elif mode == "null450" and rest:
            print(json.dumps(null450(rest[0]), indent=1,
                             ensure_ascii=False))
        elif mode == "day0":
            print(json.dumps(day0(), indent=1, ensure_ascii=False))
        elif mode == "selftest":
            rows = selftest()
            fails = [r for r in rows if r.endswith("FAIL")]
            for r in rows:
                print(" ", r)
            print(f"selftest {len(rows) - len(fails)}/{len(rows)}")
            return 1 if fails else 0
        elif mode == "manifest":
            print(json.dumps(manifest(), indent=1))
        else:
            print(__doc__)
            return 2
    except Refusal as exc:
        print(f"REFUSAL: {exc}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

