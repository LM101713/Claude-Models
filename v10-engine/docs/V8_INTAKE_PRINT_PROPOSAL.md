# V8 intake manifold - print split and hollowing proposal (for your OK)

The intake in the renders is a provisional solid envelope (188 x 156 x 69 mm,
1.28 litres of CAD volume). Before it becomes a real part I propose the
following; nothing below is built yet.

## 1. Two-piece split, both halves support-free

| Piece | What it is | Print orientation | Size (mm) |
|---|---|---|---|
| 36a plenum top | the lid: top face with the 8 runner ridges, the throttle-body flange, the top 2/3 of the flanks | **upside down**, top face on the textured plate | 188 x 156 x ~45 |
| 36b plenum base | the tray that sits in the valley: lower flanks, floor, the 8 runner stubs that press into the head pockets, the fuel-rail saddles | **upright**, floor on the bed | 180 x 112 x ~28 |

Split line: a horizontal plane at z = 124 (12 mm above the head tops), hidden
under the ridges' lowest points, with a 1.5 mm tongue-and-groove lip around
the perimeter (clearance from `fits.py`) and 4 magnets (same 6 x 3 as the
covers) so the lid lifts off - the lid is the only part the owner needs to
remove to see the valley LEDs' wiring.

Why these orientations: the lid's outer surfaces (the parts you look at) all
face the bed or lean less than 45 deg; the ridges are then "downhill" shapes
on the printed top, so no supports. The base's stubs lean 45 deg into the
heads - the limit, acceptable on a 22 x 16 mm section. The throttle body
(44 x 34 mm, 10 deg tilt) prints as a separate round part (36c) standing on
its flange, pressed into a 14 mm crush spigot in the lid's front face like
the header spigots, so the lid keeps a flat front face for printing.

## 2. Hollowing

* Both halves: 3.0 mm walls (3 perimeters at 0.42 + solid top/bottom), 3 mm
  internal ribs under the lid every 40 mm so a 180 mm roof does not sag.
* Estimated plastic: lid ~190 g, base ~140 g, throttle body ~35 g (ASA, 15 %
  infill where the slicer finds closed volumes). The solid envelope would be
  ~1.3 kg.
* Fuel rails: separate 8 mm printed rods with 4 injector plugs each, pressed
  into 4 mm holes in the base's saddles (same `peg_5`-style fit as the V10
  pegs) - or omitted; your call.

## 3. What I need from you

1. OK on the two-piece split with a magnetic lid (or prefer glued one-piece).
2. Throttle body separate (recommended) or printed with the lid (needs supports).
3. Keep the fuel rails as separate pressed-in rods, or drop them.
