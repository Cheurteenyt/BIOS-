# The ninth ring — the nameplate, the trust store unpacked, and the weight of the firmware (2026-09-11)

> Companion to `ovmf-findings.md` and rings one through eight. Same
> campaign, same rules: read-only, zero bytes written, surface freeze
> untouched. Instruments: `ring9_guid_names.py`, `ring9_siglist.py`,
> `ring9_weight_map.py`, `ring9_render_check.py`, over machinery reused
> verbatim from `ring4_lib` and `nvram_anatomy`. Ground truth fetched
> this run: eleven EDK2 `.dec` inventories plus the full edk2 master
> tarball (19 MB) for the manual closes; GitHub API for the render
> checks. Artifacts: `ovmf-guid-names.json`, `ovmf-siglist.json`,
> `ovmf-weight-map.json` (this repo).

## Front A — the GUID nameplate: every raw cell in the ledger gets a name

Rings one through eight kept a standing debt: GUIDs resolved beyond
the curated subset stayed raw. Ring 9 clears the debt in full.

- **618/618 GUID occurrences across 13 artifacts are named; 209
  distinct GUIDs; zero raw cells left.** Sources, layered: 11 `.dec`
  inventories from tianocore master (883 protocol/PPI/GUID entries) +
  the census module names + the kill-list families + a manual
  nameplate resolved by grepping the edk2 master tree.
- The manual layer exists because the legacy GitHub code search
  tokenizes hex strings poorly and secondary-ratelimits in bursts; one
  tarball and one local grep outperformed the API for all 20 residuals.
- **Ring 8's PEI apriori "?" closes**: the single entry
  (9B3ADA4F-AE56-4C24-8DEA-F03B7558AE50) is **PcdPeim** — the first
  PEIM the platform declares is the PCD database itself.
- **Ring 8's 245-B second formset closes**: fe561596-e6bf-41a6-8376-
  c72b719874d0 is **EFI_FILE_EXPLORE_FORMSET_GUID** — the File
  Explorer formset that rides inside SecureBootConfigDxe because the
  module links FileExplorerLib. The "unnamed small formset" was a
  library's passenger all along.
- **The keyring's owner field is a fingerprint**: the signature owner
  a0baa8a3-041d-48a8-bc87-c36d121b5e3d, present on every
  EnrollDefaultKeys-enrolled record, is **EnrollDefaultKeys' own
  FILE_GUID**. The enroller stamps itself as owner; who enrolled a
  store is readable from the store.
- The facade's other occupants are named: DeviceManager
  (3ebfa8e6), BootManager (847bc3fe), Boot Maintenance (642237c7),
  FrontPage (9e0c30bc), and DriverHealthManagerDxe's two formsets —
  the manager (cfb3b000) and the configure form (4296d9f4).
- Fourteen census-unnamed PEIMs get their names back (S3Resume2Pei,
  Tcg2Pei, Tcg2PlatformPei, TcgPei, DxeIpl, VariablePei,
  Tcg2ConfigPei, FaultTolerantWritePei, PlatformPei,
  StatusCodeHandlerPei, ReportStatusCodeRouterPei, SmmAccessPei,
  TpmMmioSevDecryptPei, TdTcg2Pei). One special: 280251c4 resolves
  through the `.fdf` indirection `FILE_GUID = $(UP_CPU_PEI_GUID)` to
  **CpuMpPei** — OVMF's build-time PEI swap mechanism caught in the
  artifacts.

Day-0: the vendor instrument's every GUID column now renders a name,
or records honestly that the name lives outside every known inventory
— which on a vendor image means "new silicon", itself a finding.

## Front B — the signature-list lens: the trust store, record by record

The keyring named the databases; ring 9 opens every record inside
them, on both enrolled stores (ms, snakeoil).

- **The dbx is the sha256 of the empty string, byte-exact, in both
  stores** (e3b0c442…b855). The canonical "revoke nothing" placeholder
  — OVMF ships a revocation list that revokes zero hashes. The
  instrument now recognizes the convention by value, not by position.
- **The ms store's composition**: PK = 1 X.509 owned by the global
  variable GUID; KEK = 2 entries (EnrollDefaultKeys +
  gMicrosoftVendorGuid); db = 2 X.509 (both gMicrosoftVendorGuid);
  dbx = 1 SHA-256 (the empty hash). **The snakeoil store**: every
  record owned by EnrollDefaultKeys — a self-enrolled, self-owned
  platform, coherent with ring 5's byte-identical modules verdict
  (trust is configuration).
- Per-entry SHA-256 fingerprints are now recorded for every X.509
  payload, and every owner renders through the front-A nameplate.
- **The scale rehearsal is synthetic and honest**: a generated 1000-
  entry SHA-256 dbx parses exactly in 2.3 ms (≈ 426,000 entries/s).
  A vendor dbx carrying hundreds of revocations is a rounding error
  for the walker; the 372-update reality stays registered, not
  byte-proven — OVMF cannot show it.

Day-0: the trust-store report gains per-record rows — type, owner
(name), size, fingerprint — and the empty-string placeholder stops
looking like data.

## Front C — the weight map: the frugality ledger in bytes

The doctrine prices firmware in modules; ring 9 prices it in bytes,
per FV, per build (plain / secboot / strictnx).

- **The DXEFV ships more than half empty**: 14.5 MB of volume carries
  4.74 MB of files on plain (31.15%) and 6.31 MB on secboot (41.5%).
  The PEIFV: 27.6% → 29.0%. The platform's real constraint is not
  space.
- **The secboot build grows inside the slack**: FVMAIN_COMPACT goes
  45.62% → 48.17% — the compressed FVMAIN grows by ~87 KB and the
  outer geometry never moves. The +0-octet outer layout survives the
  whole secboot swap by design.
- **SECFV is a spike**: SecMain (45.5 KB) + ResetVector (2.9 KB) +
  164 KB of pad — 22.74% utilized.
- **Top consumers, named**: TlsDxe ≈ 1.01 MB (the largest DXE module
  on every build), UEFI Shell 894 KB (plain only), VariableSmm
  868 KB, SecurityStubDxe 825 KB, SecureBootConfigDxe 716 KB.
- **The swap delta, by name**: secboot adds 18 modules (+1.91 MB —
  the complete SMM stack: PiSmmCore/Ipl/CpuDxeSmm, VariableSmm +
  runtime, FvbServicesSmm, SmmAccess/Control2, SmmLockBox,
  SmmFaultTolerantWrite, TcgMorLockSmm, SecureBootConfigDxe,
  CpuS3DataDxe, plus the PEI variable stack VariablePei/
  SmmAccessPei/FaultTolerantWritePei) and removes 9 (−1.10 MB — the
  non-SMM variable stack and **the UEFI Shell with its three dynamic
  commands**: http, tftp, VariablePolicy). Net +810 KB. The Shell is
  the largest single sacrifice the secure build makes to fit — the
  bootable setup façade loses its command line.
- **Two false-FV lessons, bought cheap**: a raw `_FVH` scan of
  compressed data breeds false volumes — the honest filter is
  ZeroVector == 0 plus a known filesystem GUID; and outer/pierced
  offsets live in different coordinate spaces that must never be
  compared. The strictnx-only decoy at 0x5e0e58 is a real FFS2 header
  living inside **FvbServicesSmm's body** (its flash-FV template)
  with a claimed length that overruns its host file — dismissed by
  the ring-8 nesting rule, verbatim: a span inside another span is a
  decoy until the outer walk fails.

Day-0: the vendor report gains a weight page — utilization per
volume, top consumers by name, and the swap page that shows exactly
what a security policy costs in bytes and in features.

## Owed item — the hub renders (GitHub-side proof)

- The served README returns 200 rendered HTML (33.7 KB, 9 `<h2>`
  sections, 37 links). The `study-en` and `study-fr` releases answer
  200 with all 4 + 4 assets `uploaded`. No internal anchors are used,
  none dangle. The offline checker still reports **ALL LINKS
  RESOLVE**. The audit's last open item closes green.

## Honesty ledger

- `CERT_TYPES` names X.509 and SHA-256 lists only; PKCS7/RSA2048-type
  lists would walk correctly but label by raw GUID. No real
  occurrence exists in the corpus to exercise them.
- The scale rehearsal's "hundreds of revocations on a vendor dbx"
  framing is registered from public knowledge, not byte-proven here.
- The FVMAIN_COMPACT-slack interpretation (secboot grows into outer
  slack, outer geometry frozen) is consistent with ring 4's byte-
  identical outer hashes and this ring's utilization shift — an
  interpretation, flagged as such.
- The `.dec` parser reads single-line entries; exotic multiline
  formatting would be missed (883 entries parsed; every GUID this
  ring actually needed validated against its source file).
- The `11111111-2222-3333-4444-1234567890ab` GUID in the facade
  artifact is a synthetic fixture, recorded as such in the nameplate.

## The ledger self-correction chain, one line per ring

Ring 6 re-derived the grammar → ring 7 dissolved the list → ring 8
dissolved pkg3 → ring 9 finds nothing left to dissolve and spends the
ring paying down names: every anonymous cell in nine rings of
artifacts becomes a name, the trust store opens record by record, and
the firmware gets its weight ledger. The instrument gained a
discipline it did not have: scan results are guilty until validated
(zero vector, filesystem GUID, container fit, coordinate space).

## Consequences for day-0 (16/09)

- The ASUS dump arrives into a pipeline that names every GUID,
  unpacks every signature list, and prices every volume — no new
  code is needed on the vendor image, only new inventories.
- The empty-string dbx convention gives day-0 its first cheap
  tripwire: a vendor dbx that is *also* just sha256("") would mean
  the board ships revocation-blind out of the box.
- The weight map's utilization method measures the vendor's slack —
  the exact headroom the eventual lab image must respect on day 5+.
