# Phase 2: motor drive and display base

## What was designed

### Drive: hidden 3:1 GT2 belt
* A **NEMA17 (40 mm long)** in the base drives the **front main shaft**
  through a **GT2 20T → 60T** belt, **3:1 reduction**.
  * Engine 20–120 RPM = motor 60–360 RPM, the range where a stepper in
    StealthChop is smoothest and quietest.
  * The motor sees 3× more torque at the crank and 3× less inertia.
* Belt: **GT2 6 mm closed loop, 210 mm**, glass or steel reinforced. Centre
  distance 63.7 mm (calculated in `config.py`; change `BELT_LEN` and
  everything moves).
* **Torque margin:** Phase 1 targets ≤ 0.03–0.06 N·m to turn the crank. The
  3:1 drive gives ~0.4 N·m × 3 = 1.2 N·m available. That is over 20× margin,
  so the motor can run at **~30% current (≈0.4–0.5 A)**, where it stays cool
  and silent.
* **Crank end float:** the front main shaft's shoulder and the machined **M04
  spacer + 60T pulley hub** clamp the front 608 inner ring. The rear 608 floats.
* **Belt service with no tools:**
  1. Pull off the magnetic front cover.
  2. Remove the front bottom panel (4 screws).
  3. Loosen the 4 motor screws.
  Nothing else comes apart.

### Thermal isolation (brief: motor and driver away from load-bearing plastic)
* The motor hangs on its own **ASA bulkhead** inside the base, with at least
  2.4 mm of air above it at full tension travel. It touches nothing that
  carries the engine.
* The **driver (TMC2209) is on the carrier PCB at the opposite end** of the base,
  under the rear half.
* **Ventilation** is a chimney: cool air enters through the bottom-panel slots
  (the rubber feet leave a 6 mm gap) and leaves through the louvres high on
  both long sides, over the motor and over the electronics.
* At ~0.45 A the motor dissipates about 1.5 W, a rise of roughly 15°C. ASA
  (softens at 95°C) has a large margin.

### Display base (400 × 250 × 72 mm)
* It is too long for one print, so it is **two halves joined at the centre**:
  2 printed pegs plus 6 hidden M3×8 screws, all inside. A small seam is visible
  across the top, under the engine.
* Top skin prints **face-down on the textured plate**, which gives the base an
  even matte top. It has a chamfered edge and a thin shadow-line groove
  outlining where the engine sits.
* The engine bolts down with **4 × M3×8 from underneath** into the inserts
  already in the crankcase floor.
* **Rear control panel** (the short end, behind the engine), each with an
  engraved label:

  | Label | Control | Hole |
  |---|---|---|
  | 12V DC | barrel jack, 5.5×2.1 panel mount | 11 mm |
  | POWER | illuminated round rocker | 20 mm (wall thinned to 2 mm for the snap clips) |
  | SPEED | 10k linear pot with anti-rotation tab | 7 mm |
  | START | stainless momentary with LED ring | 16 mm |

* **Mounting points for everything:**
  * motor bulkhead (slotted ±3 mm for belt tension)
  * 4 standoffs with inserts for the carrier PCB (70 × 60 mm, Phase 4)
  * hall-sensor wire hole directly under the sensor pocket
  * LED-harness hole hidden under the future rear cover
  * 5 cable-tie anchors along one side for routing and strain relief
  * cable pass-throughs in the bulkhead
* **Removable bottom panels:** 2, the same part, 4 screws each, with vents
  and locating rings for the rubber feet. With them off, every screw and
  connector is reachable.

### Front drive cover
* It is held by **3 × 6×3 magnets** (3 in the cover, 3 in the end plate), so
  the pulley end looks clean with no screws.
* The **rear end plate has the same magnet pattern** ready for the Phase 3
  rear cover.
* **Change from Phase 1:** part `03_end_plate` now has these 3 magnet pockets.
  If you haven't printed the end plates yet, just use the new file.

All drive-train parts are checked in CAD against the base, cover and
engine: no interference (`assembly.drive_check()`).

---

## What to print (Phase 2)

| File | Qty | Material | Layer | Walls | Infill | Orientation | Approx. time / weight |
|---|---|---|---|---|---|---|---|
| `09_base_front` | 1 | ASA | 0.20 | 4 | 25% gyroid | top skin on the textured plate (as exported) | ~12 h / ~380 g |
| `10_base_rear` | 1 | ASA | 0.20 | 4 | 25% gyroid | same | ~12 h / ~380 g |
| `11_base_panel` | 2 | ASA (PETG is fine, it's hidden) | 0.20 | 4 | 25% gyroid | flat | ~2 h each |
| `12_front_drive_cover` | 1 | ASA | 0.20 | 4 | 25% gyroid | front face on the textured plate | ~2 h |
| `03_end_plate` (updated) | 2 | ASA | 0.20 | 4 | 25% gyroid | outer face down | ~1.8 h each |

**ASA notes for the base halves** (200 × 250 mm footprints warp if rushed):
* chamber heating on, door closed, 5 mm brim
* part-cooling fan ≤ 30%
* let it cool in the printer before removing

**If you want to test before buying ASA for the whole base**, print one base
half in PETG first. Fits, the control cut-outs and the motor position can all
be checked in PETG, and the ASA ones go into production.

---

## Purchased parts (Phase 2, per unit)

| Part | Spec | Qty |
|---|---|---|
| Stepper | NEMA17, **40 mm** body, 1.8°, 5 mm D-shaft, removable 6-pin cable (e.g. 17HS4401S or LDO-42STH40) | 1 |
| Pulley, crank | GT2 **60T**, 8 mm bore, 6 mm belt, 2 grub screws | 1 |
| Pulley, motor | GT2 **20T**, 5 mm bore, 6 mm belt | 1 |
| Belt | GT2 6 mm **closed loop 210 mm**, glass/steel core | 1 (+1 spare in the box) |
| Pulley spacer | **M04** machined (drawing in `drawings/`) | 1 |
| Magnets | 6×3 N52 | 9 (3 front plate, 3 cover, 3 rear plate) |
| M3×8 SHCS | | 22 (motor 4, joint 6, engine 4, panels 8) |
| M3 heat-set inserts | M3 × 5.7 | 18 (joint 6, panel pillars 8, PCB 4) |
| Rubber feet | adhesive, Ø20 × 6 mm | 8 |
| Cable ties | 2.5 mm | 10 |
| Controls | 20 mm round illuminated rocker (SPST); 16 mm stainless momentary with LED ring; 10k linear pot (M7 bushing, 6 mm shaft) + Ø20 aluminium knurled knob; 5.5×2.1 panel-mount DC jack (11 mm) | 1 each |

Electrical choices for the controls (LED voltages, connectors) are finalised
in Phase 4. The cut-outs above fit the common versions of each part. If you
buy a different size, change its entry in `CONTROLS` in `config.py`.

---

## Build sequence (Phase 2)

**Step 1: inserts.**
- [ ] `09_base_front`: 6 horizontal inserts in the joint bosses and 4 in the
      panel pillars.
- [ ] `10_base_rear`: 4 in the panel pillars and 4 in the PCB standoffs.

**Step 2: join the halves.**
- [ ] Pegs into holes, 6 × M3×8 from inside the rear half.
- [ ] The top seam is flush. Check it with a fingernail.

**Step 3: controls.**
- [ ] Fit jack, rocker, pot (tab in the small hole) and button through the
      rear wall. Wiring comes in Phase 4.

**Step 4: motor.**
- [ ] 20T pulley on the motor shaft, hub towards the motor, grub on the flat.
- [ ] Motor behind the bulkhead. 4 × M3×8 from the front side through the
      slots. Leave them finger-loose.

**Step 5: engine on the base.**
- [ ] Sit the crankcase inside the groove outline.
- [ ] 4 × M3×8 from below.

**Step 6: crank pulley.**
- [ ] M04 spacer onto the front shaft against the bearing.
- [ ] 60T pulley, hub first, pushed against the spacer.
- [ ] Grub screws on the shaft flat, with Loctite 243.
- [ ] The crank now has no end float.

**Step 7: belt.**
- [ ] Over the 60T pulley, down through the slot, around the 20T pulley.
- [ ] Slide the 20T pulley until the belt runs dead straight (sight along
      it). Tighten its grubs with Loctite 243.

**Step 8: tension.**
- [ ] Press the motor down firmly with a thumb (about 1 kg) and tighten the
      4 motor screws diagonally.
- [ ] Mid-span, the belt deflects about 3–4 mm under light finger pressure.

**Step 9: magnets.** Polarity matters:
- [ ] End plate magnets all face **N out**.
- [ ] Cover magnets all face **S out**. Check that each cover magnet
      *attracts* the one opposite it before pressing it in.

**Step 10: close up.**
- [ ] Cover on.
- [ ] Panels on (4 × M3×8 each).
- [ ] 4 feet per panel in the rings.

## Test checklist (Phase 2)

| # | Check | Pass |
|---|---|---|
| 1 | Turn the crank by hand 20 turns (the motor turns too) | Belt stays centred on both pulleys, no rubbing on the slot or cover |
| 2 | Belt off: spin the crank | Same free-spin result as the Phase 1 test (no new drag) |
| 3 | Crank end float | None you can feel when pushing/pulling the front shaft |
| 4 | Base on a flat table | No rocking; all 8 feet touch |
| 5 | Joint seam and panels | Flush, no creaks when pressing the top skin |
| 6 | Cover | Snaps on by magnets in the right place; comes off with two fingers |
| 7 | Motor run (any stepper tester, or the Phase 4 firmware) at 30 and 120 engine RPM for 1 hour | Smooth, quiet, motor case < 50°C (comfortable to hold) |

Report anything that fails, plus photos. Fits are numbers in `config.py`
(for example `MOTOR_TENSION_TRAVEL`, `BELT_LEN`, `CONTROLS`, `PCB`).
