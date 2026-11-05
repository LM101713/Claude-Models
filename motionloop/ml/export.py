"""STL / 3MF writers and a simple shelf packer for the print plate."""

import struct
import zipfile

from mathutils import Matrix, Vector

from . import geom as G

COLORS = {"graphite": "#2B2D31", "orange": "#FF6A13", "sand": "#D9D3C7", "steel": "#9AA0A6"}

# part key -> (file stem, colour, quantity in a set)
BOM = [
    ("frame", "ML02_Frame", "graphite", 1),
    ("wheel_mirror", "ML02_Wheel_Mirror", "orange", 1),
    ("cheek", "ML02_Cheek", "sand", 2),
    ("rod", "ML02_Rod", "sand", 2),
    ("slider", "ML02_Slider", "orange", 2),
    ("pin", "ML02_Pin", "sand", 3),
    ("cap", "ML02_Cap", "graphite", 1),
    ("handle", "ML02_Handle", "graphite", 1),
    ("knob", "ML02_Knob", "orange", 1),
]
OPTIONAL = [("wheel_shuttle", "ML02_Wheel_Shuttle", "sand", 1)]


def write_stl(path, verts, tris, name="MotionLoop"):
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            a, b, c = (verts[i] for i in t)
            n = (b - a).cross(c - a)
            if n.length > 0:
                n.normalize()
            f.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z, b.x, b.y, b.z,
                                c.x, c.y, c.z, 0))


def write_3mf(path, objects, title):
    """objects: list of (name, verts, tris, (tx, ty), '#RRGGBB')."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<model unit="millimeter" xml:lang="en-US" '
           'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
           'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">',
           f'<metadata name="Title">{title}</metadata>',
           '<metadata name="Designer">Odd Layer</metadata>',
           '<resources>', '<m:colorgroup id="100">']
    for o in objects:
        xml.append(f'<m:color color="{o[4]}"/>')
    xml.append("</m:colorgroup>")
    for i, (name, verts, tris, _, _) in enumerate(objects):
        xml.append(f'<object id="{i + 1}" name="{name}" type="model" pid="100" pindex="{i}">'
                   "<mesh><vertices>")
        xml.extend(f'<vertex x="{v.x:.4f}" y="{v.y:.4f}" z="{v.z:.4f}"/>' for v in verts)
        xml.append("</vertices><triangles>")
        xml.extend(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        xml.append("</triangles></mesh></object>")
    xml.append("</resources><build>")
    for i, (_, _, _, (tx, ty), _) in enumerate(objects):
        xml.append(f'<item objectid="{i + 1}" transform="1 0 0 0 1 0 0 0 1 {tx:.3f} {ty:.3f} 0"/>')
    xml.append("</build></model>")
    ct = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          "</Types>")
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "\n".join(xml))


def centred(ob, M):
    """Mesh in print orientation, centred on x/y, sitting on z = 0."""
    v, t = G.world_tris(ob, M)
    lo = Vector((min(q.x for q in v), min(q.y for q in v), min(q.z for q in v)))
    hi = Vector((max(q.x for q in v), max(q.y for q in v), max(q.z for q in v)))
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    v = [q - c for q in v]
    return v, t, (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)


def pack(items, width=236.0, gap=6.0, origin=(10.0, 10.0)):
    """items: list of (key, (dx, dy)). Shelf packing, largest first. Returns {index: (cx, cy)}."""
    order = sorted(range(len(items)), key=lambda i: -items[i][1][1] * 1000 - items[i][1][0])
    x, y, shelf_h = origin[0], origin[1], 0.0
    pos = {}
    for i in order:
        dx, dy = items[i][1]
        if x + dx > origin[0] + width:
            x = origin[0]
            y += shelf_h + gap
            shelf_h = 0.0
        pos[i] = (x + dx / 2, y + dy / 2)
        x += dx + gap
        shelf_h = max(shelf_h, dy)
    # centre the whole layout on a 256 x 256 bed
    xs = [pos[i][0] - items[i][1][0] / 2 for i in pos] + [pos[i][0] + items[i][1][0] / 2 for i in pos]
    ys = [pos[i][1] - items[i][1][1] / 2 for i in pos] + [pos[i][1] + items[i][1][1] / 2 for i in pos]
    sx, sy = 128 - (min(xs) + max(xs)) / 2, 128 - (min(ys) + max(ys)) / 2
    return {i: (cx + sx, cy + sy) for i, (cx, cy) in pos.items()}


def export_all(parts, print_mats, out_stl, out_3mf, log=print):
    import os
    os.makedirs(out_stl, exist_ok=True)
    os.makedirs(out_3mf, exist_ok=True)
    files = []
    meshes = {}
    for key, stem, col, qty in BOM + OPTIONAL:
        v, t, size = centred(parts[key], print_mats[key])
        meshes[key] = (v, t, size)
        path = os.path.join(out_stl, stem + ".stl")
        write_stl(path, v, t, stem)
        files.append(dict(file=os.path.relpath(path, os.path.dirname(out_stl)), part=stem, qty=qty,
                          colour=col, size_mm=[round(s, 2) for s in size], tris=len(t)))
    # full set on one plate (256 x 256 class printers); the shuttle wheel on its own file
    items, objs = [], []
    for key, stem, col, qty in BOM:
        for q in range(qty):
            items.append((key, meshes[key][2][:2]))
            objs.append((f"{stem}_{q + 1}" if qty > 1 else stem, key, col))
    pos = pack(items)
    out = []
    for i, (name, key, col) in enumerate(objs):
        v, t, _ = meshes[key]
        out.append((name, v, t, pos[i], COLORS[col]))
    write_3mf(os.path.join(out_3mf, "ML02_MotionLoop_full_set.3mf"), out, "Odd Layer ML-02 MotionLoop")
    v, t, _ = meshes["wheel_shuttle"]
    write_3mf(os.path.join(out_3mf, "ML02_Wheel_Shuttle.3mf"),
              [("ML02_Wheel_Shuttle", v, t, (128.0, 128.0), COLORS["sand"])],
              "Odd Layer ML-02 Shuttle wheel")
    log(f"  exported {len(files)} STL, 2 x 3MF")
    return files, [(objs[i][0], objs[i][1], pos[i]) for i in range(len(objs))], meshes
