# 48-hour burn-in

Every engine runs 48 hours on the bench before it is packed. The firmware has a
built-in burn-in program, so the only equipment is a shelf, one 12 V adapter per
engine and (recommended) a PC with a powered USB hub for the logs.

## Why 48 h

Most problems of a mechanism like this show up early: a press fit that creeps,
a screw without threadlocker, a belt that was tensioned too hard, a rail with a
burr, a cold solder joint, an LED with a bad pad. 48 h at the profile below is
about **195,000 crank revolutions** (roughly 400 h of normal display use at
idle), with 48 start/stop cycles and hundreds of speed changes.

## The profile (repeats every hour)

| Minutes | Crank speed | What it tests |
|---|---|---|
| 0-10 | 120 RPM (maximum) | driver heat, belt, bearings at full speed |
| 10-20 | 20 RPM (minimum) | low-speed smoothness, stick-slip on the rails |
| 20-40 | 20 -> 120 -> 20 RPM sweep | resonances, LED sync through acceleration |
| 40-58 | 70 RPM | steady running |
| 58-60 | stopped | soft stop / soft start, holding current |

The hall magnet checks the crank position on every revolution. Any lost step
over 8 deg, any revolution without a magnet, any driver error stops the engine,
shows the fault code on the LEDs and ends the burn-in as FAILED.

## Procedure

1. Unit fully assembled and closed (stage H of `ASSEMBLY.md` done), on its own
   adapter, on a flat shelf with 10 cm free around it.
2. Start the burn-in, either:
   * **no PC:** hold START while switching on, with the speed knob turned fully
     clockwise; release START when the ring flashes; or
   * **with logging (recommended):** USB to the hub, then on the PC
     `python tools/burnin_logger.py --start 48` (starts and logs every connected
     engine; one CSV per engine in `burnin_logs/`).
3. Leave it. Look at the shelf twice a day: every engine running, no fault code
   blinking. Note anything you hear.
4. At the end each engine stops and shows **steady green** (passed) or its red
   fault code (failed). The logger prints a summary.

## Pass criteria (all must be true)

- [ ] Firmware reports `BURN-IN PASSED`, no `FAULT` line in the log.
- [ ] Worst sync error in the log under **3.0 deg** (typical: under 1 deg).
- [ ] `min_free_heap` column steady (no downward trend over the 48 h).
- [ ] Motor case under **50 C** at the end of a 120 RPM segment (IR thermometer).
- [ ] Quiet at 20, 70 and 120 RPM: no ticking, knocking or squeak (listen with
      the side panels off, 30 cm away).
- [ ] All torque stripes unbroken; no screw moved.
- [ ] No wear dust (black or bronze powder) under the pistons or at the rail
      tops; wipe each rail with a white cloth: at most a faint grey trace.
- [ ] Belt: no fraying, still centred, tension as in ASSEMBLY F4.
- [ ] LED test (service mode) still perfect on all 30 LEDs.
- [ ] `status` on the console: record the run hours and fault count on the QC sheet.

## If it fails

Note the fault code and the minute it happened (log), fix the cause
(`ELECTRONICS.md` fault table, `MAINTENANCE.md` troubleshooting), and **restart
the full 48 h**. Two failures on the same unit: strip it down and inspect every
sub-assembly before trying again. Keep every failed log - patterns across units
point at process problems early.

## Capacity planning

48 h per unit + 1 h handling. A shelf of 10 engines turns over every ~2 days:
50 engines = 5 rounds = about 10-11 days of burn-in, overlapping with assembly
(see `PRODUCTION_PLAN.md`).
