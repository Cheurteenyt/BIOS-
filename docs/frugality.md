# Frugality — the zero-overhead budget

The founding constraint of this project, stated by its owner: *the firmware
must absolutely not become a system heavier than the stock BIOS — that would
be stupid.* This document states the budget, how each line is enforced by
design, and what "no resident intelligence" means precisely.

## The budget, measured

| Item | Cost | Enforcement |
|---|---|---|
| One-shot passive diagnostic (`diag quick`) | ~0.3 s CPU | one process, reads 3 sensor snapshots, exits |
| RAM between runs | 0 | the doctor is a one-shot; no resident process exists |
| Optional systemd timer (every 15 min) | ~0.03 % duty cycle | 3 one-shots/hour, each sub-second |
| SPI flash added | **+0 bytes** | nothing is written to the firmware, ever |
| Network | 0 by default | `--refresh` is the only touch, on human request |
| LLM | never resident | the agent is called only when L2 says attention/critical |
| Dependencies | stdlib only (CLI) | `mcp` optional, lazy-imported |

## The three-layer response, in cost terms

```
L1  collect    — the same T0 sensor reads as the rest of the base
L2  rules      — this repo: a few kB of deterministic statistics and thresholds
L3  reasoning  — the agent, via MCP, ONLY on anomaly (never scheduled, never resident)
```

The point of the layering is economic as much as architectural: L2 is cheap
enough to run on a timer; L3 is expensive by nature, so it runs only when
L2 raises a flag — and it explains instead of watching. The BIOS keeps its
throttle and its emergency shutdown: **the agent explains, the firmware
protects.**

## Why this shape (and not the alternatives)

- **Not a resident daemon.** A daemon watching sensors continuously would
  cost more than it reports — and duplicate what the kernel already does
  (hwmon thresholds, throttling). The one-shot + optional timer shape gives
  the same coverage for ~0.03 % duty.
- **Not an embedded model.** Local LLM inference would multiply the
  machine's idle consumption for a task the agent harness already handles
  better. The intelligence lives in the agent you already run.
- **Not a BIOS replacement.** The vendor firmware keeps its four
  irreplaceable jobs (platform wake, memory training, trust chain, recovery).
  Everything else moves to the OS runtime, where it costs nothing extra and
  stays updateable.
- **Not a fork.** Zero bytes of SPI flash means zero bricks, zero recovery
  risk, zero vendor-warranty conversations.

## The timer is a choice, not a default

`install.sh` copies the systemd units **disabled**. The user opts into the
15-minute longitudinal watch with:

```bash
systemctl --user enable --now omarchy-firmware-doctor.timer
```

That is what buys the S12 signature (slow degradation — dust, drying paste):
no single boot can see a six-month drift, but a 200-entry dated baseline
compared over ≥ 7 days can. The memory the BIOS does not have, for a duty
cycle smaller than a screen saver.
