"""STL and 3MF writers (numpy + stdlib only), and a round-trip reader for the checks."""

import struct
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from manifold3d import Manifold, Mesh

TITLE = "GS-05 GIFT SLIDE"


def mesh_arrays(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float64)
    t = np.asarray(mesh.tri_verts).astype(np.int64)
    return v, t


def write_stl(path, m, name=TITLE):
    v, t = mesh_arrays(m)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-20
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(rec.tobytes())


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        rec = np.frombuffer(f.read(50 * n), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3),
                                                  ("c", "<f4", 3), ("x", "<u2")])
    tri = np.stack([rec["a"], rec["b"], rec["c"]], axis=1).reshape(-1, 3).astype(np.float64)
    uniq, inv = np.unique(np.round(tri, 5), axis=0, return_inverse=True)
    return uniq, inv.reshape(-1, 3)


def manifold_from_arrays(v, t):
    return Manifold(Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(t, np.uint32)))


def _mesh_xml(v, t):
    vs = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
    ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
    return f"<mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh>"


def write_3mf(path, items, plate=(180.0, 180.0), colours=None):
    """items: list of (name, manifold) or (name, [(part_name, manifold), ...]) for a multi-part
    object. Each item is already arranged around the plate origin; the plate centre is added.
    A multi-part item becomes one object made of components, which Bambu Studio / Orca /
    PrusaSlicer load as one object with several parts (one filament per part)."""
    res, build = [], []
    oid = 1
    cx, cy = plate[0] / 2, plate[1] / 2
    mats = []
    for name, m in items:
        if isinstance(m, list):
            comp_ids = []
            for pname, pm in m:
                v, t = mesh_arrays(pm)
                res.append(f'<object id="{oid}" name="{pname}" type="model">{_mesh_xml(v, t)}</object>')
                comp_ids.append(oid)
                oid += 1
            comps = "".join(f'<component objectid="{c}"/>' for c in comp_ids)
            res.append(f'<object id="{oid}" name="{name}" type="model"><components>{comps}</components></object>')
        else:
            v, t = mesh_arrays(m)
            res.append(f'<object id="{oid}" name="{name}" type="model">{_mesh_xml(v, t)}</object>')
        build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {cx} {cy} 0"/>')
        oid += 1
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{TITLE}</metadata><metadata name="Designer">Odd Layer</metadata>'
        '<metadata name="Description">Geometry only: open in Bambu Studio and choose your printer and filament.</metadata>'
        f"<resources>{''.join(res)}</resources><build>{''.join(build)}</build></model>"
    )
    ct = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def read_3mf(path):
    """Returns {object name: manifold} for every mesh object, in plate coordinates."""
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("3D/3dmodel.model"))
    out = {}
    objs = {o.get("id"): o for o in root.find("m:resources", ns).findall("m:object", ns)}
    shift = {}
    for it in root.find("m:build", ns).findall("m:item", ns):
        tr = [float(x) for x in it.get("transform").split()]
        o = objs[it.get("objectid")]
        comps = o.find("m:components", ns)
        ids = [c.get("objectid") for c in comps.findall("m:component", ns)] if comps is not None else [o.get("id")]
        for i in ids:
            shift[i] = (tr[9], tr[10], tr[11])
    for i, o in objs.items():
        mesh = o.find("m:mesh", ns)
        if mesh is None:
            continue
        v = np.array([[float(e.get(k)) for k in "xyz"] for e in mesh.find("m:vertices", ns)])
        t = np.array([[int(e.get(k)) for k in ("v1", "v2", "v3")] for e in mesh.find("m:triangles", ns)])
        out[o.get("name")] = manifold_from_arrays(v + np.array(shift.get(i, (0, 0, 0))), t)
    return out
