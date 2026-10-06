# V10 Display Engine: original, motorized, 90 deg V10

An original F1-style naturally aspirated V10 display model, about 340 mm long
on a 400 x 280 mm display base. Working split-pin crankshaft, 10 con-rods on
ball bearings, 10 floating pistons on stainless guide rails (they never touch
their bores), visible through cut-away cylinder windows. A hidden, silent
stepper drives it through a 3:1 belt; three LEDs over every bore flash in the
firing order 1-6-5-10-2-7-3-8-4-9 exactly when each piston reaches the top.

Designed as a premium production piece: **50 units**, years of running, built
by one person with a hex key, a soldering iron and a small vise.

**Everything is generated from code.** Every dimension, fit and clearance lives
in [`config.py`](config.py); the firmware's engine timing is generated from the
same file. If something must change, change a number there and rebuild. Never
edit an STL by hand.

## Status

| Phase | Content | Status |
|---|---|---|
| 1 | Crankcase, valley beam, banks, end plates, crank, rods, pistons, rails | **complete, verified in CAD** |
| 2 | Motor drive (3:1 GT2 belt), display base | **complete, verified in CAD** |
| 3 | Heads, cam covers, side panels, end covers, intake trumpets + throttle frame, exhausts, coil packs, LED strips | **complete, verified in CAD** |
| 4 | Electronics, wiring diagram, firmware | **complete; firmware compiles, logic unit-tested, timing cross-checked against the CAD** |
| 5 | BOM, assembly instructions, burn-in, QC, maintenance, 50-unit print and production plan | **complete** |

### What has been verified, and what has not

Verified by the tools in this repository (re-run them after any change):

* **Every printed part** sliced with the production settings: no overhang over
  45 deg, no bridge over 25 mm, no unsupported ring ceilings, every part one
  solid, every part under 300 mm (`tools/printcheck.py`, `docs/PRINT_REPORT.md`).
* **No collisions:** every pair of static parts; the drive with both belt
  lengths and the motor at both ends of its slots; every moving part against
  every other part over a full revolution in 6 deg steps; smallest running gaps
  reported (`tools/verify_all.py`, `docs/CLEARANCE_REPORT.md`).
* **The build order works:** each part can travel along its documented
  assembly path to its place without hitting anything (`tools/verify_all.py`).
* **Firmware:** compiles for the ESP32 with pinned library versions, unit tests
  pass on a PC, LED timing = CAD piston TDC for all 10 cylinders, hall magnet
  pocket where the firmware expects it (`tools/check_firmware.py`).
* **Electronics model:** every net closed, every GPIO matches the firmware
  (`tools/electronics.py`).

**Not verifiable without building one:** the real feel of the fits, noise,
motor temperature, LED brightness/look, 48 h endurance. CAD and simulation
remove the design mistakes; they cannot replace a first article. **Build unit
#1 completely and run its 48 h burn-in before committing material and printer
time to the other 49** (see `docs/PRODUCTION_PLAN.md`, gate 1).

## Design-for-manufacturing pass (in progress - read these first)

**Nothing has been printed yet.** The DFM pass turned every guessed fit into a
tested one *before* any engine part is printed:

1. [`docs/MORNING_SUMMARY.md`](docs/MORNING_SUMMARY.md) - what was done overnight, decisions, what is needed next
2. [`fits.py`](fits.py) - **the one file** holding every tolerance / clearance / fit
3. [`docs/COUPON_PRINT_GUIDE.md`](docs/COUPON_PRINT_GUIDE.md) - print the 15 coupons first (each < 25 min)
4. [`docs/TEST_CHECKLIST.md`](docs/TEST_CHECKLIST.md) - what to measure, which number to change
5. [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/DFM_PHASE0.md`](docs/DFM_PHASE0.md), [`docs/RISKS_FIRST_ENGINE.md`](docs/RISKS_FIRST_ENGINE.md)
6. [`docs/PROTO_BOM.md`](docs/PROTO_BOM.md) - the only order to place until engine #1 runs

## Start here

1. [`docs/DESIGN_NOTES.md`](docs/DESIGN_NOTES.md) - why it is built this way
2. [`docs/BOM.md`](docs/BOM.md) - everything to buy, print and machine, costs x1 / x50
3. [`docs/PRODUCTION_PLAN.md`](docs/PRODUCTION_PLAN.md) - print plan, printer-hours, timeline for 50
4. [`docs/ASSEMBLY.md`](docs/ASSEMBLY.md) - build order with checklists
5. [`docs/ELECTRONICS.md`](docs/ELECTRONICS.md) - wiring, controller board, firmware, bring-up
6. [`docs/BURN_IN.md`](docs/BURN_IN.md), [`docs/QC_CHECKLIST.md`](docs/QC_CHECKLIST.md), [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md)

## Part numbering

| # | Part | Qty | Made by |
|---|---|---|---|
| T1-T8 | fit coupons (15 small prints, print first) | 1 set | print (PLA, then ASA) |
| 01 | crankcase (open-top U) | 1 | print |
| 02 | valley beam | 1 | print |
| 03 | cylinder bank (both identical) | 2 | print |
| 04 | end plate (both identical, 608 bearing) | 2 | print |
| 05 | crank end web | 2 | print |
| 06 | crank segment "54" | 2 | print |
| 07 | crank segment "198" | 2 | print |
| 08 | con-rod | 10 | print |
| 09 | piston | 10 | print |
| 10 | cylinder head (both identical) | 2 | print |
| 11 | cam cover (magnetic) | 2 | print |
| 12 | side panel (magnetic) | 2 | print |
| 13 | intake trumpet | 10 | print (or M05) |
| 14 / 15 | exhaust header bank A / bank B | 1 + 1 | print |
| 16 | coil pack | 10 | print |
| 17 | throttle frame | 1 | print |
| 18 | end cover (magnetic, front + rear identical) | 2 | print |
| 19 / 20 | base front half (motor) / rear half (controls, board) | 1 + 1 | print |
| 21 | base bottom panel (both identical) | 2 | print |
| M01 | split crankpin | 5 | CNC, stainless |
| M02 | main shaft | 2 | CNC, stainless |
| M03 | guide rail 3 x 57 | 10 | cut from ground rod |
| M04 | pulley spacer | 1 | CNC, stainless |
| M05 | intake trumpet, aluminium (optional upgrade of 13) | 10 | CNC |
| M06 | bearing spacer ring 6 x 7.5 x 0.75 | 10 | CNC, stainless |
| P1 / P2 | printable stand-ins for M01 / M02 (early fit tests only) | 5 / 2 | print (PETG) |

**19 unique printed parts** (budget 40, pistons and rods not counted). **One
screw size** in the whole engine: M3 x 8 (92 per engine).

## Folder layout

```
v10-engine/
  config.py            ALL dimensions, fits, firing order, speeds (edit this)
  build_all.py         regenerates every STL/STEP, preview and drawing
  cad/                 the parametric model (CadQuery)
    common.py          helpers: placement, export, crush ribs, bridged steps
    coupons.py         test coupons T1-T8;  partnum.py  engraved part numbers
    crank.py  rods_pistons.py  block.py  styling.py  drive.py  base.py
    assembly.py        full engine at any crank angle, interference checks
  firmware/            ESP32 controller (Arduino IDE / PlatformIO), unit tests
  tools/
    verify_all.py      interference, clearance and assembly-path verification
    printcheck.py      slices every part, overhang/bridge analysis, times, grams
    check_fits.py      fails if a clearance is written inside a part file
    plates.py          coupon + motion-test plates (3MF) for the H2C;  proto_bom.py
    check_firmware.py  firmware vs CAD timing + unit tests
    gen_firmware_config.py  config.py -> firmware/v10_engine/engine_geometry.h
    electronics.py     netlist, pin tables, schematic and wiring drawings
    bom.py             BOM, costs, shopping list
    burnin_logger.py   logs the burn-in of many engines over USB
    render.py  drawings.py  animate.py
  stl/                 numbered STL + STEP for every part (print orientation)
  renders/  drawings/  docs/
```

## Regenerating and re-verifying

```bash
pip install -r requirements.txt
python config.py                    # summary + self-checks
python build_all.py                 # STL/STEP, renders, drawings
python tools/printcheck.py          # slice + printability (needs PrusaSlicer CLI)
python tools/verify_all.py          # interferences, clearances, assembly paths (~20 min)
python tools/check_firmware.py      # firmware vs CAD + unit tests (needs g++)
python tools/electronics.py         # netlist, tables, drawings
python tools/bom.py                 # BOM, costs, shopping list
```

On a headless Linux machine the renderer needs EGL or OSMesa
(`apt install libegl1 libosmesa6`).

## Key design facts

* 90 deg V; bank A (cylinders 1-5) is the left bank seen from the front and sits
  8 mm ahead of bank B. The crank turns **clockwise seen from the front**.
* Stroke 26 mm, rod 62 mm, piston 44 mm, **cylinder pitch 50 mm** (= 3 LEDs of a
  60/m strip).
* Split crankpins at 18 deg give true 72 deg even firing.
* 2 x 608ZZ main bearings, 10 x 686ZZ big-end bearings, 30 bronze bushings.
* Pistons never touch the bores (0.8 mm gap): they slide on stainless rails.
* Every press fit uses crush ribs: no tolerance tuning, no test print.
* Speed 20-120 RPM, StealthChop: silent.
* Limited edition: a numbered engraved plate (H14, "No. 07 / 50") sits in a bevelled recess
  on the base front (`EDITION_PLATE` in config.py; `enabled=False` for a plain front).

This design is original. It is not based on any team's engine or any existing
model, and it contains no logos or trademarks.
