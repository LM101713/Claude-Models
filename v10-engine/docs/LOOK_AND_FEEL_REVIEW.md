# Look-and-feel review (renders only - nothing printed yet)

Method: the `display-model-polish` review loop. Nine views were examined:
front 3/4 from slightly above (`renders/01_engine_iso.png`), front
(`02`), rear 3/4 (`03`), top (`04`), covers off (`05`), window close-up
(`06`), plus four new ones in `renders/review/`: side, rear 3/4 from above,
close-up of the trumpet / coil / cam-cover area, and the buyer's eye-level 3/4
from table height. **Everything here is a judgment on renders.** Renders hide layer
lines, seams, colour reality and feel; nothing below is confirmed until a
unit is printed and finished. **No exterior change was made for this review;
the items are listed for your decision.**

## 0. Reference check

No reference photos were supplied, and the engine is an original design (not
a copy of any team's unit), so the only check possible is against generic
F1-V10 proportions:

| | This model | Typical 3.0 L F1 V10 (public figures) | Verdict |
|---|---|---|---|
| Bank angle | 90 deg | 72-90 deg | fine |
| Bore / stroke | 45.6 / 26 mm = 1.75 | about 95 / 42 mm = 2.2-2.3 | ours is less over-square: the bores could look a touch small for the block length. Not worth changing (cylinder pitch is tied to the LED strip). |
| Engine length : height (with trumpets) | 383 : 241 = 1.59 | about 1.3-1.4 | ours reads slightly long and low. The trumpets are the only lever (taller bells) - see item 6. |
| Engine : base footprint | 383 x 275 on 400 x 280 | - | the engine fills the base to within 8-10 mm each side: tight. It looks "placed on a box", not "presented on a plinth" (item 2). |

## 1. Ranked: what looks or feels cheap, why, and the fix

| Rank | What | Why it reads cheap | Fix (none applied) | Exterior? |
|---|---|---|---|---|
| 1 | **Block, banks and crankcase are plain slabs.** Big flat grey faces above the windows, sharp box corners on the banks, a box crankcase. In the side and eye-level views the engine is 60 % flat rectangle. | Real castings have draft, soft edges, ribs, bosses and a parting line; CAD boxes have none. Flat faces also show layer lines and seams most. | Secondary forms on the bank outboard faces: 2 shallow horizontal ribs or a recessed panel between the windows and the deck chamfer, cast-boss discs around the side-panel magnets, a 1.5 mm chamfer on every outer vertical edge of banks and crankcase. All 45-deg-printable, all parametric. | **Yes - needs approval** |
| 2 | **The base is a 72 mm tall black box.** Vent slots and the plaque are the only features. Eye-level view: it looks like an electronics enclosure the engine sits on. | Premium display pieces sit on a plinth with a visual step or a different material; a single tall slab reads as a case. | Keep the volume (it holds the motor and board) but break it: a 6-8 mm dark recessed reveal around the bottom (a shadow gap, prints skin-down with no support) and/or a two-material look: ASA top shell, a wrapped band (leather, veneer, brushed aluminium tape) around the sides, or a real wood plinth. | **Yes - needs approval** (reveal is a small change; wood/veneer is a BOM decision) |
| 3 | **Front and rear end covers are rounded lumps.** They are the second thing the eye hits at eye level and they have no feature at all. | Flat dome, no edge definition, no echo of what is inside (pulley/belt). | A recessed ring or two concentric steps on the face (reads as a pulley cover), a 1.5 mm edge chamfer, and keep the magnets. Printed face-down on the textured plate the face will be the best surface on the engine. | **Yes - needs approval** |
| 4 | **Coil packs are five plain red cylinders.** Pure saturated red in a row = toy. | Real coil packs are dark with a small coloured cap/connector; the red here is a block of colour. | Keep the shape; change the colour slot to dark (black or dark grey) with a single red detail (top ring or a 2 mm red cap printed as a separate colour change on the small coil-pack plate - allowed by your D4). | Colour only - **your decision on palette slot 3** |
| 5 | **Cam covers are plain black boxes.** | The largest dark surface on the engine has nothing on it. | Two subtle longitudinal recessed lines 0.6 mm deep, or a recessed oblong panel with a 45 deg edge; optional engraved "V10" lettering printed in slot 4 colour on a small separate plate (your D4 allows one colour change on a small plate). | **Yes - needs approval** |
| 6 | **Trumpets look thin and all identical; the engine looks a little low.** | 32 mm bells on 44 mm stacks on a 383 mm engine; the lips are a 0.4 mm band at 0.12 mm layers - may print ragged. | Taller stacks (+6-8 mm) and a slightly thicker rolled lip (0.8 mm) - also fixes the print-fragility risk. Or the aluminium trumpets M05 (optional BOM line): machined aluminium bells are the single biggest "premium" cue available on this engine. | **Yes - height is exterior; lip thickness is minor** |
| 7 | **Exhaust colour.** Gold-ish filament looks like a toy; the collector tail is a straight cut. | Real headers are steel/titanium with heat colouring; the rendered gold is flat. | Print in slot 4 "metal" grey and spray a metallic titanium/heat-bronze coat (batch-paint 10 headers on a rack), or a dark bronze ASA. Add a 1 mm chamfer on the tail-pipe lip (interior of the pipe end; tiny). | Colour/finish - **your decision**; tail chamfer is negligible |
| 8 | **Visible exhaust-flange screw heads** (5 per header). | Bright stainless heads on a dark header. | Black-oxide M3 x 8 for the 10 exhaust screws only (same size, different finish: one extra line on the BOM). | No (BOM only) |
| 9 | **Window edges are sharp slots.** The pistons behind them are the hero feature, but the frame is a plain cut. | A cutaway display engine frames its windows; a sharp slot looks machined, not designed. | 1.0-1.5 mm chamfer on the outer window edges (prints as a 45 deg face on the deck-down bank). | **Yes - needs approval** (small) |
| 10 | **Layer lines on the large vertical show faces** (bank sides, crankcase sides, base sides) at 0.20 mm. | Not visible in renders; always visible in real life on flat vertical walls within 1 m. | Finish test (section 2); or 0.12 mm layers on the two banks and the crankcase only (+ about 12 h per engine). | No |
| 11 | **Seams.** Trumpets, coil packs, pistons and the base halves will each have a slicer seam. | A vertical seam line down 10 identical trumpets is very visible. | Set the seam to the rear ("aligned", rear) for all round parts; the trumpets' seams then face the valley. Check on unit #1. | No (slicer setting) |
| 12 | **Weight and balance.** About 3.1 kg of plastic plus steel; the base is a hollow 400 x 280 shell with a 3 mm bottom panel. | Hollow bases feel cheap when lifted and slide when the knob is turned. | A 4 mm steel plate (about 1.5 kg, 200 x 150) screwed to the inside of the rear bottom panel using the existing pillars, or two 500 g lead/steel bars. Interior only; no exterior change; adds a BOM line. | No (interior) - **needs your OK because it adds cost/weight** |
| 13 | **Base-to-engine shadow line.** The crankcase sits in a 1.5 mm recess with a shadow groove around it (good), but the end plates and front cover sit directly on the skin. | Reads as parts standing on a lid. | Already acceptable; revisit after item 2. | - |

What already reads well in the renders (keep): the 90 deg V proportions, the
visible pistons and rods through the windows, the cast parting-line chamfer on
the heads, the full-width exhaust headers, the hidden belt drive, the magnetic
covers with no visible screws on the heads, the numbered plate.

## 2. Per-part finish plan (ASA, repeatable per unit) - to be proven on test tiles

| Part family | Print face | Finish | Why | Time / unit |
|---|---|---|---|---|
| Base halves (19, 20) | top skin on the **textured** plate | raw: textured top, matte black ASA; chamfer edges deburred; plaque applied last | textured plate hides layer lines on the top; sides are vertical walls - see item 10 | 10 min |
| Bottom panels (21) | flat | raw | never seen | 0 |
| Banks (03), crankcase (01), end plates (04) - slot 1 grey | deck-down / open-top-up | **finish test required**: (a) raw 0.20, (b) raw 0.12, (c) 0.20 + 400-grit scuff + 2 coats grey filler primer + satin clear. Pick by look at 0.5 m. Masking: all bores, rail holes, insert holes, magnet pockets (fits must stay raw). | these are the biggest show surfaces and the hardest to make look like metal | (a) 0 / (b) +12 h print / (c) 45 min |
| Heads (10) | deck-down | raw; the top is covered by the cam cover, the visible sides are 28 mm tall walls | parting-line chamfer already breaks the face | 5 min deburr |
| Cam covers (11), side panels (12), end covers (18) - slot 2 dark | top-down on the **textured** plate | raw textured matte black; optional 1 coat matte clear for even sheen | textured plate on the show face is the cheapest premium finish there is | 5 min |
| Coil packs (16) | top on bed | raw; colour per your decision (item 4) | tiny parts, hidden seams | 0 |
| Trumpets (13) | bell-down | raw 0.12 mm with seam to the rear, **or** aluminium M05 | the bell interior is the best-printed surface when printed mouth-down | 2 min each to clean the lip |
| Exhausts (14, 15) | flat back down | 400-grit scuff, metallic spray (titanium / gunmetal), optional heat-bronze tint at the collector | plastic-looking gold headers are the fastest way to look like a toy | 20 min (batch 10) |
| Throttle frame (17) | flat | raw dark | mostly hidden under the trumpets | 0 |
| Crank, rods, pistons | - | raw; **no finish on any moving part** | finishes change fits | 0 |
| Screws | - | black-oxide for the 10 exhaust screws; stainless everywhere else (hidden) | | 0 |

Batch process per engine (after the finish test chooses (a)/(b)/(c) for the
grey parts): deburr all show edges -> mask fits -> primer/paint the grey parts
(if c) -> paint 2 headers -> seams check -> assemble -> plaque last. Estimate
1.0 h per engine with (a) or (b), 1.8 h with (c). All of this is unverified
until the test tiles exist: **print one bank section (a cut-down 60 mm piece)
three ways before deciding** - 3 x 25 min.

## 3. What to check on the first printed unit (look and feel)

1. Layer-line visibility on the bank sides, crankcase sides and base sides at
   0.5 m and 1 m under room light; photograph against the render.
2. Seam position on all 10 trumpets, 10 coil packs, 10 pistons (through the
   windows), both base halves. Is it consistently at the rear?
3. Colour match: block grey vs end plates vs beam (same lot); cam covers vs
   side panels vs end covers vs base (same lot). Any sheen difference between
   textured-plate faces and vertical walls.
4. Gaps: cam cover to head (should be a uniform shadow line, no daylight),
   side panel to bank, end cover to end plate, base half joint, plaque recess.
5. Edges: elephant foot on any bed edge (banks' deck edge, heads' deck edge,
   base top chamfer, trumpet rims); brim scars on coil packs and T4d.
6. Window frames: are the V-bottom gables crisp or sagged?
7. Trumpet rims: intact, round, no ragged 0.4 mm lip.
8. Heft: lift the finished unit; does the base feel solid or like a hollow
   shell (item 12)?
9. Running: at 20, 60, 120 RPM - belt whine, motor hum through the base,
   piston tick, any visible wobble of the crank webs through the windows,
   trumpet vibration.
10. Touch: the knob, the START button, the rocker - do they feel in keeping
    (the cheap rocker will be the first thing a buyer touches).
11. The plaque: centred, flat, no bubbles; is the engraving legible at arm's
    length?
12. Overall from the buyer's angle (3/4, slightly above, 1.5 m): does the
    engine or the base dominate?

## 4. Decisions needed from you (none made)

* Items 1, 2, 3, 5, 6, 9: exterior detailing changes - approve any, all or
  none. Each is parametric and printable without supports; I would do them in
  one pass and re-run every check.
* Item 4: coil-pack colour (dark with red detail vs the current solid red).
* Item 6 alternative: aluminium trumpets (M05, about $50 per engine at 50).
* Item 7: exhaust finish (paint vs dark bronze filament).
* Item 12: ballast plate inside the base (adds about $8 and 1.5 kg).
* Finish route for the grey parts: decided by the three test tiles, not by
  me.

Nothing in this document claims the model looks premium. That claim can only
be made about a printed, finished unit seen in person.
