# DFM Phase 0: inspection, risks, plan (nothing changed yet)

**Rollback point:** commit `bad6b2f`, tag `dfm-baseline` on branch
`claude/v10-engine-display-model-4r6gjr`. `git checkout dfm-baseline` restores
everything exactly as it was before the design-for-manufacturing pass.

**Status in one line:** the engine exists only in CAD. Not one part has been
printed. Every fit below is a calculated guess that a real printer has not yet
confirmed. The code checks (collisions, assembly paths, slicing) remove design
mistakes; they do not replace a print. This design is **not** production-ready
and will not be called that until a physical engine has been built and run.

---

## 0. Printer and material facts that change the plan

| Item | What the design assumed | Reality to design for |
|---|---|---|
| Printer | "H2D/H2S class", bed 340 x 320 (production plan), 320 x 320 (slicer profile) | **H2C: about 325 x 320 x 325 mm single-nozzle, about 300 x 320 x 325 mm in dual-nozzle mode** (check bambulab.com/en/h2c/specs). The plate plan must be redone for 325 x 320. |
| Longest parts | exhausts 293.5, crankcase + valley beam 268, banks + heads 260, base halves 204 x 280 | All fit the H2C in single-nozzle mode. The exhausts (293.5) are too long for dual-nozzle mode with a brim. The A1 Mini (180 mm) can print coupons, pistons, rods, crank segments, end webs, end plates, coil packs, trumpets - not the long parts. |
| Material | **ASA throughout** (chosen for heat, creep and finish) | You plan **PLA, 0.15 mm**. PLA is right for coupons and the motion test (fast, cheap, no warping). For the 50 production units PLA is a risk: it softens at 55-60 C (a van in summer, a sunny window, hot display lighting), and it creeps under the 46 magnet fits, 12 bearing fits and 92 clamped screws over years. Recommendation: **test in PLA, produce in ASA** on the enclosed H2C; PETG is the fallback if ASA warps on the 260-294 mm parts (that is a real ASA risk and is on the test list). |
| Layer heights | 0.12 rods/trumpets, 0.16 crank/pistons/exhausts/coils, 0.20 case/banks/heads/covers/base, 0.28 hidden parts | Keep as a starting point; 0.15 for precision parts is fine. Note the fits do not depend on layer height - they depend on the crush ribs resolving (section 2). |

---

## 1. Goal: super easy to assemble - problems and risks

**Already in place (keep):** one screw size (M3 x 8, 92 per engine) into 78 brass
heat-set inserts; no screws into bare plastic; crank segments keyed by D-flats
and engraved with their type; heads key to the banks by the off-centre guide
rails; banks key by an asymmetric locator and screw pattern; base halves on two
pegs; end plates identical and interchangeable; assembly order verified in CAD
with nothing taken apart again; no glue on any moving part.

| # | Problem / risk | Severity | Phase 1 action |
|---|---|---|---|
| A1 | **Every press fit relies on crush ribs (about 0.3 mm half-round ribs in a 0.3 mm oversize bore).** Unproven. A 0.4 mm nozzle may not resolve the ribs; in PLA they may crack instead of flattening. 12 bearings, 30 bushings, 46 magnets, 10 trumpets, 10 coil packs, 10 rail pockets depend on this. | **High** | Crush-rib coupon ladder (rib height 0.2 / 0.3 / 0.4 / 0.5 mm, plain-bore ladder alongside) for 608, 686, 3x5 bushing, 6x3 magnet, 3 mm rail, 10 mm coil shaft. One number per fit in the parameters file. |
| A2 | **686 bearing in the con-rod big end: 2.5 mm plastic wall** around a pressed steel bearing (rod is 18 wide, bearing 13). Risk of the eye splitting, especially in PLA. | High | Coupon; if it splits, widen the rod eye to 20 mm (invisible inside the crankcase) or switch to a slip fit + retaining lip. |
| A3 | **Built-up crank: 4 segments + 2 webs on 5 split pins + 2 shafts, 16 screws.** Print tolerance stacks along the axis (designed out with 1.0 mm rod float and a floating rear bearing) but **runout** from 6 D-flat joints is not designed out. A wobbling crank is the one failure that makes the whole piece look cheap. | High | Motion-test build first; printed V-block alignment jig for the crank build; measure runout at both shafts (target < 0.2 mm). Fallback: 100 % infill segments, or a longer D-flat engagement. |
| A4 | Clearances are **not all in one place.** `config.py` holds the fit tables (`CRUSH`, `hole()`, `HOLE_COMP`, insert size, piston gaps, pin clearances), but about **50 numeric offsets are still written inside the part code** (magnet depth +0.3, panel clearance 0.4, motor boss +0.5, lead-in cones, coil shaft -0.5, etc.). | Medium | Move every one into a `FITS` section of `config.py`; a script asserts no bare clearance literals remain in `cad/`. |
| A5 | **Part numbers are embossed only on the crank segments.** No other part carries its number. | Medium | Emboss "01".."21" (and A/B where relevant) 0.5 mm deep on a hidden face of every part. |
| A6 | Cam covers and side panels are symmetric, so they fit either way round (harmless, cosmetic). Exhaust headers A and B are mirror images shipped as two files. | Low | Keep; ship one exhaust STL and mirror in the slicer, or keep both files - your call. |
| A7 | **Soldering exists, but in the harness pre-build, not in final assembly:** LED strip leads (2), hall sensor (1), panel jack/button/pot (3). Final assembly is plug-in JST only. | Low-Med | Option: buy pre-wired panel parts and pre-wired hall sensor (fewer joints); or keep harness building as a batch job. |
| A8 | **Adhesives used (none are glue on moving parts):** LED strip's own tape, edition plate transfer tape, rubber feet, threadlocker on screws. | Low | Keep; listed so nothing is hidden. |
| A9 | Belt tensioning (push the 60T pulley on while pulling the crank forward, then slide the motor) is the one fiddly step. | Low | Printed tension gauge / spacer block in Phase 1. |

---

## 2. Goal: super easy to print - problems and risks

**Already in place:** every part was sliced with the production settings; no
part needs supports; no overhang over 45 deg; no bridge over 25 mm; heads and
banks print deck-down; bridged counterbores instead of floating ceilings;
V-bottom windows; every part under 300 mm.

| # | Problem / risk | Severity | Phase 1 action |
|---|---|---|---|
| P1 | **Plate plan is for the wrong bed** (340 x 320). | High (easy) | Redo as a fixed, named plate set for the H2C 325 x 320 bed (single-nozzle mode for the long parts). |
| P2 | **Slicer warnings on real parts:** "floating bridge anchors / long bridging" on the cylinder head, pistons, base halves, cam cover, end cover. These are the bridged counterbores (2-layer slot then square) and 20-25 mm bridges - a trick that works on paper and is untested here. | Med | Print one head and one base half early; if a bridge sags, add a sacrificial 0.2 mm layer (knock-out) or split the counterbore. |
| P3 | **Thin features likely to fail or vanish:** crush ribs (0.3 mm); 1.6 mm wall closing the LED groove at the head ends; 1.0 mm land between the LED groove and the valve recesses; 2.5 mm rod big-end wall; trumpet bell lip at 0.12 mm layers; 0.8 mm engraved text on the rear panel; coil pack (33 mm tall on a 15 x 11 footprint, brim specified). | Med | Coupons cover the ribs; the head and trumpet are in the motion-test print; thicken anything that fails (all internal, no exterior change). |
| P4 | **Strength orientation:** rods print flat (load in-layer: strong - correct). Crank segments print with the crank axis **vertical**, so bending across the crank goes **across layers**: the weakest direction, chosen because the D-flat sockets and pin sockets must print round. Pistons print crown-up. Banks/heads deck-down. Loads are small (display engine) but the crank sees cyclic load 24/7 for years. | Med | Keep orientation (accuracy wins for the crank); compensate with 40 % gyroid + 5 walls (already set) and the motion test; consider 100 % infill segments (+15 min each). |
| P5 | **ASA warping** on the 260-294 mm parts (crankcase, banks, heads, exhausts, base). | Med | First long-part print in ASA with brim + enclosure; PETG fallback for those parts only if needed. |
| P6 | Multi-colour: not used inside any part. Colour comes from printing each part family in its own filament (block grey, heads/covers black, coils red, exhausts gold-ish). AMS multi-colour would add value only for embossed lettering/plaque text. | Low | Your decision (question 4). |
| P7 | The A1 Mini cannot print 11 of the 21 parts (too long). | Low | Use it for coupons and small parts only. |

---

## 3. Goal: super easy to put the electronics in - problems and risks

**Already in place:** electronics bay in the rear base half; board on 4 insert
standoffs; removable bottom panel (4 screws, no glue); rear control panel (12 V
jack, rocker switch, speed knob, START button); 7 plug-in JST XH connectors;
cable-tie anchors under the skin; LED leads hidden behind the rear end cover;
motor behind a bulkhead with teardrop cable passages; full ESP32 firmware with
homing, soft start, speed knob, firing-order LEDs, idle, 15 min sleep, stall
fault, burn-in mode.

| # | Problem / risk | Severity | Phase 1 action / question |
|---|---|---|---|
| E1 | **Service access is from underneath:** the whole engine (about 2 kg) must be turned over to reach the board. Works, not elegant. | Med | Keep, or add a rear/side access door - that changes the exterior, so it needs your OK (question 6). |
| E2 | **Hand-built perfboard controller**, about 1 h labour each, 50 times; wiring errors possible. | Med | A small custom PCB (JLCPCB/PCBWay, about $2-5 each at 50) with the same 7 connectors. Recommended. |
| E3 | **Drive is a 3:1 GT2 belt, not a shaft coupling.** Chosen for silence and vibration isolation. Forgiveness: motor slots give +/-5.5 mm centre-distance adjustment; a GT2 belt tolerates about 1 mm parallel misalignment and about 1 deg angular error without noise. A direct flexible coupling (e.g. 5 to 8 mm helical) forgives about 0.2 mm parallel / 1.5 deg angular, transmits stepper hum into the crank, and puts the motor on the crank axis behind the engine - a visible change. | Decision | Question 2. |
| E4 | **Controls:** you asked for one power input and one switch; the design has 4 (jack, rocker, speed knob, START). | Decision | Question 1. |
| E5 | **No sound** in the design. Adding sound means a speaker + audio module + more base volume. | Decision | Question 1. |
| E6 | Wire routing space is checked only as CAD envelopes (connectors, board stack, panel parts). Real harness bulk is unproven. | Low-Med | Checked on unit #1; channels are generous (teardrops 14 mm, harness hole). |

---

## 4. Goal: super simple parts ordering - problems and risks

**Already in place:** `docs/BOM.md` / `BOM.csv` with quantities, x1 and x50
prices, purchased/machined/printed split, filament grams per part, print hours;
`SHOPPING_LIST.txt` with Amazon search terms.

| # | Problem / risk | Action |
|---|---|---|
| B1 | No supplier / link / line-total columns; spares vary by line instead of a flat 10 %. | Rebuild as a spreadsheet (XLSX) with the exact columns you listed. |
| B2 | No **prototype order** separate from the 50-unit order. | Two sheets: PROTO (1-2 engines + extra inserts, bearings, magnets, screws in a few sizes for fit testing) and FULL (50 + 10 %). You buy PROTO only. |
| B3 | Filament not broken down by colour. | Grams per colour per engine and x50, derived from the part-family colours you choose. |
| B4 | Suppliers today: CNC shop (M01-M06), bearings/bushings, fasteners/inserts/magnets, electronics (Digi-Key/Mouser or Amazon), filament, engraver (plate). Six. | Consolidate to Amazon + one electronics distributor + one CNC shop + filament, if you accept Amazon-grade bearings/inserts. |
| B5 | No one-page kit checklist. | Generate per engine from the BOM. |
| B6 | Machined parts: 28 steel pieces per engine ($341 as singles, $72 each at 50). The motion test needs 5 pins + 2 shafts. | Printed PETG stand-ins (P1/P2) exist for a first motion test; order quick-turn steel for unit #1. |

---

## 5. Phase 1 plan (after your OK)

1. **Parameters file.** Gather every clearance into a `FITS` block in
   `config.py` (shaft slip, press-fit rib height per diameter, bearing seat,
   insert pilot, magnet pocket, hole undersize, pin socket, lug pocket, D-flat,
   peg/spigot, panel). A check script fails the build if a bare clearance
   literal remains in `cad/`.
2. **Coupons, each under 30 min, value embossed on every step:**
   (a) hole ladder for 3 mm pins / 8 mm shafts / M3 clearance / base pegs;
   (b) insert pilot ladder 3.8-4.2 mm; (c) *there are no gears in this design*
   (belt drive) - replaced by a **crush-rib bearing-seat ladder** for 608 and
   686; (d) piston lug / bushing / rail ladder (the piston never touches the
   bore - the guided pair is bushing-on-rail); (e) D-flat crank joint ladder
   (the key fit) + magnet pocket ladder; (f) 608 end-plate seat with the real
   lip. Printed in PLA on the A1 Mini or H2C.
3. **Test checklist**: per coupon, what to measure or feel, pass criterion, and
   the exact parameter name to change by how much.
4. **Fixed named plates** for the H2C (325 x 320), 3MF per plate + STL per
   part; motion-test plates first (crank, rods, pistons, one bank, one head, 5
   rails), then the rest.
5. **Part numbers** embossed on hidden faces; crank alignment jig; belt tension
   block.
6. **Electronics** per your answers (bay, PCB, controls, sound), then the
   electronics bay drawing and harness sheet.
7. **BOM spreadsheet** (PROTO + FULL + kit checklist) and filament by colour.
8. Re-run every code check; export; commit. Then **you print the coupons.**

Nothing on the outside of the engine changes in Phase 1 unless you approve a
specific item.

---

## 6. Questions I need answered before Phase 1

1. **Electronics:** keep the 30 firing LEDs (3 per cylinder, timed to TDC)?
   Do you want **sound**? Speed control as a **knob**, a button that steps
   through speeds, or fixed? Is the current 4-item rear panel (12 V jack,
   power rocker, speed knob, START) OK, or strictly one input + one switch?
2. **Drive:** keep the silent 3:1 belt (recommended), or a direct shaft
   coupling (motor visible behind the engine, more noise, less tolerance)?
3. **Material:** PLA for coupons and the motion test, **ASA for production**
   on the H2C - agreed? Or PETG? Which colours per part family (block, heads
   and covers, coils, exhausts, base)?
4. **Multi-colour via AMS** for embossed lettering / plaque text, or single
   colour per part?
5. **Motion test:** printed PETG crankpins and shafts first (free, weaker), or
   order quick-turn steel M01/M02 now (about $200, 1-2 weeks)?
6. **Electronics access** from underneath (as designed) or a rear/side door
   (changes the exterior)?
7. **Controller:** custom PCB (recommended for 50) or hand-built perfboard?
8. **Numbered edition plate** on the base front: keep?
