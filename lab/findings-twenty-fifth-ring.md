# The twenty-fifth ring — the lens is code, the wall falls, and the boot speaks

*Volume 5's software wing finishes what ring 24 registered: the CBFS lens
becomes an independent instrument, the "no QEMU without root" wall falls by
the same deb-extraction lane that beat iasl and libgcc, and the image we
built boots — then confirms the static census by consuming it.*

Date: 2026-09-12 · Hardware touched: none · Bytes written to any SPI chip: 0

---

## Front 25a — the CBFS lens as code (`lab/vol5-cbfs-census.json`)

Ring 24's photograph registered the instrument task verbatim: the repo's
`fw.spi.map` reads the vendor PI/FFS world natively and honestly reports
**zero FVs** on a coreboot image — photographing the CBFS world needed its
own lens, which existed only in rehearsal form (`cbfstool print`). This ring
writes the lens as standalone code (`scripts/vol5_cbfs_lens.py`), spec-fresh
under the house rule: constants are **imported at runtime** by parsing the
25.12 tree's own headers (`src/commonlib/bsd/include/commonlib/bsd/
cbfs_serialized.h`, `fmap_serialized.h` — both sha256-recorded in the
artifact); nothing is transcribed from memory, and every packed-layout
assumption is validated by exact consumption on the real image.

The lens walks the full stack and closes it:

- **FMAP first.** Four `__FMAP__` signature hits exist in the image — one
  header and three string literals compiled into stage error messages. The
  lens validates candidates by header semantics (version, area count,
  bounds) and registers the rejects: position alone would have parsed the
  bootblock's own error strings as firmware tables. Result: FMAP "FLASH"
  v1.1 at file offset 0x0, `base 0x0`, three areas — BIOS (0x0, 8 MiB),
  FMAP (0x0, 512 B), COREBOOT (0x1000, 8,384,512 B).
- **CBFS discovery, two independent paths.** The canonical pointer in the
  last four bytes is x86-native little-endian and resolves to 0x102C; the
  CBFS metadata it points to is **big-endian** (the header's own comments
  say so: 'ORBC', '1112'). Both facts measured, neither assumed. On this
  image the master header struct is not bare — it is wrapped as the DATA of
  a `cbfs_master_header` entry (type `CBFS_TYPE_CBFSHEADER`), which the
  lens locates and validates before walking.
- **The walk.** Thirteen entries from the aligned end of the master entry:
  romstage, ramstage (LZMA), config (LZMA), revision, build_info, dsdt.aml,
  cmos_layout.bin, postcar, payload, payload_config, payload_revision, the
  free-space entry, bootblock. Attribute chains parsed per entry (compression
  with decompressed sizes, hash digests, stageheaders with loadaddr/entry/
  memlen). The free-space entry is anonymous on disk; the lens renders it
  `(empty)` like the reference tool, and it fills the region tail **exactly
  up to the bootblock entry — zero unaccounted bytes**. The eleven
  inter-entry gaps are alignment padding, every one below the 64-byte align.
- **Added value over the reference tool:** per-entry sha256 (stored and
  decompressed forms), LZMA decompression via stdlib (both configs and
  ramstage decompress clean), the payload's segment table decoded
  (`PAYLOAD_SEGMENT_CODE` LZMA at load 0xDE060, 72,943 B stored / 139,168 B
  in memory; `PAYLOAD_SEGMENT_ENTRY` at 0xFD25A — inside the loaded segment,
  as it must be), and the image's own provenance extracted from its config
  entry: `# This image was built using coreboot cc0358747d2a-dirty`.
- **The config verdict** (registered, not fudged): the ROM's config is NOT
  byte-identical to the tree's `.config` — and that is expected. The image
  carries the **defconfig** (255 lines, ending at the "End of defconfig"
  marker); the tree's `.config` is the olddefconfig expansion (628 lines)
  with every derivable value filled in. The stamp line names the exact
  build revision regardless.
- **Cross-citation, two instruments:** names and offsets identical **13/13**
  against `cbfstool print` executed at probe time, and **13/13** against the
  ring-24 photograph's stored capture (symmetric filter: the master header
  is reported in its own block on both sides).

Two parser bugs were caught before publication and kept in the artifact's
honesty trail: the dictionary-direction bug (`SEG_TYPES` maps name→value;
membership was tested with the value) and the `cbfs_payload_segment` field
order (`offset` u32 **precedes** the u64 `load_addr`; stride 28, not 24).
Both are the same species as ring 8's nesting lesson: exact consumption is
the grammar's only honest referee.

## Front 25b — the fourth wall falls (`qemu-root/`, no root ever obtained)

Ring 24 registered "no QEMU binary without root" as the next software
levier. The wall fell with ring 24's own playbook:

- `apt-cache depends --recurse` on `qemu-system-x86` gives a 96-package
  Depends closure; 28 are missing on this system; `apt-get download` +
  `dpkg -x` into `scratch-coreboot/qemu-root/` extracts all of them with
  **zero download failures**; `ldd` on the extracted binary is clean.
- `qemu-system-x86_64 --version` runs: **QEMU 10.0.11** (Debian trixie).
- One runtime follow-up: the option-ROM blobs (`vgabios-stdvga.bin`,
  NIC roms) live in the `seabios` and `ipxe-qemu` packages — downloaded and
  extracted the same way, served through `-L` share paths.
- No `apt install`, no root, no system mutation. The environment keeps its
  +0 octet discipline; the whole QEMU is disposable sandbox.

## Front 25c — the first boot, and the runtime's confirmation (`lab/vol5-qemu-boot.json`)

The boot command is taken from the tree's own
`Documentation/mainboard/emulation/qemu-q35.md`:
`qemu-system-x86_64 -bios build/coreboot.rom -M q35` — with four registered
deviations (serial captured to file instead of stdio; `-display none` for
the absent GUI libs; `-no-reboot` so a reset loop ends the run; `-L` paths
to the extracted ROM blobs). No `/dev/kvm`: **TCG software emulation**, so
timings measure code paths, not silicon.

**The boot succeeded** — exit 0 in 73 seconds wall, and the 420-line serial
log reads as the complete coreboot chain:

- `bootblock starting (log level: 7)` → FMAP found → "Booting from COREBOOT
  region" → mcache built **for 13 files** → romstage fetched at **@0x80,
  size 0x4d38**;
- `romstage starting` → SMBus enabled → QEMU firmware-config interface
  detected (version 3, `etc/e820`) → CBMEM/IMD rooted → postcar fetched at
  **@0x198c0, size 0x5530**;
- `postcar starting` → ramstage fetched at **@0x4e40, size 0x11c7a**, loaded
  with 2,397 relocs processed;
- `ramstage starting` → the full BS state machine (DEV_INIT_CHIPS 2 ms →
  DEV_ENUMERATE 3 → DEV_RESOURCES 7 → DEV_ENABLE 1 → DEV_INIT 16 →
  WRITE_TABLES 11 → PAYLOAD_LOAD 27) → coreboot table written;
- the payload boots: **SeaBIOS rel-1.17.0-0-gb52ca86e** — AHCI DVD probed,
  PS/2 keyboard initialized, option rom run at ca00:0003, e820 map handed
  over (6 items) — then, with zero disks attached, exactly the expected
  branch: `No bootable device. Retrying in 60 seconds.` → reset →
  `-no-reboot` turns it into a clean exit 0.

**The cross-citation is the crown of the ring.** Every CBFS location the
runtime actually fetched matches the front-25a static census — offset AND
size, 4/4 (romstage 0x80/19,768; ramstage 0x4e40/72,826; postcar 0x198c0/
21,808; payload 0x1ee40/72,999) — and the runtime's own mcache count
(**13 files**) matches the lens's walked entry count. The boot is the image
measuring itself by consuming itself: an independent re-measurement of the
static census by the image's only legitimate reader, with zero
coordination between the two instruments.

## The honesty ledger

- **Proven:** the CBFS lens closes 13/13 against two independent references;
  the built image boots through all four stages to its payload under the
  tree's own documented command; the runtime fetches confirm the static
  census 4/4 + mcache 13/13; the image is self-describing (defconfig +
  build stamp `cc0358747d2a-dirty` + `MAINBOARD_PART_NUMBER: QEMU x86
  q35/ich9`).
- **Flagged:** TCG, not silicon — stage timings are path timings; `-bios`
  maps the image as QEMU's BIOS (no chip, no descriptor); the FMAP rejects
  list exists because `__FMAP__` string literals would otherwise hijack a
  naive signature scan — the same species of decoy ring 8 dissolved.
- **Open:** purchase-time board-status checks on the candidate lane
  (azalea first) — unchanged from ring 24; the azalea build rehearsal needs
  the vendor blob submodules (registered, not attempted); the real-bench
  flash rehearsal stays hardware-gated. Day-0 (16/09) protocol unchanged —
  this ring touched the Volume-5 lane only.

## Consequences for the day-0 protocol

None, by design — and that is the point: the Volume-5 lane advanced two
registered fronts without touching anything the day-0 dump depends on. The
instrument gained a lens that will read the sacrificial board's coreboot
image the same way `spi-map` reads the vendor's; the doctrine gained a
booted proof that the replacement firmware is not a hypothetical; and the
flash-cycle rehearsal (ring 24, file-level 5/5) now has its counterpart:
**write+verify rehearsed, boot rehearsed** — the two halves of the bench
day, both already green in software.
