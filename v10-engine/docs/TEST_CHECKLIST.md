# Test checklist: coupons first, then the motion test, then the engine

Nothing in this design has been printed yet. These coupons turn every guessed
fit into a measured one **before** any engine part is printed. Each coupon
prints in well under 30 minutes (times in `docs/PRINT_REPORT.md`). Every
hole has its value engraved beside it; the value you pick goes straight into
**`fits.py`** (the only file that holds a tolerance), then `python build_all.py`
regenerates every part.

**Material for the coupons: PLA** (fast, no warping). Then **re-print T3, T4,
T5 and T6 in ASA** before locking the production values: ASA shrinks more and
crush ribs behave differently in it. Production parts are ASA.

**Layer height for the coupons: 0.20 mm**, same as the parts they stand for.
Fits are set by the ribs and hole diameters, not by layer height; 0.15 mm on
the precision parts (rods, pistons, crank) is fine and is already in the
`LAYER` table (0.12 / 0.16).

## How to read a ladder

Each row is one fit, printed 5 times from -0.10 to +0.10 mm around the current
`fits.py` value (the middle hole = current value). Find the hole that passes
the test, and set the parameter to **that hole's engraved value** (slip fits:
hole diameter; press fits: rib interference; inserts: pilot diameter). If the
best hole is at an end of the ladder, move by 0.10, reprint the coupon, repeat.

| Pass | Fail (too tight) | Fail (too loose) |
|---|---|---|
| **Slip fit:** part slides in by hand, no wobble you can feel | needs a push, or scuffs | rattles / tilts |
| **Press fit (crush rib):** goes in with a firm thumb press or a light tap in a vise, stays put, no cracks | needs a hammer, cracks the plastic, or the ribs shave off as swarf | falls out or turns by hand |
| **Insert:** melts in square with a 15 s push at 220-240 C, sits flush, no plastic bulge, an M3 screw torques to 0.5 N m without pulling it out | insert pushes plastic up round the rim | insert wobbles before melting / pulls out |

---

## T1 / T1c - hole ladders (slip fits)

T1 = rows R3, S8, M3. T1c = rows PEG and CAP (uses the two printed pegs T1b).

| Row | Put in | Pass | Change in fits.py |
|---|---|---|---|
| R3 | a 3 mm guide rail (M03 or any 3 mm ground rod) | slides freely, no play | `FIT["rail_3_slip"]` = engraved value - 3.00 - `HOLE_COMP` |
| S8 | the 8 mm main shaft (P2 or M02) | turns freely, no play | `FIT["shaft_8"]` likewise (nominal 8.00) |
| PEG | the printed 5 mm test peg (T1b) | pushes in by hand, holds its own weight upside down | `FIT["spigot"]` likewise (nominal 5.00) |
| M3 | an M3 screw | drops through | `M3_CLEAR` = engraved value - `HOLE_COMP` |
| CAP | an M3 x 8 screw, driven through the 1 mm lip | threads through with a screwdriver, then stays in the coupon when you turn it back out | `CAPTIVE_LIP_D` = engraved value |

**All rows tight by the same amount?** Raise `HOLE_COMP` by that amount instead
of touching each `FIT`. **Tip:** measure the printed holes with pin gauges or
drill shanks and note the printer's actual undersize; that number is `HOLE_COMP`.

## T2 - heat-set insert ladder

Melt an M3 x 5.7 insert (4.6 mm OD) into each pilot, vertical row and the
horizontal fin (the head's exhaust-face inserts print horizontal).

| Pass | Change |
|---|---|
| flush, square, no bulge, screw holds 0.5 N m | `INSERT_HOLE_DIA` = engraved value of the best pilot |

Horizontal pilots usually need to be 0.05-0.10 bigger than vertical ones. If
the fin's best value differs from the row's, tell me and I will split the
parameter.

## T3 (608) / T3b (686) - bearing seats (crush-rib press fits)

T3 has 3 steps (-0.10 / 0 / +0.10): it is 7 mm thick so the seat is as deep as the real one.

| Row | Press in | Pass | Change |
|---|---|---|---|
| 608 | 608ZZ bearing (22 mm) | firm press / light tap, bearing square, spins freely afterwards (no inner-ring drag = not crushed) | `CRUSH["bearing_608"]` interference = engraved value |
| 686 | 686ZZ bearing (13 mm) | same | `CRUSH["bearing_686"]` |

**Watch for cracks** at the rib positions - that is the PLA-cracks-instead-of-
crushing failure. If every column cracks, the ribs are too stiff for the
material: lower the interference 0.10 and tell me; I can also make the ribs
narrower (`CRUSH_RIB_R`).

## T4 / T4b / T4c / T4d - piston guide

T4 = bushing ladder. T4b = printed test lug. T4c = lug-slot ladder. T4d = wrist-pin bar.

| Row | Press / slide | Pass | Change |
|---|---|---|---|
| BU5 | 3 x 5 x 4 bronze bushing | firm press, a 3 mm rail then slides through the bushing freely | `CRUSH["bushing_5"]` |
| LUG | the printed 9 mm test lug (T4b) slid along the slot | moves freely along the slot with no rattle you can hear | `LUG_POCKET_CLEAR` = engraved value |
| T4d PIN3 | 3 x 20 wrist pin, horizontal holes in the bar | firm press, pin centred | `CRUSH["pin_3"]` |

## T5 (D-pin sockets) / T5b (magnets) - key fits

T5 has 3 steps and is full socket depth (11 mm).

| Row | Press | Pass | Change |
|---|---|---|---|
| D6 | the crankpin end (P1 printed stand-in first; steel M01 later) into the D-socket | goes in with a firm press, **cannot be turned by hand**, flat seats | `CRUSH["dpin_6"]` |
| MAG | 6 x 3 magnet, vertical | thumb press, sits 0.3 below the face, cannot be pulled by another magnet | `CRUSH["magnet_6"]` |
| MAG (fin) | same, horizontal holes (crank web, end plate, side panel) | same | if it differs from the vertical row, tell me |

## T6 - end-plate seat

The real 608 seat with its lip. Press a 608 in from the open side until it
meets the lip.

| Pass | Change |
|---|---|
| bearing square against the lip, spins freely, lip touches only the outer ring | nothing (nominal) |
| nominal cracks or needs a hammer, the -.10 seat is right | lower `CRUSH["bearing_608"]` by 0.10 (and re-check T3) |

## T7 / T8 - tools, not tests

* **T7 crank V-blocks (x2):** both main shafts rest in the Vs on a flat table
  while the crank screws are tightened; turn the crank and watch each segment
  with a feeler or dial gauge: **runout target < 0.2 mm**.
* **T8 belt feeler:** 3.0 mm bar. Belt tension is right when the long strand
  deflects by this bar's thickness under a light finger press (about 2 N).

---

## After the coupons: the motion test (printed PETG pins and shafts)

Print plates M1-M6 (`docs/PLATES.md`): crank parts, P1 pins, P2 shafts, 10
rods, 10 pistons, crankcase, valley beam, 2 end plates, 1 bank, 1 head, with
rails cut from 3 mm rod. Build per `ASSEMBLY.md` stages A-D for one bank.

| Check | Pass | If not |
|---|---|---|
| Crank runout on the V-blocks | < 0.2 mm | find the high joint, check its D-flat seat and screw torque; report which segment |
| Crank in the case, no rods | turns by hand with no tight spot | end-plate bearing seats (T6) or crank runout |
| With rods and pistons, bank on | 2 full turns smooth, no piston touches a bore, no click | note the angle and cylinder - tells me which clearance |
| Piston float on the rail | moves freely on its bushings over the full stroke | `CRUSH["bushing_5"]` too tight (bushing squeezed) or rail not square |
| Head on, rails captured | head seats flat, all 5 rails enter | `CRUSH["rail_3"]`, `RAIL_POCKET_EXTRA` |

Only when this runs smoothly: order steel (M01-M06), print the rest.

## What else to test on the first full engine

* ASA warping on the 260-294 mm parts (crankcase, banks, heads, exhausts, base
  halves): corners flat on glass after cooling. If not: brim 5 mm, enclosure
  warm, or PETG for that part.
* The bridged counterbores (head, banks, base halves): screw heads sit flat.
* LED groove: strip fits with its tape; 1.6 mm end walls intact.
* Motor temperature after 1 h at 120 RPM: < 50 C.
* 48 h burn-in (`docs/BURN_IN.md`).
