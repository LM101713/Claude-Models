# V8 headers - how they print, how they survive handling

## Primary pipes (33A x4, 33B x4 mirror)

* **Orientation:** standing on the collector spigot. Checked angles from the
  print vertical: drop 0 deg, tuck-in run 28 deg, head stub **45.5 deg**
  (0.5 deg over the 45 deg rule, on a 20 mm round section 15 mm long; this
  prints clean in practice but it is the one place to watch on the first
  print). Height 124 mm, footprint 33 x 40 mm. The part is tall for its
  14 mm base: slice with a **brim (5 mm)**, 4 pipes per plate spaced apart.
* **Wall / infill:** print as the slicer's "solid shell": 4 perimeters
  (1.7 mm wall) + 15 % gyroid. Not modelled hollow: a hollow 20 mm tube
  gains nothing visible (both ends sit in sockets) and loses stiffness at
  the bends.
* **Strength (estimate, not a test):** the weak section is the 14 mm spigot
  at each end, printed with its layers across the pipe axis. ASA at ~20 MPa
  across layers gives ~5 N m before the spigot snaps, i.e. a ~5 kg push on
  the pipe's middle. In the assembled engine each pipe is held at both ends
  (head socket and collector socket) plus the flange plate, so a knock is
  shared by 4 pipes and the collector. A loose pipe on a table is the
  fragile case.
* **Fragile - flagged:** (1) the collector-end spigot while pressing the
  pipe in: push on the drop, not on the stub; (2) the stub's 45.5 deg
  underside is the roughest surface - it faces down and inboard on the
  engine, out of sight.

## Flange plate (34 x2)

Flat, 4 mm, 198 x 33 mm, no overhangs. Robust.

## Collector (35A, 35B mirror)

* Lying on its inboard flat (hidden by the pan). The 4 saddle sockets are
  then horizontal holes with crush ribs: 14 mm horizontal holes bridge fine
  at 0.16 mm layers; the saddle counterbores (20.4 mm) are shallow.
* Tapered 28 -> 42 mm, 214 mm long, 145 cm3 solid envelope; slice with
  3 perimeters + 10 % infill (~110 g ASA each).
* Open tail (4.5 mm wall) is the only thin feature; it is 8 mm inside the
  stand footprint, so it cannot take a knock from the table edge.

## Plug boots (32 x8, translucent)

10 x 10 x 26 mm standing on the shaft end; 2 walls, 0 % infill for the glow
(coupon T9 decides). The 9 mm shaft in a crush socket is the fragile bit:
press straight, never lever.

## Flex test first: coupon T10

`T10_header_flex` is one real bank-A primary (33A geometry, same file) in
PLA with the production walls (4 perimeters, 15 % gyroid, 0.16 mm layers,
5 mm brim), on plate C1 with the fit coupons. Test it like this:

1. Hold the collector spigot in a vice with soft jaws (10 mm deep) and push
   the head stub sideways with a finger. It should flex a few mm and come
   back; if it cracks at the spigot shoulder the layer adhesion is too low
   (dry the filament, +5 C nozzle) or the spigot needs the 1 mm fillet
   adding (tell me, 10-minute change).
2. Press the head spigot into the T9 coupon's... no - T9 has a 9 mm socket.
   The 14 mm header socket is in the head itself; that fit is already proven
   by the V10 trumpet coupon (same `trumpet_14` crush fit).
3. Drop it onto a wooden floor from table height, stub first. A survivor is
   good enough for a display model.

## PLA vs ASA for the headers (what to expect)

| | PLA (coupon T10) | ASA (production) |
|---|---|---|
| Stiffness | stiffer (3.5 GPa) - feels solid, snaps rather than bends | softer (2.0 GPa) - flexes more before damage |
| Toughness across layers | poor: a sharp knock at the spigot shoulder shears the layers | about 2x PLA; still the weakest direction |
| Heat | softens at 55-60 C: a parcel in a van in summer, or a sunny window, can slump a standing pipe | fine to 95 C |
| Surface for paint | sands well, primer sticks | sands well; needs primer, bonds better with solvent-based paints |
| Verdict | only for the flex test and fit checks | the production material, as decided (D-series: ASA for everything) |

If the PLA T10 survives the three tests above, the ASA part will too.

## Handling plan (in the shop)

* Pipes travel between stations in the printed **header cradle** (part 37,
  a flat tray with eight 20 mm half-round saddles - to be added to the kit
  plates); never loose in a bin.
* Press pipes into the head sockets first, then the collector onto all
  four spigots at once, pushing on the collector's flat, not on a pipe.
* Paint before assembly, with the spigots masked (they are the press fits).
* The assembled engine is lifted by the pan rails, never by the headers or
  the intake.

## Shipping plan (one engine)

1. Headers ship **unfitted** in the first units: 8 pipes and 2 collectors
   in the cradle (37), bagged, inside the engine box; the customer presses
   them in (they are the only parts the customer fits - 30 seconds, no
   tools). This removes the only large lever arm from the packed engine.
   Once the ASA spigots have survived 5+ press cycles in testing, later
   units can ship assembled.
2. Engine on its stand in a double-wall box with at least 50 mm of closed-
   cell foam (not loose fill) cut to the stand plate outline, top and
   bottom; the pan rails carry the weight on the lower foam, the valve
   covers never touch foam under load (magnets would pop).
3. Lid of the intake (36a, magnetic) taped with low-tack tape; covers and
   bell the same.
4. Printed parts are ASA, so heat in transit is not a problem; PLA parts
   (the coupons) never ship.
5. Mark the box "this way up"; an upside-down drop lands on the intake.

Fragile - flagged again: the 14 mm spigots of loose pipes (ship them in the
cradle), the collector's 4.5 mm open tail, the 10 mm translucent boots (ship
fitted - they are inside the flange plate), the throttle body spigot (ships
fitted, inside the lid).
