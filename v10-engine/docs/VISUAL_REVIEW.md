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

## Round 4 - front cover, damper, accessories, stand (`renders/v8_round4/`)

Found and fixed for round 5:
* the accessory module's full back plate (a hull-shaped sheet behind the
  pulleys) read as a flat shield over the front cover -> slim plate: a disc
  behind each pulley plus two 14 mm arms, pump snout, alternator body;
* renders showed the stand, brackets, plinth, damper and accessories in grey
  -> render colours corrected to the approved palette (matte black);
* the static check caught: module plate on the cover's cast rim (1213 mm3),
  cover bottom above the belt at the lowest motor position (220 mm belt),
  intake ridges intruding into the lid cavity where the base's tongue sits,
  throttle-body socket tilted the wrong way, stand bracket tabs inside the
  pan's 45 deg under-cut and ribs, bank B head mirrored but not shifted by
  the 6.5 mm bank offset. All fixed; static, drive and sweep re-run clear.

## Round 5 - current state (`renders/v8_round5/`)

Full engine on its stand, every part modelled: both banks, S-curve headers
into tapered collectors, lit boots on both banks, crisp valve covers,
two-piece hollow intake with pressed-in throttle body, rail-and-sump pan,
bellhousing, front cover with turning damper, black accessory drive (pump,
alternator, idler, belt band), stand plate on 4 brackets, controls plinth,
edition plate. Checks: static CLEAR, drive CLEAR (both belts, both slot
ends), 15 deg sweep against all fixed parts CLEAR, firmware step table
cross-checked against the CAD TDCs PASS. Hero render:
`renders/v8_round5/x5_hero_front_left.png`.

What the round-5 renders still show as off (honest):
* the front cover is a flat grey slab with a rim; real timing covers are
  sculpted with a water-pump housing - the pump here is a snout and pulley
  only (the housing fell to a print-geometry conflict; cheap to add back as
  a separate boss if you want it);
* the belt band is a flat loop; it reads as a belt from 1 m, not from 20 cm;
* the alternator is a plain black can with slots; no fan, no terminals;
* the block skirt between the heads and the pan rail is still a flat wall;
* headers are smooth tubes; the collector tails are plain open pipes;
* the intake ridges are soft humps; the real casting has sharper runner
  ridges and a flange line - the two-piece split line is hidden under them;
* colours in the renders are flat approximations of the palette.

## Print check on the round-5 parts (PrusaSlicer + mesh check) - found and fixed

The slicer run on all 59 exported parts caught a class of mistake I made on
five cosmetic parts: raised details on the very face the part prints on,
so the part would have stood on its bumps instead of the bed. Fixed:
* **valve cover**: the oil cap is now a separate pressed-in part (31B) and
  the rim bolts are recessed hex sockets; the cover prints flat on the
  textured plate as intended;
* **bellhousing**: hub ring and bolt circle recessed into the rear face;
* **front cover**: cast rim and bolt heads became a parting groove and
  dimples; the accessory module's plate now sits flat on that face;
* **collector**: the inboard flat was at 82 % radius = a 55 deg overhang;
  it now prints standing on its open tail (fully round, 7 deg cone, no flat);
* **oil pan**: the six panel-screw bosses hung from the floor ring in
  mid-air when printed skin-down; they are full-height pillars now;
* **intake base**: the runner stubs reached 8 mm below its floor; the base
  got a fourth, narrower bottom section (z 92) so the stubs start inside it.

Still open from the print check, for your decision:
* **intake lid**: with the 8 runner ridges standing proud of the top, the lid
  cannot print top-down (the top face would bridge between the ridges).
  Options: (a) print it upright with soluble support inside the hollow
  (H2C dual nozzle; support is removed from the open underside) and give the
  ridge and rail undersides 45 deg chamfers; (b) split off a flat roof plate
  (ridges up, no support) and accept a seam along the top fillet. I lean to
  (a). Not built either way yet.
* **throttle body**: the slicer flags its rear face (cut to the lid's front
  face at a compound angle) and the blade shaft as loose/overhanging; a
  flat rear face with a short pad would fix it (5-minute change, after your
  intake decision).
* **heads**: horizontal 14 mm / 9 mm sockets and the flange inserts in the
  outboard face bridge their tops (same as the V10 trumpet sockets did);
  acceptable at 0.2 mm layers, listed for honesty.
* **primaries**: "low bed adhesion" (14 mm footprint) - the 5 mm brim is
  already in the settings.

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
