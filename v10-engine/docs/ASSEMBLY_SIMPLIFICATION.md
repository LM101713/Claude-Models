# Assembly simplification plan (proposal, 2026-10-07)

Goal set by Liam for the 50-unit run: more visible detail, fewer parts,
fewer fasteners, details printed into the parts rather than added as pieces.
This is the plan for the exterior (the Blender skin). The moving core stays
as it is (D55). Nothing here is implemented yet; it waits on the look
approval and on Liam's yes to the items marked "decision".

## Where the fasteners go today (exterior only, from `docs/BOM.md` and `docs/SKIN_PRINT_REPORT.md`)

| Joint | Screws | Inserts | Magnets | Parts |
|---|---|---|---|---|
| 4 brackets -> pan, 4 brackets -> stand plate | 16 | 16 | | 4 brackets + plate |
| pan -> crankcase | 4 | 4 | | pan |
| floor panel -> pan | 6 | 6 | | panel |
| controller board -> floor panel standoffs | 4 | 4 | | |
| heads -> banks | 12 | 12 | | 2 heads |
| header flange plates -> heads | 4 | 4 | | 2 plates |
| valve covers | | | 16 | 2 covers + 2 caps |
| intake lid -> base | | | 8 | lid, base, throttle body |
| front cover, bellhousing, accessory module | | | 18 | 3 + alternator body |
| hall magnets (core) | | | 2 | |
| motor -> bulkhead, crank, end plates (core, unchanged) | 38 | 28 | | |
| **today** | **84** | **74** | **44** | **46 exterior pieces, 28 files** |

## Proposed changes

| # | Change | Screws | Inserts | Magnets | Parts | Detail gained | Needs |
|---|---|---|---|---|---|---|---|
| S1 | Print the four stand brackets into the oil pan as two full-length cast saddle rails, one per side. The stand plate screws up into the rails from underneath with 4 screws (countersunk if the plate is laser-cut acrylic or aluminium, which is also the recommendation in the production estimate). | -12 | -12 | | -4 | ribbed saddle rails with printed bolt bosses; screws hidden under the plate | decision: outsource the stand plate |
| S2 | Floor panel becomes a slide-in tray: a lip at the front engages a slot in the pan, 2 screws at the rear. | -4 | -4 | | | none, it is hidden | none |
| S3 | Controller board held by four printed snap clips in the floor panel instead of standoffs and screws. | -4 | -4 | | | none, hidden | none |
| S4 | Two printed locating dowels per head (6 mm, in the bank deck) and 4 head screws per head instead of 6. The dowels take the shear, the screws only clamp. | -4 | -4 | | | the two spare bolt bosses stay as cast detail | none |
| S5 | Header flange plates held by two 6 x 3 magnets each instead of two screws and inserts; the four primaries plugged into the port counterbores locate the plate. | -4 | -4 | +4 | | the plate can carry a full bolt row as printed detail instead of two real screws | none |
| S6 | Valve covers: a locating lip around the head's cover face, two magnet pairs per cover instead of four. | | | -8 | | the cover rail gets a continuous printed bolt row | none |
| S7 (decision) | Thread-forming instead of heat-set inserts on joints that are assembled once (pan -> crankcase, heads -> banks, stand): same M3 x 8 screw into a 2.5 mm pilot hole in ASA. Inserts stay only where a part is removed for service (motor, board, bellhousing end). | | about -16 more | | | none | Liam's yes: it changes the "keep all purchased components" rule and should be pull-tested on the first printed bank before it is adopted |

Totals after S1 to S6: **56 screws (from 84), 46 inserts (from 74), 40
magnets (from 44), 42 exterior pieces in 26 files (from 46 in 28)**. The
38 remaining core screws and 28 core inserts are untouched. S7 would take
inserts to about 30.

Rough assembly time saved: an insert is about 30 s with a soldering-iron
tip, a screw with threadlocker about 20 s, a magnet press about 10 s. S1 to
S6 save about 28 inserts and 28 screws per engine, call it 25 minutes, or
about 20 hours over the 50 engines. The bigger win is fewer things to get
wrong: no bracket left-right mix-ups, no standoff heights, no plate
alignment.

## Detail that goes into existing parts (no new pieces)

These answer the round-3 critique (`docs/VISUAL_REVIEW.md`) without adding
to the parts count:

- Oil pan: cast sump bowl, side ribs and a bolt rail, saddle rails from S1.
- Intake base: a fuel rail printed along each side of the base (black, so
  it is the base's own colour), with printed injector bosses into the heads'
  trumpet pockets.
- Front cover: water-pump snout, cast bosses and a bolt row; pulleys with
  V-grooves; the belt modelled with ribs.
- Block and heads: hex bolt heads printed in a row along the deck and the
  pan rail; cast part numbers raised 0.6 mm on the bank sides (this also
  closes the open item of hand-placed numbers on 33, 40 and 41, which move
  to the model).
- Headers: longer, equal-length primary sweeps (shape change, needs the look
  approval), flared collector tips.
- Controls plinth: same chamfers as the stand, recessed control panel.

## What stays as separate pieces, and why

- Plug boots (8): colour change to amber; they are push-fit, no fasteners.
- Oil caps (2): the valve cover prints top-face down for its finish, so a
  raised cap on that face would need support; the cap is a push-fit plug.
- Intake lid, base and throttle body: the lid prints as its own part so its
  roof is on the bed (D53); the base is a different colour.
- Front cover, bellhousing, accessory module, alternator body: magnet-held
  covers that hide the core's end plates and allow service.

## Open decisions for Liam

1. Outsource the stand plate (laser-cut) and the edition plate (engraved)
   so S1 can countersink from below. Recommended.
2. S7 thread-forming screws instead of inserts on once-only joints.
3. The header shape change (longer sweeps), which is the one item here that
   changes the silhouette.
