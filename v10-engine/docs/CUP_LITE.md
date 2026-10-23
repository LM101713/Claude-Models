# Cup Lite: fewer, bigger prints and a one-hour build (D67)

Liam, 2026-10-22: yes to reworking the Cup concept (`docs/CUP_CONCEPT.md`) into something much faster to
print and assemble, with a new BOM and a firm per-engine cost. Same outside shapes as the Cup concept;
what changed is how the engine is split, joined, printed and driven.

Build: `tools/cup_lite.py --export` (STLs in `cup_lite/stl/`), renders `--photo` (in `renders/cup_lite/`,
`--layers` shows 0.4 mm print lines, `--all-silver` shows the version with the covers fused in),
collision check `tools/cup_lite_check.py`, real slice `tools/cup_lite_slice.py` (PrusaSlicer 2.7.2 CLI,
writes `cup_lite/slice.json`), the older fitted estimate `tools/cup_lite_estimate.py`. Firmware in
`firmware_cup/`, base-plate cutting drawing `cup_lite/base_plate_300x230x6.dxf`.

**Update 2026-10-23:** every part is now sliced for real (25.8 printer-h, 1.53 kg per engine on a
standard hotend), the firmware is written and its logic tests pass, and the missing details are in:
pixel seats inside the heads, a control pod with the button and USB-C socket, and the base-plate drawing.

## The short version

| | Cup concept (D66) | Cup Lite |
|---|---|---|
| Printed pieces per engine | 20 shells + 8 boots | **6 shells + 4 press-on trim + 8 small kit parts (incl. control pod) + 8 boots** |
| Print jobs (plates) per engine | about 11 | **7** |
| Screws / inserts / magnets | ~30 / 16 / 12 | **4 / 4 / 0** (only the base-plate screws) |
| Printer-hours, 0.6 mm nozzle | 36 h (plinth bought) | 34 h |
| Printer-hours, 0.8 mm nozzle, 0.4 mm layers | 31 h (estimate) | **25.8 h sliced** (19.2 h with a high-flow hotend at 28 mm3/s, untested) |
| Filament | 1.6 kg | **1.53 kg sliced** (supports included) |
| Assembly, everything included | not counted fully | **about 1 h 15 min** (see below) |
| Materials per engine | not costed | **about $140** (range $120-180) |
| Biggest part | 221 x 175 x 118 mm | 220 x 224 x 128 mm (top end) - every part fits a 256 mm bed |

**What the numbers say, honestly.** The 12-18 printer-hour target is not reached on a standard hotend.
Print time scales with how much plastic goes through the nozzle, and merging shells does not change
the surface area much, so the merge itself saves only about 2 h. The 0.8 mm nozzle saves less than it
sounds because ASA melts at roughly 16-20 mm3/s on a normal hotend whatever the nozzle size; thinner
shell walls (1.8 mm, two 0.85 mm lines) are what made most of the remaining difference. The big wins
are in hands-on time: 7 print jobs instead of 11, no screws, inserts or magnets to set, and one plug
to connect.

For 50 engines: about 1,290 printer-hours (sliced). At ~20 useful hours a day, 4 printers take about
16 days, 6 printers about 11 days. Since every part fits a 256 mm bed, P1S-class printers ($799, VERIFIED
2026-10-07 in `SOURCING.md`) work as well as the H2S. Hands-on time is now the real bottleneck: about
2 h per engine (1 h 15 build + ~50 min of print-job handling and support removal), so about 100 h for
the order.

## The parts

Sliced with PrusaSlicer 2.7.2 on `tools/slicer_cup_lite/asa_08.ini` (a Bambu-class CoreXY imitation:
0.8 mm nozzle, 0.40 mm layers, 2 walls, 10 % gyroid, organic supports from the plate only, ASA melt
limit 18 mm3/s). Bambu Studio's own time model differs a little, so read these as +-10 %.

| File | Qty | Size as printed, mm | h (18 / 28 mm3/s) | g | Colour | How it prints |
|---|---|---|---|---|---|---|
| l1_block_pan | 1 | 221 x 180 x 150 | 5.1 / 3.6 | 321 | orange ASA (black option) | pan opening down, hollow, no supports |
| l2_top_end (both heads + intake) | 1 | 220 x 224 x 128 | 8.1 / 5.9 | 492 | silver ASA | upright, 6 mm brim, organic supports under the deck edges and port bosses |
| l3_air_cleaner | 1 | 132 x 132 x 29 | 1.1 / 0.8 | 71 | black ASA | base down |
| l4 / l5 headers | 1 + 1 | 232 x 73 x 77 | 2.2 / 1.7 each | 115 each | silver ASA | port flanges down, supports; both fit one plate |
| l6_front_drive (timing cover, water pump, dry-sump pump, alternator) | 1 | 136 x 175 x 90 | 1.7 / 1.4 | 93 | silver ASA | pulley noses down, supports |
| t01_valve_cover | 2 | 196 x 62 x 44 | 1.4 / 1.0 each | 88 each | black ASA | flange down, hollow |
| t02_air_cleaner_lid | 1 | 132 x 132 x 12 | 0.7 / 0.5 | 46 | silver ASA | upright |
| k01-k06 + k08 kit: crank pulley, 3 idlers, flywheel, distributor, control pod | 7 | up to 110 dia | 1.8 / 1.5 | 101 | black ASA | one plate |
| k07_plug_boot | 8 | 7 x 10 x 13 | 0.2 total | 2 | clear PETG | one plate, batch for many engines |
| **Per engine** | | | **25.8 / 19.2** | **1,531** | | 7 print jobs |

Filament per engine: about 0.32 kg orange, 0.86 kg silver, 0.35 kg black. The fitted estimate had said
29.2 h and 1.38 kg: the slice is 12 % faster and 11 % heavier (support plastic and solid top layers).

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
- Each pixel is a 10 mm round WS2812B board that sits in a printed seat ring on the inside wall of the
  head, centred on its plug's light hole, and is glued there through the open deck before the top end
  goes onto the block. Each bank is its own 4-pixel chain on its own data pin, so no wire has to cross
  between the heads.
- A small printed control pod (k08) is glued to the front-left corner of the plate: the 16 mm start
  button on its sloped face, the USB-C power socket in its back. Its wires drop through a 10 mm hole
  in the plate, run under it (the feet give the room) and come up through a second hole inside the pan,
  where the XIAO ESP32-C3, the DRV8833 and the 74AHCT125 sit on the plate.

## Wiring (XIAO ESP32-C3)

| XIAO pad | GPIO | To |
|---|---|---|
| D2 | 4 | 74AHCT125 A1 -> 330 R -> bank A pixel chain DIN (odd cylinders 1 3 5 7, right bank seen from the front) |
| D3 | 5 | 74AHCT125 A2 -> 330 R -> bank B pixel chain DIN (even cylinders 2 4 6 8) |
| D4 / D5 | 6 / 7 | DRV8833 AIN1 / AIN2 -> front motor (crank pulley) |
| D6 / D7 | 21 / 20 | DRV8833 BIN1 / BIN2 -> rear motor (flywheel) |
| D10 | 10 | start button to GND (internal pull-up) |
| D1 | 3 | 1 k -> 2N3904 base; ring LED (5 V type) between 5 V and the collector |
| 5V / GND | | USB-C socket 5 V in; DRV8833 VM, pixels 5 V, 74AHCT125 VCC; one 470 uF across the pixel supply |

GPIO 2, 8 and 9 are the C3's strapping pins and stay unused. Pixel chains: data enters each head at the
deck hole near the rear and is run to the front boot first, so pixel 0 is the front cylinder
(`CHAIN_TO_SLOT` in `firmware_cup/src/config.h` if a harness is built the other way).

## Firmware (`firmware_cup/`)

- **Short press**: a 2-minute show (soft start, boots flash in firing order 1-8-7-3-6-5-4-2 at the
  crank speed, soft stop). Press again to stop early.
- **Long press (1.5 s)**: run continuously until the next press.
- **Stopped**: the boots keep a faint glow and the button ring breathes, so people know to press it.
- **Hold the button while plugging in**: test mode, each boot lights in firing order, then both motors
  run 3 s. This is the check after assembly.
- The default is the 2-minute show rather than running all day on purpose: small N20 gear motors are
  typically rated for hundreds to a couple of thousand hours, so a shop engine running 10 h a day could
  wear one out within a year. Continuous mode is there if Scott wants it.
- There is no crank sensor: the firing flashes follow the motor speed set in `RPM_AT_FULL` (measure one
  motor at 5 V and set it). With no visible pistons, nobody can see the timing drift.
- `firmware_cup/test/test_cup_logic.cpp` checks the firing order, bank and slot mapping, flash shape,
  motor ramp (it jumps past the stall band, so the motors never sit buzzing) and the button and show
  timer. All pass. **Not done:** a real ESP32 build. PlatformIO could not download the ESP32 toolchain in
  this container (blocked), so `main.cpp` was only compiled against stubs of the Arduino and NeoPixel
  calls it uses (`firmware_cup/test/stubs/`). Run `pio run` once on a PC before flashing.

## Base plate

`cup_lite/base_plate_300x230x6.dxf`: 300 x 230 mm, R12 corners, 6 mm black cast acrylic (or 5 mm
aluminium). Layer CUT: the outline, four 3.4 mm screw holes for the engine (countersink from the
bottom, 90 deg to 6.6 mm, drawn on its own layer) and two 10 mm wire holes. Plate origin = engine
centre. This is the file to send for a laser-cutting quote.

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
16 STLs as single closed bodies.

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
| Control pod onto plate, plug into base plate, 4 screws | 5 |
| Power-on test and QC | 5 |
| **Total** | **about 70-75** |

## Bill of materials and cost per engine

USD. VERIFIED = read from a live product page on 2026-10-07 (`docs/SOURCING.md`); everything else is
ASSUMED and needs a re-source before ordering. Nothing has been bought.

| # | Item | Qty | Each | Per engine | Status |
|---|---|---|---|---|---|
| 1 | ASA filament (orange, silver, black), 1.53 kg sliced + 10 % waste | 1.7 kg | $21.24-29.99/kg | $36-51 | VERIFIED (Polymaker 10+ / Bambu); silver and orange stock not checked |
| 2 | Clear PETG for boots | 3 g | | $0.10 | ASSUMED |
| 3 | Base plate, 300 x 230 x 6 mm black cast acrylic, laser cut, 6 holes | 1 | $25-40 | $30 | ASSUMED (needs a quote; powder-coated aluminium would be $60-90) |
| 4 | Rubber feet 20 mm, at least 8 mm tall (wires run under the plate) | 4 | $0.15 | $0.60 | ASSUMED |
| 5 | N20 6 V metal gear motor, 30-60 rpm, 3 mm D shaft | 2 | $4-7 | $10 | ASSUMED |
| 6 | Seeed XIAO ESP32-C3 | 1 | $5 | $5 | ASSUMED |
| 6b | 74AHCT125 level shifter + 2 x 330 R + 470 uF | 1 set | $1 | $1 | ASSUMED (SOURCING E4) |
| 7 | DRV8833 dual motor driver module | 1 | $2.50 | $2.50 | ASSUMED |
| 8 | WS2812B 10 mm round pixel boards, 2 pre-wired chains of 4 | 1 set | $4 | $4 | ASSUMED |
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
| | **Subtotal** | | | **$118-133** | |
| | + 10 % spares and reprints | | | **about $130-146** | |

**Firm-ish figure: about $140 per engine in materials, $7,000 for 50.** The honest range is $120-180:
the base plate quote and shipping are the big unknowns. This is about half of the round-7 materials
($268 per engine at the best prices in `SOURCING.md`) and well inside the $12,500 price.

## Still to do before a test print

1. Build the firmware once with `pio run` on a PC (the container could not fetch the ESP32 toolchain).
2. Send `cup_lite/base_plate_300x230x6.dxf` for a quote; acrylic or aluminium.
3. Re-slice the top end in Bambu Studio to confirm the time and look at the support marks.
4. Print one engine, time the assembly, check the motor shaft fit in the printed D-bores, measure
   `RPM_AT_FULL`.
5. Orange block is the default (black stays an option); no moving pistons stays the default.
