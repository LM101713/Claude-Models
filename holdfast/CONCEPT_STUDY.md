# HF-04 HOLDFAST: Phase 1 concept study

Odd Layer's fourth product has to do a real job and carry a mechanism people enjoy using. It
also has to survive being printed on printers we will never see. MotionLoop failed on that
last point, so printability and fit robustness weigh as heavily below as usefulness does.

## Three concepts

### A. HOLDFAST: gravity-locking tool grip (wall organiser)

**Problem.** Brooms, mops and garden tools fall over, lean in corners and slide off nails.
Fixed clips fit only one handle size, and spring clips lose their grip.

**Mechanism.** The handle is held by a wedge that self-locks. Each side has a roller on a
steep ramp. The handle's weight drags the rollers down the ramp, and the gap narrows until the
handle is clamped. The harder it pulls down, the harder it is gripped. Lifting the handle rolls
the rollers back up and releases it. No springs are involved.

**Why people print it.** One closet or garage needs 3–8 of them, one per handle, so
multiple copies are built in. One size fits 19–32 mm handles. It needs no hardware except the
two wall screws.

### B. TALLY: indexing "did I already…?" dial

**Problem.** Did the dog get fed, did I take my tablet, were the plants watered today?

**Mechanism.** A rotary dial with a printed flexure detent that clicks through seven days
(or AM/PM). It sticks to a fridge, a feed bin or a pill box.

**Why people print it.** One per pet, medication or plant. It is quick and cheap to print.

### C. SPAN: twist-lock adjustable drawer divider

**Problem.** Drawer dividers never fit the drawer: too short, too loose, or glued in for good.

**Mechanism.** A telescoping divider with a cam collar. A quarter turn expands the divider
against the drawer sides, the way a tension rod works.

**Why people print it.** A drawer needs 2–4 of them, and every kitchen has several drawers.

## Evaluation

Scores are 1–5 (5 = best) on the five criteria in the brief. The weights reflect Odd Layer's
situation: usefulness and reliability come first, because a failed product costs more than a
plain one.

| Criterion (weight) | A. HOLDFAST | B. TALLY | C. SPAN |
|---|:-:|:-:|:-:|
| Usefulness (×2) | **5**: daily, visible problem; replaces bought hardware | 3: helpful, but a sticky note does the same job | 4: real problem in every kitchen |
| Originality (×1) | 3: gravity holders exist; twin self-centring rollers, a designed 8° wedge, keyhole-captive rollers and a 19–32 mm range in one size are not common | 2: many day-trackers on every model site | 3: tension dividers exist, but few printable ones |
| Printability (×1.5) | **5**: 3 small parts, all flat on the bed, no supports, every working surface drawn in XY | 5 | 2: 200–300 mm parts, warp-prone, heavy |
| Mechanical reliability (×2) | 4: no springs, no flexures, no precision fits. It depends on friction ≥ 0.141, which is a single number with a wide margin | 4: a flexure detent fatigues and creeps | 2: depends on friction against unknown drawer sides; telescoping parts bind |
| Download / multi-copy potential (×1.5) | **5**: sets of 3–8; garage, closet and shed audiences | 3 | 4 |
| **Weighted total (of 40)** | **36** | 28 | 24 |

## Selection: A, HOLDFAST

- **The mechanism is the product.** Nothing is decorative. The roller wedge is why it fits
  every handle from 19 to 32 mm, why it grips harder under load, and why it lets go when you
  lift. The motion is also satisfying: push in, let go, *clunk*. Lift, and the rollers roll up
  and clack back onto their stops.
- **It suits FDM.** The one dimension that decides whether it holds is the ramp angle. It is
  drawn in the XY plane, which a printer reproduces to a fraction of a degree, and no
  dimensional error of 0.1–0.4 mm changes an angle. That is the opposite of MotionLoop, whose
  function depended on press-fit diameters.
- **It naturally gets printed in multiples**, and it serves the garage/workshop crowd, one of
  MakerWorld's strongest download categories.
- **Risks are known and testable.** Friction margin, contact pressure on steel handles, and
  wall-mount strength are each covered by a specific test in `PHYSICAL_TESTING.md`.

## Inside the concept: mechanism choices

Once A was chosen, four ways to build the wedge were compared.

| Option | Verdict | Reason |
|---|---|---|
| Pivoting log-spiral cams (climbing-cam geometry) | rejected | With a 10° camming angle, a 19–32 mm range needs ~120–140° of cam rotation. Gravity cannot close a cam reliably over that range: the centre of mass swings past the pivot, and pivot friction eats the small closing torque (rough estimate: ≈ 0.27 N·mm of gravity torque against ≈ 0.2 N·mm of pivot friction at the ends of the range). A spring over 120° strains a printed flexure 1.5–2 %, where PLA creeps and fatigues. |
| Single cam or roller against a fixed jaw | rejected | One wedge has to cover the whole 13 mm range alone. That doubles the travel, and the handle is pushed off-centre. |
| **Twin rollers on fixed ramps (selected)** | **selected** | Each roller covers only half the range (6.5 mm → 23.6 mm of travel at 16°). Gravity acts straight down the ramp with no pivot friction (≈ 70 mN, about 10× the resistance). The handle self-centres. A roller is a disc printed flat, perfectly round in XY. |
| Printed balls in conical seats | rejected | Spheres print with a flat and a stair-stepped top. Point contact on the ramp as well as on the handle. Harder to keep captive without a cover. |

**Roller retention** was compared in the same way: a screwed front cover (2 more parts, and
loose until it is screwed to the wall), a V-ridge track (it can unseat), and a **keyhole
T-slot (selected)**. With the T-slot, a short mushroom stub on each roller's axis runs in an
undercut slot in the back plate. The roller goes in through a keyhole at the top of its travel
and is then captive everywhere else. The holder is one assembled unit before it goes on the
wall, it needs no tools, and it comes apart again without damage.
