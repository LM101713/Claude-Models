# GS-05 GIFT SLIDE: print settings

Written for a **Bambu Lab A1 mini** with a 0.4 mm nozzle and Bambu PLA. Any FDM printer with a 100 × 140 mm bed works with the same settings.

## Files

| File | What |
|---|---|
| `models/3mf/GS05_fit_coupon_first.3mf` | **Print first.** Coupon tray + Standard / Loose / Snug coupon lids, one plate. |
| `models/3mf/GS05_gift_slide_plate.3mf` | Tray + Standard lid, one plate |
| `models/3mf/GS05_star_lid_two_colour.3mf` | Tray + Star lid as one object with two parts (lid + gold star inlay) for an AMS |
| `models/3mf/GS05_lid_fit_variants.3mf` | Loose and Snug lids |
| `models/stl/*.stl` | every part on its own, already in print orientation |

The 3MF files contain geometry only, placed on a 180 × 180 plate. Open them in Bambu Studio, choose your printer, nozzle and filament, then slice. They carry no printer or filament profile on purpose.

## Settings

Start from **0.20mm Standard @BBL A1M** and **Bambu PLA Basic** (or Matte). Change nothing except what is listed.

| Setting | Value | Why |
|---|---|---|
| Layer height | 0.20 mm (first layer 0.20) | every fit-critical height is a whole number of 0.2 mm layers |
| Walls | 2 (default) | the flexure beam is 1.3 mm wide and prints as solid walls either way |
| Top / bottom layers | 5 / 3 (default) | |
| Infill | 15 % grid (default) | |
| Supports | **off** | none needed; the checks found no unsupported overhang wider than 0.45 mm |
| Brim | off | |
| Elephant foot compensation | leave at the profile default | the parts also carry 0.25 / 0.4 mm chamfers |
| Seam | default (aligned) | |
| Ironing | optional, top surfaces only | makes the lid top glossy; a matte lid also looks good |
| Plate | **textured PEI** recommended | gives the tray underside a premium texture |

Orientation is already right in every file: tray floor-down, lid **underside-down with the thumb dish up**. Do not flip the lid. Its 45° dovetail bevels must face upward.

## Estimates

Computed from the solids (no slicer was available in the build environment). Trust Bambu Studio's numbers over these.

| Plate | Print time | + heat and prime | Filament |
|---|---|---|---|
| Fit coupon (tray + 3 lids) | ≈ 24 min | ≈ 28 min | ≈ 15 g |
| Gift Slide (tray + lid) | ≈ 28 min | ≈ 32 min | ≈ 24.5 g |

## Colours

The tray and lid print as separate objects, so two colours need no AMS: assign one filament to each object.

| Colourway | Tray | Lid | Star inlay |
|---|---|---|---|
| Classic | Ivory White | Scarlet Red | — |
| Pine | Sand / Beige | Pine Green | Gold |
| Midnight | Charcoal | Charcoal | Gold |

**Star lid, two colours (AMS lite):** open `GS05_star_lid_two_colour.3mf`. The star lid loads as one object with two parts. Give the part named `GS05_C_Star_Inlay` your gold filament. The star is the top 3 layers (0.6 mm) only, so it adds about 6 filament changes and a few minutes. Without an AMS, print the Star lid in one colour; the debossed star still reads well.

## After printing

* Look along the two flexure slots in the lid's shadow gap. If a string crosses either one, slice it out with a blade.
* Don't sand or grease the grooves; the fit is designed for as-printed surfaces.
