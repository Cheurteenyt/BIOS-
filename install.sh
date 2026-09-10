#!/usr/bin/env bash
# install.sh — installs the omarchy-firmware base (P5: twin + rehearsal on top
# of the P4 supervised loop) for the user, in the spirit of the Omarchy repo:
#   bin/   -> ~/.local/bin (on the PATH)
#   lib/   -> ~/.local/share/omarchy-firmware/lib  (the installed CLI is
#             self-contained — bins resolve this path as fallback)
#   twin/  -> ~/.local/share/omarchy-firmware/twin (TWIN-1: fixtures + 12
#             scenarios + sysfs tree — the rehearsal machine)
#   skill  -> ~/.config/omarchy/agents/skills/firmware/SKILL.md
#   timer  -> ~/.config/systemd/user (DISABLED by default: an explicit choice)
# Nothing is written to /usr/share/omarchy (forbidden by the omarchy skill).
#
# Two ways in:
#   install.sh                   install from the tree this file lives in
#                                (a checkout or an extracted release tarball)
#   install.sh --from release    fetch the latest release tarball, verify it
#                                against its SHA256SUMS, then install it
#   install.sh --from v0.6.0     same, pinned to an explicit tag
#   install.sh --from main       clone main (floating — for development)
# The installer floats, the payload is pinned: whatever --from installs is
# bit-verified against its published SHA256SUMS BEFORE anything runs, and
# prints the provenance (tag + digest). Day 0 should be able to quote it.

set -euo pipefail

REPO="Cheurteenyt/BIOS-"

usage() {
  cat <<'EOF'
usage:
  install.sh                     install from the tree this file lives in
  install.sh --from release      fetch the latest release tarball, verify its
                                 SHA256SUMS, install it (bit-verified)
  install.sh --from <tag>        same, pinned to an explicit tag (v0.6.0)
  install.sh --from main         clone main (floating — development)
EOF
}

# --from: fetch-then-install. The installer floats, the payload is pinned:
# nothing stages until sha256sum -c accepts the tarball, and the provenance
# (tag + digest) is echoed so the session log can quote it back.

# Resolve the latest release tag. Primary: the API. Fallback: the
# releases/latest page redirect (not the API — no rate limit), so a
# throttled install still resolves. Never guess: empty = loud failure.
resolve_latest() {
  local r
  r="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
         | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n1 || true)"
  if [[ -z "$r" ]]; then
    r="$(curl -fsSI "https://github.com/$REPO/releases/latest" \
         | tr -d '\r' | sed -n 's/^[Ll]ocation: .*\/tag\/\(v[0-9][^ /?]*\).*/\1/p' \
         | head -n1 || true)"
    if [[ -n "$r" ]]; then
      # stderr: this function's stdout is captured by the caller.
      echo "  (resolved via the releases redirect — API unavailable)" >&2
    fi
  fi
  printf '%s' "$r"
}

fetch_and_install() {
  local ref="$1" tmp ver
  tmp="$(mktemp -d)"
  # whatever the failure (bad tag, checksum mismatch, aborted smoke), the
  # temp dir never outlives this function — no debris, no half-downloaded
  # payloads left for the next run to trip over.
  trap 'rm -rf "$tmp"' EXIT

  if [[ "$ref" == "main" ]]; then
    echo "== fetching main (floating reference — development) =="
    command -v git >/dev/null 2>&1 || { echo "  git required for --from main" >&2; exit 1; }
    git clone --depth 1 "https://github.com/$REPO.git" "$tmp/src"
    bash "$tmp/src/install.sh"
    return
  fi

  if [[ "$ref" == "release" ]]; then
    ref="$(resolve_latest)"
    if [[ -z "$ref" ]]; then
      echo "  could not resolve the latest release (API + redirect unavailable)" >&2
      echo "  pass an explicit tag instead: install.sh --from v0.6.0" >&2
      exit 1
    fi
    echo "  latest release: $ref"
  fi

  ver="${ref#v}"
  echo "== fetching $ref (bit-verified payload) =="
  curl -fsSL -o "$tmp/omarchy-firmware-$ver.tar.gz" \
    "https://github.com/$REPO/releases/download/$ref/omarchy-firmware-$ver.tar.gz" \
    || { echo "  download failed: $ref has no omarchy-firmware-$ver.tar.gz asset?" >&2; exit 1; }
  curl -fsSL -o "$tmp/SHA256SUMS" \
    "https://github.com/$REPO/releases/download/$ref/SHA256SUMS" \
    || { echo "  download failed: $ref has no SHA256SUMS asset?" >&2; exit 1; }
  (cd "$tmp" && sha256sum -c SHA256SUMS) \
    || { echo "  CHECKSUM MISMATCH — refusing to install anything" >&2; exit 1; }
  echo "  sha256: $(cut -d' ' -f1 "$tmp/SHA256SUMS")"
  mkdir -p "$tmp/src"
  tar -xzf "$tmp/omarchy-firmware-$ver.tar.gz" -C "$tmp/src"
  bash "$tmp/src/omarchy-firmware-$ver/install.sh"
}

FROM_REF=""
while (($#)); do
  case "$1" in
    --from) FROM_REF="${2:?--from needs: release | <tag> | main}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [[ -n "$FROM_REF" ]]; then
  fetch_and_install "$FROM_REF"
  exit 0
fi

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
SKILL_DIR="${HOME}/.config/omarchy/agents/skills/firmware"
UNIT_DIR="${HOME}/.config/systemd/user"

echo "== omarchy-firmware — Phase 5 (digital twin + dress rehearsal) =="

# 1) Bins
mkdir -p "$BIN_DIR"
for f in "$SRC"/bin/omarchy-firmware*; do
  install -m 0755 "$f" "$BIN_DIR/$(basename "$f")"
  echo "  bin: $BIN_DIR/$(basename "$f")"
done

# 1bis) Library + digital twin — a self-contained installed CLI.
#       (Before P5 the bins were installed WITHOUT the lib: the first real
#       session would have died on ModuleNotFoundError. The rehearsal
#       machine exists precisely so this class of bug dies in rehearsal.)
SHARE_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/omarchy-firmware"
mkdir -p "$SHARE_DIR/lib/firmware_hal/data" "$SHARE_DIR/twin"
for f in "$SRC"/lib/firmware_hal/*.py; do
  install -m 0644 "$f" "$SHARE_DIR/lib/firmware_hal/$(basename "$f")"
done
install -m 0644 "$SRC"/lib/firmware_hal/data/cve_am4.json \
  "$SHARE_DIR/lib/firmware_hal/data/cve_am4.json"
echo "  lib:  $SHARE_DIR/lib/firmware_hal"
for d in b450-plus b450-plus-clean b550-f-old scenarios twin-sysfs; do
  rm -rf "$SHARE_DIR/twin/$d"
  cp -R "$SRC/tests/fixtures/$d" "$SHARE_DIR/twin/$d"
done
echo "  twin: $SHARE_DIR/twin (TWIN-1: 3 boards, 12 scenarios, sysfs)"

# 2) Agent skill (consumed by the harnesses: claude, codex, opencode…)
mkdir -p "$SKILL_DIR"
install -m 0644 "$SRC/agents/skills/firmware/SKILL.md" "$SKILL_DIR/SKILL.md"
echo "  skill: $SKILL_DIR/SKILL.md"

# 2bis) systemd units — provided but NEVER enabled here (vol. 3, ch. 4):
# no resident daemon, the doctor is a one-shot that a timer wakes up;
# the weekly watch timer (P4) is the same: an explicit choice.
mkdir -p "$UNIT_DIR"
for u in "$SRC"/etc/systemd/user/omarchy-firmware-doctor.{service,timer} \
         "$SRC"/etc/systemd/user/omarchy-firmware-watch.{service,timer}; do
  install -m 0644 "$u" "$UNIT_DIR/$(basename "$u")"
  echo "  unit: $UNIT_DIR/$(basename "$u") (inactive)"
done
echo "  option: systemctl --user enable --now omarchy-firmware-doctor.timer"
echo "  option: systemctl --user enable --now omarchy-firmware-watch.timer   # weekly CVE watch"

# 3) System dependencies — checked, never silently installed
missing=()
for cmd in dmidecode efibootmgr; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
command -v fwupdmgr >/dev/null 2>&1 || echo "  note: fwupd missing — fw.update.check will be degraded (pacman -S fwupd)"
((${#missing[@]})) && {
  echo "  to install: pacman -S ${missing[*]}" >&2
  exit 1
}

# 4) Smoke: the contract displays, one fixture audit + one scenario diagnostic run
#    (no `| head` here: tiers prints ~20 lines and a closed pipe turns the
#    python flush into a racy BrokenPipeError — pipefail would kill the install)
"$BIN_DIR/omarchy-firmware" tiers
echo
echo "Installation complete. Try:"
echo "  omarchy-firmware twin                # meet TWIN-1, the rehearsal machine"
echo "  omarchy-firmware rehearse --backend twin   # dress rehearsal, no hardware"
echo "  omarchy-firmware audit status        # on the real machine"
echo "  omarchy-firmware audit cve-watch     # KB freshness + fwupd advisories (P4)"
echo "  omarchy-firmware diag quick          # passive thermal diagnostics (T0)"
echo "  omarchy-firmware diag probe --seconds 30   # active: time constant"
echo "  omarchy-firmware report              # supervised-loop digest (P4)"
echo "  omarchy-firmware selftest            # demo on the twin fixtures"
echo "  omarchy-firmware rehearse            # day-0 drill on THIS machine"
echo "  omarchy-firmware capture             # day-0 photograph (read-only T0 snapshot)"
echo "  omarchy-firmware rehearse-diff --latest    # twin → real: the named surprises"
echo
echo "Human-only T2 (staging):"
echo "  omarchy-firmware update stage --device GUID   # dry-run plan, then --confirm YOURSELF"
echo "  omarchy-firmware update rollback              # the honest rollback inventory"
echo
echo "MCP server (the 13 harnesses):"
echo "  pip install mcp   # or: pacman -S python-mcp"
echo "  claude mcp add omarchy-firmware -- $BIN_DIR/omarchy-firmware-mcp"
