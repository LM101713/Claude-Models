# V10 Display Engine: original, motorized, 90° V10

An original F1-style naturally aspirated V10 display model, about 355 mm
(14 in) long. It has a working split-pin crankshaft, 10 con-rods on ball
bearings, and 10 floating pistons that can be seen moving through cut-away
cylinder windows. A hidden stepper motor drives it, and each cylinder has an
LED that lights in the firing order 1-6-5-10-2-7-3-8-4-9.

It is designed as a premium production piece: 50 units, years of running, one
person builds each unit with a hex key and a soldering iron.

**Everything is generated from code.** Every dimension, fit and clearance lives
in one file, [`config.py`](config.py). If a part doesn't fit, change a number
there and rebuild. Never edit an STL by hand.

## Project status

| Phase | Content | Status |
|---|---|---|
| 1 | Tolerance test piece, crankcase, cylinder banks, crank, rods, pistons, bearings, pins | **ready for test prints** |
| 2 | Motor drive (belt), display base | not started |
| 3 | Heads, cam covers, magnetic covers, intake trumpets, exhausts, styling | not started |
| 4 | Electronics, wiring diagram, firmware | not started |
| 5 | Production package: final BOM, assembly instructions, burn-in, QC, 50-unit print plan | not started |

## Folder layout

```
v10-engine/
  config.py            ALL dimensions, fits, firing order (edit this, nothing else)
  build_all.py         regenerates every STL/STEP, preview and drawing
  requirements.txt
  cad/
    common.py          shared helpers (placement, export)
    tolerance_test.py  00 tolerance test piece
    crank.py           end webs, crank segments, split crankpin, main shaft
    rods_pistons.py    con-rod, piston, rail, kinematics
    block.py           crankcase, cylinder bank, end plate
    assembly.py        full engine at any crank angle + collision/clearance sweep
  tools/
    render.py          offscreen preview renderer
    drawings.py        dimensioned drawings of the machined parts
  stl/                 numbered STL + STEP for every part (print orientation)
  renders/             preview images
  drawings/            machined-part drawings (PNG + one PDF)
  docs/
    DESIGN_NOTES.md    why the engine is built this way (read this first)
    PHASE1_PRINT_AND_TEST.md   what to print now, settings, fit checklist
```

## Part numbering

| # | Part | Qty | Made by |
|---|---|---|---|
| 00 | tolerance test piece | 1 per material | print |
| 01 | crankcase | 1 | print |
| 02 | cylinder bank (both banks identical) | 2 | print |
| 03 | end plate (front and rear identical) | 2 | print |
| 04 | crank end web | 2 | print |
| 05 | crank segment "54" | 2 | print |
| 06 | crank segment "198" | 2 | print |
| 07 | con-rod | 10 | print |
| 08 | piston | 10 | print |
| M01 | split crankpin | 5 | CNC, stainless |
| M02 | main shaft | 2 | CNC, stainless |
| M03 | guide rail, Ø3 × 54 | 10 | cut from ground rod |
| P1/P2 | printable prototypes of M01/M02 for early fit tests | 5 / 2 | print (prototype only) |

Unique printed parts so far: **6** of the 40 budget (plus pistons and rods).

## Regenerating the files

```bash
pip install -r requirements.txt
python config.py          # prints the firing/crank summary and self-checks
python build_all.py       # all STL/STEP + renders + drawings
python build_all.py --check   # ... plus the full-revolution collision sweep
```

On a headless Linux machine the renderer needs EGL or OSMesa
(`apt install libegl1 libosmesa6`).

## Key design facts

* 90° V, bank A (cyl 1–5) is the left bank seen from the front and sits
  8 mm ahead of bank B.
* The crank turns **clockwise seen from the front** (pulley end).
* Stroke 26 mm, rod 62 mm, piston Ø44 mm, cylinder pitch 52 mm.
* Split crankpins at 18° give true 72° even firing.
* 2 × 608 main bearings, 10 × 686 big-end bearings, 30 × bronze bushings.
* The pistons never touch the bores (0.8 mm gap). They slide on stainless
  rails through bronze bushings.
* All screws are M3 socket head, **M3×8 and M3×16 only**, into brass
  heat-set inserts.
* The whole mechanism is collision-checked in CAD at 10° steps.

See [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) for the reasoning behind
each decision.

This design is original. It is not based on any team's engine or any existing
model, and it contains no logos or trademarks.
