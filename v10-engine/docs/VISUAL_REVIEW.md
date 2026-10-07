# V8 visual review - critique-and-fix rounds against the references

Method (display-model-polish): render the CAD from the five reference
camera angles plus three of my own, put each next to its STYLE_ai image
(`renders/v8_roundN/*_vs_ref.png`), list what is off, fix what can be fixed
inside the print rules, re-render. The references are AI-generated: used for
style, finish and mood only, not copied mechanically.

## Round 0 - bank A only (`renders/v8_bankA/`, approved by you as the direction)

Off: stiff J-pipes into a straight log; collector tail 80 mm out the back;
soft 3.5 mm valve-cover chamfer; intake too small in width (126 mm) and too
tall (top at z 168); no pan, so the block read boxy.

## Round 1 - headers, cover, intake (`renders/v8_round1/`)

Fixed: S-curve primaries (flare out, tuck in, near-vertical drop between the
windows); tapered collector hanging from a level top line, tail inside the
stand footprint; crisp 1.5 mm cover edge with a 5 mm bolt rim, recessed top
panel and bolt heads; intake lowered to z 152 and widened to 156 mm with
runner ridges over the flank; lit boots ahead of the ports.

Found in the renders and fixed for round 2:
* the collector's constant-depth flat cut into the tapered tail bore - the
  tail showed as a half-open trough -> flat now follows the taper, 4.5 mm
  tail wall;
* intake ridges stood 14 mm proud over the top like handles -> lowered,
  ridge radius 13, now fused into the top;
* a ridge clipped the head's top strip (static check, 96 mm3) -> moved.

## Round 2 - both banks + pan + bellhousing (`renders/v8_round2/`)

Found and fixed for round 3:
* the pan read as a plain tall black box (70 mm deep, same width top to
  bottom) -> rail section 160 wide down to z -60, then a 128 mm sump with a
  45 deg under-cut, 3 ribs 3 mm proud on the sump, 6 mm bottom chamfer;
* side vent slots showed as dark rectangles in the 3/4 views -> removed
  (the floor panel has the vents);
* the front end plate with its screw heads, shaft stub and the motor slot
  are bare: that is the front cover + damper, not built until you approve
  this round.

## Round 3 - current state (`renders/v8_round3/`)

Both banks, S-curve headers into tapered collectors, lit boots, crisp valve
covers, provisional low/wide intake, rail-and-sump oil pan, cosmetic
bellhousing. Checks on this state: static check of every fixed-part pair
CLEAR; drive check (motor at both slot ends, 210 and 220 mm belts) CLEAR;
15 deg full-rotation sweep of every moving part against heads, covers,
boots, headers, collectors, intake, pan, panel, bell: NO COLLISIONS.

Still visible in the renders: the pan ribs read weakly in matte black (they
are 3 mm proud; they will read in print under side light); the front end
plate, shaft stub and motor slot are bare until the front cover and damper
exist; the collectors sit close under the sump (12 mm) - the stand brackets
will have to pass between them and the pan, which is the next design
constraint.

## What still looks off (honest list)

1. **Headers** are smooth printed tubes: no weld beads, no slip joints, no
   heat tint; the collector is a tapered log, not a 4-into-1 merge (your
   call: skip the merge). Paint test tile decides the finish.
2. **Block skirt** between the heads and the pan is a flat wall with the
   end-plate screw heads showing at both ends; the front cover and bell hide
   the ends, the sides stay plain. A cast-rib texture on the bank's outboard
   wall between the windows would help (cosmetic, cheap, not done).
3. **Fuel rails** are 8 mm rods printed with the intake; real rails have
   fittings and lines. Dropped detail by your simplification list.
4. **No accessories** yet: front cover, damper, 2-3 static pulleys and belt
   band, alternator, stand, edition plate - next phase.
5. **Intake** is still the provisional solid; the two-piece hollow version
   (`V8_INTAKE_PRINT_PROPOSAL.md`) will change its front face (separate
   throttle body spigot) and add a split line under the ridges.
6. **Plug boots** are plain cylinders with a dome; real boots have a 90 deg
   elbow and a lead. A lead would be a 2 mm filament "wire" - fragile, skipped.
7. **Colour**: renders use flat approximations of the approved palette; the
   satin-grey vs matte-black contrast will read stronger in print than here.
