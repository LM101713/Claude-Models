# BK-01 Bookmarks: print settings

Written for a **Bambu Lab H2C with a 0.4 mm nozzle and Bambu PETG Basic**. Notes for other
FDM printers are at the end. The part has not been sliced in this repository (there is no
slicer with an H2C profile here, and no profile was invented), so print time and flush grams
come from Bambu Studio when you press *Slice*.

## Orientation: upright, open top up (as exported)

The files open standing on the bed with the open top up and the front cover facing you
(−Y, the default Bambu Studio view). Don't rotate it.

- **No supports.** The cavity is open at the top and widens upward (a 45° lead-in at the
  rim). The front relief is built in 0.2 mm steps so every underside is at 45°. Measured on
  the solid: the worst unsupported area in any layer is 0.09 mm², which is slicer noise.
- **The front gets the cleanest finish.** The relief stands on a vertical wall, so the
  lettering and flowers come out crisp with layer lines running across them, the same as
  the reference product. Printed lying on its back, the front would be a top surface, but
  the cavity would then need supports through its whole length.
- **The base is a solid 3,179 mm² footprint** with a 0.4 mm chamfer, which takes up
  elephant's foot. It stands at 28° before it would tip, so it needs no brim.

## Bambu Studio settings

Start from the **Bambu PETG Basic** filament profile and the stock **0.16 mm** process for the
H2C with a 0.4 mm nozzle. Change only these:

| Setting | Value | Why |
|---|---|---|
| Layer height | **0.16 mm** (0.20 works) | Smoother letter curves and relief steps. 0.20 mm is about 20 % faster and still clean. |
| Wall loops | **5** | Makes the 2.0 mm walls solid perimeter: stiffest and cleanest, with no infill in the walls. |
| Top / bottom shell layers | top 5 / bottom 5 | The floor is 2.4 mm. |
| Sparse infill | 15 % gyroid | Only reaches the floor and the 6 mm spine wall. |
| Seam position | **Back** | Puts the seam on the plain back cover (+Y). |
| Supports | **Off** | None needed (see above). |
| Brim | None (Auto is fine) | Large flat footprint. |
| Wall generator | Arachne (default) | Prints the tapered petal and leaf tips with narrower lines instead of dropping them. |
| Ironing | Off | There is no top surface to iron. |
| Prime tower | On (default for multicolour) | |
| Flush into objects' infill | On | Lets the floor and spine infill take some of the purge. |
| Nozzle / bed temperature | Profile defaults | The PETG Basic profile already handles shrinkage, so don't pre-scale. |

## Colour plans

Each colour region is a separate **part** of one object, already assigned to a filament
slot. Open the 3MF for the plan you want, then set slots 1 to 4 to the filaments you
actually have loaded. To change a part's colour, select it in the object list and change
its filament.

| Part | FULL (4 colours, as briefed) | TRIO (3 colours) | DUO (2 colours) |
|---|---|---|---|
| 1 Body: covers, spine, nameplate | F1 Pink | F1 Pink | F1 Pink |
| 2 Pages: fore-edge and head | F4 Ivory | F2 White | F2 White |
| 3 Lettering | F2 White | F2 White | F2 White |
| 4 Petals | F2 White | F2 White | F2 White |
| 5 Flower centres | F3 Yellow | F3 Yellow | F1 Pink |
| 6 Stems, leaves, mound | F1 Pink | F1 Pink | F1 Pink |
| File | `BK01_Bookmarks_4colour.3mf` | `BK01_Bookmarks_3colour.3mf` | `BK01_Bookmarks_2colour.3mf` |

The validator measured how often each plan switches colour. The page edges run up 417 of
the 421 layers (0.2 mm), so the page colour drives the waste:

| Plan | Swaps on a single-nozzle printer | Flushes on the two-nozzle H2C | H2C nozzle grouping |
|---|---|---|---|
| FULL | 624 | about 207 | Left: Pink + Yellow. Right: Ivory + White |
| TRIO | 466 | about 49 | Left: Pink + Yellow. Right: White |
| DUO | 417 | **0** | Left: Pink. Right: White |

On the H2C, set the grouping in Bambu Studio's filament-to-nozzle mapping (manual mode).
A switch between the two nozzles needs no flush. Only two filaments that share a nozzle
need one, which works out to about one flush per layer that uses both. **DUO is the
low-waste choice** and looks closest to the reference (white lettering on pink). **FULL**
gives the briefed look, with yellow centres and ivory page edges. Bambu Studio's flush
estimate after slicing is the number to quote to the customer.

Filament use (solid volume × 1.27 g/cm³, before purge): body 70.2 g, page edges 2.9 g,
lettering 0.35 g, petals 0.33 g, centres 0.06 g, meadow 0.49 g. Total about 74 g.

## Other FDM printers (single colour)

Print `models/stl/BK01_Bookmarks_single_colour.stl` upright with the same settings. It
needs no supports, and anything that prints PETG or PLA with a 0.4 mm nozzle can do it.
A pause-and-swap at a layer height can't stand in for multicolour on this part: the
colours sit side by side in the same layers, not stacked. For colour on another machine,
import the six region STLs from `models/stl/` together as one multi-part object.

## First-print checklist (the part is CAD-validated, not yet printed)

1. Slice and look at the preview layer by layer from z = 26 to 49 mm (the flowers). Check
   that every petal and leaf tip is present, and that the yellow centres land on the
   petals.
2. Check that the preview shows no support anywhere.
3. After printing, stand a 2 × 6 in card bookmark and a 3 mm wooden bookmark in the
   compartment. Both should drop in freely: the opening is 70.4 × 39.6 mm.
4. Look at the lettering head-on from 50 cm away and confirm "Bookmarks" reads cleanly.
   If the white looks pink-tinged, raise the flush volume for pink→white.
5. Measure the part: it should be 79.0 × 44.5 × 84.3 mm, ±0.2 mm.
