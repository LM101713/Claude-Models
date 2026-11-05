# DRYDOCK P001: mechanical design review, and the V1.1 corrections

Scope: a focused review of Prototype 001 before physical testing. It covers six items: the
bayonet and its clearances, bead containment, the window, the adapters vs. the Bambu spool,
cap and lock weak points, and the fit-test plate.

**Prototype 001 is unchanged** (`../drydock.py`, `../models/`). Every correction below is in
[`drydock_v11.py`](drydock_v11.py) on branch `claude/drydock-v1.1`, with outputs in
[`models/`](models/). Each correction is a parameter change or a small local feature, not a
redesign.

**How each finding was checked.** Every finding comes from one of these:

- **B-rep boolean fit checks** in the CAD
- **3D finite-element analysis:** [`analysis/plug_fea.py`](analysis/plug_fea.py)
- **Monte Carlo tolerance stack:** [`analysis/tolerance_stack.py`](analysis/tolerance_stack.py)
- **Voxel bead-escape test:** [`analysis/containment.py`](analysis/containment.py)

Nothing has been printed. The FDM deviation model used in the tolerance stack is an
assumption, stated where it is used. The fit-test plate exists to replace it with
measurements.

## Summary

| # | Finding in P001 | Severity | Correction in V1.1 | Verified by |
|---|---|---|---|---|
| B1 | **The detent cannot work as drawn.** The plug, anchored to the neck, is 11× stiffer than the free-ring model P001 used. The detent would need ≈ 8 N·m to turn (6.7–10). In practice the cap jams at the click, or the bump shaves off | **Critical** | R2: the detent bump moves onto a spring tongue cut in the body collar. ≈ 0.26 N·m (0.22–0.31) | FEA, tolerance stack, CAD sweep |
| B2 | Load-bearing axial play of 0.20 mm is eaten by 45° flanks plus layer steps plus droop. It goes negative in ~50 % of top sockets, so the lug catches on the slot edge or the cap sits proud | High | R1: play 0.40. R3: a lead-in ramp on each lug's leading flank | Tolerance stack, CAD |
| B3 | Radial fit 0.20 mm leaves ~0.10 mm after printing, so a Z-seam blob makes contact | Medium | R1: 0.30 | Tolerance stack |
| B4 | Lug tip clearance 0.25 mm leaves ~0.15 mm | Medium | R1: 0.35 (lug made 1.3 tall so it still overlaps the lip by 1.0 mm) | Tolerance stack, CAD |
| W1 | The window is held inward only by crush-rib friction. Pressing the cap face to push the cartridge into a spool can push the window into the beads, leaving a Ø14 hole | High | R6: twist-lock window, mechanically held both ways | CAD install / turn / push checks |
| W2 | The crush-rib interference (0.15 mm) varies 0.05–0.35 mm with print tolerance: from no grip to a cracked window | Medium | Removed (R6) | — |
| A1 | **The adapter bump lead-in (0.45 mm) is shorter than the spring travel (0.55–1.0 mm).** The bump's square shoulder meets the spool bore mouth | High | R7: lead-in 1.15 mm deep at 35° | CAD |
| C1 | The head wall under the index flutes is only 1.3 mm | Medium | R5: 1.8 mm | CAD |
| C2 | The lock marks are notched into the lip exactly where the locked lug bears | Low | R4: marks moved 15° onto the stop webs (full 3.5 mm collar) | CAD |
| C3 | Sharp corner at the plug root; 0.5 mm mouth chamfer | Low | R5: 0.4 mm root chamfer, 0.8 mm mouth chamfer | CAD (0.5 mm clearance between them) |
| F1 | The fit-test plate tests only one socket orientation, and the **untested** orientation is the riskier one (B2). It has one detent setting, no window, no adapter and no bead test | High | R8: double-ended gauge, two detent tuning rings, cap + window + adapter | — |
| V1 | Vents: no problem found. 1.2 mm slots are the only path larger than 0.2 mm | — | none | Voxel test |

V1.1 passes all 21 automated checks: [`models/DD011_validation_report.md`](models/DD011_validation_report.md).

---

## 1. Bayonet locking geometry and FDM clearances

### Geometry: correct as drawn

The P001 CAD sweep confirms the motion:

- free entry
- free 0–65° turn
- detent 70–85°
- clear locked pocket
- hard stop past 90.8°
- the lug bears on the lip when pulled
- the same cap locks on both ends

The handedness is right: clockwise to lock on both ends, because the second socket is a
rotation, not a mirror. Lug engagement over the lip is 1.0 mm radially. The stop webs are
14.3° (5.2 mm) wide.

**Stop strength.** A 3 N·m over-twist puts about 50 N on each lug's side face (≈ 3.6 mm²),
about 14 MPa. That is acceptable for PETG.

### B1: the detent spring is the plug, and it is far too stiff (critical)

P001 estimated the detent force with a free thin-ring formula: 0.020 mm/N per lug, about
12 N, about 0.5 N·m. It called that a lower bound. The question was how far below reality
that bound sits.

**Method.** I ran a 3D FEA of the plug and neck: quadratic hexahedra, PETG E = 2000 MPa,
ν = 0.38, neck clamped where it meets the head, radial load on the three lug tips.

- **Check case.** The same code on a free ring gives 0.0190 mm/N against the formula's
  0.0203 mm/N, 6 % apart. The method is sound.
- **Anchored plug: 570 N/mm per lug, 10.8× stiffer than the free ring.** The lugs sit only
  4.4 mm from the neck. That is less than the shell's bending decay length (about
  √(R·t) ≈ 5.4 mm), so the neck holds the plug almost rigid.
- The clamped head makes this an upper bound. A flexible head would reduce it by tens of
  percent, not by a factor of 10.

**Tolerance effect.** The printed interference also comes out *larger* than drawn. The lug
tip is an outside surface, which prints oversize. The bump crest is part of a cavity
boundary, which prints undersize, so the material encroaches into the gap. Monte Carlo
result for the 0.25 mm nominal: **0.28–0.42 mm (p5–p95)**.

| P001 detent | p5 | p50 | p95 |
|---|---|---|---|
| Force per lug | 161 N | 199 N | 238 N |
| Torque to pass the bump | 6.7 N·m | 8.3 N·m | 10.0 N·m |

A hand on a 46 mm cap manages about 1.5–2.5 N·m. **The P001 cap would not turn past the
detent, or it would plough the bump off.** Lowering the interference cannot fix this:
±0.07 mm of printing variation against a 570 N/mm spring swings the force from zero to over
100 N.

**R2 (V1.1).** The bump now sits on a **spring tongue** cut in the collar skin behind the
groove floor. The tongue is 2.15 mm thick and 2.2 mm tall. Its root is at 52°, its free end
at 88°, and the load arm to the bump is 9.5 mm. It is cut free by 0.8 mm slits above, below
and at the free end.

- Tongue stiffness is 13 N/mm, so the plug (570 N/mm) acts as rigid in series.
- At the printed interference (nominal raised to 0.30 mm): **4.3–6.1 N per lug,
  0.22–0.31 N·m (p5–p95)**. That is a distinct click that handling and spool rotation
  won't undo.
- The sensitivity to print variation drops by 45×.
- Bending strain at the high end is about 1.4 %. That is transient (only while passing the
  bump) and under PETG yield (about 2.5 %). Fatigue still needs testing (T2: 200 cycles).
- The lugs are untouched, so pull-off is still governed by the 570 N/mm plug. It is
  material-limited, far above any handling load.
- Side effects:
  - The slit ceilings are 14.6 mm bridges, supported at both ends. The check now classifies
    these as bridges, not overhangs.
  - With all vents closed, the largest sphere that escapes is now 0.47 mm (through slit →
    groove → 0.3 mm plug gap), up from under 0.2 mm in P001. That is still four times
    smaller than any usable bead.

### B2–B4: clearances re-sized against a tolerance stack

**Deviation model** (assumed; to be replaced by fit-test results). These are radial
deviations for a tuned Bambu H2C, PETG, 0.4 mm nozzle, 0.20 mm layers:

| Feature | Deviation |
|---|---|
| Outside (convex) XY surfaces | 0 to +0.10 mm |
| Inside (concave) XY surfaces | 0 to −0.10 mm (material encroaches) |
| 45° flank position | ±0.10 mm (layer steps) |
| Down-facing 45° flank | 0 to 0.10 mm droop |
| Z-seam blob | +0.10 mm (worst case) |

A 45° flank turns a radial error into an equal axial error. The load-bearing flank faces
**down** on every cap lug and on the **top** socket's lip (printed as an overhang). On the
bottom socket's lip it faces up.

| Clearance | P001 nominal → p5 / p50 / % negative | V1.1 nominal → p5 / p50 / % negative |
|---|---|---|
| Plug to bore (radial) | 0.20 → 0.03 / 0.10 / 0 % (a seam blob closes it) | **0.30** → 0.13 / 0.20 / 0 % |
| Lug tip to groove floor | 0.25 → 0.08 / 0.15 / 0 % | **0.35** → 0.18 / 0.25 / 0 % |
| Bearing-flank play, bottom socket | 0.20 → −0.11 / 0.05 / **31 %** | **0.40** → 0.09 / 0.25 / 0.2 % |
| Bearing-flank play, top socket | 0.20 → −0.17 / 0.00 / **50 %** | **0.40** → 0.04 / 0.20 / 2.1 % |

**Why negative play matters.** The cap is seated axially by its neck on the rim, not by the
lugs. If the lug's bearing flank overlaps the lip axially, the lug's leading face meets the
lip edge head-on at the slot as the cap turns. It catches, and the user has to pull while
twisting.

**R3** adds a 0.4 mm staircase lead-in, over 4°, to the leading bearing flank of each lug.
In the 2 % of cases where play still goes negative, the lug rides under the lip instead of
catching.

**Cost of the larger play.** A locked V1.1 cap can lift 0.40 mm. That is fine for
containment (beads are ≥ 2 mm) but is felt as slight end float. If the fit test shows the
real play runs large, `bearing_play` comes down in 0.05 mm steps.

**Recommended starting clearances for PETG on an H2C** (now the V1.1 defaults):

| Clearance | Value |
|---|---|
| Radial plug fit | 0.30 |
| Lug tip | 0.35 |
| Bearing-flank play | 0.40 |
| Inner-flank play | 0.50 |
| Entry-slot sides | 0.40 |
| Stop | 0.30 |
| Detent | 0.30 on a spring tongue |

For ASA, which shrinks more: add 0.05 to the radial fit and 0.05 to the bearing play.

---

## 2. Ventilation slots vs. silica gel beads

**Method.** The voxel bead-escape test rasterises the assembled cartridge at 0.1 mm, with
both caps lifted outward by their full play. It then finds the largest sphere that can
travel from the chamber to the outside. It checks every joint, not just the slots.

| Geometry | Largest escaping sphere | Path |
|---|---|---|
| P001, vents open | 1.32 mm | the 1.2 mm slots (the voxel method reads about +0.1 mm high) |
| P001, vents closed | < 0.2 mm | joints: plug gap, cap lift, window seat |
| V1.1, vents open | 1.33 mm | the slots |
| V1.1, vents closed | 0.47 mm | tongue slit → groove → 0.3 mm plug gap |

**After printing.** Narrow gaps print *narrower*, so 1.2 mm slots come out 1.0–1.2 mm. An
under-extruded worst case is about 1.3 mm. 2–5 mm beads therefore have at least 0.7 mm of
margin. **No change needed.**

Recommendations:

- Specify "2–5 mm" or "3–5 mm" beads.
- Sieve new beads over a 2 mm mesh to remove broken fragments, which do pass the slots.
- If a supplier only offers 1–3 mm beads, set `vent_width=0.9`. That still prints cleanly
  with a 0.4 mm nozzle.

---

## 3. Indicator window: installation and replacement

**P001 installation works geometrically.** The window drops in from inside and the lip
stops it outward. But:

- **W1:** inward, nothing but crush-rib friction holds it.
  - Pushing the cartridge into a spool takes about 6 N nominal, up to 11 N (V1.1 adapters).
    With the P001 adapters (A1) the bump shoulders catch at the bore mouth, so a user pushes
    harder still.
  - The natural place to push is the cap face. A thumb bridges the Ø14 recess and touches
    the window, which is only 1.0 mm below the face.
  - If the window goes in, the cartridge empties through a 14 mm hole.
- **W2:** the rib interference (0.15 nominal) prints anywhere from 0.05 to 0.35 mm. That
  ranges from falling out to cracking the disc.

**R6 (V1.1): twist-lock window.** The disc has three ears and a grip bar on its inner face.
The ears enter three notches in a small boss on the inside of the face plate, seat on the
lip, and turn 60° clockwise under a 45° ledge. The ledge prints without support.

CAD checks:

- drops in from inside with 0 overlap at every step
- turns 0–60° with 0 overlap
- locked and pushed 0.5 mm inward: blocked (the ears hit the ledge after 0.2 mm)
- pushed 0.2 mm outward: blocked by the lip
- unlocked: lifts straight out

To replace a window, take the cap off, turn the window back with a fingertip on the grip
bar, and lift it out. It cannot be removed, or pushed in, from outside.

The no-clear-filament option is now a twist-lock **film carrier**: a Ø16.6 disc cut from
clear sheet, under a printed ring with ears.

Residual risks:

- The window is kept from turning back only by friction. No torque acts on it in service,
  but this should be confirmed in T7.
- The grip bar is in the line of sight. It is 1.2 mm wide, across a Ø14 view.

---

## 4. Do the orange adapters fit the Bambu reusable spool?

**What could be confirmed.** Retailer listings and a Bambu forum summary give the reusable
spool as about **200 mm OD × 67 mm wide with a 55 mm bore**. The same source says the AMS
lite's holders fit spools with 53–58 mm bores, which confirms that those holders *enter* the
bore.

Sources:

- [Bambu forum: spool dimensions](https://forum.bambulab.com/t/bambu-spool-dimensions/123480)
- [3DJake listing](https://www.3djake.com/bambu-lab/bambu-reusable-spool-high-temperature-resistance)

**What could not be confirmed.** The forum and MakerWorld pages were unreachable from this
environment, so nothing is confirmed about:

- internal ribs, clips or the joint between the two halves in the bore
- a stepped or chamfered mouth
- the bore's tolerance

**Measure a real spool before anything else** (T1).

| Check | Result |
|---|---|
| 55 mm adapter range | 54.1–55.8 mm bore, preload 0.55 mm at exactly 55.0. If the real bore is ≥ 55.6 mm, use the 56.5 adapter (55.6–57.3); the ranges overlap |
| Radial room | The 46 mm body leaves 4.5 mm per side. The arm needs 1.5 mm plus its gap; the base ring hides inside the body diameter |
| **A1: insertion lead-in (P001)** | **Fails.** The 0.45 mm × 45° chamfer is smaller than the spring travel (0.55 nominal, 1.0 at the overload stop). The last 0.1–0.55 mm of the bump is a square shoulder that meets the bore mouth |
| A1 corrected (R7) | 1.15 mm deep at 35° from the axis on both faces, more than the full travel. Insertion force ≈ 3 arms × 1.8 N × tan(35° + 14°) ≈ 6 N nominal, ≤ 11 N at the stop |
| Where the arms touch | 3.6 mm bands, 5.5–9.4 mm in from each cartridge end, so about 7–11 mm inside each spool face when centred. Clear of a mid-width joint between the spool halves and of mouth chamfers under 5 mm (unverified) |
| Axial hold | ≈ 2.7 N (6 arms × 1.8 N × μ 0.25) against 0.85 N of weight, a 3.2× margin. Enough on rollers; marginal if a spool is shaken by hand; creep will lower it (T5). If too low, use the next size *down* for more preload |
| Holders that enter the bore | **Incompatible:** AMS lite, and spindle-type external holders. Works where the spool rides on rollers (AMS / AMS 2 Pro / AMS HT), in dry boxes and in bags |
| No axial stop | 64 mm in a 67 mm hub: the cartridge can sit up to 1.5 mm off-centre before it protrudes. Instruction: push in until flush with the flange recess. No geometry change made |

---

## 5. Weak points in the end caps and locking features

| | Finding | P001 | V1.1 |
|---|---|---|---|
| C0 | Detent (B1) | jams | spring tongue |
| C1 | Head wall under the deep index flutes | 23 − 0.9 − 20.8 = **1.3 mm** at the face-plate junction | head wall 2.4, deep flutes 0.6: **1.8 mm** |
| C2 | Lock-mark notch | 0.6 mm deep, at the locked lug's lip | on the stop web (full collar); index flutes 15° past the lugs |
| C3 | Plug root | sharp internal corner at the neck face | 0.4 mm chamfer; body mouth chamfer 0.8 mm (0.5 mm normal clearance between them) |
| C4 | Lug catches at the slot edge (B2) | likely on top sockets | play 0.40 + lead-in ramp |
| C5 | Window pushed in (W1) | possible | twist-lock |
| C6 | Z-seam on the plug OD and bore | 0.20 radial fit | 0.30, plus a slicer setting: seam "aligned" puts the bore seam in the slot corners |
| C7 | First-layer squish | bottom socket mouth and cap face slots | 0.15 mm elephant-foot compensation (README) + 0.8 mm mouth chamfer |

**Confirmed adequate:**

- **Pull-off.** Material-limited: plug 570 N/mm per lug, 1.0 mm engagement.
- **Lug and plug load paths.** In-layer; the axial load crosses about 185 mm² of plug wall.
- **Lip.** 2.0 mm thick at the bore.
- **Groove skin.** 2.15 mm (V1.1).
- **Face plate.** 2.4 mm, with slot ribs ≥ 2.2 mm.
- **Stop web.** 14.0°, 5.1 mm (V1.1).

---

## 6. Does the fit-test plate test the important tolerances?

**P001 plate** (one socket ring + one cap):

| Tolerance | Covered? |
|---|---|
| Plug-to-bore fit, bottom-socket orientation | ✓ |
| Detent feel | ✓, but one setting, and that setting jams (B1) |
| Hard stop | ✓ |
| Pull-out | ✓ |
| **Top-socket orientation** (lip printed as an overhang, the riskiest play, B2) | **✗** |
| Window | ✗ |
| Adapter vs. a real spool | ✗ |
| Bead containment | ✗ |

**R8: V1.1 fit-test plate** (`models/3mf/DD011_plate4_fit_test.3mf`, ≈ 32 g, about 1.5–1.7 h, estimated):

| Part | Tests |
|---|---|
| **Double gauge** (2 dots): both sockets, printed exactly as on the body (one mouth-down, one mouth-up), plus a row of real 1.2 mm vents | radial fit, tip clearance, bearing play in both orientations, nominal detent, stop, pull-out; fill it with beads, cap both ends, shake: containment |
| **Detent tuning rings**: 0.20 mm (1 dot) and 0.40 mm (3 dots) | brackets the nominal 0.30 |
| **Cap** with the window and a 55 mm adapter fitted | window install, turn, retention, removal; adapter feel in the real spool bore (push the cap and adapter into the spool) |

Decision table after the test (change one value at a time and log it):

| Observation | Change |
|---|---|
| Plug enters stiffly or scrapes | `fit_radial` +0.05 |
| Turning catches at the start of the quarter turn, on either end | `bearing_play` +0.05 |
| Cap rattles noticeably when locked | `bearing_play` −0.05 |
| Click too light / too firm | pick the tuning ring that feels right; set `detent_interference` to its value |
| Window ears tight / window loose | `window_fit` ±0.05 |
| Adapter loose in the spool / hard to insert | next adapter size down / up |

---

## Remaining tests (adds to the P001 plan)

| # | Test | Pass |
|---|---|---|
| T1 | Measure 3 Bambu reusable spools: bore at both mouths and mid-depth, internal features, mouth chamfer, depth | data recorded; adapter sizes confirmed |
| T2 | V1.1 fit plate as above, plus **200 lock/unlock cycles** on the chosen tuning ring | click still distinct; no whitening or cracking at the tongue root; play unchanged |
| T7 | Window: 20 install/turn cycles; press the cap face with a thumb at 20 N | no push-in; ears intact |
| T10 | Insertion force into the spool with a luggage scale | ≤ 12 N; no snag at the mouth |
| — | Then the rest of the P001 plan (T3–T9) on a full V1.1 print | — |

## Files

- `drydock_v11.py`: the V1.1 generator. Corrections are tagged R1–R8 in the code.
- `models/`: STL, STEP and 3MF for every part, plus the validation report (21/21 pass).
- `analysis/`: FEA, tolerance stack, containment scripts and their JSON results.
- `renders/`: views of the changes (window, tongues, fit plate).
