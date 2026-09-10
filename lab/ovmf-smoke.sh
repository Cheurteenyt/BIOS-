#!/usr/bin/env bash
# ovmf-smoke.sh — the first "replacing the firmware" experiment, risk-free.
#
# Boots OVMF (the open UEFI firmware) inside QEMU, headless, captures the
# serial boot log, and reports what the boot chain actually said. Nothing
# here touches real hardware: the VM is the disposable machine.
#
# Usage:
#   ./ovmf-smoke.sh [workdir]          # default workdir: ./out
#
# Requirements: qemu-system-x86_64, an OVMF firmware image (auto-detected
# among the common distro paths), no root, no network.
# The script writes ONLY inside its workdir.

set -euo pipefail

WORKDIR="${1:-out}"
mkdir -p "$WORKDIR"
LOG="$WORKDIR/ovmf-serial.log"

say()  { printf '  %s\n' "$*"; }
die()  { printf 'ovmf-smoke: %s\n' "$*" >&2; exit 1; }

command -v qemu-system-x86_64 >/dev/null 2>&1 \
  || die "qemu-system-x86_64 not found (pacman -S qemu-full)"

OVMF=""
for cand in \
  /usr/share/edk2/x64/OVMF_CODE.4m.fd \
  /usr/share/ovmf/x64/OVMF_CODE.fd \
  /usr/share/OVMF/OVMF_CODE.fd \
  /usr/share/ovmf/OVMF.fd; do
  if [ -f "$cand" ]; then OVMF="$cand"; break; fi
done
[ -n "$OVMF" ] || die "no OVMF firmware found — install edk2/ovmf and retry"

say "== ovmf-smoke — the disposable machine boots =="
say "firmware : $OVMF"
say "workdir  : $WORKDIR (the only place this script writes)"

# -nographic: serial console to stdout; 45 s ceiling: a headless UEFI
# shell IS the success state (the boot log is the deliverable).
set +e
timeout 45 qemu-system-x86_64 \
  -machine q35 -m 512 \
  -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
  -nographic \
  >"$LOG" 2>&1
rc=$?
set -e
# timeout(1) returns 124 when the ceiling fires — expected: the VM sits
# in the UEFI shell with no boot media. 0 = the VM exited cleanly. Both
# are acceptable; anything else is a boot failure worth reading.
if [ "$rc" -ne 0 ] && [ "$rc" -ne 124 ]; then
  die "qemu exited rc=$rc — read $LOG"
fi

say "serial log: $LOG ($(wc -l <"$LOG") lines)"
say "-- what the boot chain said --"
grep -aiE "SMM|UEFI|OVMF|SecureBoot|TSEG|InstallProtocol" "$LOG" | head -20 || true

if grep -aqE "OVMF|EDK II" "$LOG"; then
  say "verdict  : the replacement firmware booted and spoke — experiment green"
  exit 0
fi
die "no OVMF signature in the boot log — read $LOG"
