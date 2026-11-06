"""Print orientations, STL / 3MF writers, plate packing, the deformed (locked) blade."""

import os
import struct
import zipfile

import numpy as np

from . import geo as G
from . import mech as M
from .params import P, D, bar_face, bow_ratio

COLORS = {"graphite": "#2B2D31", "orange": "#FF6A13", "sand": "#D9D3C7"}

# key -> (file stem, colour, qty, print orientation note)
BOM = [
    ("upper", "TC03_UpperJaw", "graphite", 1, "upside down: top face on the bed, clamp face up"),
    ("blade", "TC03_Blade_Standard", "sand", 1, "on its side (either side face on the bed)"),
    ("lever", "TC03_Lever", "orange", 1, "upside down: top face on the bed"),
    ("bail_a", "TC03_BailA_Pegs", "graphite", 1, "flat, pegs pointing up"),
    ("bail_b", "TC03_BailB", "graphite", 1, "flat"),
    ("pin_p", "TC03_Pin_Lever_12mm", "sand", 1, "standing on one end"),
    ("pin_h", "TC03_Pin_Hinge_18mm", "sand", 1, "standing on one end"),
]
OPTIONAL = [("blade_firm", "TC03_Blade_Firm", "sand", 1, "on its side; use instead of Standard with PETG")]

# use frame -> print frame (rotation only; translated to the bed afterwards)
FLIP = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)       # 180 deg about x
Y_UP = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)        # +y becomes +z
ORIENT = {"upper": FLIP, "lever": FLIP, "blade": Y_UP, "blade_firm": Y_UP, "bail_a": Y_UP,
          "bail_b": Y_UP, "pin_p": Y_UP, "pin_h": Y_UP}


def to_print(key, v):
    w = v @ ORIENT[key].T
    lo, hi = w.min(0), w.max(0)
    return w - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]), hi - lo


def write_stl(path, v, t, name="TC03"):
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n, axis=1)
        n = n / np.where(ln > 0, ln, 1)[:, None]
        rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3),
                                      ("c", "<f4", 3), ("attr", "<u2")])
        rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
        f.write(rec.tobytes())


def write_3mf(path, objects, title):
    """objects: list of (name, verts, tris, (tx, ty), '#RRGGBB')."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<model unit="millimeter" xml:lang="en-US" '
           'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
           'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">',
           f'<metadata name="Title">{title}</metadata>',
           '<metadata name="Designer">Odd Layer</metadata>', '<resources>', '<m:colorgroup id="100">']
    for o in objects:
        xml.append(f'<m:color color="{o[4]}"/>')
    xml.append("</m:colorgroup>")
    for i, (name, v, t, _, _) in enumerate(objects):
        xml.append(f'<object id="{i + 1}" name="{name}" type="model" pid="100" pindex="{i}"><mesh><vertices>')
        xml.extend(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
        xml.append("</vertices><triangles>")
        xml.extend(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
        xml.append("</triangles></mesh></object>")
    xml.append("</resources><build>")
    for i, (_, _, _, (tx, ty), _) in enumerate(objects):
        xml.append(f'<item objectid="{i + 1}" transform="1 0 0 0 1 0 0 0 1 {tx:.3f} {ty:.3f} 0"/>')
    xml.append("</build></model>")
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "\n".join(xml))


def pack(sizes, bed=220.0, gap=8.0):
    """Shelf packing of (dx, dy) footprints, longest first, centred on the bed."""
    order = sorted(range(len(sizes)), key=lambda i: -(sizes[i][0] * 1000 + sizes[i][1]))
    x = y = 0.0
    shelf = 0.0
    pos = {}
    for i in order:
        dx, dy = sizes[i]
        if x + dx > bed - 2 * gap and x > 0:
            x, y, shelf = 0.0, y + shelf + gap, 0.0
        pos[i] = (x + dx / 2, y + dy / 2)
        x += dx + gap
        shelf = max(shelf, dy)
    xs = [pos[i][0] - sizes[i][0] / 2 for i in pos] + [pos[i][0] + sizes[i][0] / 2 for i in pos]
    ys = [pos[i][1] - sizes[i][1] / 2 for i in pos] + [pos[i][1] + sizes[i][1] / 2 for i in pos]
    sx, sy = bed / 2 - (min(xs) + max(xs)) / 2, bed / 2 - (min(ys) + max(ys)) / 2
    return {i: (px + sx, py + sy) for i, (px, py) in pos.items()}, (max(xs) - min(xs), max(ys) - min(ys))


# =====================================================================================
# Locked pose: the blade with its bar pressed flush (bag thickness 0, no pin clearance)
# =====================================================================================


def deform_blade(v):
    """Move the bar down onto z = 0 (rigid) and bend the bow by the same amount at the bridge,
    in the bow's own centre-load shape. Returns new vertices (use frame, locked pose)."""
    v = v.copy()
    xm = P.BRIDGES[0]
    d_c = bar_face(xm)
    from .parts import bow_centre
    for i, (x, y, z) in enumerate(v):
        xc = min(max(x, 0.0), P.XP)
        bar_bottom = bar_face(xc) - P.BAR_T
        bow_top = bow_centre(xc) + P.BOW_T / 2
        in_bar = (P.BAR_X[0] - 0.5 <= x <= P.BAR_X[1] + 0.5) and z > (bar_bottom + bow_top) / 2
        if in_bar:
            v[i, 2] -= bar_face(xc)
        else:
            v[i, 2] -= d_c * bow_ratio(xc)
    return v


def pose_matrix(key, st):
    """4x4 use-frame placement of a part at mechanism state st (rotations about y)."""
    import math

    def rot_about(pivot, ang, to=None):
        c, s = math.cos(ang), math.sin(ang)
        # rotation in XZ by ang (CCW seen with x right, z up) = about -y
        R = np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
        p = np.array([pivot[0], 0, pivot[1]])
        t = np.array([to[0], 0, to[1]]) if to is not None else p
        M4 = np.eye(4)
        M4[:3, :3] = R
        M4[:3, 3] = t - R @ p
        return M4

    if key in ("lever", "pin_p"):
        return rot_about(D["P"], -st["theta"])
    if key in ("blade", "blade_firm", "pin_h"):
        return rot_about(D["H"], -st["phi"])
    if key in ("bail_a", "bail_b"):
        return rot_about(D["K"], st["bail_rot"], st["K"])
    return np.eye(4)
