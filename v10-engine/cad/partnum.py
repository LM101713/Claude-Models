"""Part numbers engraved (recessed, never raised) on a hidden face of every
printed part, in the part's PRINT orientation.

Raised text on a mating face would hold the part off its neighbour, so the
numbers are cut 0.5 mm INTO the face. The face is chosen per part (a mating
or inside face); the exact spot is found automatically: a probe scans the
face for a flat, feature-free patch big enough for the text (nothing above
it, solid material below it), so the label never lands on a hole, groove or
boss. If no spot is found the part is exported unlabelled and reported.
"""

import cadquery as cq

from common import C

DEPTH = 0.5
FACES = {        # name: (outward normal, text x direction)
    "+z": ((0, 0, 1), (1, 0, 0)), "-z": ((0, 0, -1), (1, 0, 0)),   # not used: bed face
    "+x": ((1, 0, 0), (0, 1, 0)), "-x": ((-1, 0, 0), (0, -1, 0)),
    "+y": ((0, 1, 0), (-1, 0, 0)), "-y": ((0, -1, 0), (1, 0, 0)),
}
# part file prefix: (label, faces to try in order, text sizes to try, max scan depth from the bbox face)
SPEC = {
    "01_": ("01", ("+x", "-x"), (5.0, 3.5), 1.0),     # crankcase: end face (under an end plate)
    "02_": ("02", ("+z",), (4.0, 3.0, 2.2), 4.0),        # valley beam: bank B land (top when printed)
    "03_": ("03", ("+z",), (5.0, 3.5, 2.5), 8.0),      # bank: mounting face (deck-down print)
    "04_": ("04", ("+z",), (4.0, 3.0), 8.0),           # end plate: inner face
    "05_": ("05", ("+z",), (3.5, 2.5), 6.0),           # end web: face against the segment
    "08_": ("08", ("+z",), (2.2, 1.8), 2.0),           # con-rod: flute floor
    "09_": ("09", ("+z",), (2.5, 1.8), 20.0),          # piston: crown underside, inside the skirt
    "10_": ("10", ("+z",), (4.0, 3.0, 2.5), 40.0),     # head: under the cam cover (cap top or head top)
    "11_": ("11", ("+z",), (4.0, 3.0, 2.2), 18.0),     # cam cover: rim or inside of the top
    "12_": ("12", ("+y", "-y"), (3.0, 2.5, 2.0), 1.0), # side panel: long edge face (under the exhaust / facing the base)
    "13_": ("13", ("+z",), (2.2, 1.8), 40.0),          # trumpet: flange underside
    "14_": ("14A", ("+x", "-x", "+y", "-y"), (3.0, 2.2, 1.8), 40.0),  # exhaust A: inside the tail-pipe mouth
    "15_": ("15B", ("+x", "-x", "+y", "-y"), (3.0, 2.2, 1.8), 40.0),  # exhaust B: inside the tail-pipe mouth
    "16_": ("16", ("+z",), (3.0, 2.2), 1.0),           # coil pack: free end of the shaft (inside its socket)
    "17_": ("17", ("+y", "-y"), (3.0, 2.5), 60.0),     # throttle frame: a rail side face (down in the valley)
    "18_": ("18", ("+z",), (4.0, 3.0, 2.2), 25.0),     # end cover: rim or inside of the end wall
    "19_": ("19", ("+z",), (5.0, 3.5), 70.0),          # base halves: wall top rim or skin underside
    "20_": ("20", ("+z",), (5.0, 3.5), 70.0),
    "21_": ("21", ("+z",), (5.0, 3.5), 1.0),           # bottom panel: inside face
}
# crank segments 06/07 carry their label in crank.py (type number + part number)


def _probe(shape, origin, n, xd, w, h):
    """True if a w x h patch centred at origin lies on a flat face: solid just
    below it, nothing just above it."""
    nv, xv = cq.Vector(*n), cq.Vector(*xd)
    yv = nv.cross(xv)
    for u in (-0.5, -0.25, 0.0, 0.25, 0.5):
        for v in (-0.5, 0.0, 0.5):
            p = origin + xv * (u * w) + yv * (v * h)
            if not shape.isInside(p - nv * (DEPTH * 0.6), 1e-3):
                return False
            if shape.isInside(p + nv * 0.3, 1e-3):
                return False
    return True


def _planar_faces(shape, n, scan):
    """Planar faces whose outward normal is n, within `scan` mm of the bbox
    extreme in that direction, nearest the extreme first."""
    nv = cq.Vector(*n)
    bb = shape.BoundingBox()
    ext = max(nv.dot(cq.Vector(x, y, z)) for x in (bb.xmin, bb.xmax) for y in (bb.ymin, bb.ymax)
              for z in (bb.zmin, bb.zmax))
    out = []
    for f in shape.Faces():
        if f.geomType() != "PLANE":
            continue
        c = f.Center()
        if f.normalAt(c).dot(nv) < 0.999:
            continue
        d = ext - nv.dot(c)
        if d <= scan + 1e-6 and f.Area() > 12.0:
            out.append((d, -f.Area(), f))
    out.sort(key=lambda t: (round(t[0], 1), t[1]))
    return [(d, f) for d, _, f in out]


def engrave(shape, label, faces, sizes, scan, grid=3.0):
    """Never on the bed face ("-z" at the bbox minimum): recessed text there
    makes small first-layer islands and the slicer flags low bed adhesion."""
    for face in faces:
        assert face != "-z", "bed face is not allowed for part numbers"
        n, xd = FACES[face]
        nv, xv = cq.Vector(*n), cq.Vector(*xd)
        yv = nv.cross(xv)
        for d, f in _planar_faces(shape, n, scan):
            fb = f.BoundingBox()
            flo, fhi = cq.Vector(fb.xmin, fb.ymin, fb.zmin), cq.Vector(fb.xmax, fb.ymax, fb.zmax)
            fc = (flo + fhi) * 0.5
            ext = fhi - flo
            half_u = abs(xv.dot(ext)) / 2
            half_v = abs(yv.dot(ext)) / 2
            for size in sizes:
                w, h = 0.75 * size * len(label) + 0.6, size + 0.6
                if w / 2 > half_u or h / 2 > half_v:
                    continue
                cands = []
                nu, nvv = int(half_u / grid) + 1, int(half_v / grid) + 1
                for i in range(nu):
                    for j in range(nvv):
                        for su in ((1,) if i == 0 else (1, -1)):
                            for sv in ((1,) if j == 0 else (1, -1)):
                                u, v = su * i * grid, sv * j * grid
                                if abs(u) + w / 2 <= half_u and abs(v) + h / 2 <= half_v:
                                    cands.append((abs(u) + abs(v), u, v))
                cands.sort()
                for _, u, v in cands[:400]:
                    origin = fc + xv * u + yv * v
                    if _probe(shape, origin, n, xd, w, h):
                        pl = cq.Plane(origin=origin.toTuple(), xDir=xd, normal=n)
                        txt = (cq.Workplane(pl).workplane(offset=-DEPTH)
                               .text(label, size, DEPTH + 0.05, halign="center", valign="center", kind="bold"))
                        out = shape.cut(txt.val())
                        if len(out.Solids()) == 1:
                            return out, f"{face} face {d:.1f} mm in, size {size}"
    return shape, None


SPEC_V8 = {
    "01_": ("01", ("+x", "-x"), (5.0, 3.5), 1.0),       # crankcase: end face (under an end plate)
    "02_": ("02", ("+z",), (4.0, 3.0, 2.2), 4.0),        # valley beam: bank B land
    "03_": ("03", ("+z",), (5.0, 3.5, 2.5), 8.0),        # bank: mounting face
    "04_": ("04", ("+z",), (4.0, 3.0), 8.0),             # end plate: inner face
    "05_": ("05", ("+z",), (3.5, 2.5), 6.0),             # end web
    "09_": ("09", ("+z",), (2.2, 1.8), 2.0),             # con-rod: flute floor
    "10_": ("10", ("+z",), (2.5, 1.8), 20.0),            # piston: crown underside
    "30_": ("30A", ("+z",), (4.0, 3.0, 2.5), 40.0),      # head A: top, under the valve cover
    "30B": ("30B", ("+z",), (4.0, 3.0, 2.5), 40.0),      # head B (mirror)
    "31_": ("31", ("+z",), (4.0, 3.0, 2.2), 18.0),       # valve cover: inside (printed top-down)
    "33_": ("33A", ("+z",), (2.2, 1.8), 1.0),            # primary: head-spigot end face (inside its socket)
    "33B": ("33B", ("+z",), (2.2, 1.8), 1.0),
    "34_": ("34A", ("+x", "-x"), (2.5, 2.0), 1.0),       # flange plate: end face
    "34B": ("34B", ("+x", "-x"), (2.5, 2.0), 1.0),
    "35_": ("35A", ("+x", "-x"), (2.5, 2.0), 1.0),       # collector: tail / nose end face
    "35B": ("35B", ("+x", "-x"), (2.5, 2.0), 1.0),
    "36_": ("36A", ("+z",), (4.0, 3.0, 2.2), 30.0),      # intake lid: inside the roof (printed upside down)
    "36B": ("36B", ("+z",), (4.0, 3.0, 2.2), 30.0),      # intake base: floor inside
    "40_": ("40", ("+z",), (5.0, 3.5), 60.0),            # pan: inside of the skin (printed skin-down)
    "41_": ("41", ("+z",), (5.0, 3.5), 1.0),             # floor panel: inside face
    "42_": ("42", ("+z",), (4.0, 3.0, 2.2), 25.0),       # bellhousing: inside the rear face
    "43_": ("43", ("+z",), (4.0, 3.0, 2.2), 25.0),       # front cover: inside the front wall
    "46_": ("46", ("+y", "-y"), (5.0, 3.5), 1.0),        # stand plate: cut-out wall
    "47_": ("47", ("+y", "-y"), (3.0, 2.2), 1.0),        # bracket: a side face (tab side, against the pan)
    "47B": ("47m", ("+y", "-y"), (3.0, 2.2), 1.0),
    "48_": ("48", ("+z",), (4.0, 3.0), 20.0),            # plinth: inside the roof (printed upside down)
}
# not labelled on purpose (no hidden flat face): 32 boots, 36C throttle body, 44 damper, 45 accessory module


def label_part(name, shape):
    """Engrave the part number if `name` has a SPEC entry. Returns (shape, note)."""
    spec = SPEC_V8 if getattr(C, "VARIANT", "v10") == "v8" else SPEC
    # longest matching prefix wins (30B before 30_)
    for prefix, (label, faces, sizes, scan) in sorted(spec.items(), key=lambda kv: -len(kv[0])):
        if name.startswith(prefix):
            return engrave(shape, label, faces, sizes, scan)
    return shape, "n/a"
