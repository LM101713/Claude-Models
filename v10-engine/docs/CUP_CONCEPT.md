# Cup production concept (D66)

Liam, 2026-10-07: "this still doesn't look like a NASCAR engine, it's not simplified, and it takes a
while to make". This is the answer to all three: a new exterior drawn on small-block V8 proportions
instead of reworking the F1 V10 body, designed for fast printing from the start. It is a proposal on
the `claude/v8-nascar-restyle` branch; the round-7 skin and the CAD core are untouched.

Build: `tools/cup_concept.py --export` (STLs in `cup/stl/`), renders `--photo` (in `renders/cup/`),
estimate `tools/cup_estimate.py` (writes `cup/estimate.json`).

## Why the old one looked wrong

- The block, heads and banks were the V10 shapes: boxy, tall and short, with windows. A small-block
  V8 is long and low, with narrow heads under long valve covers.
- The cues people know were missing: big round air cleaner, distributor at the back with plug wires,
  long 4-into-1 headers, belt-driven dry-sump pump and water pump at the front, painted block.

## What changed

| | Round 7 | Cup concept |
|---|---|---|
| Printed pieces | 90 | 20 shells + 8 small boots |
| Printer-hours, 0.4 mm nozzle (same model) | 136 h | 90 h |
| Printer-hours, 0.6 mm nozzle, 0.3 mm layers | 73 h | 46 h |
| Same, plinth bought as a cut plate | | **36 h** |
| Filament (0.6 mm) | 3.3 kg | 2.2 kg (1.6 kg without plinth) |
| What moves | 8 pistons, rods, crank behind windows | crank shaft turns the front belt drive and flywheel; LEDs pulse in the boots in firing order |

Both columns use the same estimate model (fitted on the 55 CAD parts that were really sliced; it
gives 136 h for round 7, against the earlier 137 h). Treat as +-20 % until a real slice.

Farm maths for 50 engines at 36 h: 1,800 printer-hours. At about 20 useful hours a day per printer,
4 printers take about 23 days and 8 printers about 12 days (round 7 needed 8 printers for 8 to 10 weeks).

## Parts

| File | Qty | Size mm | h each (0.6) | g each | How it prints |
|---|---|---|---|---|---|
| c01_block | 1 | 221 x 175 x 118 | 7.3 | 360 | pan rail down, hollow, open bottom |
| c02_pan | 1 | 220 x 124 x 29 | 2.3 | 114 | flange down, open top |
| c03_head | 2 | 210 x 67 x 69 | 2.4 | 118 | deck face down, hollow |
| c04_valve_cover | 2 | 196 x 58 x 58 | 1.8 | 87 | flange down, hollow, 45 deg roof inside |
| c05_intake (with throttle body) | 1 | 194 x 128 x 112 | 5.7 | 279 | upright, hollow underneath |
| c06_air_cleaner_base | 1 | 132 x 132 x 27 | 1.4 | 66 | base down, open top (the lid closes it) |
| c07_air_cleaner_lid | 1 | 132 x 132 x 12 | 1.0 | 50 | upright |
| c08_distributor | 1 | 40 x 40 x 100 | 0.8 | 24 | upright |
| c09 / c10 header right / left | 1 + 1 | 232 x 42 x 94 | 2.5 | 100 | on the port flanges, tree supports |
| c11_front_cover (timing cover, water pump, dry-sump pump) | 1 | 90 x 132 x 136 | 1.4 | 60 | back face down |
| c12_alternator | 1 | 22 x 48 x 37 | 0.3 | 10 | back face down |
| c13_crank_pulley (with damper) | 1 | 28 x 46 x 46 | 0.5 | 19 | back face down |
| c14 / c15 / c16 pulleys | 3 | up to 33 dia | 0.1 | 4 | flat |
| c17_flywheel | 1 | 110 dia x 12 | 0.9 | 45 | flat |
| c18_plinth | 1 | 316 x 280 x 38 | 10.1 | 515 | flat; recommend buying a cut plate instead |
| c19_plug_boot | 8 | 7 x 10 x 13 | 0.05 | 0.3 | translucent |

Everything fits the H2C single-nozzle bed (325 x 320 mm). No part has raised detail on its bed face.
Every STL is one closed piece (checked with manifold3d).

## Bought, not printed

- Plug wires: about 2 m of 3 mm black silicone lead, cut to 8 lengths.
- Belt: one closed-loop cog belt round the four pulleys (length to be set when the pulley pins are placed).
- Dry-sump lines: about 0.5 m of 4 mm black hose for the three scavenge lines.
- From the existing kit: 608ZZ / 686ZZ bearings and 8 mm rod for the crank shaft and pulley pins,
  M3 inserts and screws, 6 x 3 magnets, the motor and the board (inside the block, which is hollow).

## Assembly (estimate)

Pan and board into the block, heads on (screws into inserts), covers and air cleaner on magnets,
intake and distributor drop in, headers screw to the heads, front cover and alternator screw to the
block front, pulleys on pins, belt on, flywheel on the shaft, engine onto the plinth cradles.
Roughly 30 screws, 16 inserts and 12 magnets, about 45 minutes (round 7: 56 screws, 46 inserts,
44 magnets, about 1 h 25).

## Still to do before a test print

1. Holes, inserts and magnet pockets are not cut yet (this pass is the look and the print plan).
2. LED wiring path from the boots through the heads into the block.
3. Motor mount and shaft supports inside the block; belt length.
4. Colour sign-off: renders show an orange block; a black-block version is on the page.
5. A real slice of the block, intake and one header to replace the estimate.
