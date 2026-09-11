# Packaging — lever D (the Arch-native delivery shape)

Lever D is the packaging lever: delivering `omarchy-firmware` the way
Omarchy itself delivers software — pacman-owned files built from a
PKGBUILD. It exists **alongside** the day-0 default, not instead of it.

## The two delivery shapes

| | `install.sh` (day-0 default) | `packaging/PKGBUILD` (lever D) |
|---|---|---|
| Layout | user-space: `~/.local/bin`, `~/.local/share/omarchy-firmware` | system: staged tree under `/usr/share/omarchy-firmware` + `/usr/bin` symlinks |
| Trust model | the installer verifies the release `SHA256SUMS` before anything runs | makepkg verifies the pinned tag digest before anything builds |
| Twin discovery | `$XDG_DATA_HOME/omarchy-firmware/twin` (installed layout) | `FW_TWIN_DIR=/usr/share/omarchy-firmware/twin` via `/etc/profile.d` |
| Units | staged `~/.config/systemd/user`, **inactive** | staged `/usr/lib/systemd/user`, **inactive** — no `post_install` |
| Skill | installed into `~/.config/omarchy/agents/skills/firmware/` | staged at `/usr/share/omarchy-firmware/skill/` — the human wires it (one line below) |
| Writing to `/usr/share/omarchy` | never (forbidden by the omarchy skill) | never — `omarchy-firmware` is a distinct namespace |
| Writing to `$HOME` | the installer's job, explicit | **never** — a package does not own user config |
| Enabling anything | never | never |

Both shapes deliver the same frozen surface: 19 bins, one library,
TWIN-1, the skill. Neither enables a timer, writes SPI, or installs a
daemon. The choice between them is a deployment decision, not a
contract change: `install.sh` stays the day-0 path because day-0 wants
zero `/usr` footprint and per-user reversibility (`pacman -R` is
reversible too — but day-0 is measured on the user-space shape).

## The design finding: why the staged tree + symlinks

The bins locate their library with `os.path.realpath(__file__)` and
check, in order: the repo-relative `../lib`, then
`$XDG_DATA_HOME/omarchy-firmware/lib`. A naive system package (bins in
`/usr/bin`, library in `/usr/lib/omarchy-firmware`) would be **broken by
construction**: `os.path.dirname(/usr/bin)` = `/usr`, `os.path.isdir(/usr/lib)`
is always true, so the resolver stops there — and `import firmware_hal`
fails, because nothing lives at `/usr/lib/firmware_hal`.

The PKGBUILD works **with** the frozen resolution logic instead of
against it: the whole repo layout is staged intact under
`/usr/share/omarchy-firmware/`, and `/usr/bin` gets symlinks. `realpath`
resolves the symlink back into the staged tree, candidate 1 wins for the
right reason, and the import succeeds — zero changes to the frozen tool
surface. The twin resolver's `FW_TWIN_DIR` override (checked first, by
design, and only honored when it points at a real directory) makes the
staged rehearsal assets discoverable through one declarative
`/etc/profile.d` line — no $HOME writes, no activation.

## Building and verifying

```bash
cd packaging/
makepkg -f                       # fetch the pinned v0.7.1 tag, verify digest, build
pacman -Qpi omarchy-firmware-0.7.1-1-any.pkg.tar.zst   # inspect BEFORE installing
namcap PKGBUILD                  # lint (if namcap is installed)
```

After install, the honest checks (all read-only, same contract as
install.sh's smoke):

```bash
omarchy-firmware tiers           # the contract displays
omarchy-firmware twin            # TWIN-1 resolves through FW_TWIN_DIR
omarchy-firmware rehearse --backend twin    # the whole rehearsal, no hardware
systemctl --user list-unit-files 'omarchy-firmware-*'   # all: disabled, static
```

Wire the skill into the harnesses (the one line the package cannot do —
it never writes `$HOME`):

```bash
mkdir -p ~/.config/omarchy/agents/skills/firmware
ln -s /usr/share/omarchy-firmware/skill/SKILL.md \
      ~/.config/omarchy/agents/skills/firmware/SKILL.md
```

## Verification status (honest)

- The PKGBUILD is **syntax-checked and design-reviewed** in this sandbox
  (Debian — no `makepkg`/`namcap` available here); the pinned digest was
  computed from the actual `v0.7.1` tag tarball
  (`2b327f9c…ed216`). The first real `makepkg` run on an Arch box is a
  **post-day-0 task** — it must not consume any day-0 attention before
  16/09.
- The `v0.7.1` tag predates the PDF cleanup; the tarball is 6.8 MB. The
  next release tag carries the cleaned tree — bump `pkgver`, recompute
  the digest, done.

## In this repo, or in `omarchy-pkgs`?

Omarchy builds its packages from a **separate** repository
(`omarchy-pkgs`), keeping the main repo product-focused. Until this
project earns its own delivery channel, the PKGBUILD lives in
`packaging/` so it is reviewed, versioned and tested **with** the code
it packages. If a separate channel appears (the omarchy-pkgs pattern,
or an AUR package), `packaging/` moves wholesale — the file is
self-contained by design.
