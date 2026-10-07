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
