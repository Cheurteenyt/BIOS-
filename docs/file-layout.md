# File layout

How `BIOS-/` is organized, and where everything ends up on an installed
system. Modeled on the way the Omarchy repository documents itself
(`docs/file-layout.md` there): one page that answers "what is this file
doing here" for every tree in the repo.

## Mental model

One library, three consumers, one rule. `lib/firmware_hal/` is the single
implementation of everything the tool knows and does; the CLI bins, the MCP
server and the agent skill are thin consumers over it. The repo is also its
own distribution: `install.sh` stages the same tree it lives in (or a
bit-verified release tarball of it) into the user's home — nothing is ever
written to `/usr/share`, nothing is ever written to SPI.

Every tree has one job:

- **`bin/`** — the runtime surface. One router (`omarchy-firmware`) and
  single-purpose `omarchy-firmware-*` executables, all on the user's PATH.
- **`lib/`** — the Python package (`firmware_hal`), including its data
  (the AM4 CVE knowledge base). One implementation, three consumers.
- **`tests/`** — the contract: the full suite (stdlib-only, 323 checks)
  and the MCP conformance smoke, plus the TWIN-1 fixtures they run on.
- **`docs/`** — the stable documents: architecture, security doctrine,
  the write layer, the diagnostics catalog, frugality, the twin, the
  day-1 runbook, this file — and `docs/research/` (the study).
- **`lab/`** — the disposable machine: the findings of the massive
  investigation (six Markdown narratives + eight JSON artifacts), the
  QEMU/OVMF smoke, the coreboot doctrine for the sacrificial board.
- **`agents/`** — the skill shipped to the harnesses (claude, codex,
  opencode…), installed under `~/.config/omarchy/agents/skills/`.
- **`etc/`** — the systemd **user** units, provided but never enabled by
  the installer: one-shot services a timer may wake (doctor, weekly CVE
  watch). A choice, not a daemon.
- **`install.sh`** — the floating installer of a pinned payload
  (`--from release` verifies SHA256SUMS before anything runs).

## The repository tree

```
BIOS-/
├── README.md               the pitch, the founding question, the tools table
├── AGENTS.md               how AI agents operate in this repo (read first)
├── CLAUDE.md               @AGENTS.md (one-line pointer, no duplication)
├── CHANGELOG.md            every release, the honest ledger
├── LICENSE                 MIT
├── install.sh              user-space installer (bins + lib + twin + skill + units)
├── bin/                    19 executables: the router + 17 subcommands + the MCP server
├── lib/firmware_hal/       the single implementation (28 modules + data/cve_am4.json)
├── tests/                  test_suite.py (323 checks) + mcp_smoke.py + fixtures/ (TWIN-1)
├── docs/                   stable documents (see the README table)
│   └── research/           the four-volume study: summaries + links to the PDF releases
├── lab/                    the disposable machine: findings (6 rings), artifacts, doctrine
├── packaging/              lever D — the Arch-native PKGBUILD (see docs/packaging.md)
├── agents/skills/firmware/ SKILL.md — the skill the harnesses load
├── etc/systemd/user/       doctor + watch units (oneshot services, timers opt-in)
└── .github/workflows/      ci.yml — full suite (py3.11/3.13) + MCP smoke on every push
```

## The installed layout (what install.sh does)

Everything is user-space; the installer enables nothing and writes
nothing outside `$HOME`:

| Source in the repo | Lands on the system | Why |
|---|---|---|
| `bin/omarchy-firmware*` | `~/.local/bin/` | the 19 executables, on the PATH |
| `lib/firmware_hal/**/*.py` | `~/.local/share/omarchy-firmware/lib/firmware_hal/` | the installed CLI is self-contained; bins resolve this path as fallback |
| `lib/firmware_hal/data/cve_am4.json` | `~/.local/share/omarchy-firmware/lib/firmware_hal/data/` | the CVE knowledge base travels with the lib |
| `tests/fixtures/{b450-plus,b450-plus-clean,b550-f-old,scenarios,twin-sysfs}` | `~/.local/share/omarchy-firmware/twin/` | TWIN-1 — the rehearsal machine (3 boards, 12 scenarios, sysfs tree) |
| `agents/skills/firmware/SKILL.md` | `~/.config/omarchy/agents/skills/firmware/` | the skill the harnesses consume |
| `etc/systemd/user/omarchy-firmware-{doctor,watch}.{service,timer}` | `~/.config/systemd/user/` | staged **inactive**; enabling a timer is an explicit human `systemctl --user enable` |

Not installed on purpose: `tests/`' Python code (only its fixtures travel,
as the twin), `docs/`, `lab/`, `packaging/`, `.github/` — knowledge stays
with the repo.

## Deliberately not in the repository

- **The study PDFs** (9.3 MB) — archived as release assets:
  [`study-en`](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-en)
  (canonical English) and
  [`study-fr`](https://github.com/Cheurteenyt/BIOS-/releases/tag/study-fr)
  (French originals). `*.pdf` is gitignored; the repo is text + code.
- **The probe scripts** (`*_probe.py`, `ring4_lib`, `ring5_probe.py`) —
  one-shot sandbox instruments of the investigation; the `lab/` findings
  quote them, the JSON artifacts are their durable output.
- **The firmware images** (OVMF `*.fd`, vendor dumps) — downloaded into
  the sandbox per session, never committed; +0 octet applies to the repo
  too: nothing binary that could pretend to be firmware lives here.
