# After-school summary (day 2 of the DFM pass)

Everything is committed on branch `claude/v10-engine-display-model-4r6gjr`,
one commit per task (hashes in section 6). **Nothing has been printed; the
design is not proven.** The overnight summary this file replaces is in git
history (`docs/MORNING_SUMMARY.md` at commit `fad1f3e`); its content is
folded into the sections below.

## 1. What I completed today

| # | Task | Result | Where |
|---|---|---|---|
| - | Your decisions applied | Sound = **final NO** (removed from the design and the open questions; speaker reservation deleted). Palette slots **approved**, kept until you name colours. **D19 kept as provisional**, plain-words explanation written. | `docs/DECISIONS.md` (D9, D10, D19), `docs/D19_EXPLAINED.md`, `docs/ELECTRONICS.md` 5b |
| 1 | Part numbers off every bed face | Exhaust B moved into the tail-pipe outlet recess (4 mm inside the pipe mouth). Same problem found and fixed on 6 more parts: valley beam, cylinder head, side panel, exhaust A, throttle frame, crankcase. A rule in `cad/partnum.py` now forbids the bed face. Rebuilt, re-sliced: the "low bed adhesion" warnings on the crankcase, exhaust B **and the head** are gone; every part still 0 long bridges / 0 big overhangs / 0 ring ceilings. Full interference + rotation verification re-run (section 4). | `cad/partnum.py`, `docs/PRINT_REPORT.md`, `docs/DECISIONS.md` D24 |
| 2 | Coupon hardware list | Minimum hardware to run all 15 coupons with sizes and spares (bearings, bushings, pins, magnets, inserts, screws, rods, gauges, tools, 1 spool PLA). Nothing for the engine. Nothing ordered. | `docs/COUPON_HARDWARE_ORDER.md` |
| 3 | Look-and-feel review | `display-model-polish` skill, 9 render angles incl. buyer's 3/4 from above and eye level. 13 ranked items, per-part finish plan with a 3-tile finish test, 12-point first-unit check list. **No exterior change made.** | `docs/LOOK_AND_FEEL_REVIEW.md`, `renders/review/` |
| 4 | Risk re-rank | Top 10 re-ranked by likelihood x cost; 2 new in the top 10 (layer lines/seams; colour and sheen mismatch), 6 new lower items (trumpet rims, captive lip tearing, control-panel wall, magnet polarity, label visibility, PETG stand-ins). | `docs/RISKS_FIRST_ENGINE.md` |

Not done on purpose (your rules): no 50-unit BOM, no final plate files, no
kit checklist, no assembly-guide rewrite, no exterior changes, nothing
bought or sent.

## 2. What I decided (all logged in `docs/DECISIONS.md`)

* **D24** - where each moved part number went. Two spots are *low-visibility*
  rather than invisible, because those parts have no other hidden face:
  the **side panel** label is on its upper edge (under the exhaust header);
  the **throttle frame** label is on the outer side face of a rail (faces the
  cam cover, down in the valley). If either shows on the printed unit, the
  fallback is no label on those two parts.
* **D25** - the look-and-feel items are listed only; none applied.
* No new unclear decisions came up; nothing else was chosen for you.

## 3. Needs your approval

| Item | Why it needs you | Where to read |
|---|---|---|
| **D19** rod big-end wall 3.0 mm (provisional) | you asked to approve it yourself | `docs/D19_EXPLAINED.md` |
| Look-and-feel items 1, 2, 3, 5, 6, 9 (block/bank detailing, base reveal or plinth, end-cover faces, cam-cover lines, trumpet height/lip, window chamfers) | exterior changes | `docs/LOOK_AND_FEEL_REVIEW.md` section 1 and 4 |
| Coil-pack colour (item 4), exhaust finish (item 7), aluminium trumpets (item 6 alt.), ballast plate in the base (item 12) | colour / BOM / weight decisions | same |
| Finish route for the grey show parts | decided by the 3 test tiles, not by me | `LOOK_AND_FEEL_REVIEW.md` section 2 |
| Side-panel and throttle-frame label spots (D24) | low-visibility, not hidden | `docs/DECISIONS.md` |

## 4. Verification re-run after task 1

`tools/verify_all.py` on the committed geometry (labels only changed; no
exterior or fit changes): config self-check OK; static check **CLEAR**;
drive check (both belts, both slot ends) **CLEAR**; assembly paths
**CLEAR**; 60-step full-rotation sweep **CLEAR - no collisions**; smallest
running gaps unchanged (rod to web 0.75 mm by design, piston to bore 0.80 mm,
rod to crankcase 1.95 mm) - `docs/CLEARANCE_REPORT.md`. Print check: every part 0 long bridges, 0 big
overhangs, 0 ring ceilings, no adhesion warnings.

## 5. Coupon print list, in order (unchanged; details in `docs/COUPON_PRINT_GUIDE.md`)

PLA, 0.20 mm, as exported, slicer hole compensation OFF; hardware in
`docs/COUPON_HARDWARE_ORDER.md`.

1. T1_hole_ladder (0.35 h) 2. T1b_test_peg x2 (0.07 h) 3. T1c_peg_captive (0.26 h)
4. T2_insert_ladder (0.38 h) 5. T3_608_seats (0.39 h) 6. T3b_686_seats (0.34 h)
7. T4_piston_guide (0.22 h) 8. T4b_test_lug (0.10 h) 9. T4c_lug_slots (0.32 h)
10. T4d_wrist_pins (0.23 h) 11. T5_dpin_sockets (0.23 h) 12. T5b_magnets (0.39 h)
13. T6_end_plate_seat (0.25 h) 14. T7_crank_vblock x2 (0.20 h) 15. T8_belt_feeler (0.06 h)

Then T3, T3b, T4, T4d, T5, T5b, T6 again in ASA. Then plates M1-M6 (motion test).

## 6. Commits today (newest first)

* (final) verification report + this summary
* `cb4e019` Task 1: part numbers off every bed face
* `b782330` Task 4: re-ranked top-10 risks
* `a50bfae` Task 3: look-and-feel review
* `895b665` Task 2: coupon hardware list; decisions (sound no, palette, D19)
* `fad1f3e` overnight: Phase 1 complete (fits.py, coupons, checklist, verification)
* `bad6b2f` **pre-DFM baseline** (`git checkout bad6b2f` to roll everything back)

## 7. What I need from you next

1. **Buy the coupon hardware** (`docs/COUPON_HARDWARE_ORDER.md`, about 10
   small items) and **print the coupons** in the order above. Tell me the
   results in plain words; I change `fits.py`, rebuild, re-verify.
2. **Decide D19** (keep 3.0 mm, or back to 2.5 mm - one number).
3. **Pick from the look-and-feel list** which exterior items, if any, you want
   done. I would do them in one pass with a commit before and after, then
   re-run every check.
4. Still open from before: the four filament colours (palette slots).
