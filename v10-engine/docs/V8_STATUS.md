# V8 - status for your approval (front cover, stand, full engine)

**Stopped for your approval.** Nothing printed except what you print from
`dist/coupon_batch_C1.zip`. Nothing is production-ready: no physical part
of this engine exists yet.

## What is modelled and checked (every part)

| # | Part | Qty | Print size (mm) | Orientation |
|---|---|---|---|---|
| 01-05 | crankcase, valley beam, cylinder bank, end plate, crank end web | 1,1,2,2,2 | as the V10 (crankcase 217 x 105 x 50) | as the V10 |
| 06/07/08 | crank segments 90 / 180 / 270 deg | 1 each | 47 x 47 x 37 | front face down |
| 09, 10 | con-rod, piston | 8, 8 | 76 x 19 x 5 / 44 x 52 x 19 | as the V10 |
| 30 / 30B | cylinder head A / B (mirror) | 1 + 1 | 210 x 72 x 36 | deck down |
| 31 | valve cover | 2 | 200 x 54 x 36 | top down (textured plate) |
| 32 | plug boot (translucent) | 8 | 10 x 10 x 26 | standing, brim |
| 33 / 33B | header primary A / B (mirror) | 4 + 4 | 33 x 40 x 127 | standing on the collector spigot, brim |
| 34 / 34B | header flange plate A / B | 1 + 1 | 198 x 33 x 4 | flat |
| 35 / 35B | collector A / B | 1 + 1 | 205-211 x 42 x 39 | on the inboard flat |
| 36 / 36B / 36C | intake lid / base / throttle body | 1 each | 189 x 147 x 42 / 185 x 119 x 26 / 44 x 46 x 43 | lid upside down, base upright, TB bore-down |
| 40, 41 | oil pan, floor panel | 1, 1 | 237 x 166 x 70 / 219 x 111 x 13 | skin down / flat |
| 42 | bellhousing | 1 | 136 x 120 x 26 | rear face down |
| 43, 44, 45 | front cover, damper, accessory module | 1 each | 142 x 104 x 27 / 72 x 72 x 14 / 135 x 155 x 54 | face down / flat / back plate down |
| 46 | stand plate | 1 | 300 x 240 x 12 | flat, single-nozzle bed |
| 47 / 47B | bracket / mirror | 2 + 2 | 54 x 56 x 30 | on its side |
| 48 | controls plinth | 1 | 37 x 110 x 30 | upside down |
| M01-M06 | machined: 4 crankpins, main shaft rear (M02R) + longer front (M02F), 8 rails, pulley spacer, 8 spacer rings | | STEP in `stl/` | |
| T1-T10 | coupons incl. T9 boot glow, T10 header flex | | plate C1 | PLA |

Hours and grams per plate: `docs/PLATES.md` (PrusaSlicer estimates with the
production settings); overhang / bridge findings: `docs/PRINT_REPORT.md`.

## Checks on this state

* Static check, every pair of fixed parts: CLEAR (press fits overlap by
  their rib volume only).
* Drive check: motor at nominal, both slot ends, 210 and 220 mm belts: CLEAR.
* 15 deg full-rotation sweep of every moving part against every fixed part:
  NO COLLISIONS. (6 deg sweep of the core against the block: clear.)
* Firmware: 8-cylinder step table generated from `FIRING_ORDER`,
  cross-checked against the CAD TDC of every cylinder: PASS; LED pixel map
  with chained boot strips: unit tests pass.
* Fit-literal lint: all new geometry lines reviewed.

## What I need from you

1. Approve the front cover + damper + accessory drive as shown, or say what
   to change (the honest list is in `docs/VISUAL_REVIEW.md`, round 5).
2. Approve the stand with the front-right controls plinth (`docs/V8_STAND_CONTROLS.md`).
3. Approve the full engine for the motion-test prints (plates M1-M6) once
   the coupons have been printed and `TEST_CHECKLIST.md` says the fits are
   right.

## Open items I know about

* Part numbers: the primaries (33), oil pan (40) and floor panel (41) are
  exported without an engraved number - the prober finds no accepted flat
  hidden face; needs a spot chosen by hand (10 min each).
* Water pump housing is a snout only; front cover is a plain slab.
* The intake lid/base tongue fit and the throttle body spigot are new
  press fits (same `trumpet_14` and `CLEARANCE` values as proven fits, but
  not yet on a coupon).
* Customer video (crank-rotation MP4) and the kit checklist are still
  deferred until a physical engine exists.
