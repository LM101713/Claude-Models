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

---

# Blender skin - critique rounds (`renders/skin_roundN/`)

Same method, new model: the whole visible exterior rebuilt in Blender by
`tools/skin_blender.py` (D54/D55); the CAD core still shows inside the
windows. Rendered headless with Cycles on CPU, 64 samples, 1456 x 1086.

## Skin round 1 - first full-engine set (`renders/skin_round1/`)

Only three of the eight views were kept (`ref1`, `ref2`, `ref3`): the set
was stopped when the first views showed a black slab with a round socket in
it on top of the intake. That was not the intake: the *library* valve cover
(the un-rotated master the engine-frame copies are made from) was left
visible in the scene and floated over the plenum in bank-local coordinates.
Render-only bug, nothing in the STLs - fixed (library objects are hidden
from render; `render_set`). Treat the intake in these three images as not
yet judged.

Ranked, what is off against STYLE_ai_01/02/03 (worst first):

1. **A stop too dark, and a dark backdrop.** The references are a light-grey
   cyclorama with bright satin metal; ours was mid-grey on dark grey, so
   every form reads flatter than it is. *Fixed:* key/fill/top up, a wrap
   fill from the front, world 1.0, +0.5 EV, backdrop 0.56.
2. **Headers read as white plastic tubes.** No flange per port, no weld
   beads, smooth bends; the collector tail is a bright open pipe. The
   "painted header" preview material (albedo 0.80) is most of it. *Fixed:*
   a square chamfered flange pad with two hex heads per primary on the
   plate (34), weld-bead rings at the flange exit and both tangent points of
   each bend (0.7 mm proud, 45 deg lead-in and -out so the standing print
   has no ledge), preview material changed to a brushed metallic grey. The
   printed part is still painted (decision 7); the paint test tile decides.
3. **Bellhousing is a blank shell** (ref2): flat rear face, one hub ring,
   nothing on the arch. *Fixed:* 11 axial half-round ribs over the arch and
   flanks ending in hex heads on a new bolt flange band at the open end
   (45 deg underside; the rear print face keeps only recessed detail,
   D53), plus a shallow recessed ring on the rear face.
4. **Head ends are slabs** (ref1 behind the damper, ref2 behind the bell):
   two 0.3 mm bosses that never showed. *Fixed:* a raised chamfered end pad
   with four hex heads and two proper 2.3 mm bosses with hex sockets. (Found
   while doing it: the bosses were 0.3 mm proud because the inside/outside
   signs were swapped; that is what also made the first version of the pad
   float 0.3 mm off the face and pinch the mesh - the fit check caught it.)
5. **Bank outboard walls and crankcase skirt are flat** between the windows
   and ribs; the references' block sides are busy with the head-joint and
   pan-rail bolt rows. *Fixed:* hex bolt rows under the deck lip and above
   the skirt foot on each bank (10 per bank, on the ribs) and pan-rail bolts
   between the crankcase skirt ribs.
6. **Close-up framing** (ref1) cropped the intake and throttle body out of
   the frame at 1.9x. *Fixed:* 1.45x from a little further forward.
7. **Windows read as black voids** from the rear quarter (ref2): the CAD
   pistons are inside but unlit, so the five slots per bank are black
   triangles. Left for now: it is the lighting, not the geometry, and the
   LED boot glow and the lighter studio change it; re-judge in round 2. If
   it still reads as holes the fallback is `WINDOWS = False` (your
   parameter) or a lighter core material in the renders.
8. **Valve covers**: the rim bolt sockets do not read at all and the top
   panel ribs are faint; the oil cap is a plain knurled puck. Not changed
   this round - the shape is right, it needs a sharper rim shadow line and
   a cap with a cross-bar; round 2 or 3.
9. **Controls plinth** (ref3): a black brick on the stand's front right with
   four holes facing the camera reads as a power strip. It is where you put
   it (D46) and it works for reach; a lower, chamfered, half-recessed plinth
   would hide better. Not changed; your call.
10. **Pan**: reads as a black box; the three ribs per side and the flange are
    there but need the brighter key to show. Re-judge in round 2.

Print-check side effects of the fixes (all in `docs/SKIN_PRINT_REPORT.md`):
the mirrored flange plate (34B) printed with its new pads on the bed - its
print orientation is now the opposite quarter turn; the head is manifold
again after the end-pad sign fix; the `rtree` package was missing in the
render environment, which is why the previous report's min-wall column read
`nan` - installed and listed in `tools/skin/README.md`.

## Skin round 2 - full set with the round-1 fixes (`renders/skin_round2/`)

All eight views rendered. What the fixes did: the bell ribs and flange
band, the head end pads, the flange pads and weld beads, the bolt rows on
the bank walls and the crankcase skirt all show and all read as cast or
welded detail rather than stuck-on bits (ref2, ref3, x3). The LED boots glow
through the windows from every side angle. The close-up now frames the
intake (ref1).

Ranked, what is still off (worst first):

1. **Over-exposed.** +0.5 EV on top of the stronger lights blew the satin
   aluminium out to white and lifted the matte-black covers to mid-grey;
   every cast face lost its shading, which is why the ribs on the pan and
   the skirt barely read (ref4, ref5). *Fixed for round 3:* exposure back to
   0.55, aluminium base 0.50, black with a weak specular lobe (a powder
   coat), headers darker.
2. **The intake is a lunch box** (ref1, x1, x2). The eight runner ridges
   stop at |y| 50 as rounded stumps and the roof between them is a blank
   100 x 170 mm plate; the throttle body is a plain tube end. *Fixed for
   round 3:* the ridge path now runs over the top edge and dives under the
   roof at |y| 24 (`INTAKE["ridge"]`, 4 points), into a raised 44 mm plenum
   spine with a bolt row along both edges; the throttle mouth gets a bell
   rim with a 45 deg lead. Print case unchanged: raised detail on the lid's
   print face is the open D53 decision (soluble support upright, or a split
   roof).
3. **The front cover is the biggest blank face on the engine** (ref5): a
   flat plate with a parting groove and eight dimples, and the drive in
   front of it is flat discs and a ribbon. It prints face down (D53), so the
   face can only carry recessed detail. *Fixed for round 3:* eight 1.8 mm
   cast-web grooves from behind the damper to the bolt dimples; two
   concentric face grooves in each pulley and two more rings in the damper
   face (those faces are up in their prints). *Your call, bigger:* print the
   cover rim-down with tree support inside the hidden shell, which would
   allow real raised bosses and a water-pump housing on the face. It breaks
   the "no new supports" rule for one hidden interior; I would do it for a
   50-engine run because the front is the face people photograph.
4. **Valve covers read as trays** (x3, ref4): the rim bolt sockets are dots,
   the top ribs are faint, the cap is a puck. *Fixed for round 3:* a cast ear
   per bolt on the rim's outer side (vertical in the top-down print) so the
   rim scallops like the references' bolt flange; a recessed grip cross in
   the cap top.
5. **Controls plinth** (ref3, ref5): from the front it is a black brick with
   four holes staring at the camera, the first thing the eye lands on after
   the damper. Position is yours (D46). Recommendation: keep the corner, drop
   it to an 18 mm wedge with the controls on a 30 deg sloped face, so it
   reads as a console. Not changed.
6. **Proportion, side view** (ref4): the engine reads shorter and taller
   than the reference, because the reference's valve covers run almost the
   whole block length and its headers sweep forward in long S-curves. Ours
   follow the plan's 1:2.42 proportions and D37's S-curve; the covers could
   grow 8 mm each end (x_inset 8 -> 4) at no cost - a round-3 candidate if
   you want it, not done.
7. **Windows**: with the boots lit the slots read as lit windows, not
   voids, from ref2/ref3/ref4. Keeping `WINDOWS = True`.
8. **Collectors**: a plain tapered log with a bright open tail. Could take a
   rolled lip and a slip-joint bead; low priority.
9. **Alternator**: a black can; its slots barely show. Low priority.

Print-check side effects of the round-1 fixes (`SKIN_PRINT_REPORT.md`):
the flange pads were roofing the pipe holes (1465 mm2 of ceilings per
plate) - the hole cutters now go through the pads and the pad corner is
relieved around the plug boot, which sits inside a square flange's
footprint; crankcase +106 mm2 and heads +178 mm2 of sub-47 deg faces from
the horizontal hex heads and bosses (3 mm long, print without support).

## Skin round 3 - full set with the round-2 fixes (`renders/skin_round3/`)

Exposure is back to a studio level (0.55) and the materials now read as
satin aluminium, matte black and painted steel instead of chalk. The
valve-cover bolt ears, the oil-cap cross, the runner ridges running into a
spine, the head end pads, the bell ribs and flange band, and the flange pads
and weld beads are all present in the renders. Honest ranking of what still
separates these from STYLE_ai_01..05, worst first:

1. **The lower third is a slab.** Pan, brackets, stand plate and plinth read
   as one dark block (ref3, ref4). The reference pan is a cast sump with a
   deep bowl, ribs and a bolt rail; ours is a box. The stand brackets are
   flat plates. This is the single biggest "3D-printed toy" tell.
2. **Intake runners are still bumps, not runners.** The ridges are 13 mm
   radius humps sitting on a flat lid (ref1, x2). The reference runners are
   tall, full-length tubes that sweep from the plenum down to the heads and
   hide the lid's flat top entirely. The spine helps but does not fix this.
3. **Front cover is a plate with grooves** (ref3, ref5). The reference front
   is a cast cover with a water-pump snout, bosses and a ribbed belt over
   three pulleys. Our belt is a smooth band, the pulleys are plain discs.
4. **Headers are short and straight.** Primaries drop vertically into a
   plain tube collector. The reference primaries are long equal-length sweeps
   that cross each other before the collector. Scaling the arc radius and
   length up would do more for the look than any surface detail.
5. **Aluminium is too light and too even.** The block, heads and intake are
   a flat light grey with no cast texture, no darkening in the pockets and
   no colour difference between machined faces and cast faces.
6. **Nothing is bolted to anything.** Apart from the valve-cover ears and
   the head end pads there are no visible fasteners on the block, pan, front
   cover or intake flange. The reference has a bolt every 40 mm.
7. **Missing kit that the eye expects:** fuel rail along each bank, plug
   wires out of the boots, dipstick, water pump, a belt with ribs.
8. **Valve cover is low.** It reads as a lid rather than a cast cover with
   wall height; the reference cover is roughly twice as tall relative to the
   head.
9. **Controls plinth** is a black block with four holes (ref3 lower left);
   it needs to read as part of the stand (same chamfers, a recessed panel).
10. **Collector outlets** end in a flat cut; a flared tip or a slip joint
    would finish them.

This is the full-engine set Liam asked to see before approving the look.
Items 1 to 4 are shape changes, not surface detail, and are the ones to
decide on; 5 to 10 are a round of detail on top.

Fasteners and parts this round did not change; see
`docs/ASSEMBLY_SIMPLIFICATION.md` for the plan to cut them.

## Skin round 4 - shape changes (`renders/skin_round4/`)

What changed: continuous runner tubes into a raised spine with the plenum
narrowed (D61), cast saddle legs on the pan instead of brackets (D60),
longer header sweeps and flared collector tails (D62), a ribbed belt,
pulley rim grooves and a water-pump housing. Honest ranking of what is
still off, worst first:

1. **The intake now reads as runners, but the top is lumpy.** Eight tubes
   diving into a narrow 48 mm spine give a quilted roof (ref1, ref3). The
   reference has a flat cast plenum top that the runners run under. Fix:
   a wide flat top plate (about 70 mm) with a bolt row, runners ending
   under its edge.
2. **The controls plinth is still a black block with four holes** (ref3,
   lower left). It needs the stand's chamfers, a recessed control panel and
   rounded corners so it reads as part of the stand.
3. **Collectors are plain fat tubes.** A slip-joint band and a visible
   4-into-1 merge cone would finish them; the flared tails help.
4. **The front cover face stays a plate.** With the face as the print face
   only recessed detail is possible; a raised cast face needs the cover
   printed rim-down on soluble support (decision for Liam).
5. **Throttle body**: plain tube; a throttle-cam disc and shaft boss on the
   side would carry it.
6. **Pan sump sides are smooth between the legs**; a drain-plug boss and
   one more rib would do.
7. The fuel rail reads as a thin floating tube; a thicker rail (r 5) with
   end caps would read as the reference's black rail.

Items 1, 2, 3, 5, 6 and 7 are the round-5 detail pass. Item 4 is Liam's
call.

## Skin round 5 - detail pass (`renders/skin_round5/`)

What changed: wide flat plenum top plate with a bolt row, thicker fuel
rail with end fittings, throttle cam and shaft boss, collector slip-joint
bands with clamp bolts, plinth with the stand's chamfers and a panel line,
drain-plug boss on the sump. The intake now reads as the reference's cast
plenum (ref1, x2): runners under a bolted plate, rail alongside. Honest
ranking of what is still off, worst first:

1. **Almost no fasteners on the engine itself.** The reference is covered
   in bolt heads: valve-cover flange, head-to-block seam, pan rail,
   bellhousing circle, front cover. The skin has them only on the plenum
   plate, spine, flange plates and collector bands, so the engine reads as
   "clean" rather than "assembled" (ref2, ref4). Fix: raised 3 mm hex rows
   on the vertical faces (1 mm proud, 45 deg underside, no support): about
   14 per valve-cover flange, 10 per pan rail, 12 on the bellhousing, 8 on
   the front cover rim. Cosmetic only, no new parts.
2. **The valve cover is a slab with two scribed lines** (x3). The reference
   cover has a crisp 3-4 mm flange step at the base carrying the bolt row,
   and a taller, flatter top. Fix: flange step plus item 1; the cap can
   grow to r 11 with a knurl that reads from 1 m.
3. **Eight bare plug boots** (ref1, x3). Without wires they look like pegs.
   Options: one printed loom bar per bank that clips over the boots (2
   parts, 0 fasteners), or 8 lengths of 3 mm silicone cord into a drilled
   loom bar (adds a purchased item, about $3 per engine). Liam's call.
4. **The front is flat** (ref5). The belt runs between three discs on a
   plain plate; the reference has an alternator body, a water-pump snout
   and a tensioner giving the front depth. An alternator body (one part,
   magnet-held on the cover) and a longer pump snout would carry it.
5. **Rear bellhousing** (ref2): plate plus plain ring. Needs 6-8 cast
   ribs from the ring to the flange and the bolt circle from item 1.
6. **Stand legs**: the black box legs read heavy next to the reference's
   slim angled steel stands, and the plinth's four holes read as a black
   bar from the front (ref3, ref5). Either slim the legs (the pan saddle
   legs now carry the load, so the stand's own legs can be 10 mm thinner)
   or move the plinth to the rear.
7. **Surface**: ASA prints smooth; the reference is sand-cast. A slicer
   "fuzzy skin" (0.3 mm, 0.4 mm point distance) on block, heads, intake
   and pan gets most of the way for free. Test on the prototype bank
   before deciding.

Items 1, 2 and 5 are a round-6 pass with no new parts or fasteners.
Items 3, 4 and 6 add parts or change the stand and need Liam's yes.
Item 7 is a slicer setting, tested on the first prototype print.

Check results on the round-5 files: 26 files watertight; fits 207/208
within 0.02 mm (one benign vertex on the throttle-body socket lead
chamfer; the plinth panel line clipped the power-switch hole by 0.04 mm,
moved 1.5 mm inward after this render set); static interference 0 apart
from the floor-tray board pins in the CAD electronics envelope (expected);
full-rotation sweep 2216 pair checks, 0 collisions.
