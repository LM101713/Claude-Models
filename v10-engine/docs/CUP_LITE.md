# Cup Lite: fewer, bigger prints and a one-hour build (D67)

Liam, 2026-10-22: yes to reworking the Cup concept (`docs/CUP_CONCEPT.md`) into something much faster to
print and assemble, with a new BOM and a firm per-engine cost. Same outside shapes as the Cup concept;
what changed is how the engine is split, joined, printed and driven.

Build: `tools/cup_lite.py --export` (STLs in `cup_lite/stl/`), renders `--photo` (in `renders/cup_lite/`,
`--layers` shows 0.4 mm print lines, `--all-silver` shows the version with the covers fused in),
collision check `tools/cup_lite_check.py`, estimate `tools/cup_lite_estimate.py` (writes
`cup_lite/estimate.json`). Everything below is an estimate until one engine is sliced and printed.

## The short version

| | Cup concept (D66) | Cup Lite |
|---|---|---|
| Printed pieces per engine | 20 shells + 8 boots | **6 shells + 4 press-on trim + 7 small kit parts + 8 boots** |
| Print jobs (plates) per engine | about 11 | **7** |
| Screws / inserts / magnets | ~30 / 16 / 12 | **4 / 4 / 0** (only the base-plate screws) |
| Printer-hours, 0.6 mm nozzle | 36 h (plinth bought) | 34 h |
| Printer-hours, 0.8 mm nozzle, 0.4 mm layers | 31 h | **29 h** (19 h if a high-flow hotend really sustains ~28 mm3/s, untested) |
| Filament | 1.6 kg | **1.4 kg** |
| Assembly, everything included | not counted fully | **about 1 h 15 min** (see below) |
| Materials per engine | not costed | **about $135** (range $115-175) |
| Biggest part | 221 x 175 x 118 mm | 220 x 224 x 128 mm (top end) - every part fits a 256 mm bed |

**What the numbers say, honestly.** The 12-18 printer-hour target is not reached on a standard hotend.
Print time scales with how much plastic goes through the nozzle, and merging shells does not change
the surface area much, so the merge itself saves only about 2 h. The 0.8 mm nozzle saves less than it
sounds because ASA melts at roughly 16-20 mm3/s on a normal hotend whatever the nozzle size; thinner
shell walls (1.8 mm, two 0.85 mm lines) are what made most of the remaining difference. The big wins
are in hands-on time: 7 print jobs instead of 11, no screws, inserts or magnets to set, and one plug
to connect.

For 50 engines: about 1,450 printer-hours. At ~20 useful hours a day, 4 printers take about 18 days,
6 printers about 12 days. Since every part fits a 256 mm bed, P1S-class printers ($799, VERIFIED
2026-10-07 in `SOURCING.md`) work as well as the H2S. Hands-on time is now the real bottleneck: about
2 h per engine (1 h 15 build + ~50 min of print-job handling and support removal), so about 100 h for
the order.

## The parts

| File | Qty | Size mm | 0.8 mm h | g | Colour | How it prints |
|---|---|---|---|---|---|---|
| l1_block_pan | 1 | 221 x 180 x 150 | 6.0 | 309 | orange ASA (black option) | pan opening down, hollow, no supports |
| l2_top_end (both heads + intake) | 1 | 220 x 224 x 128 | 9.5 | 458 | silver ASA | upright, tree supports under the deck edges and port bosses |
| l3_air_cleaner | 1 | 132 x 132 x 29 | 1.3 | 67 | black ASA | base down |
| l4 / l5 headers | 1 + 1 | 232 x 42 x 94 | 2.1 | 88 | silver ASA | on the port flanges, tree supports; both on one plate |
| l6_front_drive (timing cover, water pump, dry-sump pump, alternator) | 1 | 90 x 175 x 136 | 1.8 | 72 | silver ASA | pulley noses down, tree supports |
| t01_valve_cover | 2 | 196 x 58 x 58 | 1.5 | 76 | black ASA | flange down, hollow |
| t02_air_cleaner_lid | 1 | 132 x 132 x 12 | 0.9 | 48 | silver ASA | upright |
| k01-k06 kit: crank pulley, 3 idler pulleys, flywheel, distributor | 6 | up to 110 dia | 2.0 | 87 | black ASA | one plate |
| k07_plug_boot | 8 | 7 x 10 x 13 | 0.3 | 2 | clear PETG | one plate, batch for many engines |

Exact numbers per part are in `cup_lite/estimate.json` (`h06`, `h08`, `g08`). The figures come from the
model fitted on the 55 CAD parts that were really sliced (median error 17 %), so treat them as +-20 %.

Filament per engine: about 0.31 kg orange, 0.75 kg silver, 0.30 kg black.

## How it goes together (no screws in the engine itself)

| Joint | How | Separable? |
|---|---|---|
| Top end onto block | two locating tabs per deck drop inside the head shells, CA glue | no (motors are reached from below) |
| Valve covers onto heads | 2 printed pins into the head roof, CA glue | no |
| Air cleaner onto throttle body | 20 mm spigot, press fit | yes |
| Lid onto air cleaner | ring and groove, press fit | yes |
| Headers onto heads | 2 printed 3 mm pins per port (8 per header) into the port pads, CA glue | no |
| Front drive onto block | 2 printed pins into the front wall, CA glue | no |
| Idler pulleys | spin on 3 mm steel dowels pressed into the front drive | yes |
| Crank pulley, flywheel | press onto the N20 motor D-shafts | yes |
| Distributor | drops into its bore in the intake, press fit | yes |
| Engine onto base plate | 4 x M3 screws up into 4 heat-set inserts in the pan bosses | yes, for service |

## Motion and lights

- Two N20 6 V metal gear motors (30-60 rpm) slide into printed sleeves inside the block: the front one
  turns the crank pulley (the cog belt turns the three idlers), the rear one sits through the rear wall
  and turns the flywheel. This replaces the stepper, driver, 8 mm shaft and bearings. Both run from one
  small motor driver. Expect a little gear hum compared with the stepper.
- Eight WS2812B pixels (a pre-wired chain) are glued inside the heads behind the plug bosses; the plug
  sockets now go through the head wall so the light reaches the clear boots. The lead drops through a
  hole in each deck into the block.
- The base plate carries a small ESP32 board, the motor driver, one push button and a USB-C power input.
  The engine connects to it with one JST plug. The firmware is new (the old one drove a stepper) and is
  not written yet.

## What is lost compared with the Cup concept

Worst first:

1. **Print lines.** 0.4 mm layers show on the 45 deg faces, the lid dome and the valve covers
   (`renders/cup_lite/*_layers.png` shows them). No sanding is planned. If they bother Scott, print the
   top end and covers at 0.28 mm on the same nozzle: about +3 h per engine.
2. **Small detail softens** with 0.85 mm lines: the 5 mm hex bolt heads round off, the air-cleaner
   pleats (1.4 mm grooves) get shallow. The renders show the model, not this softening.
3. **Support marks** on the undersides of the top end, headers and front drive (mostly hidden from a
   normal viewing angle, but the top end's port bosses face outward).
4. **Oil pan is block colour**, not machined aluminium (printing it silver separately would add one
   part and one glue joint, about 0 h).
5. **No display stand**: the engine sits on its pan on a flat black plate instead of the cradle plinth.
6. **Alternator is the same silver as the front cover**, not a separate brushed finish.
7. **Glued, not serviceable**: covers, headers and front drive cannot come off after assembly. Motors,
   LEDs and the board stay reachable from below.
8. **Controls**: one button instead of the switch, button and speed knob of the round-7 base.

Kept on purpose (my default, reversible): the black valve covers and the silver air-cleaner lid stay
separate press-on prints. Fusing the covers into the top end (`--all-silver`) saves one glue step per
side but the top turns into one silver mass (`renders/cup_lite/front_right_allsilver.png`), which was the
biggest look regression I found.

Fixed on the way: in the Cup concept the left header was not moved back with bank B (9.5 mm off its
ports), the front cover overlapped the pan-rail lip, the distributor collided with the intake, and the
alternator floated free of the front cover. `tools/cup_lite_check.py` now reports no overlaps and all
15 STLs as single closed bodies.

## Assembly time (estimate, first units will be slower)

| Step | min |
|---|---|
| Support removal and clean-up (top end, headers, front drive) | 15 |
| 4 heat-set inserts in the pan bosses | 3 |
| Motors into sleeves, leads routed | 3 |
| LED chain glued in both heads, lead through the deck holes | 6 |
| Top end onto block (tabs, CA) | 3 |
| Valve covers, air cleaner, lid, distributor | 4 |
| 8 boots, cut and fit 8 plug wires | 12 |
| Headers (pins + CA) | 3 |
| Front drive, 3 dowels, idlers, crank pulley, belt, flywheel | 6 |
| 3 dry-sump hoses | 4 |
| Plug into base plate, 4 screws | 4 |
| Power-on test and QC | 5 |
| **Total** | **about 70-75** |

## Bill of materials and cost per engine

USD. VERIFIED = read from a live product page on 2026-10-07 (`docs/SOURCING.md`); everything else is
ASSUMED and needs a re-source before ordering. Nothing has been bought.

| # | Item | Qty | Each | Per engine | Status |
|---|---|---|---|---|---|
| 1 | ASA filament (orange, silver, black), 1.37 kg + 10 % waste | 1.5 kg | $21.24-29.99/kg | $32-45 | VERIFIED (Polymaker 10+ / Bambu); silver and orange stock not checked |
| 2 | Clear PETG for boots | 3 g | | $0.10 | ASSUMED |
| 3 | Base plate, 300 x 230 x 6 mm black cast acrylic, laser cut, 6 holes | 1 | $25-40 | $30 | ASSUMED (needs a quote; powder-coated aluminium would be $60-90) |
| 4 | Rubber feet 20 mm | 4 | $0.10 | $0.40 | ASSUMED |
| 5 | N20 6 V metal gear motor, 30-60 rpm, 3 mm D shaft | 2 | $4-7 | $10 | ASSUMED |
| 6 | ESP32-C3 mini board (XIAO class) | 1 | $5 | $5 | ASSUMED |
| 7 | DRV8833 dual motor driver module | 1 | $2.50 | $2.50 | ASSUMED |
| 8 | WS2812B pixels, pre-wired chain of 8 | 1 | $4 | $4 | ASSUMED |
| 9 | 5 V 3 A USB-C wall adapter + panel USB-C socket | 1 | $10 | $10 | ASSUMED |
| 10 | 16 mm momentary button with ring LED | 1 | $2.50 | $2.50 | ASSUMED (SOURCING E9) |
| 11 | JST plug, leads, heat-shrink | 1 set | $3 | $3 | ASSUMED (SOURCING E14/E16) |
| 12 | M3 heat-set insert + M3 x 10 screw | 4 + 4 | $0.20 + $0.10 | $1.20 | VERIFIED US prices (SOURCING H5/H6) |
| 13 | 3 mm steel dowel (idler pins) | 3 | $0.54 | $1.60 | VERIFIED (Zoro 3 x 20; AliExpress ~$0.08) |
| 14 | GT2 6 mm closed belt, ~440 mm | 1 | $2 | $2 | ASSUMED; length from the model is 434 mm, the alternator pin will move ~3 mm to tension a stock 440 |
| 15 | 3 mm black silicone lead (plug wires) | 2 m | $1/m | $2 | ASSUMED |
| 16 | 4 mm black hose (dry-sump lines) | 0.5 m | $2/m | $1 | ASSUMED |
| 17 | CA gel + activator | share | | $0.80 | ASSUMED |
| 18 | Numbered edition plate (optional) | 1 | $5 | $5 | ASSUMED (SOURCING H14) |
| | **Subtotal** | | | **$113-126** | |
| | + 10 % spares and reprints | | | **about $125-140** | |

**Firm-ish figure: about $135 per engine in materials, $6,750 for 50.** The honest range is $115-175:
the base plate quote and shipping are the big unknowns. This is about half of the round-7 materials
($268 per engine at the best prices in `SOURCING.md`) and well inside the $12,500 price.

## Still to do before a test print

1. Write the new firmware (ESP32-C3: 8 pixels in firing order, two motors on one PWM, one button).
2. Get a quote for the base plate; pick acrylic or aluminium.
3. Slice the top end, block and one header for real (Bambu Studio / OrcaSlicer) and replace these
   estimates; check the tree-support marks on the top end.
4. Print one engine, time the assembly, check the motor shaft fit in the printed D-bores.
5. Colour sign-off (orange or black block).
