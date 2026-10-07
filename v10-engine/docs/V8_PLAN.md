# Stock-car V8 redesign - plan (steps 1-3; stopped at step 5 for approval)

**Status:** nothing is built. The V10 is frozen at commit `7c6cc96`
(`docs/V10_FINAL.md`). This document is the study, the plan and the decision
list. A rough proportion mockup (masses only) is in `renders/v8_mockup/`,
rendered from the same angles as the five reference images.

## Status (updated)

* Moving core rebuilt and verified (6 deg full-rotation sweep clear) - commit
  `503802e`.
* Bank A approved as the direction (`docs/V8_BANK_A_REVIEW.md`).
* Critique rounds 1-3 (`docs/VISUAL_REVIEW.md`, `renders/v8_round1..3/`):
  S-curve headers, tapered collector, crisp valve cover, lower/wider intake
  (provisional), both banks, oil pan = motor + electronics bay, bellhousing.
  **Waiting for approval** before the front cover, damper, stand, edition
  plate and the real (hollow, two-piece) intake.
* Decisions from your answers and mine: `docs/DECISIONS.md` D26-D42.

## 0. The reference images

`references/STYLE_ai_01..05.png` - all five are **AI-generated** (your note).
No `REAL_` photos were supplied, so **there is no real-photo source for
structure or proportions.** For proportions I therefore use published Cup
engine rules and a generic small-block layout (section 1b), scaled to our
existing 44 mm piston, and I use the images for style, finish and mood only.
If you have real photos, add them as `references/REAL_*.png` and they will
override everything below.

### Mechanical errors in the AI images (do not copy)

| Image | What is wrong | What a real engine has |
|---|---|---|
| 01 (close-up) | about 6-7 injector bosses on one fuel rail over a 4-cylinder bank; the rail floats with no brackets | 4 injectors per rail, rail on 2-3 stand-offs |
| 01, 03, 04 | header primaries of visibly different diameters and lengths on the same bank, some crossing | equal-length primaries, equal diameter, no crossings on a display header |
| 02 (rear 3/4) | a bellhousing/flywheel-style round cover on the same end as the throttle body's "front", and no accessory drive at all; the image is a hybrid of a front and a rear view | pulleys and damper at the front, bellhousing at the rear |
| 03, 05 (front) | the serpentine belt wraps in a way that crosses itself behind the alternator and would not stay on the idlers; an uncapped water-pump outlet pointing straight up | belt routed around one side of each pulley, tensioner, hoses attached |
| 05 (front) | the throttle body points straight at the viewer while also sitting on top of a forward-leaning plenum that would collide with it; the two header banks have different numbers of visible bends | one consistent plenum/throttle geometry; mirrored headers |
| all | random bolt counts (valve covers show 12-16 bolts of different sizes), fasteners floating off their flanges | one consistent pattern |

None of this matters for style, and none of it is copied.

## 1a. What makes this style recognizable (keep, in priority order)

1. **A wide, low 90 deg V** with two long matte-black rectangular valve covers
   with soft rounded edges and one knurled oil cap each: this reads "race V8"
   from any angle.
2. **A tall cast-aluminium single-plane intake** in the valley: a flat-topped
   plenum with **four individual curved runners per side** diving to the heads,
   and **one large throttle body** on the front of the plenum.
3. **Satin aluminium block and heads** with a clear parting line between
   block, head and valve cover (three horizontal lines per side).
4. **Stainless tube headers, 4 primaries per side**, square flanges, equal
   bends, sweeping outward and down into one collector under the block.
5. **A deep, wide, ribbed oil pan** that is as visually heavy as the block.
6. **A front cover with a big crank damper, two or three black pulleys, an
   alternator and a belt** - the front is the busiest face.
7. **A plain black steel stand**: thin plate, two pairs of angled brackets,
   engine floating above the plate.
8. Three materials only: matte black, satin aluminium, brushed stainless.

## 1b. Real-engine proportions used (Cup rules + generic small-block)

| Real | Value | Model (1 : 2.42, set by the 44 mm piston) |
|---|---|---|
| Displacement limit | 358 cu in (5.87 L), 90 deg pushrod V8, 2 valves/cyl, cam in the valley | - |
| Bore x stroke (typical) | 4.185 x 3.25 in (106.3 x 82.6 mm) | 44 x 26 mm (our piston / stroke; 1.69 vs real 1.29 bore/stroke - internal only) |
| Bore spacing | 4.500 in (114.3 mm) NASCAR-mandated | 47.2 -> **50.0 kept** (LED-strip pitch), +6 % - invisible |
| Deck height (crank centre to deck) | 9.0 in class | 95 mm (ours is 88-95 depending on the rod) |
| Firing order | GM small-block standard 1-8-4-3-6-5-7-2; race engines very often run the "4/7 swap" 1-8-7-3-6-5-4-2 (special cam; reduces crank torsional vibration and the hot 5-7 corner) | see section 4 |
| Crank | cross-plane (90 deg), 4 throws at 0 / 90 / 270 / 180 deg, two rods per journal | 4 straight crankpins, 2 x 686 bearings each |

Sources (web search summaries; Bambu and Wikipedia pages are blocked from this
machine): [Wikipedia - NASCAR engines](https://en.wikipedia.org/wiki/NASCAR_engines),
[EPI - Cup vs F1](https://www.epi-eng.com/piston_engine_technology/comparison_of_cup_to_f1.htm),
[EngineLabs - firing order swaps](https://www.enginelabs.com/engine-tech/engine/firing-order-swaps-whats-best-for-your-engine/),
[EngineLabs - 4.500 bore centres](https://www.enginelabs.com/?p=8418).

## 1c. What I will simplify for printing (and why)

| Keep (as a deliberate, repeated feature) | Drop | Why |
|---|---|---|
| 2 valve covers with a 1.5 mm raised perimeter rim and **8 larger bolt bosses each** (one between cylinders + corners), one knurled oil cap each | the AI images' 12-16 tiny bolts, the rim fasteners | a 3 mm bolt boss prints; a 1 mm one is a blob |
| Intake: plenum + 4 runners per side + 1 throttle body with a visible bore and shaft | throttle linkage, sensors, vacuum ports | tiny features |
| Fuel rail: one clean 8 mm tube per side on 2 stand-offs, 4 injector bosses as 6 mm cylinders | braided lines, fittings, wiring, every clamp | texture and sub-millimetre parts |
| Headers: 4 primaries per side (equal diameter 20 mm), square flanges, one collector, short tail | weld beads, heat-tint colour, slip joints, tabs | prints as a smooth tube; colour belongs to the finish plan |
| Oil pan with **vertical ribs 2.4 mm thick on a 20 mm pitch** (deliberate, even), a rail flange | drain plug, windage tray bolts, pick-up | ribs read as "cast" when even and bold |
| Front cover: damper (rotates), 2 idlers, 1 alternator with pulley, belt as one printed band | tensioner spring, hoses, sensors, water-pump detail | the band reads as a belt from 1 m; a real belt would need pulleys with bearings |
| Bellhousing-style round rear cover (hides the drive) | starter, flywheel teeth | hidden by design |
| Stand: plate + 4 brackets with 4 visible hex bolt heads (8 mm across flats, printed) | hardware store bolts, washers | printed bolt heads this size are crisp |

## 2. The plan

### Reused unchanged (coupon results stay valid)
`fits.py` and every value in it; `config.py` tooling structure; the build
pipeline (`build_all`, `printcheck`, `plates`, `verify_all`, `check_fits`,
`check_firmware`, `bom`, `proto_bom`, `partnum`); the coupons T1-T8 and their
hardware; **pistons, rods, wrist pins, bushings, rails, 686 big-end
bearings, 608 main bearings, magnets, inserts, M3 x 8 screws, 3 mm and 8 mm
rods** - all identical. The crush-rib seats for all of them are the same
geometry, so the coupon numbers transfer one-to-one.

### Redesigned
| Area | Change | Why |
|---|---|---|
| Cylinder count | 10 -> 8 (4 per bank), bore pitch 50 kept | Cup V8 |
| Crank | **cross-plane, 4 throws at 0/90/270/180 deg**, two rods on each pin. The crankpin becomes a **straight pin** (no 18 deg split, no offset) carrying two 686 bearings side by side; M01 gets simpler and cheaper, M06 spacer rings stay. Printed crank: 3 flying webs + 2 end webs (5 segments instead of 4 + 2), big counterweights on webs 1 and 4 like a real cross-plane crank. | 90 deg V + 90 deg crank = even 90 deg firing with no split pins |
| Firing order | **1-8-7-3-6-5-4-2 (4/7 swap) recommended**, GM cylinder numbering (left bank 1-3-5-7 front to rear, right bank 2-4-6-8) | the race-engine order; the standard 1-8-4-3-6-5-7-2 is a one-line change in config |
| Bank offset | right bank ahead of the left by one rod width + clearance (about 6 mm), as on a real V8 | two rods share a pin |
| Valvetrain | pushrod look, **static**: valve covers are solid; a later version can add 16 moving rockers driven by a printed cam from the crank (2:1 belt or gears) - noted in section 6 | part count and risk |
| Block / heads / covers / intake / headers / pan / front cover / bellhousing / base | all new exterior per 1a-1c | the look |
| Oil pan = electronics and motor bay (proposed) | the pan is 238 x 121 x 79 mm: room for the NEMA17, the controller board and a bottom access panel with captive screws. The stand plate then stays a thin plate with brackets, like the reference. Controls (jack, rocker, knob, START) on the rear face of the pan or the rear edge of the plate. | the reference stand has no box; the pan has the volume |
| Hidden drive | motor in the pan, **belt to a 60T pulley on the rear of the crank inside the bellhousing cover**; front damper rides on the crank nose and turns with it; idlers, alternator pulley and the printed belt band are static (cosmetic). | the bellhousing hides the drive naturally; nothing visible rubs |
| LEDs | **3 per cylinder = 24** (two 12-LED strips, 60 LED/m, 50 mm pitch), exactly like the V10 | the strip pitch makes 3 per bore free of custom boards; see decision 2 for *where* they shine |
| Firmware | `FIRE_STEP` table regenerated for 8 cylinders and the chosen order; hall timing re-derived; `check_firmware.py` reruns the CAD-vs-firmware TDC check | tooling exists |
| BOM / plates / kit | 8 pistons, 8 rods, 24 bushings, 8 pins, 16 x 686, 2 x 608, 4 crankpins; plates re-packed for **300 x 320 x 320** | fewer parts |

### Risks to the coupon results
* **None of the fits change.** Same bearings, bushings, pins, magnets,
  inserts, screws, rods, same rib geometry.
* The only new fit is the **shared crankpin**: two bearings on one 6 mm pin
  with one M06 ring between them. Same `CRUSH["bearing_686"]` in the rod
  (T3b) and the same D-flat socket in the webs (T5). No new coupon needed.
* The oil pan as an electronics bay adds a captive-screw panel: already
  covered by T1c.

## 3. Decisions I need from you

1. **Where does the viewer see the engine move?** The reference engine has no
   windows, and the crank is inside. Options: (a) cutaway windows in the
   block sides between the header primaries, like the V10 (pistons visible,
   LEDs light the chambers) - the mechanism is the show; (b) no windows: the
   front damper turning is the only visible motion, and the firing LEDs sit
   as **lit spark-plug boots** on the exhaust side of each head (8 single
   LEDs, one per cylinder) - cleanest reference look; (c) both. My
   recommendation: **(c)** with small windows (the pistons were the V10's
   best feature). This decides the LED count: 24 on strips for (a)/(c), 8
   single LEDs for (b).
2. **Oil pan as the electronics + motor bay** (thin reference stand) vs
   keeping a box base. Recommendation: the pan.
3. **Firing order:** 4/7 swap 1-8-7-3-6-5-4-2 (my recommendation) or standard
   1-8-4-3-6-5-7-2.
4. **Static accessory drive** (damper turns, belt band and pulleys static;
   recommended) vs a real driven belt on free-spinning pulleys (adds 3
   bearings per unit and a belt-tracking risk).
5. **Folder name:** keep `v10-engine/` (the folder rule) or rename to
   `engine/`? Everything inside is tooling now shared by both engines.
6. **Edition plate:** keep, on the stand plate's front edge?
7. **Finish palette** (section 5): matte black ASA (covers, pan? pulleys,
   stand), satin "aluminium" grey ASA (block, heads, intake, front cover,
   bellhousing), metallic grey + spray for the headers. OK to plan on that?

## 4. Firing order and crank arrangement (what I found)

* Cup engines: 358 cu in max, 90 deg V8, pushrod, 2 valves per cylinder,
  cam in the valley, 90 deg (cross-plane) crank, mandated 4.500 in bore
  centres; typical 4.185 in bore x 3.25 in stroke.
* Cross-plane crank: throws at 0, 90, 270, 180 deg (front to rear); each
  throw carries one rod from each bank; the 90 deg V gives a power stroke
  every 90 deg - even firing with no split pins.
* GM small-block standard order **1-8-4-3-6-5-7-2**. The **4/7 swap
  (1-8-7-3-6-5-4-2)** moves the two consecutively-firing adjacent cylinders
  from the hot rear corner to the front, reduces crank torsional vibration
  and is common in NASCAR and Pro Stock engines; it needs a different cam
  (for us: a different `FIRING_ORDER` line). For the model both orders use the
  same crank; only the LED sequence differs.
* Cylinder numbering (GM): left bank (driver side, our bank A) 1-3-5-7 front
  to rear, right bank 2-4-6-8; the right bank sits slightly forward.

## 5. Finish plan per part family (display-model-polish; to be proven on tiles)

| Family | Material / colour slot | Finish | Notes |
|---|---|---|---|
| Valve covers, oil caps, pulleys, belt band, stand plate + brackets | matte black ASA (slot 2) | raw off a textured plate; black-oxide screws | the matte black is the hero finish - no paint |
| Block, heads, intake, front cover, bellhousing | light grey ASA (slot 1) | **tile test**: raw 0.20 / raw 0.12 / primer + satin aluminium paint; pick by eye at 0.5 m | these are the "cast aluminium" parts; paint is most likely needed to kill layer lines on the big flat block sides |
| Oil pan | grey ASA (slot 1) | same as the block; the ribs hide layer lines well | |
| Headers (2 parts) | grey ASA (slot 4 "metal") | 400-grit scuff + metallic stainless/titanium spray; optional heat-tint at the collector | the one family that must be painted to read as steel |
| Throttle body | grey ASA | raw, bore polished with a 2 mm chamfer | |
| Hidden parts (crank, rods, pistons, inner structure) | any | none - no finish on moving parts | |

## 6. Making the valvetrain move later (not now)

Each head would get a printed camshaft driven 2:1 from the crank by a GT2
belt inside the front cover (the real front cover hides exactly this), with
16 printed rockers on a 3 mm rail and spring-less "pushrods" riding the
lobes. It is 2 cams, 2 belts, 16 rockers, 4 more 608s: a separate phase with
its own coupons. The valve covers are designed now with a removable top so
this can be added without reprinting the heads.

## 7. Printers (looked up, not guessed)

H2S 340 x 320 x 340 mm, single nozzle, multi-colour only via AMS purge.
H2C: single-nozzle 325 x 320 x 320 (left) / 305 x 320 x 325 (right),
**dual-nozzle 300 x 320 x 320**. **Design limit: 300 x 320 x 320** so every
part prints on either machine in any mode. One colour per part, so no part
needs the H2C's dual nozzle. Sources in the previous message.
