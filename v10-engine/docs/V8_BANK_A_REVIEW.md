# V8 - bank A exterior, for your approval

Status: **moving core verified, exterior of ONE bank built, STOPPED for your
approval.** Nothing of the V8 is printed. Nothing here is production-ready.

Renders (CAD left, reference right): `renders/v8_bankA/*_vs_ref.png`
(ref1-ref5 match the five STYLE_ai images); extra angles `x1_bankA_low_34`,
`x2_bankA_headers` (looking up at the windows between the pipes), `x3_top`,
`x4_no_intake_34`.

## 1. Moving core (done, checked)

* 8 cylinders, cross-plane crank (throws 0 / 90 / 270 / 180 deg), bank B
  6.5 mm ahead of bank A, two 686 bearings per straight crankpin, the same
  rods / pistons / wrist pins / rails / 608 mains as the V10.
* Firing order `1-8-7-3-6-5-4-2` (your 4/7 swap) is one line in
  `config_v8.py`; the self-check proves each cylinder fires at one of its TDCs.
* **Full rotation, 6 deg steps, every moving part against the block and each
  other: no collisions.** 15 deg sweep against the new head / cover / boots /
  headers / intake: no collisions.
* All core parts are single valid solids (3 crank web types, 2 end webs,
  4 pins, rings, shaft, 8 rods, 8 pistons, crankcase, valley beam, bank, end
  plate).

## 2. What bank A's exterior is (parts 30-36)

| Part | Print size L x W x H (mm) | Print orientation | Notes |
|---|---|---|---|
| 30 cylinder head | 210 x 72 x 36 | deck down (as the V10 head) | LED strip groove in the deck, 2 valve recesses per chamber, rail pockets, magnet seat for the cover, 20 mm exhaust port counterbores with 14 mm crush sockets, 9 mm boot sockets over a hidden strip groove, runner pockets on the valley face, 2 horizontal inserts for the flange plate |
| 31 valve cover | 197 x 51 x 36 | top down on the textured plate | rounded box, 3.5 mm top chamfer, bolt-boss rim, knurled oil cap, 4 magnet pillars (same 6x3 magnets) |
| 32 plug boot (x4 per bank) | 10 x 10 x 26 | standing on the shaft end | translucent slot of the palette; lit by the strip under the flange plate |
| 33 header primary (x4 per bank, one shape) | 25 x 40 x 124 | standing on the collector spigot | 16 mm straight out of the port, 47 deg bend (R24), 75 mm drop leaning 17 deg rearward, 14 mm crush spigots both ends; nothing steeper than 45 deg |
| 34 flange plate | 198 x 33 x 4 | flat | 4 pipe holes, 4 boot holes, 2 captive-style M3x8 counterbores into head inserts |
| 35 collector | 258 x 36 x 33 | lying on its flat inboard side | 36 mm log, saddle sockets for the 4 pipes, 60 mm open tail to the rear; bank B is the mirror |
| 36 intake (provisional) | 216 x 144 x 83 | not decided (two-piece split likely) | shown for proportion feedback only, see section 5 |

Palette as approved: head / intake satin grey, cover matte black, headers
"painted" (rendered light), boots translucent (rendered amber to show the glow).

## 3. How it compares to the references (my own critique)

Good:
* Reads as a pushrod V8 bank: low head, tall flat-topped valve cover with an
  oil cap, four primaries out of the head, lit plugs under the ports, intake
  humps above.
* The pipe drops sit between the block windows, so each window stays visible
  (your option c); from below (`x2_bankA_headers`) the pistons show through.
* The intake now spans the valley (126 mm wide at the top versus the mockup's
  56-72 mm) with four runner humps per side and a 44 mm throttle body.

Not yet right (I would fix these in the two critique rounds after approval):
1. **Header shape.** Real primaries curve in one long sweep and merge 4-into-1;
   mine are stiff J pipes into a straight log. Within the print rules I can add
   a second gentle bend (an S) and fair the pipe ends into the collector, but
   a true merge collector needs supports or a CAD artist.
2. **Collector tail** sticks 80 mm out behind the block; the stand / bellhousing
   will decide how much of that is right.
3. **Valve cover** top chamfer (3.5 mm) reads soft; references have crisp edges
   with a small radius and a visible bolt rail. Easy to change (`VC` in config).
4. **Head band** between the cover and the flange plate is plain; a cast-rib
   texture or a thin head-gasket line would help. Cosmetic only.
5. **Block** still reads boxy because there is no pan, front cover, damper or
   bellhousing yet (next phase: wide ribbed pan as motor / electronics bay,
   pulleys in a tidy arc, per your mockup feedback).
6. **Fuel rails** are printed with the intake for now; separate rails with
   injector plugs would look better but add 8 tiny fits.

## 4. Checks run on bank A

* Static check (every pair of fixed parts, bank A + core): **CLEAR**. The only
  overlaps are the designed crush-rib fits (pipe spigot in head 3.3 mm3, pipe
  spigot in collector, rails in head, bearings in end plates).
* Smallest gaps: pipe to flange-plate hole 0.20 mm (clearance fit), plate to
  block deck 0.5 mm, runner end to head pocket 0.5 mm.
* 15 deg sweep of the moving parts against head / cover / boots / headers /
  intake over a full revolution: **no collisions**.
* Windows strength (your question): 16 mm ligaments between windows, 13 mm at
  the block ends, 11.2 mm wall pierced, 2.5 mm deck lip above each window,
  head-screw inserts 6 mm from the window edge, bank is one solid. Same window
  size as the verified V10 bank. `WINDOWS = False` removes them.

## 5. Open points for you

1. **Approve bank A as a direction?** (yes / change X first). Bank B is the
   same parts mirrored or shifted 6.5 mm; it is a 10-minute step once approved.
2. **Intake direction:** keep this tall single-plane plenum, or lower / wider?
   (Reference STYLE_ai_04/05 have a boxy top with the throttle body on the
   front, which is what this is.) It must be hollowed (3 mm walls) and probably
   split in two for printing; that is design work after your OK.
3. **Header style:** accept the log collector (honest simplification) or do you
   want me to try an S-curve primary and a tapered collector within the
   no-support rule?
4. **Boot colour:** translucent natural / white (a 5th filament) or the
   satin-grey slot with a drilled light pipe? The palette rule is 4 filaments.

## 6. Not done on purpose (waits for approval)

Bank B, oil pan (motor + electronics bay; the fit check of a NEMA 17 and the
90 x 70 mm board inside it comes before building it), front cover, damper,
static belt band, pulleys, alternator, bellhousing, stand with brackets and
the swappable edition plate, firmware step table for 8 cylinders, LED plan,
plates / BOM / kit, paint test tile, VISUAL_REVIEW.md critique rounds.
