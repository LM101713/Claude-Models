# Phase 1: print, build and test the core mechanism

Phase 1 is done in **two print rounds**. The fits are tuned after the first,
cheap round, so nothing big gets printed twice.

* **Round 1 (about 1 day of printing):** the tolerance test piece in every
  material, plus a few small mechanism parts. Report the results and I update
  `config.py`.
* **Round 2 (about 3 days):** the complete Phase 1 engine with the corrected
  fits. You then run the build-and-spin test below.

---

## Round 1: what to print

| File (`stl/`) | Qty | Material | Layer | Walls | Infill | Orientation | Approx. time |
|---|---|---|---|---|---|---|---|
| `00_tolerance_test` | 1 **per material** (PLA, PETG, ASA; ABS too if you will use it) | each | 0.20 (0.15 for the PLA one) | 3 | 15% gyroid | as exported (flat, labels up) | ~2 h each |
| `07_conrod` | 2 | PLA | 0.15 | 4 | 40% gyroid | as exported (flat) | ~20 min each |
| `08_piston` | 2 | PLA | 0.15 | 4 | 25% gyroid | as exported (crown on bed) | ~50 min each |
| `05_crank_segment_54` | 1 | ASA | 0.16 | 5 | 40% gyroid | as exported (engraved face up) | ~1.5 h |
| `04_crank_end_web` | 1 | ASA | 0.16 | 5 | 40% gyroid | as exported | ~40 min |
| `P1_proto_split_crankpin` | 2 | PETG | 0.12 | 4 | 100% | standing on end | ~25 min each |

**Common settings:** textured PEI plate, no supports anywhere, seam aligned
to rear, *"arc fitting"* on, *"precise wall"* on. Turn **off** elephant-foot
compensation for the tolerance test so it shows your raw printer behaviour.
Once tuned, the same setting must be used on every production print. ASA/ABS:
chamber heating on, door closed, aux fan low, let parts cool in the printer.

### Tolerance test: how to read it

Each row tests one fit at five sizes. The column headers show the offset from
the current `config.py` value (−.10, −.05, 0, +.05, +.10 mm). For each row, find
the **best** hole using the purchased part:

| Row | Test with | "Best" means |
|---|---|---|
| **608** | 608 bearing | Presses in by thumb or light vise pressure, does not fall out, outer ring cannot be turned by hand |
| **686** | 686 bearing | same as 608 |
| **BU5** | 3×5×5 bronze bushing | Firm press with a vise; bushing bore still takes the 3 mm rod freely afterwards (the press must not squeeze the bushing) |
| **R3** | 3 mm steel rail | Slides through freely with **no** side play you can feel |
| **S8** | 8 mm rod or drill shank | Slides through with no play (this is the main-shaft clearance) |
| **MAG** | 6×3 magnet | Presses in by thumb, cannot be pulled out with fingers |
| **INS** | M3 heat-set insert | Iron at the insert maker's temperature: goes in straight, flush, with a small ring of melted plastic and no bulge on the far side |
| **D6** | machined crankpin end, or a 6 mm drill shank to judge the round part | Slides in, **no rotation play** on the flat |
| fin **P3** (horizontal holes) | 3 mm dowel pin | Light press with a vise, like a piston pin |
| fin **MAG** (horizontal) | 6×3 magnet | Presses in by thumb |

**Report back** one line per row per material, for example
`ASA 608: best +.05, 0 was too tight`. If none of the five sizes fits, tell me
which end was closest and I'll shift the whole range.

### Round 1 bench checks (small parts)

- [ ] 686 presses into the rod big end squarely (push on the **outer ring**
      only, e.g. with a 13 mm socket in a vise). It must not rock or turn.
- [ ] One bushing presses into the rod small end, two into the piston lug
      (top and bottom, flush). Use a 3 mm rod through the bushings while
      pressing to keep them in line.
- [ ] A 3 mm rail slides through **both** lug bushings in one smooth stroke,
      with no tight spot.
- [ ] Wrist pin (3×20) presses through piston boss → rod bushing → far boss.
      The pin ends up centred and recessed about 2 mm from each side of the
      piston. The rod swings freely with no side binding and 0.5 mm float
      each side.
- [ ] Proto crankpin: its D-end slides into the segment and end web D-holes with
      no rotation play. An M3×8 screw (it self-taps into the printed pin)
      pulls it home flat.
- [ ] Rod with bearing slides onto the proto pin journal and spins freely.
- [ ] **Heat soak** (this decides PLA vs ASA for the production
      rods/pistons): put one rod with its bearing and one piston with its
      bushings in an oven or filament dryer at **60°C for 2 hours**. After it
      cools, check: can the bearing outer ring be turned in the rod by hand? Can
      a bushing be pushed out by hand? Did the piston go oval (it should still
      fit through a 44.5 mm ring gauge or a printed test ring)? Report the
      results.

---

## Round 2: full Phase 1 engine

Print this **after** I have updated `config.py` with your Round 1 results and
you have re-run `python build_all.py` (or pulled the new STLs).

| File | Qty | Material | Layer | Walls | Infill | Orientation | Approx. time | Notes |
|---|---|---|---|---|---|---|---|---|
| `01_crankcase` | 1 | ASA | 0.20 | 4 | 25% gyroid | floor on bed | ~13 h, ~320 g | 5 mm brim, chamber heating on, let it cool in the printer |
| `02_cylinder_bank` | 2 | ASA | 0.20 | 4 | 25% gyroid | deck face on bed (as exported) | ~6.5 h, ~160 g each | window tops bridge 26 mm (fine on H2S/H2C) |
| `03_end_plate` | 2 | ASA | 0.20 | 4 | 25% gyroid | outer face on bed | ~1.8 h each | |
| `04_crank_end_web` | 2 | ASA | 0.16 | 5 | 40% gyroid | as exported | ~40 min each | |
| `05_crank_segment_54` | 2 | ASA | 0.16 | 5 | 40% gyroid | engraved face up | ~1.5 h each | |
| `06_crank_segment_198` | 2 | ASA | 0.16 | 5 | 40% gyroid | engraved face up | ~1.5 h each | |
| `07_conrod` | 10 (+2 spare) | PLA* | 0.15 | 4 | 40% gyroid | flat | ~20 min each | print as one plate |
| `08_piston` | 10 (+2 spare) | PLA* | 0.15 | 4 | 25% gyroid | crown on bed | ~50 min each | one plate; crown finish = bed finish |
| `P1_proto_split_crankpin` | 5 | PETG | 0.12 | 4 | 100% | on end | | **only** if the machined M01 pins are not ready yet |
| `P2_proto_main_shaft` | 2 | PETG | 0.12 | 4 | 100% | flange down | | **only** if M02 is not ready yet |

\* The heat-soak result from Round 1 decides PLA or ASA for the production rods and pistons.

**Why these materials:** see `DESIGN_NOTES.md` §7. In short: anything that
holds a bearing, insert or clamp must survive a hot van or a sunny window
without the fits relaxing, so it is ASA, not PLA. ABS works for hidden parts (crank, end plates) but
yellows in sunlight, so all visible parts are ASA.

**Load-bearing rule applied:** 4+ walls and ≥25% gyroid on every structural
part. Each part is oriented so its loads run along the layers: con-rods lie
flat so the rod force runs within the layers; crank segments stand on end so
the pins seat in round, full-circle holes; cylinder banks have their bores
vertical.

### Purchased and machined parts for ONE prototype (Phase 1 only)

| Part | Spec | Qty | Notes |
|---|---|---|---|
| Main bearing | 608-2Z (shielded), good brand (SKF/NSK/FAG, or ABEC-5 equivalent) | 2 | cheap skateboard bearings are noisy |
| Big-end bearing | 686-2Z (6×13×5) | 10 (+2) | ZZ/2Z shields, **not** 2RS rubber seals (less drag) |
| Bronze bushing | sintered oil-impregnated, ID 3 × OD 5 × L 5 | 30 (+6) | 2 per piston lug + 1 per rod small end |
| Wrist pin | dowel pin Ø3 × 20, stainless, ISO 8734 / DIN 6325 (m6) | 10 (+2) | |
| Guide rail stock | Ø3 h6 ground **stainless** rod | 540 mm | cut to 10 × 54.0 mm, chamfer ends (drawing M03) |
| Split crankpin | machined, drawing **M01**, STEP `stl/M01_split_crankpin.step` | 5 | or print P1 for early tests |
| Main shaft | machined, drawing **M02**, STEP `stl/M02_main_shaft.step` | 2 | or print P2 for early tests |
| M3×8 socket head cap screw | ISO 4762, A2 stainless or black 12.9 | 42 (+10) | 10 crankpins, 6 shaft flanges, 16 banks, 10 end plates |
| M3 heat-set insert | M3 × 5.7 mm, 4.6 mm OD (e.g. CNC-Kitchen / Ruthex type) | 36 (+6) | 16 bank face, 10 end face, 4 base, 6 end webs |
| Magnet | 6×3 mm N52 | 1 | front end web (hall sync, used in Phase 4) |
| Threadlocker | Loctite 243 (medium) | - | crankpin and flange screws |
| Oil | light oil (clock/sewing machine) | - | one drop per bushing |

Send the machine shop `drawings/machined_parts.pdf` plus the STEP files.

---

## Round 2: build sequence (with a checklist at each step)

Tools: 2.5 mm hex key, soldering iron with insert tip, small vise or
clamp, 13 mm and 22 mm sockets (for pressing bearings), 3 mm rod
(alignment mandrel).

**Step 1: inserts.**
- [ ] 01 crankcase: 8 inserts in each bank face, 5 in each end face, 4 underneath.
- [ ] 04 end webs: 3 each, in the flange face.
- [ ] All flush or 0.1 mm below the surface, and square.

**Step 2: bearings and bushings.**
- [ ] 608 pressed into each 03 end plate from the outer face, seated on the lip.
- [ ] 686 into each 07 rod (outer ring only). 1 bushing in each small end.
- [ ] 2 bushings in each 08 piston lug.

**Step 3: pistons onto rods (×10).**
- [ ] Press a wrist pin through piston → rod → piston, centred.
- [ ] Rod swings freely. 0.5 mm float each side.

**Step 4: build the crank.** Front of the engine = the end with cylinder 1.
Work from the front: end web → pin 1 → segment 54 → pin 2 → segment 198 →
pin 3 → segment 198 → pin 4 → segment 54 → pin 5 → end web.

- [ ] Every pin end goes into its D-hole flat-to-flat. One M3×8 per pin end,
      with a drop of Loctite 243, screwed through the channel in the
      opposite face.
- [ ] Before closing each throw, slide on its two rods: the **front journal
      takes the bank A rod** (cyl 1–5), the **rear journal takes the bank B
      rod** (cyl 6–10). Throw 1 = cyl 1 and 6, throw 2 = cyl 2 and 7, and so on.
- [ ] Every piston's **lug faces the middle of the V** (towards the other
      bank). To flip one, turn the rod over before fitting it.
- [ ] Main shafts: the flange fits only one way (uneven bolt pattern). 3 × M3×8
      with Loctite 243. The crankpin screw of each end web is driven through
      the flange notch.
- [ ] Spin the crank in the two end plates on the bench. It must run true: no
      visible wobble at the segments (< 0.3 mm with a feeler against a block).

**Step 5: crank into crankcase.**
- [ ] Slide the crank module into the crankcase from the **rear**, rods
      running along the two slots, pistons riding above the faces.
- [ ] Fit both end plates (spigot into the case, 5 × M3×8 each).
- [ ] Crank spins freely by hand.

**Step 6: cylinder banks.**
- [ ] Turn the crank so bank A pistons are near mid-stroke. Lower bank A
      straight down its bore axis over the pistons (lugs into their pockets).
      The two pegs only fit one way round.
- [ ] 8 × M3×8 through the deck holes (long 2.5 mm hex key).
- [ ] Repeat for bank B.

**Step 7: rails.**
- [ ] One drop of oil on each rail. Push it through the deck hole, through the
      lug bushings (wiggle the piston to line up), into the crankcase until
      flush with the deck.
- [ ] Until the heads arrive in Phase 3, put a strip of tape over the rail
      holes.

---

## Round 2: test checklist (report these)

| # | Check | Pass |
|---|---|---|
| 1 | Turn the front shaft slowly through 10 full turns each way | Smooth, even resistance, **no tight spot, no click, no scrape** |
| 2 | Breakaway torque: tape a 100 mm lever (a ruler) to the front shaft and hang a small cup at the end; add weight until it turns | **≤ 30 g target**, ≤ 60 g acceptable (0.03–0.06 N·m). Tell me the number: it sets the motor current in Phase 4 |
| 3 | Look into each bore at TDC and BDC | Even gap all round; a 0.5 mm feeler or folded paper slides all round without pinching |
| 4 | Each rod small end | Visible gap to both piston bosses |
| 5 | Each crank throw | Rods do not touch the webs or the flying web (0.75 mm gap) |
| 6 | Shake the engine gently | No rattles |
| 7 | Rails | Don't rotate or creep out while turning |
| 8 | Firing order check | With the crank at the reference position (end-web magnet pointing straight down), cyl 1 is at TDC. Turning clockwise seen from the front, TDCs come in the order 1-6-5-10-2-7-3-8-4-9, one every 72° |
| 9 | Photos | One from each side plus the front, for the record |

If anything fails, **describe it and don't file or sand anything**. Every fit
is a number in `config.py`, and I'll adjust it.
