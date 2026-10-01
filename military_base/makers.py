"""Six themed money makers for the military tycoon (cheapest -> most expensive).

Run:  blender --background --python makers.py
Out:  makers.fbx       all six side by side; meshes named <Maker>_<Material>
      makers_data.lua  ModuleScript "MakersData": per-maker origin + collision boxes
Each maker fits a 24 x 24 footprint with its pivot at bottom centre.  Coordinates below are
Roblox studs relative to that pivot (+z = the side facing the player / the base front).
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blocks  # noqa: E402
from blocks import Builder, n  # noqa: E402

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials):
    for d in list(coll):
        coll.remove(d)

B = Builder()
ORDER = ["AmmoPress", "FuelRefinery", "SupplyDepot", "TankFactory", "BlackMarket", "MissileSilo"]
SPACING = 40
ORIGINS = {name: (-100 + SPACING * i, 0, 0) for i, name in enumerate(ORDER)}


class M:
    """Offsets every call by the maker origin so designs are written around (0, 0, 0)."""
    def __init__(self, name):
        self.g = name
        self.ox, _, self.oz = ORIGINS[name]

    def box(self, m, x0, x1, y0, y1, z0, z1, col=True):
        B.box(self.g, m, x0 + self.ox, x1 + self.ox, y0, y1, z0 + self.oz, z1 + self.oz, col=col)

    def cyl(self, m, cx, cz, y0, y1, r0, r1=None, segs=16, col=False):
        B.cyl(self.g, m, cx + self.ox, cz + self.oz, y0, y1, r0, r1, segs, col)

    def hcyl(self, m, axis, a0, a1, c1, cy, r, segs=12):
        if axis == "x":
            B.hcyl(self.g, m, "x", a0 + self.ox, a1 + self.ox, c1 + self.oz, cy, r, segs)
        else:
            B.hcyl(self.g, m, "z", a0 + self.oz, a1 + self.oz, c1 + self.ox, cy, r, segs)

    def hull(self, m, pts):
        B.hull(self.g, m, [(x + self.ox, y, z + self.oz) for (x, y, z) in pts])

    def beam(self, m, p0, p1, w, h=None):
        B.beam(self.g, m, (p0[0] + self.ox, p0[1], p0[2] + self.oz), (p1[0] + self.ox, p1[1], p1[2] + self.oz), w, h)

    def coll(self, x0, x1, y0, y1, z0, z1):
        B.coll(x0 + self.ox, x1 + self.ox, y0, y1, z0 + self.oz, z1 + self.oz, self.g)

    def lamp(self, x, y, z, s=1.2, t=0.6, mat="Lamp"):
        # maker lamps keep the maker name in front so fit_base.lua groups them with the maker
        B.nlamp += 1
        g = f"{self.g}L{B.nlamp:02d}"
        B.box(g, mat, x - s / 2 + self.ox, x + s / 2 + self.ox, y - t, y, z - s / 2 + self.oz, z + s / 2 + self.oz,
              col=False, kind="lamp")
        B.lamps.append((f"{g}_{mat}", (x + self.ox, y, z + self.oz)))


def pad(m, edge="Hazard"):
    m.box("Concrete", -12, 12, 0, 0.8, -12, 12)
    m.box(edge, -12, 12, 0.8, 0.9, 11.2, 12, col=False)


# ---------------------------------------------------------------- tier 1
def ammo_press():
    m = M("AmmoPress")
    pad(m)
    for sx in (-1, 1):
        m.box("Olive", sx * 5, sx * 6.8, 0.8, 12, -2.5, 2.5)
    m.box("Olive", -7, 7, 10, 12.5, -2.8, 2.8)
    m.cyl("Steel", 0, 0, 7.2, 10, 1.3, segs=14)
    m.box("Metal", -3, 3, 4.6, 7.2, -2, 2)
    m.box("DarkOlive", -4.5, 4.5, 0.8, 2.6, -3, 3)
    m.box("Hazard", -4.6, 4.6, 2.6, 2.75, -3.1, 3.1, col=False)
    m.cyl("Metal", 0, -7.5, 5, 9.5, 1.2, 3.6, segs=14)            # input hopper
    m.box("Olive", -1, 1, 0.8, 5, -8.5, -6.5)
    m.box("Black", -1.8, 1.8, 2.2, 2.7, 3, 11.5)                   # output conveyor
    for z in (4, 10.5):
        m.box("Metal", -1.6, 1.6, 0.8, 2.2, z, z + 0.8)
    for (x, z, y) in ((6, 6, 0.8), (9, 6, 0.8), (6, 9.4, 0.8), (7.5, 7.7, 3.6)):   # ammo crates
        m.box("DarkOlive", x - 1.4, x + 1.4, y, y + 2.8, z - 1.6, z + 1.6)
        m.box("Hazard", x - 1.45, x + 1.45, y + 2.0, y + 2.3, z - 1.65, z + 1.65, col=False)
    m.lamp(0, 13.1, 0, mat="Lamp")


# ---------------------------------------------------------------- tier 2
def fuel_refinery():
    m = M("FuelRefinery")
    pad(m)
    m.cyl("Olive", -5.5, -5, 0.8, 12, 4.5, segs=20, col=True)
    m.cyl("DarkOlive", -5.5, -5, 12, 14, 4.5, 2.5, segs=20)
    m.cyl("Olive", 6, -6.5, 0.8, 10, 3.4, segs=18, col=True)
    m.cyl("DarkOlive", 6, -6.5, 10, 11.5, 3.4, 1.8, segs=18)
    m.cyl("Steel", 5.5, 4.5, 0.8, 22, 1.9, segs=16, col=True)      # distillation column
    for y in (7, 13, 19):
        m.cyl("Hazard", 5.5, 4.5, y, y + 0.6, 2.4, segs=16)
    m.cyl("Metal", 5.5, 4.5, 22, 23, 1.9, 0.8, segs=16)
    m.hcyl("Metal", "x", -1, 5.5, -5, 9, 0.6)                       # pipes
    m.hcyl("Metal", "z", -5, 4.5, 4.5, 15, 0.6)
    m.hcyl("Metal", "x", 2.6, 6, -6.5, 4, 0.6)
    m.box("DarkOlive", -2, 2, 0.8, 4, 0, 4)                          # pump
    m.box("Metal", -1.5, 1.5, 4, 5, 0.5, 3.5, col=False)
    for (x, z) in ((-8, 6), (-6, 6), (-8, 8.2), (-6, 8.2), (-7, 10.4)):
        m.cyl("Rust", x, z, 0.8, 3.6, 0.95, segs=12)
    m.coll(-9, -5, 0.8, 3.6, 5, 11.4)
    m.cyl("DarkConcrete", -9.5, -10, 0.8, 18, 0.7, 0.5, segs=10)    # flare stack
    m.lamp(-9.5, 18.8, -10, s=1.0, t=0.8, mat="Beacon")


# ---------------------------------------------------------------- tier 3
def supply_depot():
    m = M("SupplyDepot")
    pad(m)
    for x in (-11, 10.6):
        for z in (-11, 4):
            m.box("Olive", x, x + 0.6, 0.8, 10 if z < 0 else 8.5, z, z + 0.6)
    m.box("Olive", -11, 11.2, 0.8, 8, -11.6, -11)                  # back wall
    m.hull("Canvas", [(x, 10.4, -12) for x in (-11.8, 11.8)] + [(x, 8.8, 5.4) for x in (-11.8, 11.8)] +
           [(x, 10.9, -12) for x in (-11.8, 11.8)] + [(x, 9.3, 5.4) for x in (-11.8, 11.8)])
    m.coll(-11.8, 11.8, 9.0, 9.4, -12, 5.4)
    for (x, z, h) in ((-8, -8, 6), (-4, -8, 4), (0, -8, 6), (5, -8, 3), (-8, -3, 3), (6, -3.5, 5)):
        m.box("Wood", x - 1.8, x + 1.8, 0.8, 0.8 + h, z - 1.8, z + 1.8)
        m.box("Olive", x - 1.2, x + 1.2, 0.8 + h, 1.6 + h, z - 1.2, z + 1.2, col=False)
    # forklift
    m.box("Hazard", 1, 5, 0.8, 4.2, 4, 9)
    m.box("Black", 1.5, 4.5, 4.2, 6.6, 4.5, 7, col=False)
    m.box("Metal", 1.2, 1.6, 0.8, 7.5, 9, 9.4)
    m.box("Metal", 4.4, 4.8, 0.8, 7.5, 9, 9.4)
    m.box("Metal", 1.4, 4.6, 1.2, 1.5, 9.4, 12)
    for (x, z) in ((1.2, 5), (4.8, 5), (1.2, 8.2), (4.8, 8.2)):
        m.hcyl("Black", "x", x - 0.3, x + 0.3, z, 1.5, 0.75)
    m.box("Wood", -9, -3, 0.8, 1.6, 6, 10)                        # loaded pallet out front
    m.box("DarkOlive", -8.5, -3.5, 1.6, 4.4, 6.5, 9.5)


# ---------------------------------------------------------------- tier 4
def tank_factory():
    m = M("TankFactory")
    pad(m)
    m.box("Olive", -11.5, 11.5, 0.8, 14, -11.5, 3)                  # hall (solid)
    m.box("Black", -6, 6, 0.8, 9.5, 3, 3.1, col=False)             # door recess
    m.box("Hazard", -6.6, -6, 0.8, 10, 3, 3.3, col=False)
    m.box("Hazard", 6, 6.6, 0.8, 10, 3, 3.3, col=False)
    for k in range(3):                                              # sawtooth roof with glazing
        z0 = -11.5 + k * 4.83
        m.hull("DarkOlive", [(x, 14, z) for x in (-11.5, 11.5) for z in (z0, z0 + 4.83)] +
               [(x, 18, z0 + 4.83) for x in (-11.5, 11.5)])
        m.box("Glass", -11, 11, 14.2, 17.6, z0 + 4.7, z0 + 4.8, col=False)
    for x in (-8, -4):
        m.cyl("DarkConcrete", x, -9, 14, 22, 1.1, segs=12)
        m.cyl("Hazard", x, -9, 20.5, 21.3, 1.15, segs=12)
    # tank rolling out of the door
    m.box("DarkOlive", -3.6, 3.6, 1.6, 4, 2, 10.5)
    m.hull("DarkOlive", [(x, y, 10.5) for x in (-3.6, 3.6) for y in (1.6, 4)] + [(x, 2.6, 11.6) for x in (-3.2, 3.2)])
    for sx in (-1, 1):
        m.box("Black", sx * 3.6, sx * 4.8, 0.8, 3.2, 1.6, 11.4)
    m.box("Olive", -2.4, 2.4, 4, 6, 3.4, 8.2)
    m.beam("Metal", (0, 5, 8.2), (0, 5.4, 11.9), 0.6)
    m.lamp(0, 11, 3.6, s=2.0, t=0.5, mat="Lamp")


# ---------------------------------------------------------------- tier 5
def black_market():
    m = M("BlackMarket")
    m.box("Asphalt", -12, 12, 0, 0.8, -12, 12)
    m.box("Shady", -12, 12, 0.8, 0.9, 11.2, 12, col=False)
    # two shipping containers, one stacked and offset, one open toward the player
    m.box("Rust", -11.5, -1.5, 0.8, 7.5, -11.5, -4)
    m.box("Black", -11.5, 0.5, 7.5, 14, -10.5, -3.5)
    for x in (-10, -7.5, -5, -2.5):
        m.box("Rust", x, x + 0.4, 0.8, 7.5, -4, -3.8, col=False)
    m.box("DarkOlive", 2, 11.5, 0.8, 7.5, -11.5, -4.5)            # open container: back + roof + sides
    m.box("Shady", 2.5, 11, 6.8, 7.0, -11, -5, col=False)
    m.box("Wood", 3.5, 10, 0.8, 3.6, -9, -7)                       # counter inside
    # tarp canopy over the trading floor
    for (x, z) in ((-10, 1), (10, 1), (-10, 9), (10, 9)):
        m.box("Metal", x - 0.3, x + 0.3, 0.8, 8, z - 0.3, z + 0.3)
    m.hull("Canvas", [(x, 8, z) for x in (-10.8, 10.8) for z in (0.2, 9.8)] + [(x, 9.6, 5) for x in (-10.8, 10.8)])
    m.coll(-10.8, 10.8, 8, 8.4, 0.2, 9.8)
    m.box("Wood", -4, 4, 0.8, 3.6, 3, 5.5)                          # trading table
    m.box("Shady", -3, -1, 3.6, 4.0, 3.6, 4.9, col=False)
    for (x, z, h) in ((-8.5, 6, 2.4), (-6.6, 8.6, 1.8), (8, 6.5, 2.4)):
        m.box("Wood", x - 1.2, x + 1.2, 0.8, 0.8 + h, z - 1.2, z + 1.2)
    m.cyl("Rust", 8.5, 9.5, 0.8, 3.8, 1, segs=12, col=True)
    m.beam("Metal", (-1, 14, -6), (-1, 17, -6), 0.3)                # dish on the stacked container
    m.hull("Metal", [(-1 + 2.2 * math.cos(a), 17 + 2.2 * math.sin(a) * 0.7, -6 + 2.2 * math.sin(a) * 0.7)
                     for a in [i * math.pi / 5 for i in range(10)]] + [(-1, 17.6, -5)])
    m.lamp(6.75, 6.7, -8, s=1.4, t=0.4, mat="Shady")
    m.lamp(-6, 14.6, -7, s=1.0, t=0.6, mat="Beacon")


# ---------------------------------------------------------------- tier 6
def missile_silo():
    m = M("MissileSilo")
    m.box("Concrete", -12, 12, 0, 2, -12, 12)
    for (x0, x1, z0, z1) in ((-12, 12, 11.2, 12), (-12, 12, -12, -11.2), (-12, -11.2, -11.2, 11.2), (11.2, 12, -11.2, 11.2)):
        m.box("Hazard", x0, x1, 2, 2.15, z0, z1, col=False)
    # raised collar around the launch tube
    for (x0, x1, z0, z1) in ((-8, 8, 5, 8), (-8, 8, -8, -5), (-8, -5, -5, 5), (5, 8, -5, 5)):
        m.box("DarkConcrete", x0, x1, 2, 5, z0, z1)
    m.box("Black", -5, 5, 2.0, 2.1, -5, 5, col=False)
    # blast doors swung open to both sides
    for sx in (-1, 1):
        m.hull("Metal", [(sx * 8, y, z) for y in (5, 5.8) for z in (-5, 5)] +
               [(sx * 11.6, y, z) for y in (11, 11.8) for z in (-5, 5)])
        m.coll(min(sx * 8, sx * 11.2), max(sx * 8, sx * 11.2), 5, 8, -5, 5)
    # the missile
    m.cyl("Marking", 0, 0, 2.1, 22, 2.3, segs=20, col=True)
    for y in (6, 16):
        m.cyl("Black", 0, 0, y, y + 0.8, 2.35, segs=20)
    m.cyl("Hazard", 0, 0, 20, 22, 2.35, segs=20)
    m.cyl("Marking", 0, 0, 22, 28, 2.3, 0.15, segs=20)
    for a in range(4):
        t = a * math.pi / 2
        c, s = math.cos(t), math.sin(t)
        m.hull("DarkOlive", [(c * 2.2, 3, s * 2.2), (c * 2.2, 9, s * 2.2), (c * 4.6, 3, s * 4.6), (c * 4.6, 5, s * 4.6),
                             (c * 2.2 - s * 0.2, 3, s * 2.2 + c * 0.2), (c * 4.6 - s * 0.2, 3, s * 4.6 + c * 0.2)])
    # service gantry in the back-left corner with an arm to the missile
    for (x, z) in ((-11.5, -11.5), (-8.5, -11.5), (-11.5, -8.5), (-8.5, -8.5)):
        m.box("Olive", x, x + 0.8, 2, 26, z, z + 0.8)
    for y in (8, 14, 20, 26):
        m.box("DarkOlive", -11.7, -7.5, y, y + 0.6, -11.7, -7.5, col=False)
    for k in range(4):
        y = 2 + k * 6
        m.beam("DarkOlive", (-11.1, y, -11.1), (-8.1, y + 6, -11.1), 0.3)
        m.beam("DarkOlive", (-11.1, y, -11.1), (-11.1, y + 6, -8.1), 0.3)
    m.coll(-11.5, -7.7, 2, 26.6, -11.5, -7.7)
    m.beam("Olive", (-8.1, 18.3, -8.1), (-1.6, 18.3, -1.6), 1.0)
    m.box("Steel", -11.7, -7.5, 26.6, 27.2, -11.7, -7.5)
    m.lamp(-9.6, 28.2, -9.6, s=1.2, t=1.0, mat="Beacon")
    m.lamp(10, 3.0, 10, s=1.0, t=1.0, mat="Beacon")
    m.lamp(-10, 3.0, 10, s=1.0, t=1.0, mat="Beacon")


ammo_press()
fuel_refinery()
supply_depot()
tank_factory()
black_market()
missile_silo()

objs = B.build()
blocks.report(objs, "MAKERS")
blocks.check_normals(objs)
blocks.check_coplanar(B, verbose=30)

# per-maker footprint check (+-12, y >= 0) and collision lists relative to each pivot
per = {name: [] for name in ORDER}
ok = True
for name in ORDER:
    ox, _, oz = ORIGINS[name]
    xs, ys, zs = [], [], []
    for o in objs:
        if o.name.startswith(name):
            for v in o.data.vertices:
                xs.append(v.co.x - ox); zs.append(-v.co.y - oz); ys.append(v.co.z)
    fits = max(map(abs, xs)) <= 12.001 and max(map(abs, zs)) <= 12.001 and min(ys) >= -1e-4
    ok &= fits
    tris = sum(len(o.data.polygons) for o in objs if o.name.startswith(name))
    print(f"[MAKER] {name:13s} x {min(xs):6.2f}..{max(xs):5.2f}  z {min(zs):6.2f}..{max(zs):5.2f}  "
          f"height {max(ys):5.1f}  tris {tris:5d}  {'OK' if fits else 'OUTSIDE 24x24'}")
for c in B.collide:
    for name in ORDER:
        ox, _, oz = ORIGINS[name]
        if abs(c[0] - ox) <= 12.5:
            per[name].append((c[0] - ox, c[1], c[2] - oz, c[3], c[4], c[5]))
            break
print(f"[CHECK] all makers inside 24 x 24: {'OK' if ok else 'NO'}")

xs, ys, zs = [], [], []
for o in objs:
    for v in o.data.vertices:
        xs.append(v.co.x); zs.append(-v.co.y); ys.append(v.co.z)
L = ["-- MakersData: generated by makers.py. Paste into a ModuleScript named MakersData in ServerStorage.\n",
     "return {\n", "\tversion = 1,\n",
     f"\tbboxMin = {{{n(min(xs))}, {n(min(ys))}, {n(min(zs))}}},\n",
     f"\tbboxMax = {{{n(max(xs))}, {n(max(ys))}, {n(max(zs))}}},\n", "\tmakers = {\n"]
for i, name in enumerate(ORDER, 1):
    ox, oy, oz = ORIGINS[name]
    L.append(f"\t\t{{name = \"{name}\", tier = {i}, origin = {{{n(ox)}, {n(oy)}, {n(oz)}}}, collision = {{\n")
    L += [f"\t\t\t{{{', '.join(n(v) for v in c)}}},\n" for c in per[name]]
    L.append("\t\t}},\n")
L += ["\t},\n", "}\n"]
with open(os.path.join(HERE, "makers_data.lua"), "w") as f:
    f.writelines(L)
print("[EXPORT]", os.path.join(HERE, "makers_data.lua"))
if os.environ.get("NO_EXPORT") != "1":
    blocks.export_fbx(objs, os.path.join(HERE, "makers.fbx"))
MAKER_OBJECTS = objs
