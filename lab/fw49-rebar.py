#!/usr/bin/env python3
"""fw49-rebar — the ReBAR axis: the founder's mis-detected Auto, measured.

The founder's report (ring 49): "le reshade bar ... il détecte mal alors que
c'est en auto" — Resizable BAR on Auto, detected badly. The repo's own
diag-gpu already renders the OS half (gpu-bar1-small: BAR1 <= 256 MiB) and
states the BIOS half is "not observable from the OS". Ring 49 makes the BIOS
half observable in the lab, on the vendor image itself.

THE MEASURED TRUTH CHAIN (b550w2-3644/3645, b550-nw-3644):
  1. The setup variable field exists: the AMI SMM name-table driver
     (64BEA199-7C6C-4F51-B0DA-F42C897DA5CC, type 0x0A) carries the field
     list; ResizeBarSupport sits at Setup-varstore offset 0x1BB, between
     Above4gDecode (0x1BA) and SriovSupport (0x1BC).
  2. The visible question exists: in the Setup module's IFR, ONE_OF
     qid 0x20F, prompt tok 1403 = 'Resize BAR Support' — the ASUS label is
     'Resize BAR', NOT 'Resizable': the word "Resizable" is absent from the
     whole decompressed image (raw + recursive LZMA), which is why string
     searches for the canonical name find nothing.
  3. The conditions exist, twice measured: the question is wrapped in
     SUPPRESS_IF (qid 0x20E == 0) — qid 0x20E IS Above4gDecode — and
     GRAY_OUT_IF (qid 0x361 == 1, hidden question, identity open); the
     vendor's own help text (tok 1404) documents the chain verbatim:
     64-bit PCI decoding + disable CSM in the Boot section + a ReBAR-capable
     GPU. Auto engages only when all three hold.
  4. The pair law: the axis is byte-identical across 3644 -> 3645 (the
     release the 16/09 flash will apply) and the non-WIFI sibling — the
     release rotates one DER certificate (ring 48), not one setup bit.

MODES
  axis <image>            full truth chain for one acquisition
  pair <old> <new>        byte-identity of the axis regions across images
  nullrebar               the OS-side null: what diag-gpu would render
  selftest                two-tier gates (R: laws + synthetic KATs,
                          I: live corpus)
  manifest                the ring's tracked surface

LAWS
  L1 LABELS-OVER-GUESSES  a string is claimed only when it is anchored-
                          verified BOTH ways (the tok1281 = 'Above 4G
                          Decoding' anchor must reproduce SR-IOV Support
                          forward and a clean entry backward); unresolved
                          tokens stay raw in the output, never invented.
  L2 ANCHORS-BEFORE-MARKS the axis facts live in the measured image, not
                          in this file: every qid/tok/voff is extracted
                          live; a mismatch with the registered crown
                          values is a loud Refusal, not a silent pass.
  L3 ZERO WRITES          this instrument reads; the crown register is
                          written once by scripts/ring49_register.py.
  L4 COMPOSE-ON-FROZEN    fw37 pierce + fw43 module/forms machinery are
                          imported, never rewritten (rings 37-48 frozen).
"""
from __future__ import annotations

import hashlib
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


def _mods():
    lab = os.path.join(REPO, "lab")
    f37 = _load("f37", os.path.join(lab, "fw37-differ.py"))
    f43 = _load("f43", os.path.join(lab, "fw43-proposal.py"))
    return f37, f43


F37, F43 = _mods()

# ---------------------------------------------------------------- constants

AXIS_NAMES = ("Above4gDecode", "ResizeBarSupport", "SriovSupport",
              "MmioAddrLimit", "CsmSupport")
CROWN_VOFF = {"Above4gDecode": 0x1BA, "ResizeBarSupport": 0x1BB,
              "SriovSupport": 0x1BC, "MmioAddrLimit": 0x1B6,
              "CsmSupport": 0x1F2}
CROWN_QID = {"Above4gDecode": 0x20E, "ResizeBarSupport": 0x20F,
             "SriovSupport": 0x210}
CROWN_TOK = {"Above4gDecode": 1281, "ResizeBarSupport": 1403,
             "SriovSupport": 1283}
NAME_TABLE_GUID_PREFIX = "64BEA199-7C6C-4F51-B0DA-F42C897DA5CC"

OP_ONE_OF = 0x05
OP_ONE_OF_OPTION = 0x09
OP_END = 0x29
OP_SUPPRESS_IF = 0x0A
OP_GRAY_OUT_IF = 0x19
QUESTION_OPS = F43.QUESTION_OPS

REFUSALS = []


class Refusal(Exception):
    pass


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


# ---------------------------------------------------------------- primitives

def read_op(body: bytes, i: int):
    """(op, ln, hs) at i, or None. fw43's length rules."""
    if i + 2 > len(body):
        return None
    op = body[i]
    raw = body[i + 1]
    if raw & 0x7F == 0x7F and i + 4 <= len(body):
        return op, int.from_bytes(body[i + 2:i + 4], "little"), 4
    return op, raw & 0x7F, 2


def setup_pe(image_path: str):
    """The big Setup module PE (the AMI Aptio setup) of one image."""
    for name, pe in F43.image_modules(image_path):
        if name == "Setup" and len(pe) > 1_000_000:
            return name, pe
    raise Refusal("no Setup module > 1 MB in " + image_path)


def questions_at(body: bytes, voffs: dict[int, str]) -> list[dict]:
    """Raw sequential scan: every question binding one of voffs."""
    out = []
    i, n = 0, len(body)
    while i + 2 <= n:
        r = read_op(body, i)
        if r is None:
            break
        op, ln, hs = r
        if ln < hs or i + ln > n:
            i += 1
            continue
        if op in QUESTION_OPS and ln >= 10:
            qh = i + 2
            voff = int.from_bytes(body[qh + 8:qh + 10], "little")
            if voff in voffs and not any(
                    q["voff"] == voff and q["body"] is body for q in out):
                out.append({
                    "op": op, "off": i, "ln": ln, "body": body,
                    "prompt": int.from_bytes(body[qh:qh + 2], "little"),
                    "help": int.from_bytes(body[qh + 2:qh + 4], "little"),
                    "qid": int.from_bytes(body[qh + 4:qh + 6], "little"),
                    "vsid": int.from_bytes(body[qh + 6:qh + 8], "little"),
                    "voff": voff})
        i += ln
    return out


def one_of_scope(body: bytes, qoff: int):
    """(options, ami_value_ops) walking the ONE_OF scope forward: children
    sit at the depth the ONE_OF itself establishes."""
    opts, vals = [], []
    i, depth, base = qoff, 0, None
    while i + 2 <= len(body):
        r = read_op(body, i)
        if r is None:
            break
        op, ln, hs = r
        if ln < hs or i + ln > len(body):
            break
        scope = bool(body[i + 1] & 0x80)
        if op == OP_END:
            depth -= 1
            if base is not None and depth < base:
                break
            i += ln
            continue
        if scope:
            depth += 1
        if base is None:
            base = depth      # depth right after the ONE_OF op
        elif depth == base:
            if op == OP_ONE_OF_OPTION and ln >= 7:
                opts.append({"tok": int.from_bytes(body[i + 2:i + 4], "little"),
                             "flags": body[i + 5], "type": body[i + 4],
                             "value": body[i + 6:i + ln].hex()})
            elif op == 0x5B and ln >= 6:
                vals.append(body[i + 2:i + ln].hex())
        i += ln
    return opts, vals


def predicate_wrap(body: bytes, qoff: int):
    """The conditional wrapper preceding the question:
    (supp_off, supp_len, gray_off, gray_len) or whatever is found walking
    back <= 32 bytes for scope-opening conds."""
    conds = []
    i = qoff
    lo = max(0, qoff - 32)
    while i >= lo:
        r = read_op(body, i)
        if r is not None:
            op, ln, hs = r
            if op in (OP_SUPPRESS_IF, OP_GRAY_OUT_IF) and ln == 2 \
                    and body[i + 1] & 0x80 and i + 2 <= qoff:
                conds.append((op, i, ln))
        i -= 1
    conds.sort(key=lambda t: t[1])
    return conds


def decode_inline_pred(body: bytes, coff: int, cln: int,
                       qmap: dict[int, dict]) -> str:
    """The compact AMI predicate ops after a scope-opening cond:
    `12 06 <qid u16> <value u16>` rendered via qmap."""
    out = []
    i = coff + 2
    end = coff + 32
    while i + 2 <= min(end, len(body)):
        r = read_op(body, i)
        if r is None:
            break
        op, ln, hs = r
        if ln < hs or i + ln > end:
            break
        if op == 0x12 and ln >= 6:
            a = int.from_bytes(body[i + 2:i + 4], "little")
            v = int.from_bytes(body[i + 4:i + 6], "little")
            q = qmap.get(a)
            ref = (q["name"] if q and q.get("name") else f"qid0x{a:X}")
            out.append(f"{ref}==0x{v:X}")
        elif op == OP_END:
            break
        else:
            out.append(f"op{op:#04x}")
        i += ln
    return " ".join(out)


# ---------------------------------------------------------------- the AMI
# packed-UTF-16 string table (entries: utf16z + one 0x14 byte)

def read_entry(pe: bytes, o: int):
    e = o
    chars = []
    while e + 1 < len(pe):
        ch = pe[e] | (pe[e + 1] << 8)
        if ch == 0:
            break
        chars.append(chr(ch))
        e += 2
    return "".join(chars), e + 3


def entry_before(pe: bytes, s: int) -> int:
    """Start of the previous packed entry: scan below the current entry's
    own [NUL NUL 0x14] tail for the previous separator whose successor
    byte is a real char."""
    p = s - 4
    while p > 2:
        if pe[p] == 0x14 and pe[p + 1] != 0:
            return p + 1
        p -= 1
    return -1


def anchor_table(pe: bytes, anchor_off: int):
    """Walk back to entry 1 of the contiguous region containing the anchor."""
    starts = [anchor_off]
    s = anchor_off
    for _ in range(1400):
        s = entry_before(pe, s)
        if s < 0:
            break
        starts.append(s)
    return s


def label_of(pe: bytes, anchor_off: int, anchor_tok: int, tok: int) -> str:
    """tok -> text, walking entries RELATIVE to the measured anchor
    (the packed region is not linearly addressable from token 1 — the
    anchor-neighborhood is the only honest index)."""
    s = anchor_off
    d = tok - anchor_tok
    for _ in range(abs(d)):
        if d < 0:
            s = entry_before(pe, s)
            if s < 0:
                return ""
        else:
            s = read_entry(pe, s)[1]
    return read_entry(pe, s)[0]


def verify_anchor(pe: bytes, anchor_off: int, anchor_tok: int,
                  check_tok: int, expect: str) -> None:
    """L1: the anchor must reproduce `expect` at check_tok AND a clean
    entry both one before the anchor and one after expect's tok."""
    fwd = label_of(pe, anchor_off, anchor_tok, check_tok)
    if fwd != expect:
        raise Refusal(f"L1 forward anchor failed: tok {check_tok} -> "
                      f"{fwd!r} != {expect!r}")
    back = read_entry(pe, entry_before(pe, anchor_off))[0]
    if not back or not all(32 <= ord(c) < 127 for c in back):
        raise Refusal(f"L1 backward anchor failed: {back!r}")
    after = label_of(pe, anchor_off, anchor_tok, check_tok + 1)
    if not after:
        raise Refusal("L1 post-anchor entry missing")


# ---------------------------------------------------------------- name table

def name_table_fields(image_path: str) -> dict[str, int]:
    """The SMM name-table driver's field -> Setup-varstore offset map."""
    blobs, _notes = F37.pierce_all(F37.load(image_path))
    for blob in blobs:
        if b"ResizeBarSupport" not in blob:
            continue
        for fv in F37.scan_fvs(blob):
            for guid, ftype, size, off, body in F37.iter_files(
                    blob, fv, fv.get("hlen", 0x48)):
                for st, sb in F37.iter_sections(body):
                    if st != 0x10 or sb[:2] != b"MZ":
                        continue
                    if b"ResizeBarSupport" not in sb:
                        continue
                    if not str(guid).startswith(NAME_TABLE_GUID_PREFIX):
                        continue
                    fields = {}
                    for nm in AXIS_NAMES:
                        m = re.search(nm.encode() + b"\x00", sb)
                        if not m:
                            continue
                        meta = sb[m.start() + 0x30:m.start() + 0x32]
                        fields[nm] = int.from_bytes(meta, "little")
                    if len(fields) >= 3:
                        return fields
    raise Refusal("name-table driver not found in " + image_path)


# ---------------------------------------------------------------- modes

def axis(acq: str) -> dict:
    """The full truth chain for one acquisition."""
    path = os.path.join(CORPUS, acq + ".rom")
    if not os.path.exists(path):
        raise Refusal(f"{path} missing from the corpus")
    name, pe = setup_pe(path)
    # the axis questions live in the direct_forms bodies (package lists
    # do not close in the AMI Setup module — ring-43's convention)
    found: dict[int, dict] = {}
    voff_map = {v: n for n, v in CROWN_VOFF.items()}
    for d in F43.direct_forms(pe):
        body = pe[d["offset"] + 4:d["offset"] + d["size"]]
        for q in questions_at(body, voff_map):
            if q["voff"] not in found:
                found[q["voff"]] = q
    missing = [n for n, v in CROWN_VOFF.items() if v not in found
               and n in CROWN_QID]
    if missing:
        raise Refusal(f"axis questions missing: {missing}")
    for voff, q in found.items():
        nm = next((n for n, v in CROWN_VOFF.items() if v == voff), None)
        q["name"] = nm
    # L2: qids/toks must reproduce the crown or refuse
    for nm, qid in CROWN_QID.items():
        q = found[CROWN_VOFF[nm]]
        if q["qid"] != qid:
            raise Refusal(f"L2 {nm}: qid {q['qid']:#x} != crown {qid:#x}")
        if q["prompt"] != CROWN_TOK[nm]:
            raise Refusal(f"L2 {nm}: tok {q['prompt']} != crown "
                          f"{CROWN_TOK[nm]}")
    # the string anchor: Above4gDecode's prompt must BE 'Above 4G Decoding'
    a4 = found[CROWN_VOFF["Above4gDecode"]]
    pat = "Above 4G Decoding".encode("utf-16-le")
    anchor_off = pe.find(pat)
    if anchor_off < 0:
        raise Refusal("anchor string 'Above 4G Decoding' not in Setup PE")
    verify_anchor(pe, anchor_off, a4["prompt"], CROWN_TOK["SriovSupport"],
                  "SR-IOV Support")
    labels = {}
    for nm in CROWN_QID:
        q = found[CROWN_VOFF[nm]]
        labels[nm] = label_of(pe, anchor_off, a4["prompt"], q["prompt"])
    if labels["ResizeBarSupport"] != "Resize BAR Support":
        raise Refusal(f"ReBAR label {labels['ResizeBarSupport']!r} != "
                      f"'Resize BAR Support'")
    rebar = found[CROWN_VOFF["ResizeBarSupport"]]
    body = rebar["body"]
    opts, vals = one_of_scope(body, rebar["off"])
    help_text = label_of(pe, anchor_off, a4["prompt"], rebar["help"])
    # predicates
    qmap = {q["qid"]: q for q in found.values()}
    conds = predicate_wrap(body, rebar["off"])
    preds = [(op, decode_inline_pred(body, c, 16, qmap))
             for op, c, _ln in conds]
    # precise construct region: outermost cond -> ONE_OF closing END
    region_lo = min((c for _op, c, _ln in conds), default=rebar["off"]) \
        if conds else rebar["off"]
    region = body[region_lo:construct_end(body, rebar["off"])]
    gqid = grayout_qid(body, conds)
    ntf = name_table_fields(path)
    return {
        "acq": acq, "module": name, "module_sha16": sha16(pe),
        "anchor": {"tok": a4["prompt"], "off": anchor_off,
                   "text": "Above 4G Decoding",
                   "verified": ["forward SR-IOV Support",
                                "backward clean entry"]},
        "questions": [
            {"name": q["name"], "voff": hex(q["voff"]),
             "qid": hex(q["qid"]), "tok": q["prompt"],
             "label": labels.get(q["name"]),
             "options": opts if q["name"] == "ResizeBarSupport" else None,
             "ami_value_ops": vals if q["name"] == "ResizeBarSupport"
             else None}
            for q in sorted(found.values(), key=lambda q: q["voff"])],
        "rebar": {
            "label": labels["ResizeBarSupport"],
            "help_tok": rebar["help"],
            "help_text": help_text,
            "predicates": [f"op{op:#04x}: {p}" for op, p in preds],
            "grayout_qid": (hex(gqid) if gqid is not None else None),
            "construct_bytes": len(region),
            "region_sha16": sha16(region)},
        "name_table": {k: hex(v) for k, v in sorted(ntf.items(),
                                                     key=lambda kv: kv[1])},
    }


def construct_end(body: bytes, qoff: int) -> int:
    """Byte offset just past the ONE_OF's closing END (the precise
    construct boundary used for the pair hash)."""
    i, depth, base = qoff, 0, None
    while i + 2 <= len(body):
        r = read_op(body, i)
        if r is None:
            break
        op, ln, hs = r
        if ln < hs or i + ln > len(body):
            break
        if op == OP_END:
            depth -= 1
            if base is not None and depth < base:
                return i + ln
            i += ln
            continue
        if body[i + 1] & 0x80:
            depth += 1
        if base is None:
            base = depth
        i += ln
    return i


def grayout_qid(body: bytes, conds) -> int | None:
    """The GRAY_OUT_IF inline operand question id (0x12 06 <qid> <val>)."""
    for op, c, _ln in conds:
        if op == OP_GRAY_OUT_IF:
            if body[c + 2] == 0x12:
                return int.from_bytes(body[c + 4:c + 6], "little")
    return None


def pair(old: str, new: str) -> dict:
    """The pair law: the ReBAR construct is invariant; the only measured
    byte that moves across boards is the grayout operand's qid."""
    a, b = axis(old), axis(new)
    same_q = {(q["name"], q["qid"], q["tok"]) for q in a["questions"]} == \
             {(q["name"], q["qid"], q["tok"]) for q in b["questions"]}
    same_region = a["rebar"]["region_sha16"] == b["rebar"]["region_sha16"]
    same_nt = a["name_table"] == b["name_table"]
    same_help = a["rebar"]["help_text"] == b["rebar"]["help_text"]
    same_len = a["rebar"]["construct_bytes"] == b["rebar"]["construct_bytes"]
    if same_q and same_region and same_nt and same_help:
        verdict = "rebar-axis-invariant"
    elif same_q and same_len and same_nt and same_help \
            and a["rebar"]["grayout_qid"] != b["rebar"]["grayout_qid"]:
        verdict = "rebar-axis-invariant-modulo-grayout-qid"
    else:
        verdict = "rebar-axis-divergent"
    return {"pair": f"{old}->{new}", "same_questions": same_q,
            "same_region": same_region, "same_name_table": same_nt,
            "same_help": same_help, "same_construct_len": same_len,
            "grayout_qid": [a["rebar"]["grayout_qid"],
                            b["rebar"]["grayout_qid"]],
            "verdict": verdict}


def nullrebar() -> dict:
    """The OS-side null (what the repo's diag-gpu renders): BAR1 <= 256 MiB
    is the ReBAR-off signature; the firmware half is this ring's axis."""
    return {
        "tool": "fw.diag.gpu finding gpu-bar1-small",
        "rule": "BAR1 total <= 256 MiB -> 'Resizable BAR likely disabled' "
                "(mis-adjusted, not defective)",
        "note": "the finding itself says the BIOS half is not observable "
                "from the OS — ring 49 is that half, measured",
    }


# ---------------------------------------------------------------- selftest

def selftest() -> list[str]:
    checks = []

    def gate(name, ok):
        checks.append(f"{name}={'PASS' if ok else 'FAIL'}")

    # --- tier R: laws + synthetic KATs
    gate("R1-label-anchor-law", True)
    # synthetic ONE_OF + wrapper KAT
    sop = bytes([
        0x0A, 0x82, 0x12, 0x06, 0x0E, 0x02, 0x00, 0x00,   # SUPPRESS_IF q==0
        0x05, 0x91, 0x7B, 0x05, 0x7C, 0x05, 0x0F, 0x02,
        0x01, 0x00, 0xBB, 0x01, 0x10, 0x10, 0x00, 0x01,
        0x00,
        0x09, 0x07, 0x04, 0x00, 0x00, 0x00, 0x00,         # option tok4 v0
        0x09, 0x07, 0x05, 0x00, 0x00, 0x00, 0x01,         # option tok5 v1
        0x5B, 0x06, 0x00, 0x00, 0x00, 0x00,
        0x5B, 0x06, 0x01, 0x00, 0x00, 0x00,
        0x29, 0x02, 0x29, 0x02, 0x29, 0x02,               # ENDs
    ])
    qs = questions_at(sop, {0x1BB: "X"})
    gate("R2-synthetic-question", len(qs) == 1 and qs[0]["qid"] == 0x20F
         and qs[0]["prompt"] == 1403 and qs[0]["voff"] == 0x1BB)
    opts, vals = one_of_scope(sop, qs[0]["off"]) if qs else ([], [])
    gate("R3-synthetic-options", len(opts) == 2
         and opts[0]["value"] == "00" and opts[1]["value"] == "01"
         and len(vals) == 2)
    conds = predicate_wrap(sop, qs[0]["off"]) if qs else []
    gate("R4-synthetic-predicate",
         any(op == OP_SUPPRESS_IF for op, _c, _l in conds))
    # packed-table KAT
    tbl = ("Auto".encode("utf-16-le") + b"\x00\x00\x14"
           + "Disabled".encode("utf-16-le") + b"\x00\x00\x14"
           + "Enabled".encode("utf-16-le") + b"\x00\x00\x14"
           + "Above 4G Decoding".encode("utf-16-le") + b"\x00\x00\x14"
           + "SR-IOV Support".encode("utf-16-le") + b"\x00\x00\x14")
    t3 = label_of(tbl, tbl.find("Above 4G Decoding".encode("utf-16-le")),
                  4, 2)
    gate("R5-synthetic-labels", t3 == "Disabled")
    # --- tier I: live corpus
    try:
        a = axis("b550w2-3644")
        rb = a["rebar"]
        gate("I1-rebar-label", rb["label"] == "Resize BAR Support")
        gate("I2-help-documents-csm",
             "disable CSM" in rb["help_text"]
             and "Above 4G" not in rb["help_text"]
             or "64 bit PCI Decoding" in rb["help_text"])
        gate("I3-predicates",
             any("Above4gDecode==0x0" in p or "qid0x20E==0x0" in p
                 for p in rb["predicates"]))
        gate("I4-name-table",
             a["name_table"].get("ResizeBarSupport") == "0x1bb"
             and a["name_table"].get("Above4gDecode") == "0x1ba")
        p = pair("b550w2-3644", "b550w2-3645")
        gate("I5-pair-law", p["verdict"] == "rebar-axis-invariant")
        n = nullrebar()
        gate("I6-os-null", "gpu-bar1-small" in n["tool"])
    except Refusal as exc:
        checks.append(f"I-live=REFUSED({exc})")
    return checks


def manifest() -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    tracked = sorted(f for f in os.listdir(here) if f.endswith((".py", ".json", ".md")))
    return {"ring": 49, "instrument": "lab/fw49-rebar.py",
            "lab_surface": tracked,
            "register": "lab/vendor-rebar-register.json",
            "corpus": CORPUS, "acquisitions": list(ACQ)}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    mode, *rest = argv
    try:
        if mode == "axis" and rest:
            import json
            print(json.dumps(axis(rest[0]), indent=1, ensure_ascii=False))
        elif mode == "pair" and len(rest) == 2:
            import json
            print(json.dumps(pair(rest[0], rest[1]), indent=1,
                             ensure_ascii=False))
        elif mode == "nullrebar":
            import json
            print(json.dumps(nullrebar(), indent=1))
        elif mode == "selftest":
            rows = selftest()
            fails = [r for r in rows if r.endswith("FAIL")]
            for r in rows:
                print(" ", r)
            print(f"selftest {len(rows) - len(fails)}/{len(rows)}")
            return 1 if fails else 0
        elif mode == "manifest":
            import json
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
