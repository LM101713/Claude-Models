# Display case cut files (TEST CUT DRAFT)

Not final. Sheet thicknesses are guesses until the shop confirms what it stocks;
change them at the top of `tools/presentation/cutfiles.py` and re-run.

Units mm. DXF layers: **CUT** (through), **ENGRAVE** (score/mark), **NOTE** (don't cut).

| File | Material | Qty | Machine | Size (mm) |
|---|---|---|---|---|
| 01_base_bottom.dxf | wood 19.05 | 1 | CO2 | 423 x 363 |
| 02_base_pocket.dxf | wood 19.05 | 1 | CO2 | 423 x 363 |
| 03_base_deck.dxf | wood 19.05 | 1 | CO2 | 423 x 363 |
| 04_base_cover_frame.dxf | wood 19.05 | 1 | CO2 | 423 x 363 |
| 05_steel_weight.dxf | steel 12.7 | 1 | plasma | 303 x 243 |
| 06_cover_top.dxf | clear acrylic 6.35 | 1 | CO2 | 373 x 313 |
| 07_cover_front_back.dxf | clear acrylic 6.35 | 2 | CO2 | 373 x 336 |
| 08_cover_side.dxf | clear acrylic 6.35 | 2 | CO2 | 300 x 336 |
| 09_name_plate.dxf | brass 1.5 | 1 | fiber | 140 x 40 |

## How it goes together
- Wood layers 1-4 stack and screw together through the 4 corner holes (glue too).
  Layer 2's pocket holds the steel weight; layer 4's opening is where the cover sits.
- Cover: front/back are full width, sides fit between them, top sits on all four.
  Acrylic cement (Weld-On 4/16). Leave protective film on until glued.
- Engine bolt marks on layer 3 are placeholders: the stand bolt pattern is set later.

Envelope: inside cover 360 x 300 x 336, base 423 x 363 x 76.

Cheap first test: cut 06 + one 08 + 09 only, check acrylic edge quality and the engrave.
