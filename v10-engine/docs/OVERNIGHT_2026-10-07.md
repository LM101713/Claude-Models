# Overnight summary, 2026-10-07 (for Liam)

Branch with everything below: `claude/v8-skin-round4-overnight` (backup
pushes only, no PR). The original session had pushed its own rounds 1-3 to
`claude/v10-engine-display-model-4r6gjr` in parallel; this branch diverged
from 15b1d24 and supersedes that work (rounds 1-5, sourcing, simplification).

## Before and after (per engine)

| | CAD exterior (BOM.md, sliced) | Blender skin round 5 | Source |
|---|---|---|---|
| Printed pieces | 88 | 90 (42 exterior in 26 files + 48 core) | skin/parts.json, BOM.md section 1 (the skin counts the 8 plug boots and the edition plate separately) |
| M3 x 8 screws | 84 | 56 | BOM.md fastener tables (D60, D63) |
| Heat-set inserts | 74 | 46 | same |
| 6 x 3 magnets | 44 | 44 | same (8 fewer on the covers, 8 more on the flange plates) |
| Print time | 127 h (PrusaSlicer) | about 141 h (estimate, +-15 %) | tools/skin_estimate.py: each skin part scaled from its CAD twin's g/cm3 and h/cm3 |
| Filament | 3.05 kg | about 3.45 kg (estimate) | same |
| Final assembly | 1 h 50 min (stages B-H, ASSEMBLY.md) | about 1 h 25 min (estimate: 28 inserts and 28 screws fewer, 4 parts fewer) | 30 s per insert, 20 s per screw assumed |
| All-in labour | 5.0 h | about 4.5 h | PRODUCTION_PLAN.md labour table minus the above |
| Materials at 50 | $273 (old BOM prices) | about $268 at verified 50-off prices | docs/SOURCING.md |

The print time went up, not down: the sculpted exterior (sump with legs,
runner tubes, bigger lid) carries about 10 % more plastic. Outsourcing the
stand plate (laser-cut) takes 8 h and 230 g back off: about 133 h and 3.2 kg.

## What changed in the look (rounds 3 to 5)

- Round 3: materials and lighting matched to the references; the full
  eight-view set.
- Round 4 (shapes): eight continuous intake runner tubes into a raised
  spine, plenum narrowed; cast saddle legs on the pan instead of brackets;
  longer header sweeps with flared collector tails; ribbed belt, grooved
  pulley rims, water-pump housing.
- Round 5 (detail): wide flat plenum top plate with a bolt row, thicker
  fuel rail with end fittings, throttle cam, collector slip-joint bands
  with clamp bolts, plinth restyled to the stand's chamfers with a panel
  line, drain-plug boss on the sump.
- Critiques per round in VISUAL_REVIEW.md ("Skin round N"). The round-5
  list, worst first: no bolt heads on the engine itself, valve cover still
  a slab, bare plug boots, flat front (no alternator body), plain
  bellhousing, heavy stand legs, smooth surface (slicer fuzzy skin).
- Round 6, if the direction is approved: bolt rows on cover flanges, pan
  rail, bellhousing and front cover rim, a valve-cover flange step and
  bellhousing ribs. Cosmetic only, no new parts or fasteners.

## Assembly simplifications built (D60, D63)

S1 saddle legs (4 brackets, 12 screws, 12 inserts gone), S2 slide-in floor
tray (6 screws to 2), S3 board on locating pins and snap hooks (4 screws, 4
inserts gone), S4 head dowels and 4 screws per head (12 to 8), S5
magnet-held header flange plates (4 screws, 4 inserts gone), S6 two magnet
pairs per valve cover. Details: ASSEMBLY_SIMPLIFICATION.md.

## Checks run on the round-5 files

- Mesh: all 26 skin files watertight; fits within 0.02 mm except one
  benign vertex on the throttle-body socket's lead chamfer (the plinth
  panel line clipped the power-switch hole by 0.04 mm in the rendered set;
  moved 1.5 mm inward, re-exported and passing); min walls at or above
  0.8 mm except the cylinder bank's deck lip (0.5 mm slivers where the
  window-frame chamfer meets the lip, pre-existing).
- Interference against the CAD core: static 0 overlaps apart from the
  board's four locating pins sitting in the board holes (expected, 34 mm3);
  full-rotation sweep at 15 deg steps: 0 collisions (SKIN_CHECK_REPORT.md).
- Print cases that still need a decision: intake lid (runners and top plate
  on the print face: soluble support upright, or a split roof, D53); front
  cover face (rim-down on support if a cast face is wanted).

## Cheapest useful prototype print (one printer, about 3 days, ~1.6 kg)

1. One cylinder bank + one head + valve cover + oil cap + flange plate +
   4 primaries + 4 boots: tests head dowels and 4-screw clamp, cover and
   plate magnets, crush fits, header fit, primary drop test. ~35 h, 650 g.
2. Intake lid + base + throttle body: tests the D53 print case and the
   runner tubes across the split. ~15 h, 450 g.
3. Oil pan + floor tray: tests the saddle legs, tongue, snap hooks. ~17 h,
   600 g.

About $40 of ASA. Nothing else needs printing before the look is signed off.

## Needs Liam's yes

1. Look: approve round 5 as the direction (then the detail is polish).
2. Outsource the stand plate (laser-cut acrylic or aluminium) and the
   edition plate (engraved). Recommended.
3. S7 thread-forming screws on once-only joints (46 inserts to about 30):
   changes the "keep all purchased parts" rule; pull-test on the first bank.
4. Drop the Pololu regulator for a buck module; stepper substitute
   17HS15-1504S1; Mean Well cord note (docs/SOURCING.md).
5. Print the front cover rim-down on support for a cast face, or keep the
   flat face.
6. Acrylic dust cover in the BOM or not.

## Still needed from Liam

Scott's deadline or batch schedule; motor behaviour (slow continuous run
all day?); building alone or with help; colour sign-off (filament order).
