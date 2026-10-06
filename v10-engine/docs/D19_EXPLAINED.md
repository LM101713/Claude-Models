# D19 explained: the con-rod big-end wall (provisional, awaiting your OK)

## What changed

Each of the 10 con-rods has a steel ball bearing (686, 13 mm across) pressed
into its big end. The ring of plastic around that bearing was **2.5 mm**
thick; I made it **3.0 mm**. The big end therefore grew from 18 mm to 19 mm
across. Nothing else moved.

The number lives in `config.py` as `ROD_BIG_END_WALL = 3.0`.

## Why

Pressing a steel bearing into a plastic ring stretches the ring. With only
2.5 mm of plastic that ring is thin: in PLA, and in ASA printed with layer
lines running around the eye, the most likely failure is a crack along a
layer line when the bearing goes in, or weeks later as the plastic relaxes.
The crush-rib fit used here presses on 6 small ribs rather than the whole
bore, which helps, but it is unproven (nothing has been printed yet). A
thicker ring is the cheapest insurance: 3.0 mm is about 45 % more material in
the hoop.

## The risk of the change

* The big end sweeps closer to the inside of the crankcase and to the
  neighbouring rod. The full-rotation check was re-run with the 3.0 mm wall:
  **no collisions**, and the smallest rod-to-crankcase gap is unchanged at
  1.95 mm (that gap is set by the rod shank, not the eye).
* Visually: the rod eye is 1 mm bigger. Rods are only seen through the
  cylinder windows, moving; I could not see the difference in the renders.
* It adds about 0.1 g of filament per rod.

## The alternative (keep 2.5 mm)

If you prefer the original look, set `ROD_BIG_END_WALL = 2.5` in `config.py`,
run `python build_all.py`, then `python tools/verify_all.py` (about 1 hour).
The design goes back exactly to the baseline rod. You then rely on coupon
**T3b** (686 bearing ladder, 5 mm thick like the rod) to prove the 2.5 mm
ring survives: press a bearing into each step and look for cracks at the ribs
after 24 hours as well as immediately.

## My recommendation

Keep 3.0 mm unless T3b shows every step survives in ASA with margin to
spare. A split rod eye on a shipped engine is a return; 1 mm on a hidden part
is free.

## What does NOT depend on this

Nothing. The rod's centre distance, bearing, bushing, piston pin and the
crank are identical in both versions. Switching is one number and a rebuild.
