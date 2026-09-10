"""Physical diagnostics by sensor correlation — the fw.diag.thermal tool. T0.

What the BIOS cannot do (vol. 3, ch. 1-3): tell a missing thermal paste
apart from a dead pump or a clogged radiator. The BIOS sees Tctl, applies
a throttle at Tjmax, then shuts down — without ever saying why. This module
applies a deterministic thermal network to the same hwmon sensors as
volume 2 (fig. 5.1) and names the fault:

    R_th = (T_die - T_coolant) / P_package   (°C/W, steady state)

Frugal architecture (vol. 3, ch. 4) — no resident intelligence:
  - L1 collection   : the same T0 reads as the rest of the base;
  - L2 rules        : this file, a few kB of statistics and thresholds;
  - L3 reasoning    : the agent (via MCP), called ONLY if L2 says
    "attention" or "critical". No daemon: the doctor runs one-shot
    (optional systemd timer) and hands back control.

Honesty (vol. 3, ch. 6): every finding carries its confidence. Without a
coolant sensor or a power counter, paste is detected through the time
constant (active --probe diagnostic), not through R_th; without a load,
the verdict stays "undetermined" rather than falsely reassuring.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import statistics
import time
from pathlib import Path

from . import journal, sensors

PKG_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = PKG_ROOT / "tests" / "fixtures" / "scenarios"

# ---------------------------------------------------------------------------
# Thresholds — orders of magnitude calibrated for a 5950X (PPT 142 W,
# Tjmax 90 °C) on a B450/B550 board; fine calibration is done by the
# baseline (--no-record disables writing the reference baseline to XDG
# state).
# ---------------------------------------------------------------------------
SEUILS = {
    "pump_min_rpm": 300,           # below this, a pump is dead
    "fan_min_rpm": 300,            # below this, a fan is stopped
    "tctl_load_attention": 82.0,
    "tctl_tjmax": 89.5,            # plateau ≈ Tjmax: thermal protection engaged
    "dt_idle_suspect": 25.0,       # Tctl - ambient proxy at idle (°C)
    "rth_liquid_ok": 0.32,         # °C/W — 240/360 AIO, good paste, proper mount
    "rth_liquid_suspect": 0.42,
    "rth_liquid_critical": 0.55,
    "rth_air_ok": 0.40,            # °C/W — big tower cooler
    "rth_air_suspect": 0.52,
    "rth_air_critical": 0.65,
    "rise_suspect_s": 8.0,         # reaching 85 °C in under 8 s = suspect interface
    "slope_critical_cs": 0.5,      # sustained °C/s: runaway
    "plateau_ok": 78.0,
    "plateau_attention": 88.0,
    "vrm_attention": 89.0,
    "v12_min": 11.40,              # V — Super I/O ADC reading (± 3 %)
    "generic_temp": 85.0,
    "coolant_delta_attention": 15.0,
    "trend_pct_attention": 25.0,   # cooling efficiency drop vs baseline
    "trend_min_age_days": 7,
    "trend_min_abs": 0.05,         # avoids noise on small deltas
}


# ---------------------------------------------------------------------------
# Normalization — hwmon chips -> one flat, chip-independent sample
# ---------------------------------------------------------------------------
def normalize(chips: list[dict]) -> dict:
    """Reduce the output of sensors.collect() to a canonical sample."""
    s: dict = {
        "t": time.time(), "tctl": None, "ambient": None, "coolant": None,
        "vrm": None, "power_w": None, "fans": {}, "volts": {}, "phase": None,
    }
    for chip in chips:
        name = (chip.get("name") or "").lower()
        for lab, val in (chip.get("temps") or {}).items():
            l = lab.lower()
            if "tctl" in l or "tdie" in l:
                if s["tctl"] is None or "tctl" in l:
                    s["tctl"] = val
            elif "coolant" in l or "liquide" in l or "t_sensor" in l.replace(" ", "_"):
                s["coolant"] = val
            elif "vrm" in l:
                s["vrm"] = val
            elif "systin" in l:
                s["ambient"] = val
            elif l.startswith("temp"):
                s["generic_temps"] = s.get("generic_temps", {})
                s["generic_temps"][f"{name}/{lab}"] = val
        for lab, rpm in (chip.get("fans") or {}).items():
            key = "pump" if "pump" in lab.lower() else lab
            s["fans"][key] = rpm
        for lab, v in (chip.get("volts") or {}).items():
            s["volts"][lab] = v
    # remaining generic temperatures: candidates for hot sensors (ch. 3, S10)
    hot = {
        k: v for k, v in s.get("generic_temps", {}).items()
        if v is not None and v >= SEUILS["generic_temp"]
    }
    if hot:
        s["hot_sensors"] = hot
    return s


def read_sample(fixture_dir=None) -> dict:
    """One instantaneous sample (T0) — live or standard audit fixture."""
    return normalize(sensors.collect(fixture_dir)["chips"])


# ---------------------------------------------------------------------------
# Bundled scenarios — pre-recorded series, the "no hardware" mode
# ---------------------------------------------------------------------------
def list_scenarios() -> list[dict]:
    out = []
    if SCENARIO_DIR.is_dir():
        for p in sorted(SCENARIO_DIR.glob("*.json")):
            try:
                meta = json.loads(p.read_text(encoding="utf-8")).get("meta", {})
                out.append({"name": p.stem, "meta": meta})
            except json.JSONDecodeError:
                out.append({"name": p.stem, "meta": {"error": "unreadable scenario"}})
    return out


def load_scenario(name_or_path: str) -> dict:
    """Load a scenario by short name or absolute path."""
    p = Path(name_or_path)
    if not p.is_absolute():
        p = SCENARIO_DIR / f"{name_or_path}.json"
    if not p.exists():
        raise FileNotFoundError(
            f"scenario not found: {name_or_path} "
            f"(bundled: {', '.join(sorted(x.stem for x in SCENARIO_DIR.glob('*.json'))) or 'none'})"
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _med(vals: list[float]) -> float | None:
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 2) if vals else None


# ---------------------------------------------------------------------------
# The signature engine — L2, deterministic, no network, no model
# ---------------------------------------------------------------------------
def _finding(fid: str, severity: str, title: str, evidence: dict,
             hypothesis: str, next_steps: str, confidence: str) -> dict:
    return {
        "id": fid, "severity": severity, "title": title,
        "evidence": evidence, "hypothesis": hypothesis,
        "next_steps": next_steps, "confidence": confidence,
    }


def diagnose(samples: list[dict], meta: dict | None = None,
             baseline: list[dict] | None = None) -> dict:
    """Apply signatures S1-S12 from vol. 3 (table 3.1) to a series.

    All the value is here: the same Tctl the BIOS watches, correlated with
    the other sensors, becomes a named diagnosis instead of a hard stop.
    Thresholds are owned orders of magnitude; every finding carries its
    confidence and its quantified evidence.
    """
    meta = meta or {}
    cooling = meta.get("cooling") or (
        "liquid" if any(s.get("coolant") is not None for s in samples) else None
    )
    load_marks = [s for s in samples if s.get("phase") == "load"]
    # Steady state: R_th and load measurements are read on the plateau
    # (last 60 % of the load), not during the ramp — that is the very
    # definition of a thermal resistance (vol. 3, ch. 3).
    if load_marks and len(load_marks) >= 5:
        steady = load_marks[int(len(load_marks) * 0.4):]
    else:
        steady = [s for s in samples if s.get("phase") in ("load", None)]
    tctl_med = _med([s.get("tctl") for s in steady])
    ambient_med = _med([s.get("ambient") for s in samples])
    coolant_med = _med([s.get("coolant") for s in steady])
    vrm_med = _med([s.get("vrm") for s in steady])
    power_med = _med([s.get("power_w") for s in steady])

    findings: list[dict] = []
    fans = {}
    for s in samples:
        fans.update(s.get("fans") or {})
    has_fans = bool(fans)

    # --- S1/S2: pump and fans ---------------------------------------------
    for key, rpm in sorted(fans.items()):
        if rpm is None or rpm >= (SEUILS["pump_min_rpm"] if key == "pump"
                                  else SEUILS["fan_min_rpm"]):
            continue
        if key == "pump" and tctl_med is not None and tctl_med > 80:
            findings.append(_finding(
                "pump-dead", "critical",
                "Cooling loop pump stopped",
                {"pump_rpm": rpm, "tctl_med": tctl_med, "coolant_med": coolant_med},
                "The pump no longer circulates: heat accumulates in the block, "
                "the radiator fans spin for nothing.",
                "Power off under load, check pump cable/Pump_Fan header and "
                "rotation; a dead pump gets replaced — do not resume loading.",
                "high" if coolant_med is not None else "medium"))
        else:
            sev = "critical" if tctl_med is not None and tctl_med > 78 else "attention"
            findings.append(_finding(
                "fan-zero-rpm", sev,
                f"Fan \u00ab {key} \u00bb at 0 RPM",
                {"header": key, "rpm": rpm, "tctl_med": tctl_med},
                "Dead head, unplugged cable, or PWM curve at 0 % below a "
                "temperature that is too high.",
                "Check the cable and spin by hand; fix the PWM curve in the "
                "BIOS (guided T3) or via the future T1 HAL.",
                "medium"))

    # --- S3: coolant hot -> radiator / airflow ------------------------------
    if (coolant_med is not None and ambient_med is not None
            and coolant_med - ambient_med >= SEUILS["coolant_delta_attention"]):
        findings.append(_finding(
            "coolant-hot", "attention",
            "Coolant well above ambient",
            {"coolant_med": coolant_med, "ambient_med": ambient_med,
             "delta": round(coolant_med - ambient_med, 1)},
            "The radiator sheds heat poorly: weak radiator fans, insufficient "
            "case airflow or a clogged radiator.",
            "Check radiator fans, filters and airflow direction; the "
            "die->liquid path stays healthy (separate R_th).",
            "medium"))

    # --- S4: R_th — the physical signature of paste / mounting --------------
    # If the pump is already identified as dead, it explains the resistance:
    # no double diagnosis (honesty of vol. 3, ch. 6).
    pump_dead = any(f["id"] == "pump-dead" for f in findings)
    rth = None
    if (not pump_dead and coolant_med is not None and power_med is not None
            and tctl_med is not None and tctl_med >= 65):
        rth = round((tctl_med - coolant_med) / power_med, 3)
        ok = SEUILS["rth_liquid_ok"] if cooling == "liquid" else SEUILS["rth_air_ok"]
        susp = (SEUILS["rth_liquid_suspect"] if cooling == "liquid"
                else SEUILS["rth_air_suspect"])
        crit = (SEUILS["rth_liquid_critical"] if cooling == "liquid"
                else SEUILS["rth_air_critical"])
        if rth >= susp:
            sev = "critical" if rth >= crit else "attention"
            findings.append(_finding(
                "interface-degraded", sev,
                "Die->liquid thermal resistance abnormally high (paste / mounting)",
                {"r_th": rth, "unit": "°C/W", "threshold_ok": ok,
                 "threshold_suspect": susp,
                 "tctl_med": tctl_med, "coolant_med": coolant_med, "power_med": power_med,
                 "cooling": cooling or "unknown"},
                "Die -> cold plate conduction is degraded: paste absent, dried "
                "out, or cooler poorly mounted. The liquid itself stays cold — "
                "exactly the case the BIOS cannot name.",
                "Redo the thermal joint and re-mount the cooler (cross "
                "pattern, progressive torque); aim for R_th < " + str(ok) + ".",
                "high" if power_med > 100 else "medium"))

    # --- S5: idle DeltaT — weak signal, no load ------------------------------
    if (findings == [] and tctl_med is not None and ambient_med is not None
            and tctl_med - ambient_med >= SEUILS["dt_idle_suspect"]
            and tctl_med > 55 and (power_med is None or power_med < 60)):
        findings.append(_finding(
            "interface-degraded", "attention",
            "Excessive Tctl / ambient gap at idle",
            {"tctl_med": tctl_med, "ambient_med": ambient_med,
             "delta": round(tctl_med - ambient_med, 1),
             "threshold": SEUILS["dt_idle_suspect"]},
            "At idle, healthy paste keeps the die within 10-15 °C of case "
            "ambient; beyond 25 °C, mounting or paste is suspect.",
            "Confirm with an active diagnostic: omarchy-firmware diag probe "
            "(measures the time constant under controlled load).",
            "low"))

    # --- S6/S7/S8: active diagnostics (time constant, runaway, plateau) ------
    if load_marks:
        t0 = load_marks[0].get("t", 0.0)
        rise = None
        for s in load_marks:
            if (s.get("tctl") or 0) >= 85.0:
                rise = round(s["t"] - t0, 1)
                break
        plateau = _med([s.get("tctl") for s in load_marks[int(len(load_marks) * 0.4):]])
        end = load_marks[-1]
        start = load_marks[max(0, int(len(load_marks) * 0.2))]
        dt = max(end["t"] - start["t"], 1e-6)
        slope = round(((end.get("tctl") or 0) - (start.get("tctl") or 0)) / dt, 3)

        if rise is not None and rise < SEUILS["rise_suspect_s"] and not pump_dead:
            findings.append(_finding(
                "instant-rise", "attention",
                f"Reached 85 °C in {rise} s under controlled load",
                {"t_rise_s": rise, "threshold": SEUILS["rise_suspect_s"],
                 "t0": t0},
                "A healthy interface damps the rise (10-20 s on a 5950X); "
                "a jump in under 8 s points to a failing die/cold plate "
                "contact — paste absent or mounting.",
                "Redo the thermal joint; if the rise persists, check contact "
                "and mounting torque.", "medium"))

        if slope >= SEUILS["slope_critical_cs"] and (end.get("tctl") or 0) >= 88:
            findings.append(_finding(
                "runaway", "critical",
                "Undamped thermal slope at end of load",
                {"slope": slope, "unit": "°C/s", "tctl_end": end.get("tctl")},
                "Temperature no longer stabilizes: cooling cannot keep up with "
                "the power (pump, airflow, or contact).",
                "Stop the load; go back over the pump/fan/interface findings "
                "above.", "medium"))

        if plateau is not None and plateau >= SEUILS["tctl_tjmax"]:
            # power fold-back = thermal protection engaged
            pw = [s.get("power_w") for s in load_marks if s.get("power_w") is not None]
            fold = None
            if len(pw) >= 6:
                third = max(3, len(pw) // 3)
                fold = round(statistics.median(pw[:third])
                             / max(statistics.median(pw[-third:]), 1e-6), 2)
            findings.append(_finding(
                "thermal-protection-active", "info",
                "Tjmax reached: power fold-back observed (what the BIOS does silently)",
                {"plateau_tctl": plateau, "power_fold_x": fold,
                 "tjmax": 90},
                "The processor reduced its frequency to survive. This is the "
                "BIOS's only 'diagnosis': it throttles, then shuts down if it "
                "continues — never saying why.",
                "Treat the root cause (findings above), not the symptom.",
                "high"))
        elif plateau is not None and plateau >= SEUILS["plateau_attention"]:
            findings.append(_finding(
                "insufficient-cooling", "attention",
                f"Thermal plateau {plateau} °C under controlled load",
                {"plateau_tctl": plateau, "threshold_ok": SEUILS["plateau_ok"],
                 "power_med": power_med},
                "Marginal cooling: tired paste, airflow or PWM curve to fix; "
                "the margin before throttle is thin.",
                "Redo the joint, blow the dust, retune the curves — then run "
                "diag probe again to measure the gain.",
                "medium"))

    # --- S9: VRM --------------------------------------------------------------
    if vrm_med is not None and vrm_med >= SEUILS["vrm_attention"]:
        findings.append(_finding(
            "vrm-hot", "attention",
            "Power delivery (VRM) above 89 °C",
            {"vrm_med": vrm_med, "threshold": SEUILS["vrm_attention"]},
            "On B450/B550 boards with lightly-cooled VRMs, a 5950X under "
            "sustained load heats the stage: the CPU may drop frequency "
            "without Tctl explaining why.",
            "Improve airflow over the socket, retune the case-fan curve; "
            "limit PBO if VRM throttle persists.",
            "medium"))

    # --- S10: 12 V rail -------------------------------------------------------
    v12 = _med([s.get("volts", {}).get("in1") for s in samples])
    if v12 is not None and v12 < SEUILS["v12_min"]:
        findings.append(_finding(
            "v12-low", "attention",
            f"+12 V rail measured at {v12} V",
            {"v12_med": v12, "threshold": SEUILS["v12_min"],
             "precision": "Super I/O ADC ± 3 %"},
            "Sag under load: PSU at its limit, cable or connector suspect. "
            "The ADC reading is coarse but such a low value is still a real "
            "signal.",
            "Retest with a multimeter or another rail/PSU; watch for freezes "
            "and random resets.", "low"))

    # --- S11: hot generic sensors ----------------------------------------------
    for s in samples:
        for k, v in (s.get("hot_sensors") or {}).items():
            findings.append(_finding(
                "hot-sensor", "info",
                f"Sensor \u00ab {k} \u00bb at {v} °C",
                {"sensor": k, "value": v, "threshold": SEUILS["generic_temp"]},
                "A hot spot outside the CPU: SSD, chipset, PCH — often a "
                "locally insufficient airflow.",
                "Identify the sensor location and its local airflow.",
                "medium"))

    # --- S12: longitudinal trend (what no BIOS keeps) --------------------------
    base = baseline if baseline is not None else load_baseline()
    if base:
        trend = compare_trend(base, {
            "mode": "probe" if load_marks else "quick",
            "rth": rth, "dt_idle": (round(tctl_med - ambient_med, 1)
                                    if tctl_med is not None and ambient_med is not None
                                    else None),
        })
        if trend:
            findings.append(trend)

    # --- verdict ----------------------------------------------------------------
    sev_order = {"critical": 3, "attention": 2, "info": 1}
    findings.sort(key=lambda f: -sev_order.get(f["severity"], 0))
    if any(f["severity"] == "critical" for f in findings):
        verdict, confidence = "critical", "high"
    elif any(f["severity"] == "attention" for f in findings):
        verdict, confidence = "attention", "high"
    elif has_fans and tctl_med is not None and tctl_med <= 70:
        verdict = "healthy (at idle — run diag probe to validate under load)"
        confidence = "medium"
    else:
        verdict, confidence = "undetermined", "low"

    from . import __version__
    return {
        "tool": "fw.diag.thermal",
        "mode": "probe" if load_marks else "quick",
        "cooling": cooling or "unknown",
        "measurements": {
            "tctl_med": tctl_med, "ambient_med": ambient_med,
            "coolant_med": coolant_med, "vrm_med": vrm_med,
            "power_med": power_med, "r_th": rth,
            "fans": fans, "v12_med": v12,
            "samples": len(samples),
            "confidence": confidence,
        },
        "findings": findings,
        "verdict": verdict,
        "hal_version": __version__,
        "note": ("R_th and signatures: 5950X-calibrated orders of magnitude; "
                 "every finding carries its evidence — never judge hardware "
                 "on a single threshold (vol. 3, ch. 6)."),
    }


# ---------------------------------------------------------------------------
# Longitudinal baseline — the memory the BIOS does not have
# ---------------------------------------------------------------------------
def _baseline_path() -> Path:
    return journal.state_dir() / "baseline.json"


def load_baseline() -> list[dict]:
    p = _baseline_path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def record_baseline(result: dict) -> dict | None:
    """Append today's reference baseline (T0: stays re-readable)."""
    m = result.get("measurements", {})
    entry = {
        "ts": time.strftime("%Y-%m-%d"),
        "mode": result.get("mode", "quick"),
        "tctl_med": m.get("tctl_med"),
        "rth": m.get("r_th"),
        "dt_idle": (round(m["tctl_med"] - m["ambient_med"], 1)
                    if m.get("tctl_med") is not None and m.get("ambient_med") is not None
                    else None),
    }
    try:
        entries = load_baseline()
        entries.append(entry)
        _baseline_path().write_text(
            json.dumps(entries[-200:], ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        return None
    return entry


def _age_days(iso: str) -> float:
    try:
        return (time.time() - time.mktime(time.strptime(iso, "%Y-%m-%d"))) / 86400.0
    except ValueError:
        return 0.0


def compare_trend(baseline: list[dict], now: dict) -> dict | None:
    """Compare against the oldest baseline entry of the same mode (>= 7 days).

    This is slow-degradation detection — dust, drying paste — invisible on
    every individual boot and therefore invisible to the BIOS, which keeps
    no thermal memory.
    """
    mode = now.get("mode", "quick")
    old_entries = [b for b in baseline
                   if b.get("mode") == mode and _age_days(b.get("ts", "")) >= SEUILS["trend_min_age_days"]]
    if not old_entries:
        return None
    old = min(old_entries, key=lambda b: _age_days(b.get("ts", "")))
    for metric in ("rth", "dt_idle"):
        o, n = old.get(metric), now.get(metric)
        if o is None or n is None or o <= 0:
            continue
        pct = round((n - o) / o * 100.0, 1)
        if pct >= SEUILS["trend_pct_attention"] and (n - o) >= SEUILS["trend_min_abs"]:
            return _finding(
                "gradual-degradation", "attention",
                f"Cooling efficiency degraded by {pct} % since {old['ts']}",
                {"metric": metric, "old": o, "current": n, "pct": pct,
                 "baseline_date": old["ts"], "days": round(_age_days(old["ts"]))},
                "A slow degradation over weeks is the signature of a needed "
                "dust cleaning (filters, radiator) or of drying paste — "
                "invisible on each individual boot.",
                "Dust off filters and radiators, then run diag probe again "
                "and compare: the baseline should come back toward " + str(o) + ".",
                "medium")
    return None


# ---------------------------------------------------------------------------
# Active diagnostic (--probe) — controlled load, then back to idle
# ---------------------------------------------------------------------------
def _burn(_unused, stop_event):
    x = 1.000001
    while not stop_event.is_set():
        for _ in range(200_000):
            x = x * 1.0000001 % 10.0


def run_probe(seconds: int = 30, fixture=None) -> tuple[list[dict], dict]:
    """Controlled load on half the cores, 1 Hz sampling.

    No write, no configuration: we heat on purpose, we measure, we hand
    back. The pattern (idle -> load -> idle) gives the time constant the
    passive mode cannot see.
    """
    if fixture is not None:
        sc = load_scenario(fixture) if isinstance(fixture, str) else fixture
        return sc["samples"], sc.get("meta", {})

    n_workers = max(1, (os.cpu_count() or 4) // 2)
    stop = multiprocessing.Event()
    procs = [multiprocessing.Process(target=_burn, args=(None, stop), daemon=True)
             for _ in range(n_workers)]
    samples: list[dict] = []

    def snap(phase: str) -> None:
        s = read_sample()
        s["phase"] = phase
        s["power_w"] = _live_power()
        samples.append(s)

    try:
        for _ in range(5):          # idle: the baseline line
            snap("idle"); time.sleep(1.0)
        for p in procs:
            p.start()
        t0 = time.time()
        while time.time() - t0 < seconds:
            snap("load"); time.sleep(1.0)
        stop.set()
        for p in procs:
            p.join(timeout=2)
        for _ in range(12):         # idle: the decay
            snap("idle"); time.sleep(1.0)
    finally:
        stop.set()
        for p in procs:
            if p.is_alive():
                p.terminate()
    return samples, {"cooling": None, "probe_live": True}


def _live_power() -> float | None:
    """Package power if a counter exposes it — otherwise None, owned.

    On stock AM4, no hwmon counter exposes the PPT: the base does not
    guess. R_th then stays unavailable and the fold-back signatures (time
    constant, plateau, DeltaT) take over — see the limits table in vol. 3
    (ch. 6).
    """
    for cand in ("/sys/class/hwmon/zenpower/power1_input",
                 "/sys/bus/pci/devices/0000:00:18.3/hwmon/power1_input"):
        try:
            with open(cand) as fh:
                return round(int(fh.read().strip()) / 1_000_000, 1)
        except (OSError, ValueError):
            continue
    return None


# ---------------------------------------------------------------------------
# Orchestration — the single CLI / MCP entry point
# ---------------------------------------------------------------------------
def quick(scenario: str | None = None, fixture_dir: str | None = None,
          record: bool = True, probe_seconds: int | None = None) -> dict:
    """Diagnostic in one call: passive (quick) or active (probe)."""
    if scenario:
        sc = load_scenario(scenario)
        samples, meta = sc["samples"], sc.get("meta", {})
        source = f"scenario {scenario}"
    elif probe_seconds:
        samples, meta = run_probe(probe_seconds)
        source = f"live probe {probe_seconds} s"
    elif fixture_dir:
        samples, meta = [read_sample(fixture_dir)], {}
        source = "audit fixture"
    else:
        samples, meta = [read_sample()], {}
        source = "passive live"

    result = diagnose(samples, meta, baseline=load_baseline() if record else None)
    result["source"] = source
    if record:
        result["baseline_entry"] = record_baseline(result)
    return result
