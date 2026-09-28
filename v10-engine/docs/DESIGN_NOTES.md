# Design notes: why the engine is built the way it is

This file records the engineering decisions behind the design, with the
reasoning, so they can be revisited deliberately rather than by accident.
Where quality and convenience pulled in different directions, quality won,
and the reason is written down here.

---

## 1. Even firing on a 90° V needs split crankpins (decision: split pins)

The brief asks for a **90° V10** that fires **evenly every 72°** in the order
1-6-5-10-2-7-3-8-4-9. Those two requirements conflict with a conventional crank.

* With one crankpin per throw shared by both banks, the second cylinder on each
  throw reaches TDC one *bank angle* (90°) after the first. The firing gaps
  would then alternate 90° / 54°. That is uneven, and the lights would visibly
  "lope".
* To get a true 72° gap on a 90° V, the two journals on each throw must be
  offset by 90° − 72° = **18°**. This is a "split-pin" crank, the same solution
  real even-fire 90° V6 and V10 engines use.

`config.py` works this out from `BANK_ANGLE` and `FIRING_ORDER`:

| throw | journal A (bank A) | journal B (bank B) |
|------:|-------------------:|-------------------:|
| 1 | −45° | −27° |
| 2 | +27° | +45° |
| 3 | −117° | −99° |
| 4 | +99° | +117° |
| 5 | +171° | −171° |

`python config.py` checks the result: consecutive TDCs in the firing order are
exactly 72° apart. If you ever change the bank angle or firing order, the pin
angles, the crank segments and the LED timing table all follow automatically.

**Consequence:** each crankpin is a small machined steel part with two journals
4.07 mm apart (drawing M01). All five pins are identical and symmetric
end-for-end, so the pin cannot be fitted backwards.

## 2. A floating piston must be guided by something (decision: steel rail + bronze bushings)

The brief says the pistons should float, *"guided only by the rods and crank"*.
Unfortunately that isn't possible. A con-rod pivots at both ends, so a piston
held only by its rod has nothing stopping it from tipping over on the wrist pin
or swinging sideways with the rod. Every slider-crank needs a straight-line guide
for the piston. In a real engine that guide is the cylinder wall, and that is
exactly the rubbing contact we want to avoid.

The solution used here:

* Each piston has a small **lug on its valley side** carrying **two sintered
  (oil-impregnated) bronze bushings**, 3×5×5 mm.
* The lug slides on a fixed **3 mm polished stainless rail**. The rail is held
  at the top by the deck of the cylinder bank and at the bottom by the crankcase.
* The piston body keeps **0.8 mm radial clearance** to the bore all the way
  round (`PISTON_RADIAL_CLEARANCE`). The lug keeps 0.8 mm from its pocket.
  **No plastic touches the cylinder, ever.**
* The only sliding pair in the cylinder is bronze on polished stainless, a
  proper bearing pair that runs quietly for thousands of hours with one drop of
  oil.
* The rail sits on the valley side, behind the piston. From the cut-away side
  you see a clean piston moving in a clean bore. The crown has nothing through
  it.

The rail layout tolerates the small errors of printed parts. A rail that is
off-position or slightly tilted only moves the piston by a fraction of a
millimetre, and the rod's ±0.5 mm side float absorbs that.

## 3. Only two main bearings (decision: one 608 at each end)

Real engines have a main bearing between every throw. On a printed block, six
bearings in a line would need their seats aligned to a few hundredths of a
millimetre over 270 mm. Printed parts cannot hold that, so the crank would bind,
and the binding would get worse as the plastic creeps.

Two bearings define an axis exactly and cannot fight each other. The crank
between them is a stiff, rigid assembly: every joint is keyed with a D-flat and
clamped with a screw. The display loads are tiny, only 10 light pistons at up to
2 rev/s, so the calculated deflection is negligible. The trade-off is fewer
"real engine" details inside the crankcase. That is invisible in a display, and
it means much less friction, so the motor needs very little current.

## 4. Built-up crank with ball-bearing big ends

Each con-rod carries a one-piece **686-2Z ball bearing** (6×13×5). That keeps
plastic from rubbing on the crankpin and makes rod replacement easy. A one-piece
bearing can only go onto the pin if the crank comes apart, so the crank is
**built up**:

```
[main shaft]-[end web]-(pin 1)-[segment 54]-(pin 2)-[segment 198]-(pin 3)
             -[segment 198]-(pin 4)-[segment 54]-(pin 5)-[end web]-[main shaft]
```

* **Only 3 different printed crank parts** (end web x2, segment "54" x2,
  segment "198" x2). The segment type is engraved on it.
* Every pin end has a **D-flat** that fits a D-hole in the web. Every joint can
  go together only one way and cannot slip. Each end is pulled home by **one
  M3×8** screw into the pin's tapped end. **No glue anywhere.**
* The main shafts bolt to the end webs with 3 screws in an **uneven pattern**
  (110°/110°/140°), so they also fit only one way.
* The segments are solid and heavy. The extra mass works as a flywheel and
  smooths out the stepper's micro-steps at low RPM.

## 5. Cylinder banks slide on over the pistons

The block is split into a **crankcase** plus **two identical cylinder banks**.
This matches how real engines with wet liners are built, and it makes assembly
easy and repeatable:

1. The crank module (crank, rods and pistons) slides into the crankcase from
   the end. The rods run along two long slots.
2. The end plates with their 608 bearings slide onto the shafts and bolt on.
3. Each bank lowers straight down its bore axis over its five pistons. Two
   printed pegs make it fit only one way round.
4. The rails drop in through the deck.

Both banks are the *same part*, turned 180°. That halves the number of
different parts and the print-farm setup.

## 6. Clearances verified in CAD over a full revolution

`python cad/assembly.py` places every part at 10° steps through a full turn and
intersects every moving part with every other part. The current design is
**collision-free**. The sweep caught two real problems during design, and both
were fixed in `config.py`:

* The guide lug hit the deck ring at TDC. The lug top is now 2 mm below the crown.
* The con-rods clipped the crankcase slots at maximum swing. The slot is now
  ±15 mm.

`clearances()` in the same file reports the minimum running gap for every pair
of parts.

## 7. Materials and why

PLA is excellent for accuracy and stiffness at room temperature. However:

* It softens at about 55°C. A display cabinet in the sun, or a delivery van in
  summer, easily reaches that.
* Under constant load it creeps. Bearing press-fits and screw clamps slowly
  loosen.

So the rule used throughout:

| Part type | Material | Why |
|---|---|---|
| Anything holding a bearing, insert or clamp, and large structural parts (crankcase, banks, end plates) | **ASA** | Softens at ~95°C, stable dimensions, UV-proof, premium matte finish. The H2S/H2C enclosure handles its warping. |
| Crank webs/segments | **PETG-CF** (or ASA) | Stiff, low creep, ~80°C heat resistance, holds D-holes accurately. |
| Con-rods, pistons (moving, precise) | **PLA @ 0.15 mm for the prototype**; production choice made by the heat test in the Phase 1 checklist | PLA gives you the best fits today. If the 60°C soak test loosens the bearing or bushing fits, production switches to PETG-CF with re-tuned fits. |
| Crank pins, main shafts, rails, wrist pins | **Steel** (stainless) | Wear surfaces and precision journals; see drawings M01–M03. |
| Covers, cosmetic parts (Phase 3) | ASA or PETG | Heat and UV for a product that ships worldwide. |

## 8. Fasteners

* **M3 socket-head screws in two lengths only: M3×8 and M3×16.** Phase 1 uses
  M3×8 everywhere. Counterbores are sized so that 4 mm of plastic under the
  head plus 4 mm of thread in the insert always works out to an M3×8.
* Brass heat-set inserts: M3 × 5.7 mm (4.6 mm OD), pilot hole 4.0 mm
  (`INSERT_HOLE_DIA`).
* Screws that clamp moving assemblies (crankpins and main shaft flanges) get
  **medium threadlocker** (Loctite 243). It holds against vibration and still
  comes apart with a hex key.

## 9. Things deliberately left for later phases

* The drive pulley goes on the front main shaft, outside the front end plate
  (Phase 2). The shaft already has the flat for the pulley grub screws.
* The hall-sensor magnet pocket is already in the end web rim. The sensor
  pocket and wire slot are already in the crankcase floor.
* The heads bolt onto the deck and also cap the top ends of the rails (Phase 3).
