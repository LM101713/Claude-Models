# Coupon print guide - exact order, material, settings, what to measure

Print these before any engine part. Every coupon prints in under 25 minutes
(PrusaSlicer estimate with an H2S-like profile; Bambu Studio will differ by
up to about 20 %). Files: `stl/T*.stl` (print orientation as exported, do not
rotate) or the single plate `stl/plates/C1_coupons.3mf` (all 15 at once, about
4.1 h, H2C). On the A1 Mini print them one or two at a time.

## Settings (all coupons)

| Setting | Value | Why |
|---|---|---|
| Material | **PLA** first. Then **re-print T3, T3b, T4, T4d, T5, T5b, T6 in ASA** before locking the production values. | PLA is quick and flat; ASA shrinks more and its crush ribs behave differently - production is ASA. |
| Layer height | **0.20 mm**, first layer 0.20 | Same as the parts they stand for. Fits are set by hole diameters and ribs, not by layer height. |
| Walls | T1, T1c, T2: 2. All others: **3** | Crush-rib coupons must have the same wall count as the real parts (ribs are formed by the walls). |
| Infill | 10 % gyroid | Fits live in the walls; this keeps every coupon short. |
| Top / bottom | 3 / 2 layers | |
| Supports | none | none needed |
| Brim | none, except **T4d: 3 mm brim** (tall thin bar) | |
| Orientation | **as exported** - flat face on the bed, engraved values facing up | the horizontal holes (fins and T4d) must print horizontal, as in the real parts |
| Seam | rear / aligned | keeps the hole walls clean |
| Hole compensation in the slicer | **OFF** (X-Y hole compensation = 0) | the design compensates holes itself (`fits.py HOLE_COMP`); a slicer offset on top would corrupt the ladder |

## Print order

Order follows what the motion test needs first. Times are per coupon.

| # | File | Time | Grams | Tests | Hardware needed to test it |
|---|---|---|---|---|---|
| 1 | T1_hole_ladder | 0.35 h | 7.7 | 3 mm rail slip, 8 mm shaft slip, M3 clearance | 3 mm rod, 8 mm shaft (P2 printed or any 8 mm rod), M3 screw |
| 2 | T1b_test_peg (x2) | 0.07 h | 0.4 each | the 5 mm printed peg for T1c | - |
| 3 | T1c_peg_captive | 0.26 h | 5.8 | 5 mm peg hole, captive-screw lip | T1b pegs, M3 x 8 screw |
| 4 | T2_insert_ladder | 0.38 h | 9.4 | insert pilots, vertical + horizontal | 10 x M3 x 5.7 inserts, soldering iron with M3 insert tip |
| 5 | T3_608_seats | 0.39 h | 11.0 | 608 bearing press fit, 3 steps | 3 x 608ZZ |
| 6 | T3b_686_seats | 0.34 h | 8.7 | 686 bearing press fit, 5 steps | 5 x 686ZZ |
| 7 | T4_piston_guide | 0.22 h | 5.0 | bronze bushing press fit | 5 x 3x5x4 bushings, a 3 mm rod |
| 8 | T4b_test_lug | 0.10 h | 1.5 | the piston's guide lug for T4c | - |
| 9 | T4c_lug_slots | 0.32 h | 8.7 | lug-to-slot clearance | T4b |
| 10 | T4d_wrist_pins | 0.23 h | 5.9 | wrist pin press fit (horizontal) | 5 x 3x20 dowel pins |
| 11 | T5_dpin_sockets | 0.23 h | 5.9 | D-flat crankpin socket, 3 steps | P1 printed crankpin (print one P1 first, 0.36 h, PETG) |
| 12 | T5b_magnets | 0.39 h | 9.3 | magnet pockets, vertical + horizontal | 10 x 6x3 magnets |
| 13 | T6_end_plate_seat | 0.25 h | 7.2 | the real 608 seat with its lip | 2 x 608ZZ |
| 14 | T7_crank_vblock (x2) | 0.20 h | 5.7 each | crank assembly jig | - |
| 15 | T8_belt_feeler | 0.06 h | 1.3 | belt deflection gauge | - |

Total about 4.1 h of printing, 100 g of PLA.

## What to measure on each coupon

Full pass/fail criteria and the exact `fits.py` parameter for every row:
**`docs/TEST_CHECKLIST.md`**. In short:

1. **Measure first, feel second.** Measure each hole of T1 with pin gauges or
   drill shanks and write down the printer's undersize. That number is
   `HOLE_COMP`; setting it right fixes most slip fits at once.
2. **Slip fits (T1, T1c, T4c):** the part slides in by hand with no wobble you
   can feel. Pick the hole; set the parameter to its engraved value.
3. **Press fits (T3, T3b, T4, T4d, T5, T5b, T6):** firm thumb press or light
   tap, stays put, no cracks, bearings still spin free. Pick the step; set the
   `CRUSH[...]` interference to its engraved value. If every step cracks, the
   material is not crushing the ribs: tell me (narrower ribs are a one-line
   change).
4. **Inserts (T2):** flush, square, no bulge, screw torques to 0.5 N m. Set
   `INSERT_HOLE_DIA`. Note whether the horizontal fin wanted a different size.
5. **Captive lip (T1c CAP):** an M3 screw threads through the 1 mm lip with a
   screwdriver and stays in the coupon when backed out. Set `CAPTIVE_LIP_D`.

After changing `fits.py`: `python build_all.py --only T` reprints only the
coupons; `python build_all.py` regenerates everything. **Change one number
per reprint**, so you always know what fixed it.

## Then: the motion test

Plates `stl/plates/M1_crank.3mf` ... `M6_beam_plates.3mf` (`docs/PLATES.md`),
PLA or PETG, settings from `docs/PRINT_REPORT.md` (these are real parts: 4-5
walls, 25-40 % gyroid, their own layer heights). Build and check per the
"motion test" section of `docs/TEST_CHECKLIST.md`.
