# Morning summary - overnight DFM Phase 1

Everything below is committed on branch `claude/v10-engine-display-model-4r6gjr`.
Roll back any step with the commit hashes in section 7. **Nothing has been
printed; the design is not proven.** The point of tonight's work is that your
first prints will be cheap and will each tell us exactly which number to change.

## 1. What I completed

| Item | Where | Status |
|---|---|---|
| **One parameters file** for every tolerance, clearance and fit | `fits.py` (imported by `config.py`) | done - 27 named values; the move changed no geometry (all 30 STLs compared before/after: 0 differences) |
| Lint that stops anyone (me included) hard-coding a clearance again | `tools/check_fits.py` + reviewed allow list | done, passes |
| **15 test coupons**, each under 25 min, values engraved on every step | `cad/coupons.py` -> `stl/T*.stl`, plate `stl/plates/C1_coupons.3mf` | done, all sliced clean (0.06-0.39 h each, 4.1 h total, 100 g PLA) |
| **Test checklist**: what to measure or feel on each coupon, pass criteria, which `fits.py` number to change and by how much | `docs/TEST_CHECKLIST.md` | done |
| **Coupon print guide** (order, material, layer height, orientation, settings) | `docs/COUPON_PRINT_GUIDE.md` | done |
| Part number engraved (recessed 0.5 mm) on a hidden face of **every** printed part, placed automatically on a verified flat spot | `cad/partnum.py` | done, 21/21 parts (crank segments: "06-54", "07-198") |
| Captive screws on the bottom access panels (M3 threads through a 1 mm lip and stays in the panel) | `cad/base.py`, `CAPTIVE_LIP_D/T` in fits.py, coupon T1c | done |
| Con-rod big-end wall 2.5 -> 3.0 mm (splitting risk) | `ROD_BIG_END_WALL` in config.py | done; see verification |
| Full code verification on the new geometry (interference, both belts, assembly paths, 60-step full rotation, clearance scan) | `tools/verify_all.py` -> `docs/CLEARANCE_REPORT.md` | **see section 4** |
| Printability check of every part with production settings | `docs/PRINT_REPORT.md` | done: 0 long bridges, 0 big overhangs, 0 unsupported ring ceilings on every part |
| Motion-test plates for the H2C (325 x 320 single-nozzle bed) | `stl/plates/M1..M6*.3mf`, `docs/PLATES.md`, `renders/plates/` | done (F plates listed but NOT exported, per your rule 7) |
| **Prototype BOM draft** (2 engines + 25 % spares, alternative sizes, measuring tools, spare belt) | `docs/PROTO_BOM.md` / `.csv` | done, about $650 - nothing ordered |
| Electronics wiring diagram (draft) | `docs/img/wiring_overview.png`, `controller_schematic.png`, `docs/ELECTRONICS.md` | existing diagrams re-generated; sound reservation + PCB-later note added (section 5b) |
| Ranked risks on the first physical engine | `docs/RISKS_FIRST_ENGINE.md` | done |
| Firmware vs CAD timing cross-check | `tools/check_firmware.py` | PASS (unchanged) |

Not done on purpose (your rule 7): 50-unit BOM, final plate files for the
whole engine, kit checklist, assembly guide rewrite.

## 2. Every decision I made

All in **`docs/DECISIONS.md`** (D1-D23) with reasoning. The ones you should
look at first:

* **D9 Sound:** left out (your note said "check with Scott"); space reserved
  in the rear base half, nothing cut. Adding it later = reprint one bottom
  panel (grille) + a small module.
* **D10 Colours:** your colour fields were "[x]", so I defined a 4-slot
  palette (block / dark / accent / metal) and report filament per slot. Rename
  the slots in `config.py PALETTE` when you pick colours.
* **D12 Part numbers are recessed, not raised** (raised text on a mating face
  would hold parts apart).
* **D15/D16** 608 and D-pin coupons have 3 steps instead of 5 and all coupons
  use light infill, to stay under 30 min.
* **D19 Rod big-end wall 3.0 mm** (was 2.5).

## 3. Exterior changes

**None.** Every change is on hidden or mating faces or inside the engine. (The
rod eye is 1 mm larger, visible only through the cylinder windows if you look
for it.)

## 4. Verification results on the final geometry

(filled in when `verify_all.py` finished - see below)

## 5. Anything that failed or needs your approval

* **Approve or veto:** D9 (no sound yet), D10 (palette slots), D19 (rod wall).
* **Slicer heuristic warnings** (not failures): "low bed adhesion" on the
  exhaust header B because its part number is cut into the bed face; "long
  bridging" / "floating bridge anchors" on pistons, heads, base halves and
  covers from the bridged counterbores - unchanged from before, untested on a
  real printer (risk list #7).
* Nothing else failed.

## 6. Coupon print list, in order (details: `docs/COUPON_PRINT_GUIDE.md`)

PLA, 0.20 mm, as exported, slicer hole compensation OFF.

1. T1_hole_ladder (0.35 h) 2. T1b_test_peg x2 (0.07 h) 3. T1c_peg_captive (0.26 h)
4. T2_insert_ladder (0.38 h) 5. T3_608_seats (0.39 h) 6. T3b_686_seats (0.34 h)
7. T4_piston_guide (0.22 h) 8. T4b_test_lug (0.10 h) 9. T4c_lug_slots (0.32 h)
10. T4d_wrist_pins (0.23 h) 11. T5_dpin_sockets (0.23 h) 12. T5b_magnets (0.39 h)
13. T6_end_plate_seat (0.25 h) 14. T7_crank_vblock x2 (0.20 h) 15. T8_belt_feeler (0.06 h)

Then re-print T3, T3b, T4, T4d, T5, T5b, T6 in **ASA** before locking the
production values. Then plates M1-M6 (motion test, PLA/PETG).

## 7. Commits (newest first)

* `0a8d287` DFM Phase 1: fits.py, lint, coupons, checklist, proto BOM, risks
* `f0d1200` DFM Phase 0 report (no design changes)
* `bad6b2f` **dfm-baseline** - the design before this pass (`git checkout bad6b2f`)

(the final verification/labels commit hash is in section 4)

## 8. What I need from you next

1. **Print the coupons** (section 6) and fill in `docs/TEST_CHECKLIST.md` -
   or just tell me the results in plain words ("608 nominal cracked, -0.10
   was good; inserts best at 4.1"). I change `fits.py`, rebuild, re-verify.
2. **Order `docs/PROTO_BOM.md`** when you are ready (about $650 for 2
   engines + spares + tools). Do not order steel yet.
3. **Answer:** sound yes/no (Scott); the 4 filament colours; OK on D19.
4. After the coupons: print plates M1-M6 and run the motion test. That is
   the first moment anyone can say whether this engine works.
