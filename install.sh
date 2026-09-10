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

set -euo pipefail

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
"$BIN_DIR/omarchy-firmware" tiers | head -14
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
echo
echo "Human-only T2 (staging):"
echo "  omarchy-firmware update stage --device GUID   # dry-run plan, then --confirm YOURSELF"
echo "  omarchy-firmware update rollback              # the honest rollback inventory"
echo
echo "MCP server (the 13 harnesses):"
echo "  pip install mcp   # or: pacman -S python-mcp"
echo "  claude mcp add omarchy-firmware -- $BIN_DIR/omarchy-firmware-mcp"
