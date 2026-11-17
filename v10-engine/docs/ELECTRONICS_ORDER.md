# Order list: electronics, drive and rails for engine #1 (2026-11-18)

No firing LEDs (decision D77), so the LED strip and the level shifter are left out.
Links are Amazon searches: pick a listing that matches the **spec** column exactly.
Quantities are for one engine plus a spare where a part is cheap or easy to kill.

## Electronics

| Part | Spec (must match) | Qty | About | Link |
|---|---|---|---|---|
| ESP32 board | Espressif **ESP32-DevKitC-32E**, 38 pin | 2 | $10 each | [search](https://www.amazon.com/s?k=ESP32-DevKitC-32E) |
| Stepper driver | **BIGTREETECH TMC2209 V1.3** (comes as a 2-4 pack) | 1 pack | $12 | [search](https://www.amazon.com/s?k=BIGTREETECH+TMC2209+V1.3) |
| 5 V regulator | **Pololu D24V22F5** (5 V, 2.5 A) | 1 | $11 | [search](https://www.amazon.com/s?k=Pololu+D24V22F5) |
| Hall sensor | **TI DRV5033AJQLPG** (TO-92, 3 legs) | 3 | $1 each | Digi-Key, part DRV5033AJQLPG (not on Amazon) |
| Stepper motor | **StepperOnline 17HS4401S** (NEMA 17, 1.7 A, 40 mm long) | 1 | $12 | [search](https://www.amazon.com/s?k=17HS4401S) |
| Power supply | **12 V, 2 A or more**, plug **5.5 x 2.1 mm, centre positive** | 1 | $10 | [search](https://www.amazon.com/s?k=12V+2A+power+supply+5.5x2.1mm) |
| DC panel jack | 5.5 x 2.1 mm, panel mount, 11 mm thread, with nut | 1 pack | $6 | [search](https://www.amazon.com/s?k=5.5x2.1mm+DC+panel+mount+jack+female) |
| Power switch | round 20 mm rocker, KCD1, 3 pin, **12 V** lamp | 1 pack | $7 | [search](https://www.amazon.com/s?k=20mm+round+rocker+switch+12V+illuminated+3+pin) |
| START button | 16 mm stainless momentary, 1NO, **12 V** ring LED | 1 | $5 | [search](https://www.amazon.com/s?k=16mm+momentary+push+button+12V+ring+LED+stainless) |
| Speed knob | 10 k **linear** pot (B10K), 16 mm body, **M7 threaded bushing**, 6 mm shaft, with an anti-rotation tab; plus a 20 mm aluminium knob made for the **same shaft type** (D-shaft or knurled) | 1 each | $8 | [search](https://www.amazon.com/s?k=B10K+potentiometer+16mm+M7+6mm+D+shaft) |
| Prototype board | 70 x 90 mm double-sided | 1 pack | $8 | [search](https://www.amazon.com/s?k=70x90mm+double+sided+prototype+pcb) |
| JST XH kit | connectors + housings + pre-crimped leads | 1 kit | $12 | [search](https://www.amazon.com/s?k=JST+XH+2.54mm+connector+kit+pre-crimped) |
| Wire | silicone 22 and 26 AWG | 1 set | $10 | [search](https://www.amazon.com/s?k=silicone+wire+22+26+awg+kit) |
| Heat-shrink | assorted | 1 kit | $7 | [search](https://www.amazon.com/s?k=heat+shrink+tubing+kit) |

Small parts for the board (fuse, diodes, capacitors, resistors, 1 transistor): the full
list is `docs/ELECTRONICS.md`, part E15. Digi-Key has all of them in one order with the
hall sensors.

## Drive

| Part | Spec | Qty | About | Link |
|---|---|---|---|---|
| GT2 pulley, big | **60 teeth, 8 mm bore**, 6 mm belt | 1 | $7 | [search](https://www.amazon.com/s?k=GT2+60+teeth+8mm+bore+pulley+6mm) |
| GT2 pulley, small | **20 teeth, 5 mm bore**, 6 mm belt | 1 | $4 | [search](https://www.amazon.com/s?k=GT2+20+teeth+5mm+bore+pulley+6mm) |
| GT2 closed belt | **6 mm wide, 210 mm long** (220 mm also fits) | 2 | $6 | [search](https://www.amazon.com/s?k=GT2+closed+loop+belt+210mm+6mm) |

## Rails (replaces the craft rod)

| Part | Spec | Qty | About | Link |
|---|---|---|---|---|
| Precision rod | **3 mm linear shaft, h6, ground**, stainless, 300 mm or longer | 2 | $8 | [search](https://www.amazon.com/s?k=3mm+linear+shaft+h6+stainless+300mm) |

Superseded (D79): the rails are now **pre-cut 3 x 60 mm rods** (uxcell HSS 3 x 60, 20-pack), no cutting.

## Still missing from the coupon order

| Part | Spec | Qty | Link |
|---|---|---|---|
| Wrist pins | **3 x 20 mm** dowel pin, stainless | 20 | [search](https://www.amazon.com/s?k=3x20mm+dowel+pin+stainless) |

Only if the first pins never show up. Pieces of the 3 mm rod work for the motion test.

**Rough total: $150-180**, plus about $10 at Digi-Key.

## What was actually picked (2026-11-18) - differences that change the wiring

| Item | Picked | Difference from the design |
|---|---|---|
| 5 V regulator | Pololu **D24V25F5** | older version of the D24V22F5, same 5 V 2.5 A; pin order may differ: wire by the labels on the board |
| Stepper motor | generic 17HS4401, 42 x 38 mm, 1.5 A | 2 mm shorter, a little less torque; firmware runs it at 0.6 A, fits the motor bay |
| Power switch | DaierTek 20 mm round rocker, **2 pin, no lamp** | no lamp wire: the lamp lead in the harness is left out |
| Speed pot | B10K linear, 15 mm shaft (WH148 type) | usually a knurled 6 mm shaft: buy a knob with a **set screw** for a 6 mm shaft |
| START button | APIELE 16 mm, 12 V ring LED, red | as designed |
