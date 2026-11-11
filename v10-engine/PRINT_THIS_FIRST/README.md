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
