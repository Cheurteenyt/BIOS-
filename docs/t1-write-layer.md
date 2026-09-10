# The T1 write layer — two keys, one backup, mechanical guards

Volume 4 (ch. 4) promised that if the agent ever writes, it would be under
mechanical, structural constraints — never under good will. Phase 3 makes
that promise executable for exactly **two targets**: the CPU EPP hint and
the fan curve of an ASUS-class Super I/O. This document is the contract of
that implementation (`lib/firmware_hal/actions.py`).

## The five mechanical rules

1. **Dry-run is the default.** `cpu epp set balance_performance` without
   `--confirm` returns the exact plan — current values, targets, the diff —
   and writes nothing. The same holds over MCP: `confirm: false` (the
   default) is a plan request, not a write.
2. **Two keys for one write.** Applying requires an explicit second key
   (`--confirm` on the CLI, `confirm: true` over MCP). There is no timeout
   trickery, no "force" flag, no environment shortcut.
3. **Backup before write.** Every applied write pushes the previous state
   into the rollback store
   (`$XDG_STATE_HOME/omarchy-firmware/rollback/<target>.json`, last ten
   frames kept). `undo` (`cpu epp undo --confirm`, `fans curve undo
   --confirm`) restores the latest frame and is itself journaled as
   `rolled-back`.
4. **The curve can never cap cooling.** A fan curve is refused before any
   write unless: 2-7 points, strictly ascending temperatures (20-90 °C),
   pwm values 0-255, **the last point at pwm=255 and at most 90 °C**. A
   curve whose tail is missing or capped is refused with the reason — the
   machine must always be allowed to save itself.
5. **Only the declared targets.** EPP writes touch only
   `energy_performance_preference` files; fan curves touch only
   `pwm*_enable` and `pwm*_auto_point*` attributes of an nct67xx-family
   chip. There is no generic "write this file" path. Other Super I/O
   families are refused honestly (their auto-point semantics are not
   guessed), and the T2/T3 domains (NVRAM, flash) have no call path.

## What is written, exactly

**cpu.epp.set** — one value, applied to every existing
`/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference`.
The value must be in the chip's own
`energy_performance_available_preferences` list; anything else is refused.

**fans.curve.set** — the curve object:

```json
{"hwmon": "nct6798", "pwm": 1, "points": [
  {"temp": 40, "pwm": 90},
  {"temp": 60, "pwm": 140},
  {"temp": 85, "pwm": 255}
]}
```

The chip is located by its `name` file under `/sys/class/hwmon`, must be
nct67xx-family, must expose the output (`pwm{N}`) and at least two
auto-point slots. If the curve has fewer points than the chip exposes, the
remaining slots are filled with the last point (hold 255 at the top); if it
has more points than slots, it is **refused** — silently dropping a point
could drop the mandatory 255 tail. Writes happen points-first, mode-switch
(`pwm_enable = 5`, Smart Fan IV) last: the fan keeps its previous behaviour
until the whole curve is in place.

## The journal carries the truth

Every T1 call is journaled with its exact status:

| status | meaning |
|---|---|
| `dry-run` | plan returned, nothing written (the default outcome) |
| `applied` | writes done, backup frame id recorded |
| `rolled-back` | undo restored the previous values |
| `refused` | a guard or validation said no — with the reason |
| `error` | something failed mid-call (never silently) |

`journal.show()` therefore reads like an audit trail: who proposed what,
what was written, what was restored.

## Tests prove each rule

The suite (`tests/test_suite.py`, T1 sections) runs against a temp sysfs
tree injected through `FW_SYSFS_CPU` / `FW_SYSFS_HWMON`:

- dry-run writes nothing (file content asserted unchanged);
- invalid EPP value refused; curve tail != 255 refused; tail > 90 °C
  refused; non-ascending temps refused; single point refused;
- unsupported chip family refused; more points than slots refused;
- confirm applies, backup exists, undo restores byte-for-byte;
- MCP `cpu.epp.set` without `confirm` is a dry-run and its journal entry
  says so (`tests/mcp_smoke.py`).

## Why only two writes

Volume 4's catalogue lists 18 named findings; only a small subset has a
software remedy that is *reversible* (the reversibility criterion is what
defines T1). Paste, dusting, reseating, cable swaps are physical; BIOS
settings beyond EPP/fans are NVRAM (T2, Phase 4, human-confirmed);
flashing is T3 — human-only forever. "Omniscience in reading, chastity in
writing" is the doctrine; these two writes are the chastity's exception,
engineered to stay reversible.
