# Day-0 protocol — reading a vendor image

> The dump arrives; nothing is written back. Every read in this
> protocol is read-only, and every outcome is a document.

Sept. 16 is the first contact with the real board (ASUS B450-PLUS,
BIOS 3644). The machine half of the day — `capture`, `rehearse`,
`rehearse-diff`, `spi-map` — is covered by
[docs/digital-twin.md](digital-twin.md) and is already proven against
TWIN-1. This document is the other half: what happens when the vendor
BIOS image itself is read, in the lab, by the instrument the OVMF
rings built.

## The claim under test

Ring 9 asserted: *the vendor dump arrives into a pipeline that names
every GUID, unpacks every signature list, and prices every volume —
no new code is needed on the vendor image, only new inventories.*
Ring 10 proved the claim on the OVMF specimens: the full chain
re-runs end to end, all 14 stages exit 0 in ~25 s, and all 16 lab
artifacts reproduce content-identical (canonical comparison, one
registered wall-clock noise field). The rehearsal record lives in
[lab/ovmf-rehearsal.json](../lab/ovmf-rehearsal.json).

## The lab pipeline

The stages run in this order (later stages read earlier artifacts).
On day-0 each stage runs unchanged; only its inputs are new.

| # | Stage | Artifact | The question it answers |
|---|---|---|---|
| 1 | census | `ovmf-census.json` | What volumes and modules does the image contain? |
| 2 | keyring | `ovmf-keyring.json` | Which GUIDs exist, per build? |
| 3 | build-delta | `ovmf-build-delta.json` | What differs between builds? |
| 4 | pe-provenance | `ovmf-pe-provenance.json` | Where did each PE section come from? |
| 5 | ring5 (3 artifacts) | `ovmf-ms-delta`, `ovmf-acpi-footprint`, `ovmf-ifr-grammar` | MS vs OVMF deltas, ACPI tables, the IFR grammar |
| 6 | ifr-census | `ovmf-ifr-census.json` | How many setup questions does the façade have? |
| 7–8 | facade | `ovmf-ifr-facade.json` | What words, varstores, defaults sit behind them? |
| 9 | depex-dag | `ovmf-depex-dag.json` | What gates each driver's dispatch? |
| 10 | scsu | `ovmf-scsu-strings.json` | Is any string SCSU-compressed? (In OVMF: never.) |
| 11 | pkg3 | `ovmf-pkg3-head.json` | The nested-anchor resolution record |
| 12 | guid-names | `ovmf-guid-names.json` | Is any GUID still anonymous? (Target: zero raw.) |
| 13 | siglist | `ovmf-siglist.json` | What does the trust store actually enroll? |
| 14 | weight-map | `ovmf-weight-map.json` | What does every byte cost, per volume? |

The chain re-runs clean and deterministic; the only file the rehearsal
itself writes is its own record. Stage 7–8's rewrite of the facade
artifact is mid-chain churn by design — the pkg3 stage re-finalizes
it, and chain identity is judged at chain end.

## The tripwires

Five rules, each bought in a ring, applied on day-0 verbatim:

1. **The empty-string dbx.** In OVMF both enrolled dbx stores are
   byte-exact `sha256("")` — revoke-nothing by value. A vendor dbx
   that is *also* just the empty-string hash would mean the board
   ships revocation-blind out of the box. Check this first.
2. **The nesting rule.** `_FVH` candidates are guilty until validated:
   ZeroVector must be zero, the filesystem GUID must be known, the
   span must fit its container, and outer/pierced offsets must never
   be compared. A span inside another span is a decoy until the outer
   walk fails (the strictnx lesson).
3. **Unknown-opcode policy.** Undefined opcodes are registered, never
   forced. The pkg3 saga exists because an unknown 0x00 head was once
   interpreted instead of resolved; it turned out to be a nested
   anchor, not an opcode.
4. **GUID coverage: zero raw.** Every GUID occurrence must leave the
   nameplate with a name. The OVMF corpus closes at 618/618 named;
   the vendor image starts from zero and must end there too.
5. **Category errors.** An HII package list never ships inside a PE
   (HiiAddPackages builds it at runtime — walk packages, not lists);
   compressed and uncompressed offsets live in different coordinate
   spaces that must never be compared.

## The vendor report skeleton

The day-0 write-up reuses the artifact structure directly: inventory
(census + nameplate coverage), dispatch (the DAG, hubs and apriori
order), the façade (question count, varstores, the words behind them),
the trust store (PK/KEK/db/dbx, owners and fingerprints), the weight
map (utilization per volume, top consumers, slack). Each section
carries its artifact; each artifact carries its honesty ledger.

## What day-0 does not do

No write touches the machine or the image: +0 octet is the standing
rule. Nothing flashes, nothing installs, nothing auto-runs. The
outcomes are documents and JSON artifacts — knowledge, not code paths.
New instrument code is written only if the vendor image presents a
structure the standard grammar does not cover, and it lands in the
sandbox first, like every ring before it.

## Honesty

The rehearsal proved reproducibility on OVMF, not on vendor silicon.
A production image will exercise formats OVMF never shows: larger
flash maps, vendor NVRAM layouts, AMI-specific FV structs, and
possibly compressed sections outside the LZMA-alone shape. Those are
registered as inventories when they appear — the protocol's promise
is that the *reading order and the rules* are already fixed, not that
the answers are known.
