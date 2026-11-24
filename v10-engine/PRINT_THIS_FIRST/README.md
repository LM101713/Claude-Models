# What to print next (updated 2026-11-17)

The coupons are printed. These are the motion-test plates, in the order to print them.
How to build them: [`docs/BUILD_GUIDE.md`](../docs/BUILD_GUIDE.md), one picture per step.

| File | What | Layer | Notes |
|---|---|---|---|
| `NEXT_M1_crank_LAYER_0.16mm.3mf` | crank parts, 2 shafts, 3 shaft plugs, hand knob | 0.16 | Safe to print now. Shafts and plugs 100 % infill. No supports |
| `NEXT_M2_rods_pins_rings_LAYER_0.12mm.3mf` | 8 rods, 4 crankpins, 12 spacer rings | 0.12 | Wait for the T4 result (bushings). Pins and rings 100 % infill, no brim |
| `NEXT_M3_pistons_LAYER_0.16mm.3mf` | 8 pistons | 0.16 | Wait for the T4 and T4d results (bushings, wrist pins). No brim |

Plates M4-M7 (bank, head, crankcase, valley beam, end plates, second bank) are in
`stl/plates/`. They have heat inserts, so wait for the T2 result first.

PLA, any plain colour. X-Y hole compensation 0.

---

# Print this first: the fit coupons (plate C1)

Small test pieces that check every press fit, hole and pin before any engine
part is printed. One plate, **about 6 hours, about 130 g of PLA.**

## Which file

**`C1_coupons.3mf`**: open it in Bambu Studio. All 25 pieces are already
placed on the bed in the right orientation. Do not rotate anything.
(`single_coupon_stls/` has each piece on its own, if you want to reprint one.)

Print it on the printer that will print the engine parts. If you'll use
both the H2S and the H2C, print the plate on both and mark each batch.

## Bambu Studio settings

Set these for the whole plate:

| Setting | Value |
|---|---|
| Filament | **PLA**, any colour (plain, not silk or matte) |
| Nozzle | 0.4 mm |
| Layer height | **0.20 mm** (first layer 0.20) |
| Wall loops | **3** |
| Sparse infill | **10 %**, gyroid |
| Top / bottom shell layers | 3 / 2 |
| Supports | **off** |
| Brim | **off** |
| Seam | aligned (or rear) |
| X-Y hole compensation | **0** (leave off: the design already corrects hole sizes) |
| X-Y contour compensation | **0** |
| Elephant-foot compensation | default is fine |

Then change these pieces only (right-click the piece, Add settings):

| Piece | Change |
|---|---|
| T1_hole_ladder, T1c_peg_captive, T2_insert_ladder | wall loops **2** |
| T4d_wrist_pins (tall thin bar) | brim **3 mm** |
| T9b_boot (x2, the little domes) | filament **clear / natural PETG**, wall loops **2**, infill **0 %**, brim **3 mm**. On the H2C put it on the second nozzle. If you don't have clear PETG yet, delete these two from the plate and print them later. |
| T10_header_flex (the exhaust pipe) | wall loops **4**, infill **15 %**, brim **5 mm** |

**One extra piece:** test T5 needs one printed crankpin,
`single_coupon_stls/P1_proto_crankpin_for_T5.stl`. Print it separately in
**PETG**, 0.12 mm layers, 4 walls, 100 % infill. If you have no PETG, PLA
works for the test.

## After printing

1. Clean any lip off the bottom edges with a knife (it spoils the fits).
2. Run the tests in **`TEST_CHECKLIST.md`**. You can do T1, T1b, T1c, T10 and
   T11 straight away with no bought parts.
3. Send me the results, for example "T5b magnet loose, T11 fits", and photos
   if you can. I change the numbers and rebuild everything.

Parts to buy for the other tests: **`COUPON_HARDWARE_ORDER.md`**.
More detail on each piece: `COUPON_PRINT_GUIDE.md`.
