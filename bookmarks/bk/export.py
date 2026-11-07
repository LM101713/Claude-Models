"""BK-01 BOOKMARKS: STL and 3MF writers (numpy + stdlib only).

The multicolour 3MF follows the layout Bambu Studio itself writes: one build object whose
<components> point at one mesh file per colour region in 3D/Objects/, and
Metadata/model_settings.config giving every part its name and filament slot ("extruder").
It carries no printer, filament or process profile (none is invented): Bambu Studio applies
the printer and filaments selected when the file is opened.
"""

import struct
import uuid
import zipfile

import numpy as np

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BBS = "http://schemas.bambulab.com/package/2021"
REL_3D = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
REL_THUMB = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"


def mesh_arrays(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float64)
    t = np.asarray(mesh.tri_verts).astype(np.int64)
    return v, t


def _sliver_pass(v, t, tol):
    """Remove zero-area triangles whose three vertices are distinct but collinear: the
    middle vertex r lies on the long edge p-q, so the neighbour across p-q is split at r
    and the sliver dropped. Geometry is unchanged; only the triangulation is."""
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    area2 = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    bad = np.where(area2 < tol)[0]
    if not len(bad):
        return t, 0
    edge = {}
    for i, (x, y, z) in enumerate(t):
        edge[(x, y)] = i
        edge[(y, z)] = i
        edge[(z, x)] = i
    dead, new, touched, done = set(), [], set(), 0
    for i in bad:
        if i in touched:
            continue
        tri = t[i]
        L = [np.linalg.norm(v[tri[(k + 1) % 3]] - v[tri[k]]) for k in range(3)]
        k = int(np.argmax(L))
        p_, q_, r_ = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]
        j = edge.get((q_, p_))
        if j is None or j in touched or j == i:
            continue
        nb = list(t[j])
        m_ = nb.index(q_)
        s_ = nb[(m_ + 2) % 3]
        if s_ == r_:
            continue
        dead.update((i, j))
        touched.update((i, j))
        new += [(q_, r_, s_), (r_, p_, s_)]
        done += 1
    keep = np.array([i for i in range(len(t)) if i not in dead], dtype=np.int64)
    t2 = np.vstack([t[keep], np.array(new, dtype=np.int64).reshape(-1, 3)])
    return t2, done


WELD = 0.00005   # mm: vertices closer than 0.05 micron are one vertex (float32 resolves ~0.01 micron here)


def export_arrays(m):
    """Mesh arrays ready for file formats without topology (STL; a 3MF read by a slicer).

    manifold3d's output is a valid closed mesh, but its booleans leave zero-length edges
    (needle triangles whose two vertices sit at one position under two indices) and
    collinear zero-area slivers wherever coplanar faces met. A reader that welds vertices
    by position, as every slicer does with STL, then sees non-manifold edges. So:
        1. weld vertices closer than 0.05 micron (manifold3d leaves pairs ~0.1 micron apart,
           which a slicer's tolerant welding would merge anyway),
        2. drop the needle triangles that collapse to a repeated index,
        3. drop zero-thickness fins (a triangle and its exact mirror),
        4. remove collinear slivers by splitting their neighbour (edge flip).
    No vertex moves by more than 0.05 micron; volumes change by < 0.02 mm3.
    Returns (vertices, triangles, number of triangles repaired)."""
    v, t = mesh_arrays(m)
    # weld: union-find over every pair of vertices closer than WELD
    from scipy.spatial import cKDTree
    parent = np.arange(len(v))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in cKDTree(v).query_pairs(WELD, output_type="ndarray"):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)
    root = np.array([find(i) for i in range(len(v))])
    reps, inv = np.unique(root, return_inverse=True)
    v2 = v[reps]
    t2 = inv[t]
    ok = (t2[:, 0] != t2[:, 1]) & (t2[:, 1] != t2[:, 2]) & (t2[:, 0] != t2[:, 2])
    n_needle = int((~ok).sum())
    t2 = t2[ok]
    # zero-thickness fins: the same three vertices twice with opposite winding
    srt = np.sort(t2, axis=1)
    _, first_i, cnt_t = np.unique(srt, axis=0, return_index=True, return_counts=True)
    inv_t = np.unique(srt, axis=0, return_inverse=True)[1].ravel()
    fin = cnt_t[inv_t] == 2
    n_fin = int(fin.sum())
    t2 = t2[~fin]
    tol = 1e-9
    n_sliver = 0
    for _ in range(50):
        t2, done = _sliver_pass(v2, t2, tol)
        n_sliver += done
        if not done:
            break
    # drop vertices nothing references
    used = np.unique(t2)
    remap = np.full(len(v2), -1)
    remap[used] = np.arange(len(used))
    return v2[used], remap[t2], n_needle + n_sliver + n_fin


def write_stl(path, m, name="BK-01 BOOKMARKS"):
    v, t, _ = export_arrays(m)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-20
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(rec.tobytes())


def _mesh_xml(oid, v, t, name):
    vs = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
    ts = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
    return (f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model" name="{name}">\n   <mesh>\n'
            f"    <vertices>\n{vs}\n    </vertices>\n    <triangles>\n{ts}\n    </triangles>\n"
            "   </mesh>\n  </object>\n")


def write_3mf(path, parts, obj_name, extruders, bed_centre=(162.5, 160.0), thumbnail=None,
              title="BK-01 Bookmarks", filament_note=""):
    """parts: list of (part name, manifold) in the print frame (bed at z = 0).
    extruders: list of filament slots (1-based), one per part."""
    # centre the object's footprint on the bed; keep z as built (it already sits on z = 0)
    arrays = [export_arrays(m)[:2] for _, m in parts]
    allv = np.vstack([a[0] for a in arrays])
    cx, cy = 0.5 * (allv[:, 0].min() + allv[:, 0].max()), 0.5 * (allv[:, 1].min() + allv[:, 1].max())
    sub_objects, comps, rels, part_cfg = [], [], [], []
    oid_obj = len(parts) + 1
    for i, ((pname, m), ext, (v, t)) in enumerate(zip(parts, extruders, arrays), start=1):
        v = v - np.array([cx, cy, 0.0])
        sub_objects.append(_mesh_xml(i, v, t, pname))
        comps.append(f'    <component p:path="/3D/Objects/object_{i}.model" objectid="{i}" '
                     f'p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
        part_cfg.append(
            f'    <part id="{i}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{pname}"/>\n'
            f'      <metadata key="matrix" value="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
            f'      <metadata key="extruder" value="{ext}"/>\n'
            f'      <mesh_stat face_count="{len(t)}" edges_fixed="0" degenerate_facets="0" '
            f'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
            f"    </part>")

    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE}" xmlns:BambuStudio="{BBS}" '
            f'xmlns:p="{PROD}" requiredextensions="p">\n')
    # one mesh file per part (the layout the skill's project_3mf.py uses with real H2C projects)
    object_files = {f"3D/Objects/object_{i}.model":
                    head + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                    + so + " </resources>\n <build/>\n</model>\n"
                    for i, so in enumerate(sub_objects, start=1)}
    main = (head
            + ' <metadata name="Application">BK-01 generator (bookmarks.py)</metadata>\n'
            + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            + f' <metadata name="Title">{title}</metadata>\n'
            + ' <metadata name="Designer">Claude-Models</metadata>\n'
            + f' <metadata name="Description">{filament_note}</metadata>\n'
            + ' <metadata name="Units">millimeter</metadata>\n'
            + f' <resources>\n  <object id="{oid_obj}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
            + "\n".join(comps) + "\n   </components>\n  </object>\n </resources>\n"
            + f' <build p:UUID="{uuid.uuid4()}">\n'
            + f'  <item objectid="{oid_obj}" p:UUID="{uuid.uuid4()}" '
            + f'transform="1 0 0 0 1 0 0 0 1 {bed_centre[0]:.4f} {bed_centre[1]:.4f} 0" printable="1"/>\n'
            + " </build>\n</model>\n")
    settings = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
                f'  <object id="{oid_obj}">\n'
                f'    <metadata key="name" value="{obj_name}"/>\n'
                f'    <metadata key="extruder" value="{extruders[0]}"/>\n'
                + "\n".join(part_cfg) + "\n  </object>\n"
                "  <plate>\n"
                '    <metadata key="plater_id" value="1"/>\n'
                '    <metadata key="plater_name" value=""/>\n'
                '    <metadata key="locked" value="false"/>\n'
                + ('    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>\n' if thumbnail else "")
                + "    <model_instance>\n"
                f'      <metadata key="object_id" value="{oid_obj}"/>\n'
                '      <metadata key="instance_id" value="0"/>\n'
                '      <metadata key="identify_id" value="1"/>\n'
                "    </model_instance>\n  </plate>\n</config>\n")
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
          ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
          ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
          ' <Default Extension="png" ContentType="image/png"/>\n'
          ' <Default Extension="config" ContentType="text/xml"/>\n'
          "</Types>\n")
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            f' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{REL_3D}"/>\n'
            + (f' <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="{REL_THUMB}"/>\n' if thumbnail else "")
            + "</Relationships>\n")
    model_rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                  + "".join(f' <Relationship Target="/{n}" Id="rel-{i}" Type="{REL_3D}"/>\n'
                            for i, n in enumerate(object_files, start=1))
                  + "</Relationships>\n")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", main)
        z.writestr("3D/_rels/3dmodel.model.rels", model_rels)
        for n, body in object_files.items():
            z.writestr(n, body)
        z.writestr("Metadata/model_settings.config", settings)
        if thumbnail:
            z.write(thumbnail, "Metadata/plate_1.png")
