# SD-01 SINKDOCK: what still needs a physical test

**Status: the design is checked in CAD only.** None of it has been printed or tested.
Every item below is something the CAD checks can't settle. The two "Gate" items must pass
before the model is published.

## Print

| # | Test | How | Pass |
|---|---|---|---|
| P1 | **Real grams and time** | Slice `SD01_SinkDock_A1mini_plate.3mf` in Bambu Studio, A1 mini, 0.20 mm Standard, PLA and PETG | ≤ 60 g. Time ≤ 120 min in PLA. Record the PETG time; the estimate is about 126 min. |
| P2 | First layer on a 160 mm footprint | Print in PETG on a textured PEI plate, no brim | No corner lift. If corners lift, add a 3 mm brim and note it in the listing. |
| P3 | Drip-break grooves survive the first layer | Look under each spout | A 1.6 mm wide groove is visible. Elephant-foot compensation or a heavily squished first layer can close it. |
| P4 | Thin dividers and vents | Inspect the 1.5 mm dividers and the diamond vent tops | Clean walls, no sagging at the vent tops |

## Fit (bring the real items)

| # | Test | Pass |
|---|---|---|
| F1 | **Gate:** Scrub Daddy and Scrub Mommy, dry and soaked, in each disc bay | They drop in and lift out with one wet hand without catching, and stand upright against the front stops |
| F2 | Flat sponge (Scotch-Brite heavy duty or a supermarket brand) stood on its short end | Stands without falling over; can't slide out of the 11 mm front opening |
| F3 | At least three dish brushes (OXO Good Grips, an IKEA-type brush, a round-handled bamboo brush). Measure each handle | Each handle drops into the 36 × 28 mm cup. Record any handle that doesn't fit. A soap-dispensing brush with a fat handle may not fit: say so in the listing. |
| F4 | Leaving sponges in for a week | No permanent dent or set in the sponges from the 22 mm stops |

## Drainage (the reason the product exists)

| # | Test | Pass |
|---|---|---|
| D1 | **Gate:** pour 50 ml of water over a soaked sponge in each bay, with the dock on a level counter and the spouts overhanging a sink by about 8–12 mm | Water leaves through the spouts. No water reaches the counter behind or beside the dock. |
| D2 | Residual water | 30 min after D1, the gutters hold no more than isolated droplets: no film or puddle under the sponges. A 2.5° fall is enough in CAD, but surface tension can pin drops. If it does, raise `slope_y` to 3.5°. |
| D3 | Drying time vs a flat tray | Squeeze both sponges equally, place one in SinkDock and one on a flat dish. Weigh both after 4 h. Expect SinkDock to dry faster; record by how much. |
| D4 | Drop-in sink with a raised rim | Note whether the spouts clear the rim. If the dock tilts back on the rim, its 2.5° fall is cancelled. Give placement advice in the listing. |
| D5 | Two weeks of daily use | No slime in the gutters; the dock rinses clean under a tap |

## Stability

| # | Test | Pass |
|---|---|---|
| S1 | Tilt test: empty dock with the heaviest brush from F3, on a board tilted to 10° in each direction | Does not tip. CAD predicts a worst case of 12.8° (brush leaning back) and assumes a 90 g brush with its centre of mass 150 mm up. |
| S2 | Pull the brush out with one hand | The dock does not lift or slide. If it does, suggest a few drops of silicone or rubber feet. |

## Material

- PETG is recommended: it tolerates warm water and detergent. PLA softens around 55–60 °C. That's fine for sponge water, but don't rinse the dock with near-boiling water. Note this in the listing. Neither material is dishwasher-safe; rinse by hand.
