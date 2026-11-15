# Display case cut files (TEST CUT DRAFT)

Not final. Sheet thicknesses are guesses until the shop confirms what it stocks;
change them at the top of `tools/presentation/cutfiles.py` and re-run.

Units mm. DXF layers: **CUT** (through), **ENGRAVE** (score/mark), **NOTE** (don't cut).

| File | Material | Qty | Machine | Size (mm) |
|---|---|---|---|---|
| 01_base_slab.dxf | hardwood 50.8 | 1 | CO2 | 423 x 363 |
| OPTIONAL_04_base_cover_frame.dxf | wood 19.05 | 1 | CO2 | 423 x 363 |
| 05_steel_weight.dxf | steel 12.7 | 1 | plasma | 303 x 243 |
| OPTIONAL_06_cover_top.dxf | clear acrylic 6.35 | 1 | CO2 | 373 x 313 |
| OPTIONAL_07_cover_front_back.dxf | clear acrylic 6.35 | 2 | CO2 | 373 x 336 |
| OPTIONAL_08_cover_side.dxf | clear acrylic 6.35 | 2 | CO2 | 300 x 336 |
| 09_name_plate.dxf | brass 1.5 | 1 | fiber | 140 x 40 |

**Plan (D65/D66): engine on a custom wood base with a brass name plate (not numbered). The clear cover
(OPTIONAL_ files) is NOT being made unless Scott asks for it.**

## How it goes together
- Base is ONE solid 2 in hardwood block (walnut suggested). Green outline = pocket cut
  into the underside for the steel weight (epoxy it in). Felt pads on the bottom.
- Thick laser cuts char the edge: sand the sides, then chamfer/round the top edge.
- Cover: front/back are full width, sides fit between them, top sits on all four.
  Acrylic cement (Weld-On 4/16). Leave protective film on until glued.
- Engine bolt marks on layer 3 are placeholders: the stand bolt pattern is set later.

Base 423 x 363 x 50.8 mm. Optional cover inside 360 x 300 x 336.

Cheap first test: cut 06 + one 08 + 09 only, check acrylic edge quality and the engrave.
