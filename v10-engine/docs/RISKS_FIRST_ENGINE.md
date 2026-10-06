# The biggest risks on the first physical engine, ranked

Nothing has been printed. These are the things most likely to bite, in the
order they would hurt a $12,500 piece, each with the coupon or check that
catches it early and what I would change if it fails.

| Rank | Risk | How it would show | Catches it | If it fails |
|---|---|---|---|---|
| 1 | **Crush ribs do not behave** (don't resolve at 0.4 mm, or PLA cracks instead of crushing). Every bearing, bushing, magnet, trumpet, coil pack and rail pocket depends on them. | parts fall out, or the plastic splits at the rib positions | T3, T3b, T4, T4d, T5, T5b, T6 | change the interference in `fits.py CRUSH`; if ASA also cracks, lower `CRUSH_RIB_R` (narrower ribs) or switch that fit to a plain press bore |
| 2 | **Crank wobble (runout)** from 6 D-flat joints and 16 screws in a built-up crank | visible wobble of the webs through the windows, periodic tight spot, bearing drag | T5 (D-socket fit), T7 V-blocks during the crank build (target < 0.2 mm) | tighten `CRUSH["dpin_6"]`; 100 % infill segments; longer D-flat engagement (`PIN_END_LEN`) |
| 3 | **Con-rod big end splits** when the 686 bearing is pressed in | crack along the eye | T3b (same wall as the rod: 3.0 mm now, was 2.5) | lower `CRUSH["bearing_686"]`; raise `ROD_BIG_END_WALL` to 3.5 (rod is invisible inside the case) |
| 4 | **Piston rubs or ticks** (lug-to-slot or bushing-to-rail binding, print scale error) | ticking, a stiff spot every revolution, dust | T4c (lug slot), T4 (bushing), motion test with one bank | `LUG_POCKET_CLEAR`, `CRUSH["bushing_5"]`, `PISTON_RADIAL_CLEARANCE` |
| 5 | **ASA warps or lifts** on the 260-294 mm parts (crankcase, banks, heads, exhausts, base halves) | corners up off the bed, banks not flat on the crankcase | first long ASA print, flatness check on glass | 5 mm brim, warm enclosure, slower first layers; PETG for that part as fallback |
| 6 | **Heat-set inserts** pull out or sit proud (78 per engine) | screws strip, parts don't seat | T2 | `INSERT_HOLE_DIA`; different insert type (5.0 mm OD long series) |
| 7 | **Bridged counterbores and 20-25 mm bridges sag** (heads, banks, base halves, covers) | screw heads not flat, rough ceilings | first head / base half print | add a sacrificial 0.2 mm knock-out layer; split the counterbore |
| 8 | **Belt noise / motor hum** reaching the base and acting as a sound box | audible hum at some speeds | first power-up, 20-120 RPM sweep | belt tension (T8), rubber feet, StealthChop current (`MOTOR_RUN_MA`), lower speed cap |
| 9 | **LED strip** does not fit its groove or its leads get pinched by the head | dark bank, flicker | head dry-fit before final assembly | `LED_GROOVE` depth/width (config), `LED_WIRE_GROOVE` |
| 10 | **Belt tracking** off the pulleys with printed-part misalignment | belt walks to a flange, rubbing noise | run with the front cover off | motor slot adjustment; pulley spacing (`PULLEY_GAP`, `M04`) |
| 11 | **Base halves and bottom panels** do not meet flat (print tolerance on 200 mm parts) | visible seam, rocking | first base print | joint pegs (`FIT["spigot"]`), `PANEL_EDGE_CLEAR` |
| 12 | **Surface finish** of the deck-down heads and banks (bed texture on show faces is fine, but seams and brim scars are not) | visible scars | first head | seam position in the slicer (rear), brim ears only, textured plate |

**Not a risk list entry but the rule:** nothing above is proven until a real
engine has been printed and assembled. Code checks removed design mistakes;
they cannot see print tolerance, material behaviour, or feel.
