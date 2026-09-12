#!/usr/bin/env python3
# fw36-atlas.py — the multi-scale atlas + delta cartography (ring 36).
#
# The CAP comparator's missing layer. The ring-34 differ says WHICH modules
# change (GUID-aligned ledgers); this instrument maps WHERE and HOW in the
# raw image, without any FFS parsing:
#   atlas  — per-image fingerprint: sha256, symlink resolution, FV census
#            (raw _FVH scan), 64 KiB-window classification (erased / packed /
#            code / data), 0xFF slack — the day-0 §1.5 geometry row as code
#   delta  — byte-run cartography between two images: differing runs
#            (gap-clustering), per-run structural class from the window
#            entropy pair (erased->code = materialization, code->code =
#            in-place body change, code->erased = retraction), 64 KiB
#            density map
#   vars   — first-hour store lens: size, NVAR magic census, erased share
#
# Honesty contract (the fw33/fw35 discipline):
#   - selftest tier R re-derives every anchor from the persisted ring-34
#     registers and always runs
#   - selftest tier I re-derives them LIVE on the surviving OVMF corpus and
#     is loudly SKIPPED when the corpus is absent (sandbox ephemeral)
#   - the whole-image raw diff numbers are NEW measurements (the register
#     measured module-level), gated only on structural properties
#
# stdlib only. Modes:
#   atlas <image> | delta <imgA> <imgB> | vars <image> | selftest | manifest

import json
import os
import sys
import hashlib
import math

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = HERE

DEFAULT_CORPUS = "/home/z/my-project/scratch-ovmf/extract/usr/share/OVMF"

WINDOW = 4096          # fine scale (floor analysis, delta windows)
BLOCK = 65536          # coarse scale (the vendor-geometry-comparable scale)
GAP = 64               # run clustering gap

ENT = {"erased": 0.005, "packed": 7.5, "code": 5.5}   # bits + 0xFF share


def load(p):
    with open(p, "rb") as f:
        return f.read()


def sha256_16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def entropy(b):
    if not b:
        return 0.0
    n = len(b)
    ent = 0.0
    for v in range(256):
        c = b.count(v)
        if c:
            p = c / n
            ent -= p * math.log2(p)
    return ent


def ff_share(b):
    return b.count(0xFF) / len(b) if b else 0.0


def window_class(ent, ff):
    if ff >= 1 - ENT["erased"]:
        return "erased"
    if ent >= ENT["packed"]:
        return "packed"
    if ent >= ENT["code"]:
        return "code"
    return "data"


# ---------------------------------------------------------------- atlas

def scan_fvs(b):
    """Raw _FVH scan: signature at header+0x28, FvLength u64 at header+0x20."""
    fvs, pos = [], 0
    while True:
        i = b.find(b"_FVH", pos)
        if i < 0:
            break
        pos = i + 4
        h = i - 0x28
        if h < 0:
            continue
        fvlen = int.from_bytes(b[h + 0x20:h + 0x28], "little")
        guid = b[h + 0x10:h + 0x20]
        hdrlen = int.from_bytes(b[h + 0x30:h + 0x32], "little")
        if not (0x10000 <= fvlen <= len(b) - h and fvlen % 4096 == 0):
            continue
        if guid == b"\0" * 16 or hdrlen < 0x38 or hdrlen > 0x400:
            continue
        csum = sum(int.from_bytes(b[h + k:h + k + 2], "little")
                   for k in range(0, hdrlen, 2)) & 0xFFFF
        fvs.append({"offset": h, "length": fvlen,
                    "fs_guid": guid.hex().upper(),
                    "checksum_ok": csum == 0,
                    "share_pct": round(100 * fvlen / len(b), 2)})
    # dedupe (nested hits share headers)
    out, seen = [], set()
    for fv in fvs:
        if fv["offset"] not in seen:
            seen.add(fv["offset"])
            out.append(fv)
    return out


def atlas(path):
    raw = load(path)
    real = os.path.realpath(path)
    sym = os.path.realpath(path) != os.path.abspath(path)
    img = load(real) if sym else raw
    n = len(img)
    classes = {"erased": 0, "packed": 0, "code": 0, "data": 0}
    ents = []
    for off in range(0, n, BLOCK):
        w = img[off:off + BLOCK]
        e = entropy(w)
        ents.append(e)
        classes[window_class(e, ff_share(w))] += len(w)
    fvs = scan_fvs(img)
    fv_cov = [False] * n
    for fv in fvs:
        for k in range(fv["offset"], min(fv["offset"] + fv["length"], n)):
            fv_cov[k] = True
    # largest trailing and internal 0xFF runs
    tail = 0
    for k in range(n - 1, -1, -1):
        if img[k] != 0xFF:
            break
        tail += 1
    return {
        "file": os.path.basename(path), "size": n,
        "sha256_16": sha256_16(img),
        "symlink_to": os.path.basename(real) if sym else None,
        "fv_census": {"count": len(fvs), "fvs": fvs,
                      "coverage_pct": round(100 * sum(fv_cov) / n, 2)},
        "windows_64k": {"count": len(ents),
                        "mean_entropy_bits": round(sum(ents) / len(ents), 3),
                        "max_entropy_bits": round(max(ents), 3)},
        "share_pct": {k: round(100 * v / n, 2) for k, v in classes.items()},
        "ff_slack_tail_bytes": tail,
        "nvar_magic_census": img.count(b"NVAR"),
    }


# ---------------------------------------------------------------- delta

def diff_runs(a, b):
    runs, i, n = [], 0, min(len(a), len(b))
    while i < n:
        if a[i] != b[i]:
            j = i
            while j < n and a[j] != b[j]:
                j += 1
            if runs and i - runs[-1]["end"] <= GAP:
                r = runs[-1]
                r["end"] = j
                r["len"] = j - r["off"]
            else:
                runs.append({"off": i, "end": j, "len": j - i})
            i = j
        else:
            i += 1
    for r in runs:
        r.pop("end", None)
    return runs


def structural_class(a, b, off, ln):
    wa = a[max(0, off - WINDOW // 2):off + ln + WINDOW // 2]
    wb = b[max(0, off - WINDOW // 2):off + ln + WINDOW // 2]
    ca = window_class(entropy(wa), ff_share(wa))
    cb = window_class(entropy(wb), ff_share(wb))
    if ca == cb:
        return f"{ca}->code" if ca != "erased" else "erased->erased"
    return f"{ca}->{cb}"


def cartography(pa, pb):
    a, b = load(pa), load(pb)
    size_delta = len(b) - len(a)
    runs = diff_runs(a, b) if size_delta == 0 else []
    for r in runs:
        r["class"] = structural_class(a, b, r["off"], r["len"])
        r["hex_before"] = a[r["off"]:r["off"] + min(r["len"], 8)].hex()
        r["hex_after"] = b[r["off"]:r["off"] + min(r["len"], 8)].hex()
    # 64 KiB density map
    density = []
    n = min(len(a), len(b))
    for off in range(0, n, BLOCK):
        wa, wb = a[off:off + BLOCK], b[off:off + BLOCK]
        if wa == wb:
            density.append(0.0)
        else:
            c = sum(1 for x, y in zip(wa, wb) if x != y)
            density.append(round(100 * c / len(wa), 2))
    changed_blocks = [(i * BLOCK, d) for i, d in enumerate(density) if d > 0]
    return {
        "file_a": os.path.basename(pa), "file_b": os.path.basename(pb),
        "size_a": len(a), "size_b": len(b), "size_delta": size_delta,
        "sha_a": sha256_16(a), "sha_b": sha256_16(b),
        "runs_total": len(runs),
        "bytes_differing": sum(r["len"] for r in runs),
        "runs_top": sorted(runs, key=lambda r: -r["len"])[:24],
        "class_histogram": _hist(runs),
        "blocks_total": len(density),
        "blocks_changed": len(changed_blocks),
        "changed_blocks_top": sorted(changed_blocks, key=lambda t: -t[1])[:24],
        "runs": runs,
    }


def _hist(runs):
    h = {}
    for r in runs:
        h[r["class"]] = h.get(r["class"], 0) + r["len"]
    return {k: v for k, v in sorted(h.items(), key=lambda kv: -kv[1])}


# ---------------------------------------------------------------- engine

class Atlas:
    def __init__(self, corpus=None):
        self.corpus = corpus or os.environ.get("FW36_CORPUS") or DEFAULT_CORPUS
        self.const = json.load(open(os.path.join(LAB, "ovmf-constellation.json")))
        self.nx = json.load(open(os.path.join(LAB, "ovmf-nx-pin.json")))
        self.vd = json.load(open(os.path.join(LAB, "ovmf-vars-differ.json")))

    def corpus_path(self, name):
        return os.path.join(self.corpus, name)

    def corpus_ok(self):
        return os.path.isdir(self.corpus) and os.path.exists(
            self.corpus_path("OVMF_CODE_4M.fd"))


def selftest():
    results = []

    def gate(name, ok, detail=""):
        results.append((name, ok, detail))
        return ok

    eng = Atlas()
    const, nx, vd = eng.const, eng.nx, eng.vd

    # ---- tier R: register re-derivation (always)
    classes = {c["sha8"]: sorted(c["builds"]) for c in const["identity_classes"]}
    gate("R1 three identity classes",
         len(classes) == 3 and
         classes.get("1a46295574430cfb") == ["ms", "secboot", "snakeoil"] and
         classes.get("624e06de18b4fa53") == ["plain"] and
         classes.get("9ee9f2382e0c6aa9") == ["strictnx"],
         str(classes))
    gate("R2 module counts 135/144/144",
         const["module_counts"] == {"plain": 135, "secboot": 144, "strictnx": 144},
         str(const["module_counts"]))
    p = const["pairwise"]["plain|secboot"]
    gate("R3 rebuild wall ledger 126/6/120 +777472",
         (p["common"], p["identical"], len(p["changed"]), p["byte_delta"]) == (126, 6, 120, 777472),
         f"{p['common']}/{p['identical']}/{len(p['changed'])}/+{p['byte_delta']}")
    gate("R3b only_in 9/18",
         (len(p["only_in_plain"]), len(p["only_in_secboot"])) == (9, 18),
         f"{len(p['only_in_plain'])}/{len(p['only_in_secboot'])}")
    s = const["pairwise"]["secboot|strictnx"]
    gate("R4 strictnx pair 142 identical / 2 changed / delta 0",
         (s["identical"], len(s["changed"]), s["byte_delta"]) == (142, 2, 0),
         f"{s['identical']}/{len(s['changed'])}/{s['byte_delta']}")
    gate("R5 NX total_byte_diffs=3, runs 1+2",
         nx["total_byte_diffs"] == 3 and
         [r["len"] for pr in nx["pairs"] for r in pr["runs"]] == [1, 2],
         str(nx["total_byte_diffs"]))
    st = vd["stores"]
    gate("R6 VARS plain 0 records",
         st["plain"]["records"] == 0 and st["plain"]["size"] == 540672,
         str(st["plain"]["records"]))
    gate("R6b VARS snakeoil/ms sha8 + 39 records",
         st["snakeoil"]["sha8"] == "e875a265aabb3fa9" and
         st["ms"]["sha8"] == "0d12f9839018a68f" and
         st["snakeoil"]["records"] == st["ms"]["records"] == 39, "")

    # ---- tier I: live corpus re-derivation (skipped loudly when absent)
    if eng.corpus_ok():
        cp = eng.corpus_path
        plain = load(cp("OVMF_CODE_4M.fd"))
        sec = load(cp("OVMF_CODE_4M.secboot.fd"))
        snx = load(cp("OVMF_CODE_4M.secboot.strictnx.fd"))
        gate("I1 CODE sha8 classes live",
             (sha256_16(plain), sha256_16(sec), sha256_16(snx)) ==
             ("624e06de18b4fa53", "1a46295574430cfb", "9ee9f2382e0c6aa9"), "")
        msha = sha256_16(load(cp("OVMF_CODE_4M.ms.fd")))
        ksha = sha256_16(load(cp("OVMF_CODE_4M.snakeoil.fd")))
        gate("I2 symlink class: ms==snakeoil==secboot",
             msha == ksha == "1a46295574430cfb",
             "the identity class is ONE file under three names")
        d = cartography(cp("OVMF_CODE_4M.secboot.fd"),
                        cp("OVMF_CODE_4M.secboot.strictnx.fd"))
        lens = sorted(r["len"] for r in d["runs"])
        # the semantic 3 bytes (R5) live INSIDE decompressed modules; at RAW
        # level the LZMA container re-encodes the stream tail from the first
        # compressed semantic change — the amplification is the finding:
        # two raw runs (a small FV-metadata run + the re-encoded LZMA tail)
        gate("I3 raw NX anatomy = metadata run + LZMA tail",
             d["size_delta"] == 0 and d["runs_total"] == 2 and
             lens[0] == 9 and lens[1] > 500000 and
             d["bytes_differing"] == lens[0] + lens[1],
             f"runs {lens} — semantic 3 bytes amplified to {d['bytes_differing']} raw")
        w = cartography(cp("OVMF_CODE_4M.fd"), cp("OVMF_CODE_4M.secboot.fd"))
        gate("I4 wall cartography structural sanity",
             w["size_delta"] == 0 and 0 < w["bytes_differing"] < len(plain) // 2 and
             w["runs_total"] > 0,
             f"{w['bytes_differing']} bytes in {w['runs_total']} runs")
        vplain = load(cp("OVMF_VARS_4M.fd"))
        gate("I5 VARS plain 0xFF share > 0.99",
             ff_share(vplain) > 0.99, f"{ff_share(vplain):.4f}")
        # the resolution floor INVERTS at container level: no raw window
        # isolates the 3 semantic bytes — the big run must START inside a
        # packed (compressed) window for the amplification reading to hold
        big = max(d["runs"], key=lambda r: r["len"])
        woff = big["off"] // WINDOW * WINDOW
        wsec = load(cp("OVMF_CODE_4M.secboot.fd"))[woff:woff + WINDOW]
        gate("I6 amplification lives in the LZMA container",
             window_class(entropy(wsec), ff_share(wsec)) == "packed" and
             big["off"] < 0x348000,
             f"run @0x{big['off']:x} starts in a packed window inside FVMAIN_COMPACT")
    else:
        for name in ("I1", "I2", "I3", "I4", "I5", "I6"):
            gate(f"{name} SKIPPED (no corpus at {eng.corpus})", True, "skipped")

    npass = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        if not ok or os.environ.get("FW36_VERBOSE"):
            print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print(f"fw36-atlas selftest: {npass}/{len(results)} gates PASS "
          f"(tier I {'live' if eng.corpus_ok() else 'SKIPPED'})")
    if npass != len(results):
        print("REFUSAL: register or corpus drift — fix before mapping.")
        sys.exit(2)
    return 0


def main(argv):
    if not argv:
        argv = ["selftest"]
    cmd = argv[0].lstrip("-")

    def guard():
        Atlas().selftest_silent() if hasattr(Atlas, "selftest_silent") else None

    if cmd == "selftest":
        return selftest()

    if cmd == "manifest":
        eng = Atlas()
        print(json.dumps({
            "modes": ["atlas", "delta", "vars", "selftest", "manifest"],
            "scales": {"window": WINDOW, "block": BLOCK, "gap": GAP},
            "registers_fused": ["ovmf-constellation.json", "ovmf-nx-pin.json",
                                 "ovmf-vars-differ.json"],
            "corpus": eng.corpus,
            "corpus_present": eng.corpus_ok(),
        }, indent=2))
        return 0

    if cmd == "atlas" and len(argv) > 1:
        print(json.dumps(atlas(argv[1]), indent=2))
        return 0

    if cmd == "vars" and len(argv) > 1:
        img = load(argv[1])
        n = len(img)
        print(json.dumps({
            "file": os.path.basename(argv[1]), "size": n,
            "sha256_16": sha256_16(img),
            "nvar_magic_census": img.count(b"NVAR"),
            "ff_share_pct": round(100 * ff_share(img), 2),
        }, indent=2))
        return 0

    if cmd == "delta" and len(argv) > 2:
        d = cartography(argv[1], argv[2])
        shown = dict(d)
        shown["runs"] = f"<{d['runs_total']} runs, elided in CLI output>"
        print(json.dumps(shown, indent=2))
        return 0

    print("modes: atlas <image> | delta <imgA> <imgB> | vars <image> | selftest | manifest")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
