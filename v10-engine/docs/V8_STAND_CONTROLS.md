# V8 stand, controls plinth location, wiring route

## Where the controls go - comparison (viewer stands at the FRONT, damper end)

| Location | Reach | Visibility | Clashes / notes |
|---|---|---|---|
| **Rear edge** (your original idea) | poor: reach over or around a 300 mm engine with headers; the power rocker is the thing you touch most | hidden, cleanest look | bellhousing above it; cable run shortest |
| **Right side edge, middle** | medium: you reach under the bank-A header pipes and collector (collector bottom is only 46 mm above the plate; the pipes drop to 13 mm above the collector) | visible from the side only | box sits in the shadow of the collector; fingers near the header tube ends |
| **Front-right corner** (recommended) | best: the front face of a low box, same face as the edition plate, nothing above it below z -86 | visible, but it reads as a "pit console" at the base, not on the engine | sits under the alternator (z > 46) and the collector A tail (z > -86); 37 mm deep so the pan's front wall is 4 mm behind it |

**Recommendation: front-right corner plinth, controls on its front face**, in
this order left to right as you look at it: 12 V jack, power rocker, speed
pot, start button (`PLINTH["controls"]`). The edition plate stays on the
stand's front edge face to the left of the plinth, 120 x 30, swappable (the
same recess + tape spec as the V10, drawing H14).

Built as part 48 (`cad/stand_v8.py`): 110 x 37 x 30 mm, 3 mm walls, 2.5 mm
front face for the control nuts, prints upside down.

## Wiring route and strain relief

1. The four controls' leads leave the plinth through a 10 x 10 mm hole in
   its floor, straight into a **10 x 6 mm channel on the underside of the
   stand plate** that runs to the cut-out under the pan.
2. Two pairs of **cable-tie slots** flank the channel (30 mm either side of
   the plinth): one tie anchors the loom to the plate (strain relief for the
   plinth end), the second at the cut-out edge (strain relief for the pan
   end). Pulling on the plinth or the engine never loads a solder joint.
3. From the cut-out the loom goes up through the pan's floor panel: a 12 mm
   grommet hole in the panel (rubber grommet from `PROTO_BOM.md`), then to
   the board on the panel. The panel comes off with its 6 captive screws
   and the loom has 150 mm of slack coiled under the board so the panel can
   be laid beside the stand while connected.
4. The LED harness from the heads comes down the rear of the block inside
   the bellhousing and enters the pan through the 12 mm hole in its rear
   wall (grommet).
5. The stand's rubber feet are 20 mm x 4 mm, so the channel and the screw
   heads under the plate never touch the table.

## Stand plate and brackets

* Plate 300 x 240 x 12 (part 46), top edge 3 mm chamfer, printed flat,
  single-nozzle mode (300 + brim fits the 325 mm axis). Plate centre is
  shifted 9 mm forward so the damper (x 158) and the bellhousing (x -140)
  both stay inside it; the collector tails end 8 mm inside the rear edge.
* 190 x 90 cut-out under the pan floor panel: with the stand lifted onto
  its side the panel's 6 captive screws are reachable, the engine never
  comes off the brackets.
* 4 brackets (part 47, two mirrored): 6 mm bent-plate look, foot screwed
  from under the plate (2 x M3 into inserts in the foot), tab screwed to
  the pan's sump wall (2 x M3 into inserts in bosses inside the sump).
  The strut passes 17 mm below the collectors.
