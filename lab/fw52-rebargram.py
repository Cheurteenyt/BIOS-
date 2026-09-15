#!/usr/bin/env python3
"""fw52-rebargram — the grammar of the Setup variable: what the vendor's
own shipped C source says the 515 bytes ARE, and the census of who reads
them.

Ring 49 measured the AXIS (the option, its SUPPRESS_IF/GRAY_OUT wrappers,
the pair law); ring 50 the LANGUAGE (the labels: {0x00: Disabled,
0x01: Auto}, no Enabled — the founder's "c'est en auto" byte-true, the
Auto heuristic the only path); ring 51 the FACTORY LAW (the shipped
bytes, two independent sources — the NVRAM canon and the IFR defaults:
the whole decode chain ships OFF, and the founder's Auto is a written
state). Ring 52 measures the GRAMMAR and the EXECUTOR —

  SOURCE T (TEXT): the vendor ships INSIDE the image the AMI SETUP_DATA
    structure as raw C-source FFS text (GUID AB017B39-014F-4A69-A457-
    7E16B09DE825, 53,050 B on the WIFI II): 396 fields, packed size 515 —
    byte-equal to the measured Setup variable of ring 50's varstore
    census and ring 51's factory blob. Every gate field lands EXACTLY on
    the ring-49 crown voffs (MmioAddrLimit 0x1B6, Above4gDecode 0x1BA,
    ResizeBarSupport 0x1BB, SriovSupport 0x1BC, CsmSupport 0x1F2). The
    grammar NAMES every byte of the varstore the first three rings only
    addressed — a THIRD independent source, and the only one that speaks
    field names. The B450 null carries its own generation's text
    (50,486 B): 361 fields, packed 456 == the measured B450 blob, gates
    at 0x187/0x18A/0x18B/0x18C — the grammar law is GENERATION-WIDE.
  SOURCE E (EXECUTORS): the census of who READS the Setup variable (the
    EC87D643 GUID carriers): 34 modules per acquisition, the SAME GUID
    set across release and board. Exactly one consumer is AGESA-sized
    (49818FD1-7413-4C71-84CF-6BFE670C6496, 4,254,978 B, stringless
    PE32+, .text 4.2 MB) and it carries the variable names
    L"Setup"/L"QFan"/L"SetupLedData" — the ASUS policy-bridge shape.
    Release-invariant (sha16 cbf56bec7d3cfaac on 3644 AND 3645), board-
    variant (f2fbd03edccf722a), B550-generation (absent on B450). The
    Auto heuristic's INTERNAL logic stays vendor-code territory (the
    named open question, the SystemAccess precedent): ring 52 bounds it
    — behind 34 readers, inside one 4.25 MB release-invariant binary.

The founder's symptom, one ring further: the byte the Auto heuristic
will one day read sits at SETUP_DATA.ResizeBarSupport — a field with a
NAME, a packed offset the image itself documents in C source, and a
factory value of 0x00 (ring 51). The 16/09 dump inherits the grammar
identity (sha16 9bfea5a1540da7f1 expected on the flashed board) and the
executor identity — the flash cannot change either (release-invariant).

MODES
  grammar <image>     the SETUP_DATA walk + crown cross + CBS census
  executor <image>    the Setup-GUID consumer census + the AGESA-sized
                      bridge profile + the name-table carrier
  pair <old> <new>    the grammar/executor pair laws (sha equality, the
                      named tail field, consumer-set equality)
  null450             the generational null: the B450 grammar under the
                      ring-51 register anchors (reliable metas only)
  day0                the pre-registered dump card: grammar identity,
                      executor identity, the live gate court
  selftest            two-tier gates (R: laws + synthetic KATs,
                      I: live corpus + crown bridge)
  manifest            the ring's tracked surface

LAWS
  L1 TEXT-OVER-GUESSES  an offset is claimed only from the walked text;
                        a field whose type has no fixed size (UINTN and
                        friends) poisons the walk — the instrument
                        refuses rather than guess (the SETUP_DATA text
                        is measured type-pure: UINT8/16/32/64/BOOLEAN).
  L2 ANCHORS-BEFORE-MARKS  every gate offset must reproduce the ring-49
                        crown (imported, never re-typed); the packed
                        size must equal the ring-51 blob size; the B450
                        walk must reproduce the ring-51 register's
                        reliable name-table anchors — or loud Refusal.
  L3 ZERO WRITES        this instrument reads; the crown register is
                        written once by scripts/ring52_register.py.
  L4 COMPOSE-ON-FROZEN  fw49 imported (and through it fw37/fw43) for the
                        pierce and the crown constants; fw51 imported for
                        the factory anchors — never rewritten.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys

REPO = os.environ.get("OMARCHY_FW_REPO", "/home/z/my-project/repo-bios")
CORPUS = os.environ.get("OMARCHY_FW_CORPUS", "/tmp/my-project/scratch-vendor")
ACQ = ("b550w2-3644", "b550w2-3645", "b550-nw-3644")
NULL450 = "asus-prime-b450-plus-ref"

# ---------------------------------------------------------------- imports


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _mods():
    f49 = _load("f49", os.path.join(REPO, "lab", "fw49-rebar.py"))
    f51 = _load("f51", os.path.join(REPO, "lab", "fw51-rebarfact.py"))
    return f49, f51


F49, F51 = _mods()
F37 = F49.F37

# ---------------------------------------------------------------- constants

SETUP_DATA_GUID_PREFIX = "AB017B39-014F-4A69-A457-7E16B09DE825"
SETUP_VAR_GUID = bytes.fromhex("43D687ECA4EBB54BA1E53F3E36B20DA9")
SYSTEMACCESS_GUID = bytes.fromhex("69BB70E7B4BC044D9E9723FF9456FEAC")
NAME_TABLE_GUID_PREFIX = F49.NAME_TABLE_GUID_PREFIX
BRIDGE_GUID_PREFIX = "49818FD1-7413-4C71-84CF-6BFE670C6496"
CBS_TEXT_GUIDS = ("7961C026-4B04-4959-A2E2-0B3926DE8F60",
                  "93F18B9F-71D8-49DC-B62B-8B257A284D28",
                  "89BE47F4-80CE-4B87-ABD1-D279AB6A16AE",
                  "129E7F52-DE9B-402B-BFE8-2B41E5D254ED")
DECODE_FIELDS = ("MmioAddrLimit", "Above4gDecode", "ResizeBarSupport",
                 "SriovSupport", "CsmSupport")

SIZES = {"UINT8": 1, "UINT16": 2, "UINT32": 4, "UINT64": 8,
         "BOOLEAN": 1, "INT8": 1, "INT16": 2, "INT32": 4, "INT64": 8,
         "CHAR8": 1}
DECL = re.compile(
    rb"(UINT8|UINT16|UINT32|UINT64|BOOLEAN|INT8|INT16|INT32|INT64|CHAR8|"
    rb"UINTN)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[\s*(\d+)\s*\])?\s*;",
    re.S)
STRUCT_START = re.compile(rb"typedef\s+struct\s*\{", re.S)
STRUCT_END = re.compile(rb"\}\s*([A-Za-z_][A-Za-z0-9_]*)\s*;", re.S)

# The ring-52 pre-registration ledger — FROZEN before the instrument's
# own live runs; the verdicts are derived by scripts/ring52_register.py
# from fresh runs (never hardcoded here). Probe bases are stated per PR.
PRE_REG_LEDGER = {
    "PR-1": {
        "claim": "the SETUP_DATA text walk lands every gate field on the "
                 "ring-49 crown voff (0x1B6/0x1BA/0x1BB/0x1BC/0x1F2) on "
                 "b550w2-3644 — a third independent source agreeing with "
                 "the IFR census (ring 50) and the NVRAM canon (ring 51)",
        "basis": "probe9 (packed walk 5/5 == crown)"},
    "PR-2": {
        "claim": "the packed size equals the measured Setup-blob size "
                 "PER BOARD: 515 == 515 on 3644 and 3645, 514 == 514 on "
                 "nw-3644 (the sibling's text carries 395 fields)",
        "basis": "probe9/probe10 (515/515/514 vs the ring-51 blobs)"},
    "PR-3": {
        "claim": "the B450 null grammar: 361 fields, packed 456 == the "
                 "ring-51 B450 blob; MmioAddrLimit/Above4gDecode/"
                 "ResizeBarSupport/SriovSupport land on the ring-51 "
                 "register's reliable name-table anchors (0x187/0x18A/"
                 "0x18B/0x18C); CsmSupport is text-claimed only (the "
                 "register's 0x0 meta stays unclaimed)",
        "basis": "probe10 (456 exact, anchors exact)"},
    "PR-4": {
        "claim": "grammar pair laws: release 3644->3645 text sha16 equal "
                 "(9bfea5a1540da7f1); board pair differs (eef483c4097bff"
                 "ff) and the delta is NAMED — the field MyAsusControl "
                 "(@0x201, span [513,514]) present on the WIFI II and "
                 "absent on the sibling: ring 51's anonymous tail span "
                 "[513,514] gets its field name",
        "basis": "probe10 (shas, 396 vs 395 fields, tail listing)"},
    "PR-5": {
        "claim": "the executor census: exactly 34 Setup-GUID consumers "
                 "per B550 acquisition, the SAME GUID set across release "
                 "and board; exactly one consumer is >= 1 MB (the "
                 "4,254,978 B bridge 49818FD1), carrying the variable "
                 "names L\"Setup\"/L\"QFan\"/L\"SetupLedData\"",
        "basis": "probe4/probe6/probe10 (34/34/34, one >= 1 MB, the "
                 "three UTF-16 names)"},
    "PR-6": {
        "claim": "executor pair laws: the bridge is release-INVARIANT "
                 "(sha16 cbf56bec7d3cfaac on 3644 and 3645) and "
                 "board-variant (f2fbd03edccf722a on nw-3644) — the "
                 "16/09 flash cannot change the ReBAR executor's code",
        "basis": "probe3 (sha16s)"},
    "PR-7": {
        "claim": "the bridge is B550-GENERATION: 49818FD1 is ABSENT on "
                 "the B450 null (which runs its own consumer set under "
                 "other GUIDs) — the executor census is per-generation",
        "basis": "probe9 (absent; B450 triad otherwise present)"},
    "PR-8": {
        "claim": "the name-table carrier (64BEA199) exists on all four "
                 "images; its body sha16 is equal across the three B550 "
                 "acquisitions and differs on B450 (33,894 B vs "
                 "37,478 B) — same role, per-generation build",
        "basis": "probe3/probe9 (sizes, sections)"},
    "PR-9": {
        "claim": "the decode family (Above4gDecode/ResizeBarSupport "
                 "names) is ABSENT from every CBS_CONFIG text on B550 "
                 "(the decode chain is Setup-grammar-owned, never "
                 "CBS-owned); B550 carries four CBS texts, B450 three",
        "basis": "probe1/probe9 (token scans)"},
    "PR-10": {
        "claim": "SystemAccess is ABSENT from every SETUP_DATA text — "
                 "the grayout gate is not a Setup field; ring 50's "
                 "varstore independence gains its text anchor",
        "basis": "probe10 (absence cross)"},
    "PR-11": {
        "claim": "the 1M/2M/4M/8M u32 ladder is NOT executor evidence — "
                 "a generic data pattern with dozens of owners; the "
                 "claim is REFUTED BY PROBE and kept visible (the "
                 "pre-named informative outcome)",
        "basis": "probe7 (dozens of ladder4 owners)"},
    "PR-12": {
        "claim": "the SETUP_DATA walk is size-UNAMBIGUOUS: zero UINTN/"
                 "pointer-typed fields (measured census UINT8 x379, "
                 "UINT16 x7, UINT32 x9, UINT64 x1, four fixed arrays); "
                 "any UINTN poisons the walk and the instrument refuses",
        "basis": "probe11 (type census)"},
}

GENOME_MIGRATION_LAW = (
    "the grammar law is generation-wide: each generation ships its own "
    "SETUP_DATA text and its packed size equals that generation's "
    "measured Setup blob (B550 515/514, B450 456)")


class Refusal(Exception):
    """Loud refusal — an anchor moved or an ambiguity poisoned a walk."""


def sha16(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()[:16]


# ---------------------------------------------------------------- walker

def walk_typedefs(text: bytes) -> list[dict]:
    """Every typedef struct in the C-source text, with PACKED field
    offsets. L1: a type without a fixed size (UINTN or unknown) raises
    Refusal — the walk dies rather than guess."""
    out = []
    pos = 0
    while True:
        ms = STRUCT_START.search(text, pos)
        if not ms:
            break
        me = STRUCT_END.search(text, ms.end())
        if not me:
            break
        inner = text[ms.end():me.start()]
        name = me.group(1).decode()
        fields = []
        off = 0
        for dm in DECL.finditer(inner):
            ty = dm.group(1).decode()
            nm = dm.group(2).decode()
            cnt = int(dm.group(3)) if dm.group(3) else 1
            if ty not in SIZES:
                raise Refusal(
                    f"typedef {name}: field {nm} has type {ty} with no "
                    "fixed size — the walk refuses (L1)")
            fields.append({"off": off, "type": ty, "name": nm,
                           "count": cnt})
            off += SIZES[ty] * cnt
        out.append({"name": name, "fields": fields, "packed": off})
        pos = me.end()
    return out


def find_ffs_body(image_path: str, guid_prefix: str) -> bytes | None:
    """The FFS body of one module, raw + pierced payloads (fw37)."""
    img = open(image_path, "rb").read()
    payloads, _ = F37.pierce_all(img)
    for blob in [img] + list(payloads):
        for fv in F37.scan_fvs(blob):
            for guid, ftype, size, off, body in F37.iter_files(blob, fv):
                if ftype in (0xF0, 0x01):
                    continue
                if guid.startswith(guid_prefix):
                    return body
    return None


def setup_data_grammar(image_path: str, expect_packed: int | None = None,
                       crown_cross: bool = True) -> dict:
    """SOURCE T: the SETUP_DATA text walk + the crown cross."""
    body = find_ffs_body(image_path, SETUP_DATA_GUID_PREFIX)
    if body is None:
        raise Refusal(f"{os.path.basename(image_path)}: SETUP_DATA text "
                      f"{SETUP_DATA_GUID_PREFIX} not found")
    structs = walk_typedefs(body)
    row = next((s for s in structs if s["name"] == "SETUP_DATA"), None)
    if row is None:
        raise Refusal(f"{os.path.basename(image_path)}: no SETUP_DATA "
                      "typedef in the shipped text")
    gates = {f["name"]: f["off"] for f in row["fields"]
             if f["name"] in DECODE_FIELDS}
    names = {f["name"] for f in row["fields"]}
    g = {
        "guid": SETUP_DATA_GUID_PREFIX,
        "text_sha16": sha16(body),
        "text_size": len(body),
        "typedefs_in_file": len(structs),
        "field_count": len(row["fields"]),
        "packed_size": row["packed"],
        "gates": {k: f"0x{gates[k]:X}" for k in DECODE_FIELDS
                  if k in gates},
        "systemaccess_in_setup_data": "SystemAccess" in names,
        "type_census": _type_census(row["fields"]),
        "tail_fields": [
            {"name": f["name"], "type": f["type"], "off": f"0x{f['off']:X}"}
            for f in row["fields"][-6:]
        ],
    }
    if crown_cross:
        for k, voff in F49.CROWN_VOFF.items():
            if k in gates and gates[k] != voff:
                raise Refusal(
                    f"{os.path.basename(image_path)}: grammar gate "
                    f"{k} @0x{gates[k]:X} != crown 0x{voff:X} (L2)")
    if expect_packed is not None and row["packed"] != expect_packed:
        raise Refusal(
            f"{os.path.basename(image_path)}: grammar packed "
            f"{row['packed']} != expected blob {expect_packed} (L2)")
    return g


def _type_census(fields: list[dict]) -> dict:
    c: dict[str, int] = {}
    for f in fields:
        c[f["type"]] = c.get(f["type"], 0) + 1
    return dict(sorted(c.items()))


def cbs_census(image_path: str) -> dict:
    """The CBS variable-struct texts: census + decode-family absence."""
    rows = []
    for guid in CBS_TEXT_GUIDS:
        body = find_ffs_body(image_path, guid)
        if body is None:
            rows.append({"guid": guid, "present": False})
            continue
        try:
            structs = walk_typedefs(body)
        except Refusal:
            structs = None
        cbs = next((s for s in (structs or [])
                    if s["name"].startswith("CBS_CONFIG")), None)
        dec = [f for f in DECODE_FIELDS[:4]
               if f.encode() in body]
        rows.append({
            "guid": guid, "present": True, "size": len(body),
            "sha16": sha16(body),
            "cbs_config_fields": len(cbs["fields"]) if cbs else None,
            "cbs_config_packed": cbs["packed"] if cbs else None,
            "decode_field_names_present": dec,
        })
    return {"texts": rows,
            "count": sum(1 for r in rows if r["present"]),
            "decode_absent_everywhere": all(
                not r.get("decode_field_names_present")
                for r in rows if r["present"])}

# ---------------------------------------------------------------- executor

def _utf16_names(body: bytes, probes: tuple[str, ...]) -> dict:
    """Which of the probed variable names the module body carries."""
    return {p: (p.encode("utf-16-le") in body) for p in probes}


def executor_census(image_path: str, require_bridge: bool = True) -> dict:
    """SOURCE E: every Setup-GUID consumer, the bridge profile, the
    SystemAccess readers, the name-table carrier. require_bridge=False
    for the generational null (the B450 has no bridge — PR-7's law:
    its ABSENCE there is the measurement, not a refusal)."""
    img = open(image_path, "rb").read()
    payloads, _ = F37.pierce_all(img)
    consumers = {}
    sa_consumers = []
    for blob in [img] + list(payloads):
        for fv in F37.scan_fvs(blob):
            for guid, ftype, size, off, body in F37.iter_files(blob, fv):
                if ftype in (0xF0, 0x01) or not body:
                    continue
                if SETUP_VAR_GUID in body and guid not in consumers:
                    consumers[guid] = {
                        "guid": guid,
                        "ftype": F37.FILE_TYPES.get(
                            ftype, f"type_{ftype:#04x}"),
                        "size": size,
                        "sha16": sha16(body),
                    }
                if SYSTEMACCESS_GUID in body:
                    sa_consumers.append(guid)
    big = [c for c in consumers.values() if c["size"] >= 1_000_000]
    bridge = None
    for c in big:
        if c["guid"].startswith(BRIDGE_GUID_PREFIX):
            body = find_ffs_body(image_path, c["guid"])
            c["utf16_variable_names"] = _utf16_names(
                body, ("Setup", "QFan", "SetupLedData", "SystemAccess"))
            bridge = c
    if bridge is None and require_bridge:
        # no bridge under the registered GUID — loud, not silent
        raise Refusal(f"{os.path.basename(image_path)}: the bridge "
                      f"{BRIDGE_GUID_PREFIX} is absent from the census")
    nt = find_ffs_body(image_path, NAME_TABLE_GUID_PREFIX)
    return {
        "consumer_count": len(consumers),
        "consumer_guid_set_sha16": sha16(
            json.dumps(sorted(consumers), separators=(",", ":")).encode()),
        "consumers_big": [
            {"guid": c["guid"], "size": c["size"], "sha16": c["sha16"],
             "utf16_variable_names": c.get("utf16_variable_names")}
            for c in big],
        "bridge": bridge,
        "systemaccess_guid_consumers": len(sa_consumers),
        "name_table_carrier": {
            "present": nt is not None,
            "size": len(nt) if nt else None,
            "sha16": sha16(nt) if nt else None,
        },
    }


# ---------------------------------------------------------------- pairs

def _grammar_row(acq: str) -> dict:
    """Grammar + blob cross for one acquisition (the blob size comes from
    the frozen ring-51 machinery)."""
    img_path = os.path.join(CORPUS, acq + ".rom")
    f51fact = F51.fact(acq)
    expect = f51fact["setup_blob"]["data_size"]
    g = setup_data_grammar(img_path, expect_packed=expect)
    g["blob_size"] = expect
    g["blob_sha16"] = f51fact["setup_blob"]["sha16"]
    g["size_cross"] = ("agree" if g["packed_size"] == expect
                       else "REFUSED")
    return g


def pair(old: str, new: str) -> dict:
    go, gn = _grammar_row(old), _grammar_row(new)
    eo, en = executor_census(os.path.join(CORPUS, old + ".rom")), \
        executor_census(os.path.join(CORPUS, new + ".rom"))
    bo = find_ffs_body(os.path.join(CORPUS, old + ".rom"),
                       SETUP_DATA_GUID_PREFIX)
    bn = find_ffs_body(os.path.join(CORPUS, new + ".rom"),
                       SETUP_DATA_GUID_PREFIX)
    tail = []
    if go["packed_size"] != gn["packed_size"]:
        names_o = [f["name"] for f in _setup_fields(bo)]
        names_n = [f["name"] for f in _setup_fields(bn)]
        tail = [n for n in names_o if n not in names_n] + \
               [n for n in names_n if n not in names_o]
    bridge_old = eo["bridge"]
    bridge_new = en["bridge"]
    return {
        "grammar": {
            "text_sha16_old": go["text_sha16"],
            "text_sha16_new": gn["text_sha16"],
            "text_equal": go["text_sha16"] == gn["text_sha16"],
            "packed_old": go["packed_size"],
            "packed_new": gn["packed_size"],
            "gate_bytes_equal": go["gates"] == gn["gates"],
        },
        "tail_delta_fields": tail,
        "executor": {
            "bridge_sha16_old": bridge_old["sha16"] if bridge_old else None,
            "bridge_sha16_new": bridge_new["sha16"] if bridge_new else None,
            "bridge_release_invariant": (
                bridge_old and bridge_new
                and bridge_old["sha16"] == bridge_new["sha16"]),
            "consumer_set_equal":
                eo["consumer_guid_set_sha16"] == en["consumer_guid_set_sha16"],
            "consumer_count_old": eo["consumer_count"],
            "consumer_count_new": en["consumer_count"],
        },
        "name_table_equal":
            eo["name_table_carrier"]["sha16"]
            == en["name_table_carrier"]["sha16"],
    }


def _setup_fields(text: bytes) -> list[dict]:
    structs = walk_typedefs(text)
    row = next((s for s in structs if s["name"] == "SETUP_DATA"), None)
    if row is None:
        raise Refusal("no SETUP_DATA typedef in a pair walk")
    return row["fields"]


# ---------------------------------------------------------------- null

def null450() -> dict:
    """The generational null: the B450 grammar under the ring-51
    register's RELIABLE anchors (the 0x0 metas stay unclaimed)."""
    reg_path = os.path.join(REPO, "lab", "vendor-rebarfact-register.json")
    reg = json.load(open(reg_path))
    nb = reg["b450_null"]
    anchors = {k: int(v, 16) for k, v in nb["name_table"].items()
               if v.lower() != "0x0"}
    img_path = os.path.join(CORPUS, NULL450 + ".rom")
    body = find_ffs_body(img_path, SETUP_DATA_GUID_PREFIX)
    if body is None:
        raise Refusal("B450 null: SETUP_DATA text not found")
    structs = walk_typedefs(body)
    row = next((s for s in structs if s["name"] == "SETUP_DATA"), None)
    if row is None:
        raise Refusal("B450 null: no SETUP_DATA typedef")
    gates = {f["name"]: f["off"] for f in row["fields"]
             if f["name"] in anchors}
    for k, voff in anchors.items():
        if k in gates and gates[k] != voff:
            raise Refusal(
                f"B450 null: grammar {k} @0x{gates[k]:X} != register "
                f"anchor 0x{voff:X} (L2)")
    expect = nb["setup_blob"]["data_size"]
    if row["packed"] != expect:
        raise Refusal(
            f"B450 null: grammar packed {row['packed']} != blob "
            f"{expect} (L2)")
    ex = executor_census(img_path, require_bridge=False)
    return {
        "acq": NULL450,
        "field_count": len(row["fields"]),
        "packed_size": row["packed"],
        "blob_size": expect,
        "size_cross": "agree",
        "gate_offsets": {k: f"0x{v:X}" for k, v in sorted(gates.items())},
        "anchor_source": "vendor-rebarfact-register.json b450_null "
                         "(reliable metas only)",
        "text_sha16": sha16(body),
        "text_size": len(body),
        "bridge_present": ex["bridge"] is not None,
        "consumer_count": ex["consumer_count"],
        "name_table_carrier": ex["name_table_carrier"],
        "cbs": cbs_census(img_path),
    }


# ---------------------------------------------------------------- day0

def day0() -> dict:
    """The pre-registered dump card: what the 16/09 dump must reproduce
    (grammar identity, executor identity) and the live gate court."""
    g = _grammar_row("b550w2-3644")
    ex = executor_census(os.path.join(CORPUS, "b550w2-3644.rom"))
    return {
        "dump_expectations": {
            "setup_data_text_sha16": g["text_sha16"],
            "setup_data_packed": g["packed_size"],
            "bridge_sha16": (ex["bridge"] or {}).get("sha16"),
            "consumer_count": ex["consumer_count"],
            "consumer_guid_set_sha16": ex["consumer_guid_set_sha16"],
            "name_table_sha16": ex["name_table_carrier"]["sha16"],
        },
        "live_gate_court": {
            "Above4gDecode": "0x01 (else the question is SUPPRESSED — "
                             "the founder could not read it)",
            "ResizeBarSupport": "0x01 (the form says Auto)",
            "CsmSupport": "0x00 (the board ships UEFI-only)",
        },
        "delta_protocol": "ring-14 live-minus-factory, gate-scoped; the "
                          "factory bytes are ring-51's (all 0x00 but "
                          "Mmio 0x27)",
        "os_half": "diag-gpu BAR1 <= 256 MiB -> 'Resizable BAR likely "
                   "disabled'; lspci 'Physical Resizable BAR' current "
                   "size; dmesg rebar lines; /proc/iomem above 4 GB",
    }


# ---------------------------------------------------------------- selftest

def selftest() -> list[str]:
    notes: list[str] = []

    # ---- R tier: laws + synthetic KATs
    # KAT-1: packed arithmetic on a synthetic struct
    kat = (b"typedef struct {\n  UINT8 A;\n  UINT16 B[3];\n"
           b"  UINT32 C;\n} T;\n")
    t = walk_typedefs(kat)[0]
    offs = [(f["name"], f["off"]) for f in t["fields"]]
    if offs != [("A", 0), ("B", 1), ("C", 7)] or t["packed"] != 11:
        raise Refusal(f"KAT-1 packed arithmetic wrong: {offs} "
                      f"packed={t['packed']}")
    notes.append("R1 KAT packed arithmetic (arrays, u16/u32) ok")

    # KAT-2: multi-typedef file
    kat2 = (b"typedef struct { UINT8 A; } S1;\ntypedef struct { "
            b"UINT32 B; } S2;\n")
    s = walk_typedefs(kat2)
    if [x["name"] for x in s] != ["S1", "S2"] or \
            [x["packed"] for x in s] != [1, 4]:
        raise Refusal("KAT-2 multi-typedef walk wrong")
    notes.append("R2 KAT multi-typedef boundaries ok")

    # KAT-3: UINTN poisons the walk (L1)
    kat3 = b"typedef struct { UINT8 A; UINTN P; } T3;\n"
    try:
        walk_typedefs(kat3)
        raise Refusal("KAT-3 failed: UINTN walk did not refuse")
    except Refusal:
        notes.append("R3 KAT UINTN refusal (L1) ok")

    # KAT-4: crown-cross refusal on a shifted gate (L2)
    fake = os.path.join(CORPUS, "b550w2-3644.rom")
    real = find_ffs_body(fake, SETUP_DATA_GUID_PREFIX)
    shifted = real.replace(b"  UINT8 Above4gDecode;", b"  UINT8 XxPad;\n"
                            b"  UINT8 Above4gDecode;", 1)
    tmp_cache = walk_typedefs(shifted)
    row = next(s for s in tmp_cache if s["name"] == "SETUP_DATA")
    gates = {f["name"]: f["off"] for f in row["fields"]}
    if gates["Above4gDecode"] == F49.CROWN_VOFF["Above4gDecode"]:
        raise Refusal("KAT-4 failed: the shifted walk still hits the "
                      "crown — the cross has no teeth")
    notes.append("R4 KAT crown-cross teeth ok (shifted text misses)")

    # KAT-5: tail-delta naming
    names_o = [f["name"] for f in _setup_fields(real)]
    synth = real.replace(b"  UINT8 MyAsusControl;", b"", 1)
    names_n = [f["name"] for f in _setup_fields(synth)]
    delta = [n for n in names_o if n not in names_n]
    if delta != ["MyAsusControl"]:
        raise Refusal(f"KAT-5 tail naming wrong: {delta}")
    notes.append("R5 KAT tail-delta naming ok (MyAsusControl)")

    # KAT-6: zero writes (L3) — static scan of this file
    src = open(os.path.join(REPO, "lab", "fw52-rebargram.py"), "rb").read()
    for pat in (rb'open\([^)]*["\']w["\']', rb"\.write\("):
        if re.search(pat, src):
            raise Refusal(f"KAT-6 failed: write-mode pattern {pat!r} "
                          "in the instrument source")
    notes.append("R6 zero-writes static scan ok (L3)")

    # KAT-7: compose-on-frozen — the crown is fw49's object, not a retype
    if F49.CROWN_VOFF["ResizeBarSupport"] != 0x1BB or \
            F49.CROWN_VOFF["CsmSupport"] != 0x1F2:
        raise Refusal("KAT-7 failed: crown constants drifted")
    notes.append("R7 compose-on-frozen ok (fw49 crown imported)")

    # ---- I tier: live corpus
    g = _grammar_row("b550w2-3644")
    if g["packed_size"] != 515 or g["size_cross"] != "agree" or \
            len(g["gates"]) != 5:
        raise Refusal("I1 failed: live grammar/crown cross")
    notes.append(f"I1 grammar 3644 ok ({g['field_count']} fields, "
                 f"515 B, gates 5/5)")

    g45 = setup_data_grammar(os.path.join(CORPUS, "b550w2-3645.rom"),
                             expect_packed=515)
    gnw = setup_data_grammar(os.path.join(CORPUS, "b550-nw-3644.rom"),
                             expect_packed=514)
    if g["text_sha16"] != g45["text_sha16"] or \
            g["text_sha16"] == gnw["text_sha16"]:
        raise Refusal("I2 failed: grammar pair law")
    notes.append("I2 grammar pair law ok (release equal, board differs)")

    ex = executor_census(os.path.join(CORPUS, "b550w2-3644.rom"))
    # PR-5 was REFUTED by this very gate's first run: TWO consumers are
    # >= 1 MB — the bridge AND the Setup module itself (the varstore's
    # owner, 1,421,242 B, x24 GUID refs). The corrected law: exactly one
    # AGESA-sized reader BEYOND the owner. The refutation stays visible
    # in the register (rings 45/47/48/50 precedent).
    if ex["consumer_count"] != 34 or len(ex["consumers_big"]) != 2:
        raise Refusal(f"I3 failed: census {ex['consumer_count']} / "
                      f"big {len(ex['consumers_big'])}")
    if not ex["bridge"] or ex["bridge"]["sha16"] != "cbf56bec7d3cfaac":
        raise Refusal("I3 failed: bridge sha drifted")
    owner = [c for c in ex["consumers_big"]
             if c["guid"].startswith("899407D7")]
    if not owner:
        raise Refusal("I3 failed: the Setup owner vanished from the big "
                      "consumers")
    notes.append(f"I3 executor census ok (34 consumers, 2 big: owner + "
                 f"bridge {ex['bridge']['sha16']})")

    p = pair("b550w2-3644", "b550-nw-3644")
    if p["tail_delta_fields"] != ["MyAsusControl"]:
        raise Refusal(f"I4 failed: tail delta {p['tail_delta_fields']}")
    notes.append("I4 board-pair tail naming ok (MyAsusControl)")

    n = null450()
    if n["packed_size"] != 456 or n["bridge_present"]:
        raise Refusal("I5 failed: B450 null (456/bridge)")
    notes.append(f"I5 B450 null ok ({n['field_count']} fields, 456 B, "
                 f"no bridge)")

    return notes


# ---------------------------------------------------------------- manifest

def manifest() -> dict:
    return {
        "ring": 52,
        "instrument": "lab/fw52-rebargram.py",
        "composes": ["lab/fw49-rebar.py", "lab/fw51-rebarfact.py",
                     "lab/fw37-differ.py", "lab/fw43-proposal.py"],
        "register": "lab/vendor-rebargram-register.json",
        "writer": "scripts/ring52_register.py",
        "acquisitions": list(ACQ) + [NULL450],
        "modes": ["grammar", "executor", "pair", "null450", "day0",
                  "selftest", "manifest"],
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "grammar":
        acq = rest[0] if rest else "b550w2-3644"
        g = _grammar_row(acq)
        print(json.dumps(g, indent=1))
    elif cmd == "executor":
        acq = rest[0] if rest else "b550w2-3644"
        print(json.dumps(executor_census(os.path.join(CORPUS, acq + ".rom")),
                         indent=1))
    elif cmd == "pair":
        print(json.dumps(pair(rest[0], rest[1]), indent=1))
    elif cmd == "null450":
        print(json.dumps(null450(), indent=1))
    elif cmd == "day0":
        print(json.dumps(day0(), indent=1))
    elif cmd == "selftest":
        rows = selftest()
        print("\n".join(rows))
        print(f"SELFTEST PASS ({len(rows)} gates)")
    elif cmd == "manifest":
        print(json.dumps(manifest(), indent=1))
    else:
        print(f"unknown mode {cmd!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
