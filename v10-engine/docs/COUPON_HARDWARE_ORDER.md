# Hardware needed to run the coupons (and nothing else)

This is the minimum shopping list to print and test coupons T1-T10
(`docs/COUPON_PRINT_GUIDE.md`). It deliberately contains **nothing for the
engine itself** - no motor, electronics, pulleys, belts, steel parts or ASA.
Quantities include spares: pressing bearings and magnets in and out of
plastic damages some of them, and the ASA re-run needs a second set.

Nothing has been ordered; this is a list for you.

## Hardware that goes into the coupons

| Item | Exact size / spec | Used by | Needed | Buy | Notes |
|---|---|---|---|---|---|
| Ball bearing **608ZZ** | 8 x 22 x 7 mm, metal shields (ZZ) | T3 (3 seats), T6 (2 seats) | 5 | **10** | same part as the engine's main bearings; a 10-pack is the normal retail unit |
| Ball bearing **686ZZ** | 6 x 13 x 5 mm, metal shields | T3b (5 seats) | 5 | **10** | same as the big-end bearings |
| Sintered bronze bushing | **3 x 5 x 4 mm** (ID 3, OD 5, length 4), oil-impregnated | T4 (5) | 5 | **10** | same as the rail bushings |
| Dowel pin (wrist pin) | **3 x 20 mm**, stainless or hardened steel, ISO 8734 / DIN 6325 (m6) | T4d (5) | 5 | **10** | same as the wrist pins |
| Neodymium disc magnet | **6 x 3 mm**, N52 (N42 is fine for the test), nickel plated | T5b (5 vertical + 5 horizontal) | 10 | **20** | same as the cover magnets |
| Heat-set insert | **M3 x 5.7 mm**, brass, **4.6 mm OD** (the "M3 x D4.6 x L5.7" type) | T2 (5 vertical + 5 horizontal) | 10 | **50** (one bag) | the engine's insert; the bag covers the ASA re-run and mistakes |
| Socket head cap screw | **M3 x 8 mm**, ISO 4762, stainless A2 | T1 (M3 clearance row), T1c (captive row, 5), T2 (torque test after inserting) | 10 | **25-50** (one bag) | the engine's only screw size |
| Round rod | **3.0 mm** diameter, ground/precision (h6 or "linear shaft"), **stainless**, 300 mm | T1 row R3, T4 (slides through the pressed bushings) | 1 | **1** piece | a 3.0 mm drill-bit shank works for T1 if you already have one, but the bushing slide test wants a smooth rod |
| Round rod | **8.0 mm** diameter, ground steel, 100 mm | T1 row S8 | 1 | **1** piece (or an 8 mm drill shank, or print P2) | the printed P2 shaft also works - print it before T1 |

Everything above is the same part number as the engine, so **none of it is
wasted**: the survivors go straight into engine #1.

## New for the V8 coupons T9 (lit plug boot) and T10 (header flex test)

Nothing below is assumed bought. T10 needs nothing but PLA.

| Item | Exact size / spec | Used by | Needed | Buy | Notes |
|---|---|---|---|---|---|
| Addressable LED strip | **WS2812B, 5 V, 60 LEDs/m, 10 mm wide, black PCB, IP20 (no silicone sleeve)** | T9 (one LED under the boot) | 1 LED | **1 m reel** | the engine's own strip type: the heads use 12 LEDs per bank and the boot strips 11 per bank, so the metre is used up later |
| Something to light one WS2812B LED | any of: the **ESP32 dev board** from `PROTO_BOM.md` (needed anyway) + 3 jumper wires, **or** a cheap "WS2812 USB mini controller / tester" with a USB-A plug | T9 | 1 | **1** | a 5 V USB phone charger powers one LED; no PSU needed for the coupon |
| Jumper wires | Dupont female-female, 10-20 cm | T9 | 3 | **1 pack (40)** | strip pads: 5V, DIN, GND |
| Translucent filament | **PETG, natural / clear (not "white")**, 1.75 mm; "transparent" or "natural" in the colour name | T9b boots (2), later 16 boots | 5 g | **1 spool** | this is the 5th palette slot you approved for the boots; PLA natural also glows but ASA is the match for the rest of the engine - test what you can buy, the boot is the only part in it |
| Solder + iron (or the strip's clip connector) | any | T9 | - | - | tin the three pads on the strip end; or buy the strip with a pre-soldered JST lead |

What T9 proves: boot glow (even / hot spot), boot press fit (`boot_9`), and
that the LED-under-the-flange-plate idea reads from 1 m away. Takes 10 min.

## Things to measure with

| Item | Spec | Why |
|---|---|---|
| Digital calipers | 150 mm, 0.01 mm | every coupon |
| Pin gauge set **or** a metric drill-bit set | 2.5-8.5 mm in 0.1 mm steps (pin gauges "minus" set), or drill bits used as plug gauges | measure the printed holes in T1 and T2 and read the printer's undersize directly (that number is `HOLE_COMP`) |
| Dial indicator + magnetic base | 0.01 mm | later: crank runout on T7 (not needed for the coupons themselves) |

## Tools

| Item | Spec | Why |
|---|---|---|
| Soldering iron with an **M3 heat-set insert tip** | any 220-260 C iron; M3 tip (e.g. the common brass insert tip set) | T2 |
| Small bench vise with smooth jaws, or a 1-ton arbor press | aluminium / plastic soft jaws | pressing bearings, bushings, pins and magnets square; fingers are not enough for the 608 |
| Hex key | 2.5 mm | M3 screws |
| Deburring knife or a small file | - | clean the coupon edges before testing (an elephant-foot lip falsifies slip fits) |
| Permanent marker | - | mark the winning step on each coupon |

## Filament

| Material | Amount | For |
|---|---|---|
| **PLA**, any brand, 0.4 mm nozzle | **1 spool (1 kg)** | all 18 coupon parts incl. the T10 header (about 150 g) plus the ASA-comparison pair of coupons printed again in PLA if a fit looks odd |
| **ASA** (the production material) | **1 spool** - optional at this stage | the mandatory re-run of T3, T3b, T4, T4d, T5, T5b, T6 before production values are locked (about 55 g); the rest of the spool is used by the motion test |
| **PETG** | **1 spool** - optional | the printed crankpin P1 that T5 needs (about 1.2 g), and the motion-test pins/shafts/rods later |

## What is intentionally NOT here

Stepper motor, driver, ESP32, power supply, LED strip, connectors, pulleys,
belt, machined steel parts, rubber feet, threadlocker, oil, edition plate,
ASA for the engine. Those are in `docs/PROTO_BOM.md` and wait for the coupon
results.
