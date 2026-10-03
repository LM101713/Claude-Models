# Design notes: why the engine is built the way it is

> **Owner decisions:** split-pin even-firing crank - "whatever makes the engine
> the best"; rail-guided floating pistons - "make it look and feel premium";
> materials on hand: ASA/ABS and PETG (no PETG-CF); 50-unit order, no test
> prints wanted. All production parts are therefore **ASA**, and every fit is
> designed to work without a tolerance test (section 7).

This file records the engineering decisions and the reasoning, so they can be
revisited deliberately rather than by accident. Where quality and convenience
pulled in different directions, quality won.

---

## 1. Even firing on a 90 deg V needs split crankpins

A **90 deg V10** firing evenly every **72 deg** (1-6-5-10-2-7-3-8-4-9) is impossible with
one shared crankpin per throw: the firing gaps would alternate 90/54 deg and the
lights would visibly lope. The two journals of each throw are therefore offset
by 90 - 72 = **18 deg** (a split-pin crank, as in real even-fire 90 deg V6/V10s).
`config.py` derives the pin angles from `BANK_ANGLE` and `FIRING_ORDER` and its
self-check proves consecutive TDCs are exactly 72 deg apart.

| throw | journal A (bank A) | journal B (bank B) |
|------:|-------------------:|-------------------:|
| 1 | -45 | -27 |
| 2 | +27 | +45 |
| 3 | -117 | -99 |
| 4 | +99 | +117 |
| 5 | +171 | -171 |

Each crankpin (M01) is a small machined steel part with two journals 4.07 mm
apart. All five are identical and symmetric end-for-end.

**Correction made during the production review:** the pin originally had a
shoulder on *both* sides of each journal, which would have made it impossible to
slide the one-piece 686 bearing on. Each journal now has its shoulder only on
the inner (flying-web) side; the outer locating shoulder is a separate steel
**spacer ring (M06)** that goes on after the bearing. Same geometry, assemblable.

## 2. Floating pistons are guided by a steel rail, never by the bore

A piston on a pivoting con-rod must be guided along the cylinder axis, or it
tips over. A real engine uses the bore wall - exactly the rubbing contact we
avoid. Instead:

* Each piston has a **lug on its valley side** with **two sintered bronze
  bushings (3 x 5 x 4 mm)** sliding on a fixed **3 mm ground stainless rail**.
* The rail sits in the valley beam at the bottom (6 mm, crush-rib centred) and
  runs **3 mm up into a crush-rib pocket in the cylinder head** at the top, so it
  is held at both ends. The 5 rails also locate the head on the deck (they are
  off-centre, so the head fits one way only).
* The piston keeps **0.8 mm** radial clearance to the bore all round. **No
  plastic touches the cylinder, ever.** The only sliding pair is bronze on
  polished stainless.
* The rod's small end has **1.0 mm** side float each way between the piston
  bosses. That absorbs the crank's assembled axial position (0.3 mm forward, see
  section 4) and the print-length tolerance of the crank stack.

## 3. Only two main bearings

Six printed bearing seats in a line cannot be aligned to the hundredths a crank
needs; the crank would bind and get worse as plastic creeps. Two bearings (608ZZ,
one per end plate) define the axis exactly. The crank between them is a stiff
built-up assembly (keyed D-flats, clamped joints). Display loads are tiny.

## 4. Axial location: one locating bearing, one floating

* Both 608ZZ bearings are pressed into the end plates from the inside against a
  lip on the outside.
* **Front = locating bearing:** its inner ring is clamped between the front
  shaft's shoulder and the M04 spacer + 60T pulley. Clamping pulls the crank
  0.3 mm forward (`CRANK_DX`), which the CAD models.
* **Rear = floating:** the rear shaft slides in its inner ring (shaft g6) with a
  0.6 mm gap to its shoulder, so crank-length tolerance can never preload the
  bearings. ZZ (shielded, not sealed) bearings are specified on purpose: their
  drag is low enough that the shaft's friction always carries the rear inner ring
  round (no creep).

## 5. Build order designed in, and checked

The crankcase is an **open-top U** with a separate **valley beam**, so the whole
crank module (crank, rods, pistons) is lowered in from above; the beam then
slides in from the front end (from above it would hit the piston lugs); the end
plates slide over the shafts; the banks lower along their bore axes over the
pistons (45 deg lead-ins on bores and lug pockets); rails drop in; heads go on.
`tools/verify_all.py` moves every part along its documented path in CAD and
checks it touches nothing already in place.

## 6. 50 mm cylinder pitch = a stock LED strip

The firing lights are a stock **WS2812B 60 LED/m** strip (16.67 mm pitch). The
cylinder pitch was set to **50.0 mm = exactly 3 LEDs**, so a 15-LED piece puts
three LEDs over every bore with no custom LED board and only 3 solder joints per
bank. The strip lies LEDs-down in a groove in the head's deck face and lights
the combustion chamber directly. The block end margin grew to 30 mm, so the
engine's length and look are unchanged.
The groove stops 1.6 mm short of each head end (no notch in the end faces, no
light leaking out of the joint line); a deeper pocket at each end lets the soldered
lead turn and run to the valley side.

## 6b. Numbered edition plate

Each of the 50 units carries an engraved metal plate (H14) with its number in a
bevelled recess on the base front. The 45 deg bevel all round frames the plate and
prints without any ledge on the vertical face. It is fitted last, after QC.

## 7. Fits that do not need a test print: crush ribs

Printers differ by +/-0.1-0.15 mm. Every press fit (bearings, bushings, pins,
magnets, trumpets, coil packs, rails, D-flat crank joints) uses a bore 0.3 mm
oversize with small half-round **crush ribs** standing proud; pressing the part
in flattens the ribs. Interference at the rib tips stays between ~0.1 and 0.45
mm for any printer within +/-0.15 mm, so the fit is firm and centred without
tuning. Slip fits (rail-in-bushing, shaft-in-bearing) are steel/bronze parts,
not printed. The `00_fit_check_optional` print exists only for a curious
builder.

## 8. Printability rules (checked automatically)

`tools/printcheck.py` slices every part with the production settings and
analyses the mesh: no overhang steeper than 45 deg over 25 mm2, no bridge longer
than 25 mm, no flat ring-shaped ceiling whose inner edge hangs in the air. To get
there:

* Cylinder heads print **deck-down**; banks print deck-down with **V-bottom
  windows** (a gable of two 45 deg overhangs instead of a bridge or a shallow curve
  where a sloped sill met the bore).
* Screw counterbores and crankpin sockets that face the bed use the **bridged
  counterbore** trick (2-layer slot, then 2-layer square) - `common.bridge_step`.
* Exhaust headers are "85 % round" pipes with a flat back that prints on the bed.
* Trumpets print bell-down with every flare <= 45 deg; coil packs get a 3 mm brim.
* Load-bearing parts: 4 walls, 25 % gyroid or more (crank parts and rods 40 %);
  cosmetic parts 3 walls, 15 %.

## 9. Materials

| Part type | Material | Why |
|---|---|---|
| All printed production parts | **ASA** | Softens ~95 C (shipping, sunny rooms), low creep under press fits and screw clamps, UV stable, premium matte finish; prints well on an enclosed printer. One material = simple production. |
| Crankpins, shafts, rails, wrist pins, spacers | **Stainless steel** | wear surfaces and precise journals (drawings M01-M06) |
| Guide bushings | sintered bronze, oil-impregnated | quiet, self-lubricating on steel |
| PETG | prototypes only (P1/P2) | creeps under a constant clamp |

## 10. Fasteners

* **One screw size in the whole engine: M3 x 8** socket head (92 per engine).
  Counterbores leave 4 mm of plastic under the head, so 4 mm of thread always
  lands in the brass insert.
* M3 x 5.7 brass heat-set inserts, 4.0 mm pilot holes (78 per engine).
* Threadlocker: **Vibra-TITE VC-3** (plastic-safe, removable) pre-applied on
  every screw. Anaerobic threadlockers (Loctite 2xx) are not used: they
  stress-crack ASA.

## 11. Electronics and firmware

See `ELECTRONICS.md`. In short: ESP32 (hardware step generation, hardware LED
timing, hardware step counter) instead of a Nano (would drop step pulses while
updating 30 LEDs); TMC2209 in StealthChop at 35 % of the motor's rating (cool,
silent); a DRV5033 omnipolar hall sensor under the **rear** crank web (its leads
drop next to the controller, well clear of the motor) checks the step count once
per revolution, so the LEDs can never drift out of time.
