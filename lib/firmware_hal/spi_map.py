"""spi-map — the map of the invisible: read-only cartography of the SPI flash.

Everything this tool normally reads (sysfs, SMBIOS, dmidecode, MSR,
fwupd) stops at the frontier of the flash chip. Below that frontier live
the firmware volumes, the DXE and SMM modules, the variable stores, the
ME/PSP region and the boot manifests — the "things never seen" of the
study, where the vol. 4 pathologies sit at the source.

The founding rule is restated with a stricter accent:

  +0 octet means ZERO BYTES WRITTEN. This module only reads — ever.
  The read itself is an EXPLICIT deep probe: it never runs by default,
  `capture` only does it when the human passes --spi-read, and it is
  deliberately NOT part of the MCP surface (an SPI read is a declared
  gesture, not an ambient tool).

Sources, in priority order:
  1. dump_path argument  — analyse an existing dump file (offline);
  2. FW_SPI_DUMP env     — the fixture/CI form (same, injected);
  3. `flashrom -r`       — the live read: root required, the chip is
     read twice by flashrom itself (read + verify), the temporary dump
     is deleted after parsing unless --save-dump keeps a copy.

What is parsed (stdlib only, every heuristic labelled):
  - the Intel flash descriptor (FLVALSIG, FLMAP0/FRBA, FLREG regions);
    region names follow the Intel PCH convention — on AMD platforms the
    "ME" region carries the PSP/AGESA blobs instead;
  - firmware volumes (the '_FVH' signature, header checksum verified),
    classified by filesystem GUID (FFS2/FFS3/NV stores);
  - FFS files inside FFS2/FFS3 volumes: counts by type, plus the DXE
    and SMM modules with their GUIDs and, when present, their UI names;
  - variable-store FVs: variable NAMES by utf-16 heuristic (labels only);
  - the ME region: presence, size, best-effort ASCII version guess;
  - boot manifests: BPM/KM signature presence — the fused-vs-deactivated
    state is NOT determinable from the image alone, and the tool says so.

A failed read is reported ("unavailable"), never guessed; nothing here
ever writes to the chip, to NVRAM, to the ESP or anywhere else.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

SCHEMA = "omarchy-firmware/spi-map@1"

_FLSIG = 0x0FF0A55A  # FLVALSIG — the Intel flash descriptor marker

FFS2_GUID = "8C8CE578-8A3D-4F1C-9935-896185C32DD3"
FFS3_GUID = "5473C07A-3DCB-4DCA-BD6F-1E9689E7349A"
_FS_GUID_NAMES = {
    FFS2_GUID: "FFS2 (PI firmware filesystem v2)",
    FFS3_GUID: "FFS3 (PI firmware filesystem v3)",
    "EE4E5898-3914-4259-9D6E-DC7BD79403CF": "system NV data store",
    "FFF12B8D-7696-4C8B-A985-2747075B4F50": "variable store (EVSA)",
    "AAF32C78-947B-439A-A180-2E144EC37792": "authenticated variable store",
}
_NV_STORE_GUIDS = {"EE4E5898-3914-4259-9D6E-DC7BD79403CF",
                   "FFF12B8D-7696-4C8B-A985-2747075B4F50",
                   "AAF32C78-947B-439A-A180-2E144EC37792"}

_FILE_TYPES = {
    0x01: "raw", 0x02: "freeform", 0x03: "sec_core", 0x04: "pei_core",
    0x05: "dxe_core", 0x06: "peim", 0x07: "dxe_driver",
    0x08: "combined_peim_driver", 0x09: "application", 0x0A: "smm_driver",
    0x0B: "fv_image", 0x0C: "combined_smm_dxe", 0x0D: "smm_core", 0xF0: "pad",
}
_DXE_TYPES = {0x07, 0x0C}
_SMM_TYPES = {0x0A, 0x0D}
_NAMED_TYPES = ({0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0C, 0x0D})

_MAX_FVS = 48
_MAX_FILES_PER_FV = 2048
_MAX_DXE = 256
_MAX_SMM = 128
_MAX_NVRAM_NAMES = 120

_VERSION_RE = re.compile(rb"(?<!\d)\d{1,4}\.\d{1,4}\.\d{1,4}\.\d{1,4}(?!\d)")
_UTF16_RUN = re.compile(rb"(?:[\x20-\x7e]\x00){3,}")
_ZERO_GUID = "00000000-0000-0000-0000-000000000000"


def _guid(b: bytes) -> str:
    """EFI GUID — first three fields little-endian, the rest raw."""
    return (f"{int.from_bytes(b[0:4], 'little'):08X}-"
            f"{int.from_bytes(b[4:6], 'little'):04X}-"
            f"{int.from_bytes(b[6:8], 'little'):04X}-"
            f"{b[8]:02X}{b[9]:02X}-" + b[10:16].hex().upper())


# ------------------------------------------------------------- descriptor


def _parse_descriptor(img: bytes) -> dict:
    out: dict = {"present": False}
    if len(img) < 0x100:
        out["note"] = "image too small for a descriptor map"
        return out
    if int.from_bytes(img[0x10:0x14], "little") != _FLSIG:
        out["note"] = ("no Intel flash descriptor (FLVALSIG) — descriptorless "
                       "image (coreboot-style) or a partial region dump")
        return out
    flmap0 = int.from_bytes(img[0x40:0x44], "little")
    frba = ((flmap0 >> 12) & 0xFF) << 4
    nr = (flmap0 >> 24) & 0x07
    if frba < 0x40 or frba + 20 > len(img) or nr == 0:
        out["note"] = "descriptor present but the region map is unreadable"
        return out
    names = ["descriptor", "BIOS", "ME", "GbE", "platform_data"]
    regions = []
    for i in range(5):
        fl = int.from_bytes(img[frba + 4 * i:frba + 4 * i + 4], "little")
        base = (fl & 0x7FFF) << 12                      # ICH_FREG_BASE
        limit = (((fl >> 16) & 0x7FFF) << 12) | 0xFFF   # ICH_FREG_LIMIT
        used = fl != 0 and base <= limit
        regions.append({
            "name": names[i] if i < len(names) else f"region_{i}",
            "base": base, "limit": limit,
            "size_bytes": (limit - base + 1) if used else 0,
            "used": used,
        })
    out["present"] = True
    out["regions"] = regions
    out["note"] = ("region names follow the Intel PCH convention; on AMD "
                   "platforms the 'ME' region carries the PSP/AGESA blobs; "
                   "classic FLREG interpretation — a zeroed register may "
                   "show as an unused region")
    return out


# --------------------------------------------------------- firmware volumes


def _ffs_inventory(img: bytes, fv_off: int, fv_len: int, hlen: int) -> dict:
    end = fv_off + fv_len
    off = fv_off + hlen
    by_type: dict[str, int] = {}
    dxe: list[dict] = []
    smm: list[dict] = []
    total = 0
    while off + 24 <= end and total < _MAX_FILES_PER_FV:
        ftype = img[off + 18]
        size = img[off + 20] | (img[off + 21] << 8) | (img[off + 22] << 16)
        state = img[off + 23] ^ 0xFF                    # state bits are active-low
        if size == 0xFFFFFF:
            if off + 32 > end:
                break
            size = int.from_bytes(img[off + 24:off + 32], "little")
            hlen_f = 32
        else:
            hlen_f = 24
        if size < hlen_f or off + size > end:
            break
        if state & 0x07 != 0x07:                        # header not valid
            break
        total += 1
        tname = _FILE_TYPES.get(ftype, f"type_{ftype:#04x}")
        by_type[tname] = by_type.get(tname, 0) + 1
        if state & 0x10 == 0 and ftype in _NAMED_TYPES:
            entry = {"guid": _guid(img[off:off + 16]),
                     "name": _ui_name(img, off + hlen_f, size - hlen_f)}
            if ftype in _DXE_TYPES and len(dxe) < _MAX_DXE:
                dxe.append(entry)
            elif ftype in _SMM_TYPES and len(smm) < _MAX_SMM:
                smm.append(entry)
        off = (off + size + 7) & ~7                     # files are 8-byte aligned
    return {"total": total, "by_type": by_type, "dxe": dxe, "smm": smm,
            "dxe_truncated": total >= _MAX_FILES_PER_FV,
            "smm_truncated": len(smm) >= _MAX_SMM}


def _ui_name(img: bytes, off: int, length: int) -> str | None:
    """The USER_INTERFACE section name (utf-16le) of one FFS file."""
    stop = off + length
    p = off
    while p + 4 <= stop:
        ssize = img[p] | (img[p + 1] << 8) | (img[p + 2] << 16)
        stype = img[p + 3]
        if ssize < 4 or p + ssize > stop:
            break
        if stype == 0x15:
            raw = img[p + 4:p + ssize]
            try:
                # decode first, THEN cut at the null — a byte-level split on
                # b"\x00\x00" would eat the final character whenever its own
                # high byte is 0 (every ASCII name ends that way)
                s = raw.decode("utf-16-le", "replace").split("\x00", 1)[0]
            except UnicodeDecodeError:
                return None
            s = "".join(ch for ch in s if 32 <= ord(ch) < 127).strip()
            return s or None
        p = (p + ssize + 3) & ~3                        # sections are 4-byte aligned
    return None


def _scan_fvs(img: bytes, regions: list[dict]) -> list[dict]:
    fvs: list[dict] = []
    spans: list[tuple[int, int]] = []
    pos = 0
    while len(fvs) < _MAX_FVS:
        idx = img.find(b"_FVH", pos)
        if idx < 0:
            break
        pos = idx + 4
        hdr = idx - 0x28                                # signature sits at +0x28
        if hdr < 0 or hdr % 8:
            continue
        fs_guid = _guid(img[hdr + 0x10:hdr + 0x20])
        if fs_guid == _ZERO_GUID:
            continue
        fv_len = int.from_bytes(img[hdr + 0x20:hdr + 0x28], "little")
        hlen = int.from_bytes(img[hdr + 0x30:hdr + 0x32], "little")
        if not 0x48 <= hlen <= 0x600 or hlen % 2:
            continue
        if fv_len < hlen or hdr + fv_len > len(img) or fv_len > 0x2000000:
            continue
        csum = 0
        for i in range(0, hlen, 2):
            csum = (csum + int.from_bytes(img[hdr + i:hdr + i + 2], "little")) & 0xFFFF
        if csum != 0:                                   # header checksum must close
            continue
        if any(s <= hdr < e for s, e in spans):
            continue
        entry: dict = {"offset": hdr, "length": fv_len, "fs_guid": fs_guid,
                       "filesystem": _FS_GUID_NAMES.get(fs_guid, "unknown filesystem")}
        region = next((r["name"] for r in regions if r.get("used")
                       and r["base"] <= hdr <= r["limit"]), None)
        if region:
            entry["region"] = region
        if fs_guid in (FFS2_GUID, FFS3_GUID):
            inv = _ffs_inventory(img, hdr, fv_len, hlen)
            entry["files"] = inv["total"]
            entry["by_type"] = inv["by_type"]
            if inv["dxe"]:
                entry["dxe_drivers"] = inv["dxe"]
            if inv["smm"]:
                entry["smm_drivers"] = inv["smm"]
            if inv["dxe_truncated"] or inv["smm_truncated"]:
                entry["list_truncated"] = True
        elif fs_guid in _NV_STORE_GUIDS:
            names: list[str] = []
            for m in _UTF16_RUN.finditer(img[hdr + hlen:hdr + fv_len]):
                s = m.group(0).decode("utf-16-le", "replace")
                if s not in names:
                    names.append(s)
                if len(names) >= _MAX_NVRAM_NAMES:
                    entry["nvram_truncated"] = True
                    break
            entry["nvram_names"] = names
            entry["nvram_method"] = "heuristic utf-16 strings"
        fvs.append(entry)
        spans.append((hdr, hdr + fv_len))
    return fvs


# --------------------------------------------------------------- regions


def _me_probe(img: bytes, regions: list[dict]) -> dict:
    me = next((r for r in regions if r["name"] == "ME" and r.get("used")), None)
    if me is None:
        return {"region_present": False,
                "note": "no ME region in the descriptor map "
                        "(AMD boards carry PSP there instead)"}
    out: dict = {"region_present": True, "base": me["base"],
                 "size_bytes": me["size_bytes"]}
    body = img[me["base"]:me["limit"] + 1]
    idx = body.find(b"$MN2")
    out["manifest"] = "$MN2 manifest found" if idx >= 0 else "no $MN2 manifest found"
    out["version_guess"] = None
    if idx >= 0:
        m = _VERSION_RE.search(body[idx:idx + 0x400])
        if m:
            out["version_guess"] = m.group(0).decode("ascii", "replace")
    out["note"] = "the version is an ASCII heuristic inside the manifest, not a parsed structure"
    return out


def _boot_guard_probe(img: bytes, regions: list[dict]) -> dict:
    bios = next((r for r in regions if r["name"] == "BIOS" and r.get("used")), None)
    body = img[bios["base"]:bios["limit"] + 1] if bios else img
    bpm, km = b"$BPM" in body, b"$KSH" in body
    return {
        "bpm_found": bpm, "km_found": km,
        "status": ("Boot Guard manifests found in the BIOS region"
                   if bpm or km else
                   "no Intel Boot Guard manifests — expected on AMD boards "
                   "(the PSP signs the AGESA blobs instead)"),
        "note": "the fused-vs-deactivated state is NOT determinable from "
                "the image alone — the FPF fuses are not readable here",
    }


# ---------------------------------------------------------------- reading


def _read_live(save_dump: str | None):
    """One flashrom read. Reads twice (read + verify), writes never."""
    t0 = time.perf_counter()
    ms = lambda: round((time.perf_counter() - t0) * 1000.0, 1)
    if shutil.which("flashrom") is None:
        return None, None, ms(), ("flashrom is not installed (pacman -S "
                                  "flashrom) — or analyse an existing dump "
                                  "via --dump / FW_SPI_DUMP"), None
    fd, tmp = tempfile.mkstemp(prefix="omarchy-firmware-spi-", suffix=".bin")
    os.close(fd)
    try:
        try:
            proc = subprocess.run(["flashrom", "-r", tmp],
                                  capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            return None, None, ms(), "flashrom timed out after 120 s — " \
                                     "read aborted, nothing written", None
        except OSError as exc:
            return None, None, ms(), f"flashrom could not be run: {exc}", None
        if proc.returncode != 0:
            out = (proc.stderr or proc.stdout or b"").decode("utf-8", "replace")
            tail = [l for l in out.strip().splitlines() if l.strip()]
            reason = tail[-1][:160] if tail else f"rc={proc.returncode}"
            return None, None, ms(), (f"flashrom failed (rc={proc.returncode}): "
                                      f"{reason} — typically: run as root, or "
                                      "kernel lockdown blocks /dev/mem "
                                      "(Secure Boot on?)"), None
        if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
            return None, None, ms(), ("flashrom reported success but produced "
                                      "no dump — refusing to guess"), None
        if save_dump:
            shutil.copyfile(tmp, save_dump)
        return Path(tmp).read_bytes(), "flashrom-live", ms(), None, \
            (save_dump if save_dump else None)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def collect(dump_path: str | None = None, save_dump: str | None = None) -> dict:
    """The SPI cartography — read-only, explicit, honest."""
    t0 = time.perf_counter()
    out: dict = {"schema": SCHEMA, "read_only": True, "bytes_written": 0}
    img: bytes | None = None
    origin: str | None = None
    ms_read = 0.0
    err: str | None = None

    if dump_path:
        try:
            img = Path(dump_path).read_bytes()
            origin, out["image_source"] = "file", str(dump_path)
        except OSError as exc:
            err = f"dump unreadable: {exc}"
    elif os.environ.get("FW_SPI_DUMP"):
        env = os.environ["FW_SPI_DUMP"]
        try:
            img = Path(env).read_bytes()
            origin, out["image_source"] = "file", env
            out["note"] = "dump injected via FW_SPI_DUMP — flashrom not invoked"
        except OSError as exc:
            err = f"FW_SPI_DUMP unreadable: {exc}"
    else:
        img, origin, ms_read, err, kept = _read_live(save_dump)
        if kept:
            out["dump_saved"] = kept

    if img is None:
        out["status"] = "unavailable"
        out["reason"] = err or "no image source"
        out["ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        return out

    desc = _parse_descriptor(img)
    regions = desc.get("regions") or []
    fvs = _scan_fvs(img, regions)
    nv_total = sum(len(fv.get("nvram_names") or []) for fv in fvs)
    dxe_total = sum(len(fv.get("dxe_drivers") or []) for fv in fvs)
    smm_total = sum(len(fv.get("smm_drivers") or []) for fv in fvs)
    ffs_total = sum(fv.get("files", 0) for fv in fvs)

    out.update(
        status="ok",
        origin=origin,
        ms_read=ms_read,
        image={"size_bytes": len(img),
               "sha256": hashlib.sha256(img).hexdigest()},
        descriptor=desc,
        firmware_volumes=fvs,
        summary={"fv_count": len(fvs), "ffs_files": ffs_total,
                 "dxe_drivers": dxe_total, "smm_drivers": smm_total,
                 "nvram_names": nv_total},
        nvram={"method": "heuristic utf-16 strings in variable-store FVs",
               "count": nv_total,
               "names": [n for fv in fvs for n in fv.get("nvram_names", [])]},
        me=_me_probe(img, regions),
        boot_guard=_boot_guard_probe(img, regions),
        notes=[
            "everything below the runtime frontier is read from the image; "
            "no write of any kind reaches the chip",
            "counts are structural (headers), names are heuristics — both "
            "are labelled, neither is guessed beyond its label",
        ],
        ms=round((time.perf_counter() - t0) * 1000.0, 1),
    )
    return out
