"""Military tycoon base v2 -- one 400 x 400 stud walled compound with enterable buildings.

Run:  blender --background --python military_base.py
Out:  military_base.fbx   visual meshes, one per Group_Material (CanCollide off in Studio)
      base_data.lua       ModuleScript "BaseData": collision boxes, ladder trusses, bbox
Coordinates in this file are Roblox studs: x right, y up, z toward the front gate (+z).
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
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for d in list(coll):
        coll.remove(d)

B = Builder()
HALF = 200          # outer wall face
WALL_T = 4
WALL_H = 16

# ---------------------------------------------------------------- gameplay reservations
# (name, x0, x1, z0, z1, y0, y1, decals_allowed)
RESERVED = [("PlotSpawn", -151, -137, -151, -137, 0, 999, False),
            ("Collector", -7, 7, -7, 7, 0, 31.4, False),   # drop shaft up to just above the Dropper
            ("UpgradePad", -107, -93, 33, 47, 0, 999, False),
            ("VehiclePad", 96, 128, 96, 128, 0, 999, False),
            ("Gate", -24, 24, 192, 200.1, 0, 17, True),
            ("DrivePath_GateRoad", -24, 24, 140, 192, 0, 8, True),
            ("DrivePath_Service", -24, 128, 140, 168, 0, 8, True),
            ("DrivePath_PadLink", 96, 128, 128, 140, 0, 8, True)]
for i, x in enumerate((-150, -90, -30, 30, 90, 150), 1):
    RESERVED.append((f"MakerSlot{i}", x - 12, x + 12, -92, -68, 0, 999, False))
    RESERVED.append((f"MakerSlot{i}_front", x - 12, x + 12, -68, -58, 0, 999, False))


# ================================================================= perimeter + gate
def perimeter():
    g = "Wall"
    i = HALF - WALL_T
    B.box(g, "Concrete", -HALF, -27, 0, WALL_H, i, HALF)
    B.box(g, "Concrete", 27, HALF, 0, WALL_H, i, HALF)
    B.box(g, "Concrete", -HALF, HALF, 0, WALL_H, -HALF, -i)
    B.box(g, "Concrete", -HALF, -i, 0, WALL_H, -i, i)
    B.box(g, "Concrete", i, HALF, 0, WALL_H, -i, i)
    # coping (walkable wall top, reached from the tower cabins)
    c = "DarkConcrete"
    B.box(g, c, -HALF, -27, WALL_H, WALL_H + 0.8, i - 0.6, HALF, col=True)
    B.box(g, c, 27, HALF, WALL_H, WALL_H + 0.8, i - 0.6, HALF)
    B.box(g, c, -HALF, HALF, WALL_H, WALL_H + 0.8, -HALF, -i + 0.6)
    B.box(g, c, -HALF, -i + 0.6, WALL_H, WALL_H + 0.8, -i + 0.6, i - 0.6)
    B.box(g, c, i - 0.6, HALF, WALL_H, WALL_H + 0.8, -i + 0.6, i - 0.6)
    # pilasters on the inside face, every 40 studs (skip towers and gate)
    for t in range(-160, 161, 40):
        if abs(t) < 40:
            continue
        for (x0, x1, z0, z1) in ((t - 1.5, t + 1.5, -i, -i + 1.5), (-i, -i + 1.5, t - 1.5, t + 1.5),
                                 (i - 1.5, i, t - 1.5, t + 1.5), (t - 1.5, t + 1.5, i - 1.5, i)):
            B.box(g, "DarkConcrete", x0, x1, 0, WALL_H + 1.6, z0, z1)
    # gate: two heavy posts and an overhead beam (18 studs clear)
    gg = "Gate"
    for sx in (-1, 1):
        B.box(gg, "DarkConcrete", sx * 24, sx * 31, 0, 22, i - 3, HALF - 0.3)
        B.box(gg, "Hazard", sx * 24, sx * 31, 22, 23, i - 3, HALF - 0.3)
    B.box(gg, "Olive", -30.7, 30.7, 18, 21.5, i - 2, HALF - 0.6)
    B.box(gg, "Hazard", -24, 24, 17.8, 18, i - 1.5, HALF - 1, col=False)
    B.lamp(-14, 17.8, i - 1, mat="Lamp")
    B.lamp(14, 17.8, i - 1, mat="Lamp")
    # sandbag nests flanking the inside of the gate
    for sx in (-1, 1):
        B.box("Sandbags", "Sand", sx * 46, sx * 62, 0, 3.5, 172, 176)
        B.box("Sandbags", "Sand", sx * 62, sx * 66, 0, 3.5, 172, 184)


# ================================================================= corner towers
def tower(cx, cz):
    g = "Tower"
    h = 7.0                      # half footprint
    fy = 23.0                    # cabin floor top
    ry = 34.0                    # roof underside
    sx, sz = (-1 if cx > 0 else 1), (-1 if cz > 0 else 1)   # toward base centre
    for dx in (-1, 1):
        for dz in (-1, 1):
            x, z = cx + dx * (h - 0.75), cz + dz * (h - 0.75)
            B.box(g, "Olive", x - 0.75, x + 0.75, 0, fy - 1, z - 0.75, z + 0.75)
    # X bracing on the two outer faces (visual, above head height)
    for dz in (-1, 1):
        z = cz + dz * (h - 0.75)
        B.beam(g, "DarkOlive", (cx - h + 0.75, 8, z), (cx + h - 0.75, fy - 1.5, z), 0.5)
        B.beam(g, "DarkOlive", (cx + h - 0.75, 8, z), (cx - h + 0.75, fy - 1.5, z), 0.5)
    for dx in (-1, 1):
        x = cx + dx * (h - 0.75)
        B.beam(g, "DarkOlive", (x, 8, cz - h + 0.75), (x, fy - 1.5, cz + h - 0.75), 0.5)
        B.beam(g, "DarkOlive", (x, 8, cz + h - 0.75), (x, fy - 1.5, cz - h + 0.75), 0.5)
    B.box(g, "DarkConcrete", cx - h - 0.5, cx + h + 0.5, fy - 1, fy, cz - h - 0.5, cz + h + 0.5)
    # ladder on the face toward the base centre: truss + visible rails
    lx = cx + sx * (h + 1.5)
    lz = cz + sz * 2.5
    B.truss(lx, 0, lz, fy + 3)
    for d in (-0.9, 0.9):
        B.box(g, "Metal", lx - 0.15, lx + 0.15, 0, fy + 3, lz + d - 0.15, lz + d + 0.15, col=False)
    for k in range(2, int(fy + 3), 3):
        B.box(g, "Metal", lx - 0.12, lx + 0.12, k, k + 0.25, lz - 0.9, lz + 0.9, col=False)
    # cabin: half walls with a gap where the ladder arrives, corner posts, roof
    t = 0.8
    gap = (lz - 2.2, lz + 2.2)
    for (axis, a0, a1, c0, c1) in (("x", cx - h, cx + h, cz - h, cz - h + t), ("x", cx - h, cx + h, cz + h - t, cz + h),
                                   ("z", cz - h + t, cz + h - t, cx - h, cx - h + t), ("z", cz - h + t, cz + h - t, cx + h - t, cx + h)):
        ops = []
        if axis == "z" and abs((c0 + c1) / 2 - (cx + sx * (h - t / 2))) < 0.01:
            ops = [(gap[0], gap[1], fy, fy + 3.2)]
        B.wall(g, "Olive", axis, a0, a1, c0, c1, fy, fy + 3.2, ops, glass=False)
    for dx in (-1, 1):
        for dz in (-1, 1):
            x, z = cx + dx * (h - 0.55), cz + dz * (h - 0.55)
            B.box(g, "DarkOlive", x - 0.45, x + 0.45, fy + 3.2, ry - 1, z - 0.45, z + 0.45)
    B.box(g, "DarkOlive", cx - h, cx + h, ry - 1, ry, cz - h, cz - h + 0.6)
    B.box(g, "DarkOlive", cx - h, cx + h, ry - 1, ry, cz + h - 0.6, cz + h)
    B.box(g, "DarkOlive", cx - h, cx - h + 0.6, ry - 1, ry, cz - h + 0.6, cz + h - 0.6)
    B.box(g, "DarkOlive", cx + h - 0.6, cx + h, ry - 1, ry, cz - h + 0.6, cz + h - 0.6)
    B.box(g, "Metal", cx - h - 1, cx + h + 1, ry, ry + 0.8, cz - h - 1, cz + h + 1)
    B.hull(g, "Metal", [(cx + a * (h + 1), ry + 0.8, cz + c * (h + 1)) for a in (-1, 1) for c in (-1, 1)] +
           [(cx + a * 2, ry + 3.5, cz + c * 2) for a in (-1, 1) for c in (-1, 1)])
    B.lamp(cx, ry - 1.1, cz)


# ================================================================= HQ (2 floors + roof)
def hq():
    g = "HQ"
    X0, X1, Z0, Z1 = -40, 40, -170, -122
    T = 1.5
    F2 = 13.0          # floor 2 top
    RF = 26.0          # roof top
    ix0, ix1, iz0, iz1 = X0 + T, X1 - T, Z0 + T, Z1 - T
    SX0, SX1 = 6, 32   # stair run
    BAND1 = (iz0, iz0 + 6)          # flight 1 (ground -> F2), climbs +x
    BAND2 = (iz0 + 6, iz0 + 12)     # flight 2 (F2 -> roof), climbs -x
    lo, hi = 4, 9.5                  # ground-floor window sill/head
    ulo, uhi = 17, 22.5
    # exterior walls (full two-storey height), openings for doors/windows
    front = [(-4, 4, 0, 9.5)] + [(c - 3, c + 3, lo, hi) for c in (-30, -20, 20, 30)] + \
            [(c - 3, c + 3, ulo, uhi) for c in (-30, -20, -7, 7, 20, 30)]
    back = [(c - 3, c + 3, lo, hi) for c in (-30, -20)] + [(c - 3, c + 3, ulo, uhi) for c in (-30, -20, -6)]
    west = [(-147, -140, 0, 9)] + [(c - 3, c + 3, lo, hi) for c in (-160, -131)] + \
           [(c - 3, c + 3, ulo, uhi) for c in (-160, -146, -131)]
    east = [(c - 3, c + 3, lo, hi) for c in (-136,)] + [(c - 3, c + 3, ulo, uhi) for c in (-136, -146)]
    B.wall(g, "Concrete", "x", X0, X1, Z1 - T, Z1, 0, RF - 1, front)
    B.wall(g, "Concrete", "x", X0, X1, Z0, Z0 + T, 0, RF - 1, back)
    B.wall(g, "Concrete", "z", iz0, iz1, X0, X0 + T, 0, RF - 1, west)
    B.wall(g, "Concrete", "z", iz0, iz1, X1 - T, X1, 0, RF - 1, east)
    # olive band at floor-2 level and plinth (visual)
    for (a, b_, c0, c1, ax) in ((X0 - 0.3, X1 + 0.3, Z1, Z1 + 0.3, "x"), (X0 - 0.3, X1 + 0.3, Z0 - 0.3, Z0, "x"),
                                (Z0, Z1, X0 - 0.3, X0, "z"), (Z0, Z1, X1, X1 + 0.3, "z")):
        for (y0, y1) in ((0, 1.2), (12, 13.2)):
            if ax == "x":
                for (u0, u1, _, _) in B.rect_subtract((a, b_, y0, y1), [(o[0], o[1], o[2], o[3]) for o in (front if c0 > Z0 else back)]):
                    B.box(g, "DarkOlive", u0, u1, y0, y1, c0, c1, col=False)
            else:
                for (u0, u1, _, _) in B.rect_subtract((a, b_, y0, y1), [(o[0], o[1], o[2], o[3]) for o in (west if c0 < X0 else east)]):
                    B.box(g, "DarkOlive", c0, c1, y0, y1, u0, u1, col=False)
    # floor 2 slab with hole over flight 1; roof slab with hole over flight 2
    B.box(g, "DarkConcrete", ix0, ix1, 0.02, 0.1, iz0, iz1, col=False, kind="decal")
    B.slab(g, "DarkConcrete", ix0, ix1, iz0, iz1, F2 - 1, F2, holes=[(SX0, SX1, BAND1[0], BAND1[1])])
    B.slab(g, "DarkConcrete", X0, X1, Z0, Z1, RF - 1, RF, holes=[(SX0, SX1, BAND2[0], BAND2[1])])
    # parapet
    for (x0, x1, z0, z1) in ((X0, X1, Z1 - 1, Z1), (X0, X1, Z0, Z0 + 1), (X0, X0 + 1, Z0 + 1, Z1 - 1), (X1 - 1, X1, Z0 + 1, Z1 - 1)):
        B.box(g, "Olive", x0, x1, RF, RF + 3.5, z0, z1)
    # interior partitions, both floors
    for (y0, y1) in ((0, F2 - 1), (F2, RF - 1)):
        dy = y0
        B.wall(g, "Olive", "z", iz0, iz1, -14.5, -13.5, y0, y1, [(-150, -142, dy, dy + 9)], glass=False)
        B.wall(g, "Olive", "z", -150.5, iz1, 13.5, 14.5, y0, y1, [(-142, -134, dy, dy + 9)], glass=False)
        B.box(g, "Olive", 14.5, ix1, y0, y1, -150.5, -149.5)
    # stairs: flight 1 ground -> floor 2 (+x), flight 2 floor 2 -> roof (-x)
    B.stairs(g, "Steel", SX0, SX1, BAND1[0], BAND1[1], "x", +1, 0, F2, solid=True)
    B.stairs(g, "Steel", SX0, SX1, BAND2[0], BAND2[1], "x", -1, F2, RF)
    # rails: between hole/flight 2, under flight 2 on floor 2, hole end, roof hatch
    B.rail(g, "x", SX0, SX1, BAND1[1], F2, h=RF + 3.5 - F2)
    B.rail(g, "x", SX0, SX1, BAND2[1], F2, h=RF + 3.5 - F2)
    B.rail(g, "z", BAND1[0], BAND1[1], SX0, F2)
    B.rail(g, "z", BAND2[0], BAND2[1], SX1, RF)
    # interior wall band (dark olive dado) on both floors, broken at the doorways
    for (y0, y1) in ((0.1, 3.5), (F2, F2 + 3.5)):
        for (axis, lo_, hi_, c0, c1, ops) in (("x", ix0, ix1, iz1 - 0.2, iz1, front), ("x", ix0, ix1, iz0, iz0 + 0.2, back),
                                             ("z", iz0 + 0.2, iz1 - 0.2, ix0, ix0 + 0.2, west), ("z", iz0 + 0.2, iz1 - 0.2, ix1 - 0.2, ix1, east)):
            doors = [(o[0], o[1], 0, 99) for o in ops if o[2] == 0]
            for (u0, u1, _, _) in B.rect_subtract((lo_, hi_, y0, y1), doors):
                if axis == "x":
                    B.box(g, "DarkOlive", u0, u1, y0, y1, c0, c1, col=False)
                else:
                    B.box(g, "DarkOlive", c0, c1, y0, y1, u0, u1, col=False)
    # reception counter facing the front door
    B.box(g, "Wood", -9, 9, 0, 3.5, -134, -132)
    B.box(g, "DarkOlive", -9.3, 9.3, 3.5, 3.9, -134.3, -131.7, col=False)
    # entrance canopy
    B.box(g, "Olive", -8, 8, 10.2, 11, Z1, Z1 + 5)
    # roof kit: AC units + radio mast with beacon
    B.box(g, "Metal", -32, -24, RF, RF + 3, -140, -132)
    B.box(g, "Metal", -32, -24, RF, RF + 3, -152, -144)
    B.box(g, "Metal", 18, 30, RF, RF + 2.5, -138, -130)
    B.box(g, "Metal", -34.5, -33.5, RF, RF + 26, -162.5, -161.5)
    for d in (8, 16):
        B.beam(g, "Metal", (-34, RF + 0.5, -162), (-34 + (26 - d) * 0.25, RF + d, -162 + 3), 0.25)
    B.lamp(-34, RF + 26.6, -162, s=1.2, t=0.6, mat="Beacon")
    B.lamp(0, F2 - 1.1, -146)
    B.lamp(0, RF - 1.1, -146)
    # desks / map table (cover inside)
    B.box(g, "Wood", -30, -22, 0, 3, -140, -134)
    B.box(g, "Wood", -30, -22, 0, 3, -158, -152)
    B.box(g, "DarkOlive", -6, 6, F2, F2 + 3, -142, -134)          # briefing table upstairs
    B.box(g, "Wood", 22, 34, 0, 3, -142, -138)
    B.box(g, "Metal", -36, -34, F2, F2 + 6, -166, -152)           # filing cabinets


# ================================================================= barracks
def barracks(zc, k):
    g = "Barracks"
    X0, X1 = -180, -132
    Z0, Z1 = zc - 10, zc + 10
    T, H = 1.5, 11
    door = [(zc - 3.5, zc + 3.5, 0, 8.5)]
    wins = [(c - 2, c + 2, 4, 8) for c in (-172, -161, -151, -140)]
    B.wall(g, "Olive", "x", X0, X1, Z0, Z0 + T, 0, H, wins)
    B.wall(g, "Olive", "x", X0, X1, Z1 - T, Z1, 0, H, wins)
    B.wall(g, "Olive", "z", Z0 + T, Z1 - T, X0, X0 + T, 0, H, door, glass=False)
    B.wall(g, "Olive", "z", Z0 + T, Z1 - T, X1 - T, X1, 0, H, door, glass=False)
    B.box(g, "DarkConcrete", X0, X1, H, H + 0.8, Z0, Z1)
    B.box(g, "Wood", X0 + T, X1 - T, 0.02, 0.1, Z0 + T, Z1 - T, col=False, kind="decal")
    # gable roof (visual; walls are 11 tall so nobody can reach it)
    B.hull(g, "DarkOlive", [(x, H + 0.8, z) for x in (X0 - 1, X1 + 1) for z in (Z0 - 1.2, Z1 + 1.2)] +
           [(x, H + 5, zc) for x in (X0 - 1, X1 + 1)])
    for x in (X0, X1):     # door canopies
        s = -1 if x == X0 else 1
        B.box(g, "DarkOlive", x + (0 if s > 0 else -3), x + (3 if s > 0 else 0), 9, 9.6, zc - 5, zc + 5)
    # bunks along both long walls: solid lower bed, upper bunk you can climb on
    for side in (-1, 1):
        zw = zc + side * 8.5
        z0, z1 = sorted((zw, zw - side * 3.5))
        for x in (-176, -168, -160, -152, -144):
            B.box(g, "Metal", x, x + 6, 0, 1.8, z0, z1)
            B.box(g, "Canvas", x + 0.2, x + 5.8, 1.8, 2.2, z0 + 0.2, z1 - 0.2, col=False)
            B.box(g, "Metal", x, x + 6, 4.6, 5.3, z0, z1)
            B.box(g, "Canvas", x + 0.2, x + 5.8, 5.3, 5.7, z0 + 0.2, z1 - 0.2, col=False)
            for px in (x, x + 5.6):
                for pz in (z0, z1 - 0.4):
                    B.box(g, "Metal", px, px + 0.4, 1.8, 4.6, pz, pz + 0.4)
    B.box(g, "Metal", -136, -134, 0, 6, zc - 8.5, zc - 5)     # lockers by the east door
    B.lamp(-156, H - 0.1, zc)


# ================================================================= hangar
def hangar():
    g = "Hangar"
    X0, X1, Z0, Z1 = 98, 178, -184, -120
    T, H = 1.5, 24
    big = [(-172, -132, 0, 20)]
    side = [(X1 - 12, X1 - 5, 0, 8.5)] + [(X0 + c - 5, X0 + c + 5, 15, 20) for c in (16, 36, 56)]
    B.wall(g, "Olive", "z", Z0, Z1, X0, X0 + T, 0, H, big)
    B.wall(g, "Olive", "z", Z0, Z1, X1 - T, X1, 0, H)
    B.wall(g, "Olive", "x", X0 + T, X1 - T, Z1 - T, Z1, 0, H, side)
    B.wall(g, "Olive", "x", X0 + T, X1 - T, Z0, Z0 + T, 0, H)
    B.box(g, "DarkConcrete", X0 + T, X1 - T, 0.02, 0.1, Z0 + T, Z1 - T, col=False, kind="decal")
    # roll-up door drum + hazard jambs on the opening
    B.hcyl(g, "DarkOlive", "z", -173, -131, X0 - 0.9, 21.6, 1.3)
    B.box(g, "Hazard", X0 - 0.2, X0 + T + 0.2, 0, 20.1, -173, -171.9, col=False)
    B.box(g, "Hazard", X0 - 0.2, X0 + T + 0.2, 0, 20.1, -132.1, -131, col=False)
    # arched roof (visual; out of reach) + arched gable ends
    zc, a, bb, N = (Z0 + Z1) / 2, (Z1 - Z0) / 2 + 1, 12, 16
    pts_o = [(zc + a * math.cos(math.pi * (1 - i / N)), H + bb * math.sin(math.pi * i / N)) for i in range(N + 1)]
    pts_i = [(zc + (a - 1.2) * math.cos(math.pi * (1 - i / N)), H + (bb - 1.2) * math.sin(math.pi * i / N)) for i in range(N + 1)]
    for i in range(N):
        quad = [pts_o[i], pts_o[i + 1], pts_i[i + 1], pts_i[i]]
        B.hull(g, "DarkOlive", [(x, y, z) for x in (X0 - 1, X1 + 1) for (z, y) in quad])
        for (xa, xb) in ((X0, X0 + T), (X1 - T, X1)):
            zl, yl = pts_i[i]
            zr, yr = pts_i[i + 1]
            zl, zr = max(zl, Z0), min(zr, Z1)
            if zr - zl > 0.05:
                B.hull(g, "Olive", [(x, y, z) for x in (xa, xb) for (z, y) in ((zl, H), (zl, max(yl, H + 0.01)),
                                                                                 (zr, max(yr, H + 0.01)), (zr, H))])
    # catwalk along the back wall at y=14, stairs up from the door end
    CY = 14
    cz0, cz1 = Z0 + T, Z0 + T + 5
    B.stairs(g, "Steel", X0 + 2, X0 + 30, cz0, cz1, "x", +1, 0, CY)
    B.box(g, "Steel", X0 + 30, X1 - T, CY - 0.8, CY, cz0, cz1)
    B.rail(g, "x", X0 + 30, X1 - T, cz1, CY)
    B.rail(g, "x", X0 + 8, X0 + 30, cz1, 6, yb=CY)
    for x in range(int(X0 + 34), int(X1 - 2), 12):
        B.box(g, "Metal", x, x + 0.8, 0, CY - 0.8, cz1 - 1, cz1 - 0.2)
    B.box(g, "Metal", X0 + 30, X0 + 31, 0, CY - 0.8, cz1 - 1, cz1 - 0.2)
    # parked helicopter (big readable shape)
    hx, hz = X0 + 44, -150
    B.box(g, "DarkOlive", hx - 7, hx + 7, 1.5, 7.5, hz - 3, hz + 3)
    B.hull(g, "DarkOlive", [(hx + 7, y, z) for y in (1.5, 7.5) for z in (hz - 3, hz + 3)] +
           [(hx + 11, y, z) for y in (2.5, 6) for z in (hz - 1.8, hz + 1.8)])
    B.hull(g, "Glass", [(hx + 11, y, z) for y in (2.5, 6) for z in (hz - 1.8, hz + 1.8)] +
           [(hx + 12.5, 3.2, hz - 1.2), (hx + 12.5, 3.2, hz + 1.2)])
    B.beam(g, "DarkOlive", (hx - 7, 6, hz), (hx - 22, 7.5, hz), 1.6)
    B.box(g, "DarkOlive", hx - 23, hx - 21, 6.5, 11, hz - 0.3, hz + 0.3, col=False)
    B.box(g, "Black", hx - 0.5, hx + 0.5, 7.5, 9.5, hz - 0.5, hz + 0.5, col=False)
    B.box(g, "Black", hx - 16, hx + 16, 9.5, 9.9, hz - 0.6, hz + 0.6, col=False)
    B.box(g, "Black", hx - 0.6, hx + 0.6, 9.55, 9.95, hz - 16, hz + 16, col=False)
    for dz in (-3.5, 3.5):
        B.box(g, "Black", hx - 6, hx + 6, 0.1, 0.5, hz + dz - 0.3, hz + dz + 0.3, col=False)
    B.coll(hx - 7, hx + 12, 0, 7.5, hz - 3, hz + 3, "Heli")
    # floor markings
    B.decal(g, "Hazard", X0 + 3, X1 - 3, -159.5, -158.5, y=0.1, t=0.04)
    B.decal(g, "Hazard", X0 + 3, X1 - 3, -133.5, -132.5, y=0.1, t=0.04)
    B.box(g, "Wood", X1 - 12, X1 - 2, 0, 4, -130, -124)              # crate stack by the side door
    B.box(g, "Wood", X1 - 10, X1 - 4, 4, 7, -129, -125)
    B.lamp(X0 + 24, H - 1, -152)
    B.lamp(X0 + 58, H - 1, -152)


# ================================================================= garage
def garage():
    g = "Garage"
    X0, X1, Z0, Z1 = 140, 192, 72, 132
    T, H = 1.5, 16
    bays = [(75, 91), (94, 110), (113, 129)]
    B.wall(g, "Olive", "z", Z0, Z1, X0, X0 + T, 0, H, [(a, c, 0, 12) for a, c in bays])
    B.wall(g, "Olive", "z", Z0, Z1, X1 - T, X1, 0, H, [(c - 4, c + 4, 9, 13) for c in (85, 102, 121)])
    B.wall(g, "Olive", "x", X0 + T, X1 - T, Z0, Z0 + T, 0, H, [(170, 177, 0, 8.5)])
    B.wall(g, "Olive", "x", X0 + T, X1 - T, Z1 - T, Z1, 0, H)
    B.box(g, "DarkConcrete", X0 - 1, X1 + 1, H, H + 1, Z0 - 1, Z1 + 1)
    B.box(g, "DarkConcrete", X0 + T, X1 - T, 0.02, 0.1, Z0 + T, Z1 - T, col=False, kind="decal")
    for a, c in bays:
        B.hcyl(g, "DarkOlive", "z", a - 0.5, c + 0.5, X0 - 0.9, 13.4, 1.1)
        B.box(g, "Hazard", X0 - 0.2, X0 + T + 0.2, 0, 12.1, a - 1, a + 0.1, col=False)
        B.box(g, "Hazard", X0 - 0.2, X0 + T + 0.2, 0, 12.1, c - 0.1, c + 1, col=False)
        B.decal(g, "Marking", X0 + 2, X1 - 8, a - 1.2, a - 0.6, y=0.1, t=0.04)
    B.decal(g, "Marking", X0 + 2, X1 - 8, 129.6, 130.2, y=0.1, t=0.04)
    # workbench + tool wall along the back, tyre stack
    B.box(g, "Wood", X1 - 5, X1 - T, 0, 3.2, 76, 96)
    B.box(g, "Wood", X1 - 5, X1 - T, 0, 3.2, 108, 128)
    B.box(g, "Metal", X1 - 2.5, X1 - T, 3.2, 9, 76, 96, col=False)
    for k in range(3):
        B.cyl(g, "Black", X1 - 6, 101.5, k * 1.4, k * 1.4 + 1.3, 1.8, segs=12)
    B.coll(X1 - 8, X1 - 4, 0, 4.2, 99.5, 103.5, "Tyres")
    B.lamp(166, H - 0.1, 102)


# ================================================================= bunkers
def bunker(zc):
    g = "Bunker"
    X0, X1, Z0, Z1 = 156, 182, zc - 11, zc + 11
    T, H = 2, 12
    B.wall(g, "Concrete", "z", Z0, Z1, X0, X0 + T, 0, H, [(zc - 3.5, zc + 3.5, 0, 8.5)], glass=False)
    B.wall(g, "Concrete", "z", Z0, Z1, X1 - T, X1, 0, H)
    B.wall(g, "Concrete", "x", X0 + T, X1 - T, Z0, Z0 + T, 0, H)
    B.wall(g, "Concrete", "x", X0 + T, X1 - T, Z1 - T, Z1, 0, H)
    B.box(g, "DarkConcrete", X0 - 0.5, X1 + 0.5, H, H + 1.5, Z0 - 0.5, Z1 + 0.5)
    B.hull(g, "DarkConcrete", [(x, H + 1.5, z) for x in (X0 - 0.5, X1 + 0.5) for z in (Z0 - 0.5, Z1 + 0.5)] +
           [(x, H + 3, z) for x in (X0 + 3, X1 - 3) for z in (Z0 + 3, Z1 - 3)])
    B.box(g, "Hazard", X0 - 0.3, X0, 8.5, 9.3, zc - 4.5, zc + 4.5, col=False)
    B.box(g, "DarkConcrete", X0 + T, X1 - T, 0.02, 0.1, Z0 + T, Z1 - T, col=False, kind="decal")
    # ammo racks: back wall + both side walls, crates on the shelves
    racks = [(X1 - T - 3, X1 - T, Z0 + T + 1, Z1 - T - 1),
             (X0 + 5, X1 - T - 5, Z0 + T, Z0 + T + 2.6),
             (X0 + 5, X1 - T - 5, Z1 - T - 2.6, Z1 - T)]
    for (x0, x1, z0, z1) in racks:
        B.coll(x0, x1, 0, 7, z0, z1, "Rack")
        for (px, pz) in ((x0, z0), (x1 - 0.3, z0), (x0, z1 - 0.3), (x1 - 0.3, z1 - 0.3)):
            B.box(g, "Metal", px, px + 0.3, 0, 7, pz, pz + 0.3, col=False)
        for y in (0.4, 3.0, 5.6):
            B.box(g, "Metal", x0 + 0.05, x1 - 0.05, y, y + 0.25, z0 + 0.05, z1 - 0.05, col=False)
            L = (x1 - x0) if (x1 - x0) > (z1 - z0) else (z1 - z0)
            for k in range(int(L // 2.6)):
                if (x1 - x0) > (z1 - z0):
                    B.box(g, "Olive", x0 + 0.4 + k * 2.6, x0 + 2.4 + k * 2.6, y + 0.25, y + 1.6, z0 + 0.3, z1 - 0.3, col=False)
                else:
                    B.box(g, "Olive", x0 + 0.3, x1 - 0.3, y + 0.25, y + 1.6, z0 + 0.4 + k * 2.6, z0 + 2.4 + k * 2.6, col=False)
    # sandbag walls protecting the door
    B.box("Sandbags", "Sand", X0 - 7, X0 - 3, 0, 3.5, zc - 10, zc - 5)
    B.box("Sandbags", "Sand", X0 - 7, X0 - 3, 0, 3.5, zc + 5, zc + 10)
    B.lamp((X0 + X1) / 2, H - 0.1, zc)


# ================================================================= guardhouses
def guardhouse(cx, cz):
    g = "Guard"
    X0, X1, Z0, Z1 = cx - 6, cx + 6, cz - 6, cz + 6
    T, H = 1, 11
    dw, ow = ((X0, X0 + T), (X1 - T, X1)) if cx > 0 else ((X1 - T, X1), (X0, X0 + T))   # door faces the gate road
    B.wall(g, "Concrete", "z", Z0, Z1, dw[0], dw[1], 0, H, [(cz - 3, cz + 3, 0, 8.2)], glass=False)
    B.wall(g, "Concrete", "z", Z0, Z1, ow[0], ow[1], 0, H, [(cz - 2, cz + 2, 4, 8)])
    B.wall(g, "Concrete", "x", X0 + T, X1 - T, Z0, Z0 + T, 0, H, [(cx - 2.5, cx + 2.5, 4, 8)])
    B.wall(g, "Concrete", "x", X0 + T, X1 - T, Z1 - T, Z1, 0, H, [(cx - 2.5, cx + 2.5, 4, 8)])
    B.box(g, "Olive", X0 - 1, X1 + 1, H, H + 1, Z0 - 1, Z1 + 1)
    for (x0, x1, z0, z1) in ((X0 - 1, X1 + 1, Z0 - 1, Z0 - 0.4), (X0 - 1, X1 + 1, Z1 + 0.4, Z1 + 1),
                             (X0 - 1, X0 - 0.4, Z0 - 0.4, Z1 + 0.4), (X1 + 0.4, X1 + 1, Z0 - 0.4, Z1 + 0.4)):
        B.box(g, "Hazard", x0, x1, H + 1, H + 1.3, z0, z1, col=False)      # hazard rim on the roof edge
    B.box(g, "Wood", cx - 4.5, cx + 4.5, 0, 3, cz + 2.5, cz + 4.5)      # desk
    B.lamp(cx, H - 0.1, cz)


# ================================================================= production core
def core():
    g = "Core"
    DECK = 30.0
    # four legs carry the hopper; deck ring around the open drop shaft
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.box(g, "Olive", sx * 19, sx * 21.5, 0, 46, sz * 19, sz * 21.5)
            B.hull(g, "Olive", [(sx * x, 46, sz * z) for x in (19, 21.5) for z in (19, 21.5)] + [(sx * 20.25, 47.2, sz * 20.25)])
            B.box(g, "DarkConcrete", sx * 18.5, sx * 22, 0, 1.2, sz * 18.5, sz * 22)
    for (x0, x1, z0, z1) in ((-24, 24, 10, 24), (-24, 24, -24, -10), (10, 24, -10, 10), (-24, -10, -10, 10)):
        B.box(g, "Steel", x0, x1, DECK - 1, DECK, z0, z1)
    # top landing joins the deck
    B.box(g, "Steel", 24, 30, DECK - 1, DECK, 8, 14)
    # rails: inner hole, outer edge (gap at the landing)
    for (ax, a0, a1, c) in (("x", -10, 10, 10), ("x", -10, 10, -10), ("z", -10, 10, 10), ("z", -10, 10, -10)):
        B.rail(g, ax, a0, a1, c, DECK)
    B.rail(g, "x", -24, 24, 24, DECK)
    B.rail(g, "x", -24, 24, -24, DECK)
    B.rail(g, "z", -24, 24, -24, DECK)
    B.rail(g, "z", -24, 8, 24, DECK)
    B.rail(g, "z", 14, 24, 24, DECK)
    B.rail(g, "x", 24, 30, 14, DECK)
    B.rail(g, "z", 8, 14, 30, DECK)
    # stairs: flight A along the south side (0 -> 15), landing, flight B up the east side (15 -> 30)
    B.stairs(g, "Steel", -8, 22, -30, -25, "x", +1, 0, 15)
    B.box(g, "Steel", 22, 30, 14, 15, -30, -22)
    B.stairs(g, "Steel", 25, 30, -22, 8, "z", +1, 15, DECK)
    B.rail(g, "x", -8, 22, -30, 0, yb=15)
    B.rail(g, "x", 2, 22, -25, 5, yb=15)
    B.rail(g, "x", 22, 30, -30, 15)
    B.rail(g, "z", -30, -22, 30, 15)
    B.rail(g, "z", -22, 8, 30, 15, yb=DECK)
    for (x, z) in ((22.2, -29.6), (29, -29.6), (29, -22.4), (29, -5), (25.6, -5), (29, 8), (25.6, 8)):
        top = 14 if z < -20 else (DECK - 1 if z > 7 else 22.5)
        B.box(g, "Metal", x - 0.4, x + 0.4, 0, top, z - 0.4, z + 0.4)
    # frame ring under the hopper + struts
    HY = 42.0
    for (x0, x1, z0, z1) in ((-19, 19, 19.3, 21.2), (-19, 19, -21.2, -19.3), (19.3, 21.2, -19, 19), (-21.2, -19.3, -19, 19)):
        B.box(g, "DarkOlive", x0, x1, HY, HY + 2, z0, z1, col=False)
    for sx in (-1, 1):
        for sz in (-1, 1):
            B.beam(g, "DarkOlive", (sx * 20, HY + 1, sz * 20), (sx * 7, HY + 1, sz * 7), 1.2)
            B.beam(g, "DarkOlive", (sx * 20, DECK + 2, sz * 20), (sx * 20, HY, 0), 0.8)
            B.beam(g, "DarkOlive", (sx * 20, DECK + 2, sz * 20), (0, HY, sz * 20), 0.8)
    # hopper: chute outlet (hazard ring, open mouth) -> cone -> drum -> cap
    B.cyl(g, "Hazard", 0, 0, 31.5, 33.2, 3.2, segs=20)
    B.cyl(g, "Black", 0, 0, 31.45, 31.55, 2.6, segs=20)
    B.cyl(g, "Metal", 0, 0, 33.2, HY + 1, 3.0, 10.5, segs=24)
    B.cyl(g, "Olive", 0, 0, HY + 1, 60, 10.5, segs=24)
    for y in (48, 54):
        B.cyl(g, "DarkOlive", 0, 0, y, y + 0.8, 10.9, segs=24)
    B.cyl(g, "Metal", 0, 0, 60, 63.5, 10.5, 4, segs=24)
    B.box(g, "Metal", -3, 3, 63.5, 66, -3, 3, col=False)
    # conveyor feeding the hopper from a ground bin (north-west)
    B.box(g, "Metal", -54, -42, 0, 6, -54, -42)
    B.hull(g, "Metal", [(x, 6, z) for x in (-54, -42) for z in (-54, -42)] + [(x, 9, z) for x in (-56, -40) for z in (-56, -40)])
    B.beam(g, "DarkOlive", (-47, 9, -47), (-9.5, 63.5, -9.5), 3.0, 1.2)
    B.box(g, "Metal", -12.5, -8.5, 60, 65, -12.5, -8.5, col=False)          # feed hood on the hopper rim
    B.box(g, "Olive", -37, -35.5, 0, 22, -37, -35.5)                     # trestle
    # exhaust stack: tallest thing on the base, red beacon on top
    B.cyl(g, "DarkConcrete", -30, 22, 0, 84, 3.2, 2.4, segs=16, col=True)
    for y in (30, 60):
        B.cyl(g, "Hazard", -30, 22, y, y + 1.5, 2.95 - y * 0.0095, segs=16)
    B.lamp(-30, 85, 22, s=2.2, t=1.0, mat="Beacon")


# ================================================================= ground + props
def ground():
    g = "Ground"
    B.decal(g, "Asphalt", -16, 16, 34, 196)                      # gate road
    B.decal(g, "Asphalt", -16, 16, 196, 200)                     # through the gate
    B.decal(g, "Asphalt", 16, 128, 140, 168)                     # service road to the vehicle pad
    B.decal(g, "Asphalt", 96, 128, 128, 140)
    B.decal(g, "Asphalt", -10, 10, -122, -34)                    # plaza -> HQ
    B.decal(g, "Asphalt", -166, 166, -56, -48, y=0.03, t=0.1)   # maker walkway (a hair higher than the HQ road it crosses)
    for z in range(40, 196, 12):                                 # centre line
        B.decal(g, "Marking", -0.3, 0.3, z, z + 6, y=0.1, t=0.04)
    # core plaza ring (around, not over, the Collector)
    for (x0, x1, z0, z1) in ((-34, 34, 9, 34), (-34, 34, -34, -9), (9, 34, -9, 9), (-34, -9, -9, 9)):
        B.decal(g, "Concrete", x0, x1, z0, z1)
    for (x0, x1, z0, z1) in ((-9, 9, 7.6, 9), (-9, 9, -9, -7.6), (7.6, 9, -7.6, 7.6), (-9, -7.6, -7.6, 7.6)):
        B.decal(g, "Hazard", x0, x1, z0, z1, y=0.1, t=0.04)
    # helipad
    B.cyl(g, "Concrete", 72, -150, 0.02, 0.1, 13, segs=24, kind="decal")
    for (x0, x1, z0, z1) in ((66, 68, -156, -144), (76, 78, -156, -144), (68, 76, -151, -149)):
        B.decal(g, "Marking", x0, x1, z0, z1, y=0.1, t=0.04)
    # fuel tanks behind the HQ
    for x in (-78, -96):
        B.cyl("Props", "Olive", x, -172, 0, 12, 7, segs=20, col=True)
        B.cyl("Props", "DarkOlive", x, -172, 12, 13.5, 7, 5, segs=20)
    B.box("Props", "Metal", -100, -74, 0, 1, -181, -163)
    # crate stacks: cover for the capture-point fights
    for (x, z) in ((-60, 100), (60, 60), (-60, -20), (64, -20), (-40, 150)):
        B.box("Props", "Wood", x - 4, x + 4, 0, 4, z - 3, z + 3)
        B.box("Props", "Olive", x - 2, x + 3, 4, 7, z - 2, z + 2)
        B.box("Props", "Wood", x + 4.5, x + 8, 0, 3.5, z - 2, z + 2)


perimeter()
for cx in (-188, 188):
    for cz in (-188, 188):
        tower(cx, cz)
hq()
for k, zc in enumerate((-20, 25, 70)):
    barracks(zc, k)
hangar()
garage()
bunker(-26)
bunker(16)
guardhouse(-36, 184)
guardhouse(36, 184)
core()
ground()

objs = B.build()

# ================================================================= checks + export
def check_bounds(objs):
    bad = 0
    lo_y = 0.0
    for o in objs:
        for v in o.data.vertices:
            x, z, y = v.co.x, -v.co.y, v.co.z
            if abs(x) > HALF + 1e-4 or abs(z) > HALF + 1e-4 or y < lo_y - 1e-4:
                bad += 1
                if bad < 10:
                    print(f"  OUT OF BOUNDS: {o.name} ({x:.2f}, {y:.2f}, {z:.2f})")
                break
    print(f"[CHECK] inside +-{HALF} and above ground: {'OK' if bad == 0 else str(bad) + ' objects out'}")
    return bad == 0


def check_reserved():
    bad = 0
    for (label, kind, (x0, x1, y0, y1, z0, z1)) in B.prims:
        for (rn, rx0, rx1, rz0, rz1, ry0, ry1, decal_ok) in RESERVED:
            if decal_ok and kind == "decal":
                continue
            if x0 < rx1 - 1e-6 and x1 > rx0 + 1e-6 and z0 < rz1 - 1e-6 and z1 > rz0 + 1e-6 and y0 < ry1 and y1 > ry0:
                bad += 1
                if bad < 25:
                    print(f"  OVERLAP {rn}: {label} [{kind}] x {x0:.1f}..{x1:.1f} y {y0:.1f}..{y1:.1f} z {z0:.1f}..{z1:.1f}")
    print(f"[CHECK] gameplay areas clear: {'OK' if bad == 0 else str(bad) + ' overlaps'}")
    return bad == 0


def check_fits():
    """Dummy player / Humvee boxes at the gate, a garage bay and interior doorways vs collision."""
    tests = [("Humvee @ gate", (-4, 4, 0.1, 6, 188, 206)),
             ("Humvee @ garage bay 1", (130, 150, 0.1, 6, 79, 87)),
             ("Humvee @ hangar door", (90, 110, 0.1, 6, -156, -148)),
             ("Player @ HQ front door", (-1, 1, 0.1, 5, -125, -119)),
             ("Player @ HQ interior doorway", (-16, -12, 0.1, 5, -147, -145)),
             ("Player @ HQ upper doorway", (-16, -12, 13.1, 18, -147, -145)),
             ("Player @ HQ stair top (roof)", (1, 3, 26.1, 31, -160.5, -158.5)),
             ("Player @ barracks door", (-184, -176, 0.1, 5, 24, 26)),
             ("Player @ bunker door", (150, 162, 0.1, 5, -27, -25)),
             ("Player @ guardhouse door", (25, 33, 0.1, 5, 183, 185)),
             ("Player @ tower cabin", (186, 188, 23.1, 28, 186, 188)),
             ("Player @ core catwalk", (14, 16, 30.1, 35, 0, 2)),
             ("Player @ hangar catwalk", (150, 152, 14.1, 19, -181, -179))]
    allok = True
    for name, (x0, x1, y0, y1, z0, z1) in tests:
        hits = [c for c in B.collide if abs(c[0] - (x0 + x1) / 2) < (c[3] + x1 - x0) / 2 - 1e-6 and
                abs(c[1] - (y0 + y1) / 2) < (c[4] + y1 - y0) / 2 - 1e-6 and
                abs(c[2] - (z0 + z1) / 2) < (c[5] + z1 - z0) / 2 - 1e-6]
        print(f"[FIT] {'OK  ' if not hits else 'FAIL'} {name}" + (f"  hits {len(hits)} e.g. {hits[0]}" if hits else ""))
        allok &= not hits
    return allok, tests


total = blocks.report(objs, "BASE")
print(f"  collision boxes={len(B.collide)} trusses={len(B.trusses)} lamps={len(B.lamps)}")
blocks.check_normals(objs)
blocks.check_coplanar(B, verbose=60)
check_bounds(objs)
check_reserved()
FIT_OK, FIT_TESTS = check_fits()

# bbox of the visual model (Roblox coords) -- fit_base.lua aligns the import to this
xs, ys, zs = [], [], []
for o in objs:
    for v in o.data.vertices:
        xs.append(v.co.x); zs.append(-v.co.y); ys.append(v.co.z)
BBMIN = (min(xs), min(ys), min(zs))
BBMAX = (max(xs), max(ys), max(zs))
print(f"[BBOX] min {BBMIN}  max {BBMAX}")

lines = ["-- BaseData: generated by military_base.py. Paste into a ModuleScript named BaseData in ServerStorage.\n",
         "-- Coordinates are studs relative to the base origin (ground centre, +Z = front gate).\n",
         "return {\n", "\tversion = 2,\n",
         f"\tbboxMin = {{{n(BBMIN[0])}, {n(BBMIN[1])}, {n(BBMIN[2])}}},\n",
         f"\tbboxMax = {{{n(BBMAX[0])}, {n(BBMAX[1])}, {n(BBMAX[2])}}},\n",
         "\t-- {cx, cy, cz, sx, sy, sz}\n\tcollision = {\n"]
lines += [f"\t\t{{{', '.join(n(v) for v in c)}}},\n" for c in B.collide]
lines += ["\t},\n", "\t-- {x, yBottom, z, height}\n\ttrusses = {\n"]
lines += [f"\t\t{{{', '.join(n(v) for v in t)}}},\n" for t in B.trusses]
lines += ["\t},\n", "}\n"]
with open(os.path.join(HERE, "base_data.lua"), "w") as f:
    f.writelines(lines)
print("[EXPORT]", os.path.join(HERE, "base_data.lua"))
if os.environ.get("NO_EXPORT") != "1":
    blocks.export_fbx(objs, os.path.join(HERE, "military_base.fbx"))
BASE_OBJECTS = objs
