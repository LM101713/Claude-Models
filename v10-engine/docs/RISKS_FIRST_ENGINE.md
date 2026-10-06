# The 10 things most likely to go wrong on the first physical engine

Re-ranked after the DFM pass and the look-and-feel review. Ranking = how
likely it is **times** how much it would hurt a $12,500 piece. Each row names
the coupon or check that catches it early and the one-line fix. Everything is
still unproven: nothing has been printed.

| Rank | Risk | How it shows up | Catches it early | If it happens |
|---|---|---|---|---|
| 1 | **Crush ribs do not behave.** Every bearing, bushing, pin, magnet, trumpet, coil pack and rail pocket is a crush-rib press fit. At 0.4 mm nozzle the 0.6 mm ribs may print as blobs; PLA may crack instead of crushing; ASA shrinks more than PLA so a fit proven in PLA can be wrong in ASA. | parts fall out, or the plastic splits at the rib positions, or ribs shave off as swarf | T3, T3b, T4, T4d, T5, T5b, T6 - in PLA **and then in ASA** | change `CRUSH[...]` interference in `fits.py`; if a material still cracks, lower `CRUSH_RIB_R` (narrower ribs) or switch that fit to a plain press bore |
| 2 | **Crank runout** from six D-flat joints and 16 screws in a built-up crank. | webs visibly wobble through the windows; a tight spot every turn; bearing drag; belt noise rising and falling | T5 (D-socket fit), T7 V-blocks during the crank build (target < 0.2 mm), motion test | tighter `CRUSH["dpin_6"]`; 100 % infill segments; longer `PIN_END_LEN`; in the worst case a one-piece printed crank for the prototype to prove everything else |
| 3 | **Con-rod big end splits** when the 686 bearing is pressed in (10 rods). | crack along a layer line through the eye, immediately or days later | T3b (same 5 mm thickness as the rod); inspect pressed rods again after 24 h | lower `CRUSH["bearing_686"]`; keep or raise `ROD_BIG_END_WALL` (D19, provisional 3.0) |
| 4 | **Piston tick or bind.** The pistons are guided by bushings on steel rails and by a lug in a slot; three clearances must all be right at once, and a 0.3 % print-scale error over a 260 mm bank shifts every rail. | ticking at one point of the stroke, a stiff spot, dust in the windows | T4 (bushing), T4c (lug slot), T1 (rail slip); motion test with one bank | `LUG_POCKET_CLEAR`, `CRUSH["bushing_5"]`, `FIT["rail_3_slip"]`, `PISTON_RADIAL_CLEARANCE` |
| 5 | **ASA warps or lifts** on the 260-294 mm parts (crankcase, banks, heads, exhausts, base halves). | corners off the bed; banks not flat on the crankcase; base halves do not meet | first long ASA print, flatness on glass, corner gap with a feeler | 5 mm brim, warm enclosure, slower first layers, lower chamber draughts; PETG for that part as a fallback |
| 6 | **Layer lines and seams make it look printed, not made** (new, from the look-and-feel review). The big flat vertical faces of the banks, crankcase and base show 0.20 mm lines within 1 m; ten trumpets with a vertical seam each. | obvious in daylight at arm's length | the three finish test tiles (`LOOK_AND_FEEL_REVIEW.md` section 2) before the first full engine | 0.12 mm on the three grey show parts, or primer + satin paint; seam to the rear on all round parts |
| 7 | **Heat-set inserts** pull out, sit proud or bulge (78 per engine, 10 of them horizontal). | screws strip; cam caps or exhaust flanges will not seat | T2 (vertical row + horizontal fin) | `INSERT_HOLE_DIA` (possibly a separate value for horizontal holes); longer 5.0 mm OD inserts |
| 8 | **Bridged counterbores and 20-25 mm bridges sag** (heads, banks, base halves, cam covers, end covers). The slicer already flags "long bridging" on these. | screw heads not flat; rough ceilings; a drooped first bridge layer | first head and first base half | sacrificial 0.2 mm knock-out layer under each counterbore; split the counterbore; slower bridge speed in the slicer |
| 9 | **Motor hum and belt whine amplified by the hollow base** (a 400 x 280 shell is a soundboard). | audible at 60-120 RPM in a quiet room | first power-up, 20 -> 120 RPM sweep, hand on the base | belt tension (T8), `MOTOR_RUN_MA` lower, rubber feet, ballast plate inside the base (also fixes heft), speed cap |
| 10 | **Colour and sheen mismatch between parts** (new). Slot 2 covers five parts printed on two different bed faces (textured plate vs smooth); slot 1 covers the block, end plates and beam from possibly different spools. | cam covers a different black from the base; grey banks not matching the end plates | first full set from one filament lot, side by side under daylight | one lot per slot per batch; same plate type for every show face of a slot; matte filaments hide it best |

## Newly noticed, lower in the ranking

* **Trumpet rims** are a 0.4 mm lip at 0.12 mm layers: likely ragged on some
  of the ten (`T13` has no coupon; the first trumpet print is the test). Fix:
  0.8 mm lip (minor exterior change, needs approval) or aluminium M05.
* **Captive-lip screw holes**: the M3 thread must cut a 1 mm lip of ASA; if
  the lip is too thin it tears instead of threading. T1c tests it; fallback is
  a plain hole (screws then are not captive).
* **Control panel inserts**: the rear wall is thinned to 2.5 mm for the jack
  and rocker nuts; no inserts there, but the 2.5 mm wall must not crack when
  the jack nut is tightened. Check on the first rear base half.
* **Magnet polarity errors** (46 magnets, every cover snaps on only one way).
  Pure assembly error; the QC sheet covers it; cost is a reprint of a cover if
  a magnet is pressed in wrong.
* **Exhaust label inside the pipe mouth and the throttle-frame label on a
  rail face** are low-visibility rather than invisible (DECISIONS D24). If
  either shows, those two go back to "no label" or a different spot.
* **Rod stand-ins (printed PETG crankpins/shafts) are weaker than steel**:
  the motion test may run rough for that reason alone. Judge fits and
  alignment, not smoothness, until steel pins are in.

Previously listed and still true, now below the top 10: LED strip fit in its
groove, belt tracking, base halves meeting flat, surface scars from brims.

**The rule:** none of this is proven until a real engine has been printed and
assembled. Code checks removed design mistakes; they cannot see print
tolerance, material behaviour or feel.
