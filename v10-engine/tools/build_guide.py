"""Step pictures for docs/BUILD_GUIDE.md (the V8 motion test, plates M1-M6).

    python3.13 tools/build_guide.py                 # every step
    python3.13 tools/build_guide.py --only 07,08    # some steps
    python3.13 tools/build_guide.py --draft         # fast, small, noisy

Reads the engine-frame meshes the pipeline writes (skin/core/*.stl from
tools/export_core_meshes.py, skin/assembly/*.stl from tools/skin_blender.py) and
the print-orientation STLs in stl/ and skin/. Every position comes from config.py;
nothing is drawn by hand. Output: docs/img/build/NN_name.png.

Colours: blue = the printed part(s) this step adds, grey = printed parts already
there, metal colours = bought hardware (steel bearings / screws / rails, bronze
bushings, brass inserts).
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import config as C  # noqa: E402
from skin import bpyutil as U, materials as M, studio as S  # noqa: E402

OUT = os.path.join(ROOT, "docs", "img", "build")
CORE = os.path.join(ROOT, "skin", "core")
ASM = os.path.join(ROOT, "skin", "assembly")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SIZE = (1400, 1050)
SAMPLES = 48
DRAFT = False
MARGIN = 330                  # label column each side of the render (px)

DX = C.CRANK_DX
H = C.CASE_HALF_LEN
I4 = Matrix.Identity(4)


# ---------------------------------------------------------------------------
# geometry helpers (engine frame; crank angles from +Z towards +Y, as config.py)
# ---------------------------------------------------------------------------
def polar(r, deg):
    a = math.radians(deg)
    return r * math.sin(a), r * math.cos(a)


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def RX(crank_deg):
    """Turn about X so a feature at crank angle psi ends up at psi + crank_deg."""
    return Matrix.Rotation(math.radians(-crank_deg), 4, 'X')


def RY(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Y')


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


BANK_A = RX(C.BANK_A_ANGLE)              # bank-local -> engine, bank A
BANK_B = RX(C.BANK_B_ANGLE) @ RZ(180)    # bank-local -> engine, bank B
AXIS_A = Vector((0.0, *polar(1.0, C.BANK_A_ANGLE)))


def bank_pt(x, y, z, bank="A"):
    return (BANK_A if bank == "A" else BANK_B) @ Vector((x, y, z))


def between_x():
    xs = C.BANK_A_CYL_X
    return [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)]


def end_screws_x():
    xs = C.BANK_A_CYL_X
    return [xs[0] + 18.0, xs[-1] - 19.0]


CASE_END_SCREWS = [(-40.0, -22.0), (40.0, -22.0), (-42.0, -3.0), (42.0, -3.0)]   # as cad/block.py
BEAM_END_SCREWS = [(-9.0, 39.0), (9.0, 39.0)]


def cyl_x_pos(c):
    k = C.cyl_throw(c)
    return C.BANK_A_CYL_X[k] if C.cyl_bank(c) == "A" else C.BANK_B_CYL_X[k]


def wrist(c, phi=0.0):
    """Engine-frame wrist-pin centre of cylinder c."""
    y, z = polar(C.piston_travel(phi, c), C.bank_angle(C.cyl_bank(c)))
    return Vector((cyl_x_pos(c), y, z))


def pin_c(k):
    y, z = polar(C.CRANK_R, C.THROW_PIN_A[k])
    return Vector((C.THROW_X[k] + DX, y, z))


def rod_angle(c, phi=0.0):
    psi = C.bank_angle(C.cyl_bank(c))
    beta = math.radians(C.PIN_ANGLE[c] + phi - psi)
    r, L = C.CRANK_R, C.ROD_LENGTH
    s = r * math.cos(beta) + math.sqrt(L * L - (r * math.sin(beta)) ** 2)
    return psi + math.degrees(math.atan2(-r * math.sin(beta), s - r * math.cos(beta)))


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def mat(role):
    P = M._principled
    return {
        "old": lambda: P("g_old", (0.62, 0.63, 0.65), roughness=0.55),
        "new": lambda: P("g_new", (0.05, 0.27, 0.80), roughness=0.45),
        "dark": lambda: P("g_dark", (0.30, 0.31, 0.33), roughness=0.55),
        "steel": lambda: P("g_steel", (0.78, 0.79, 0.81), metallic=1.0, roughness=0.28),
        "bronze": lambda: P("g_bronze", (0.72, 0.42, 0.18), metallic=1.0, roughness=0.35),
        "brass": lambda: P("g_brass", (0.90, 0.68, 0.22), metallic=1.0, roughness=0.25),
        "black": lambda: P("g_black", (0.03, 0.03, 0.035), roughness=0.4),
    }[role]()


def default_role(name):
    if name.startswith(("bearing", "rail_", "wristpin", "screw")):
        return "steel"
    if name.startswith("bush"):
        return "bronze"
    if name.startswith("insert"):
        return "brass"
    return "old"


# ---------------------------------------------------------------------------
# mesh library
# ---------------------------------------------------------------------------
LIB = {}


def _import(path, name):
    bpy.ops.wm.stl_import(filepath=path, global_scale=1.0)
    o = bpy.context.selected_objects[0]
    o.name = name
    for c in o.users_collection:
        c.objects.unlink(o)
    U.collection("COL_lib").objects.link(o)
    U.shade(o)
    o.hide_render = True
    LIB[name] = o
    return o


def lib(name):
    """Engine-frame mesh by name (skin/core or skin/assembly), or a print-orientation
    part as 'print:<file stem>'."""
    if name in LIB:
        return LIB[name]
    if name.startswith("print:"):
        stem = name[6:]
        for d in ("skin", "stl"):
            p = os.path.join(ROOT, d, stem + ".stl")
            if os.path.exists(p):
                return _import(p, name)
        raise FileNotFoundError(stem)
    if name.startswith("wristpin_"):
        c = int(name.split("_")[1])
        w = wrist(c)
        o = U.cylinder(name, C.WRIST_PIN["d"] / 2, w.x - C.WRIST_PIN["l"] / 2, w.x + C.WRIST_PIN["l"] / 2,
                       w.y, w.z, axis="X", segs=32, col="COL_lib")
        U.shade(o)
        o.hide_render = True
        LIB[name] = o
        return o
    for d in (CORE, ASM):
        p = os.path.join(d, name + ".stl")
        if os.path.exists(p):
            return _import(p, name)
    raise FileNotFoundError(f"{name}: run tools/pipeline_v8.py first (skin/core, skin/assembly)")


def _prim(key, build):
    if key not in LIB:
        o = build()
        U.shade(o)
        o.hide_render = True
        LIB[key] = o
    return LIB[key]


def screw_mesh():
    """M3 x 8 socket head screw, tip at the origin, pointing down -Z (head on top)."""
    def build():
        s = U.cylinder("screw_shank", 1.5, 0.0, 8.0, segs=24, col="COL_lib")
        h = U.cylinder("screw_head", C.M3_HEAD_D / 2, 8.0, 8.0 + C.M3_HEAD_H, segs=32, col="COL_lib")
        k = U.cylinder("screw_hex", 1.45, 8.0 + C.M3_HEAD_H - 1.6, 8.0 + C.M3_HEAD_H + 0.1, segs=6, col="COL_lib")
        U.boolean(h, k)
        return U.union([s, h], "screw")
    return _prim("screw", build)


def insert_mesh():
    """M3 heat-set insert, bottom at the origin, axis +Z."""
    def build():
        o = U.cylinder("insert", 2.3, 0.0, 5.7, segs=32, col="COL_lib")
        U.boolean(o, U.cylinder("insert_bore", 1.25, -1.0, 7.0, segs=24, col="COL_lib"))
        return o
    return _prim("insert", build)


def along(direction):
    """Rotation taking -Z (a screw's travel direction / an insert's push direction) onto `direction`."""
    return Vector((0, 0, -1)).rotation_difference(Vector(direction).normalized()).to_matrix().to_4x4()


# ---------------------------------------------------------------------------
# a step = list of (object, role, matrix) + labels + camera
# ---------------------------------------------------------------------------
class Step:
    def __init__(self, name):
        self.name = name
        self.items = []          # (lib object, role, matrix)
        self.labels = []         # (text, world point)
        self.inline = []         # (text, world point) drawn under the point
        self.cam = (1.0, -0.85, 0.55)
        self.zoom = 1.0
        self.floor = None
        self.lens = 55.0
        self.size = None         # (w, h) override
        self.margin = MARGIN     # label column width each side (0 = labels only inside the picture)

    def add(self, names, role=None, m=I4):
        for n in ([names] if isinstance(names, str) else names):
            self.items.append((lib(n), role or default_role(n), m.copy()))
        return self

    def screw(self, tip, direction, lift=0.0):
        """A screw whose tip sits `lift` mm short of `tip`, travelling along `direction`."""
        d = Vector(direction).normalized()
        self.items.append((screw_mesh(), "steel", T(*(Vector(tip) - d * lift)) @ along(d)))
        return self

    def insert(self, mouth, direction, lift=0.0):
        """An insert about to be pushed along `direction` into a hole whose mouth is at `mouth`."""
        d = Vector(direction).normalized()
        self.items.append((insert_mesh(), "brass", T(*(Vector(mouth) - d * lift)) @ along(d) @ T(0, 0, 0)))
        return self

    def label(self, text, point):
        self.labels.append((text, Vector(point)))
        return self

    def under(self, text, point):
        self.inline.append((text, Vector(point)))
        return self


def centre(name, m=I4):
    o = lib(name)
    cs = [m @ Vector(c) for c in o.bound_box]
    return sum(cs, Vector()) / 8.0


def top_of(name, m=I4):
    o = lib(name)
    cs = [m @ Vector(c) for c in o.bound_box]
    c = sum(cs, Vector()) / 8.0
    return Vector((c.x, c.y, max(p.z for p in cs)))


# ---------------------------------------------------------------------------
# render + callouts
# ---------------------------------------------------------------------------
def _clear(col):
    c = U.collection(col)
    for o in list(c.objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Light):
                bpy.data.lights.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)


def _callouts(img_path, step, cam):
    sc = bpy.context.scene
    img = Image.open(img_path).convert("RGB")
    W, Hh = img.size
    k = 0.6 if DRAFT else 1.0
    MARGIN = int(step.margin * k)
    canvas = Image.new("RGB", (W + 2 * MARGIN, Hh), (246, 246, 244))
    canvas.paste(img, (MARGIN, 0))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, int(22 * k))
    LH = int(28 * k)

    def px(p):
        v = world_to_camera_view(sc, cam, p)
        return MARGIN + v.x * W, (1.0 - v.y) * Hh

    def box(text, x, y, anchor):
        lines = text.split("\n")
        w = max(d.textlength(t, font=f) for t in lines)
        h = LH * len(lines)
        x0 = x - w / 2 if anchor == "c" else (x if anchor == "l" else x - w)
        d.rounded_rectangle((x0 - 8, y - h / 2 - 6, x0 + w + 8, y + h / 2 + 6), 7, fill=(255, 255, 255), outline=(40, 40, 40), width=2)
        for i, t in enumerate(lines):
            d.text((x0, y - h / 2 + LH * i + 1), t, font=f, fill=(15, 15, 15))
        return x0 - 8, x0 + w + 8

    pts = [(text, *px(p)) for text, p in step.labels]
    for side in ("l", "r"):
        col = sorted([q for q in pts if (q[1] < MARGIN + W / 2) == (side == "l")], key=lambda q: q[2])
        if not col:
            continue
        hs = [LH * len(q[0].split("\n")) + int(26 * k) for q in col]
        total = sum(hs)
        y = max(20.0, min(Hh - total - 20.0, sum(q[2] for q in col) / len(col) - total / 2))
        # keep the order of the anchors, spread evenly, never above/below the picture
        ys = []
        for q, hgt in zip(col, hs):
            yc = max(y + hgt / 2, q[2] if not ys else max(q[2], ys[-1][0] + ys[-1][1] / 2 + hgt / 2))
            ys.append((yc, hgt))
            y = yc + hgt / 2
        over = ys[-1][0] + ys[-1][1] / 2 - (Hh - 14)
        if over > 0:
            ys = [(yc - over, hgt) for yc, hgt in ys]
            for i in range(len(ys) - 2, -1, -1):          # push up only where they now overlap
                lim = ys[i + 1][0] - ys[i + 1][1] / 2 - ys[i][1] / 2
                if ys[i][0] > lim:
                    ys[i] = (lim, ys[i][1])
        for (text, ax, ay), (yc, _) in zip(col, ys):
            if side == "l":
                _, x1 = box(text, 16, yc, "l")
                d.line((x1, yc, ax, ay), fill=(20, 20, 20), width=3)
            else:
                x0, _ = box(text, W + 2 * MARGIN - 16, yc, "r")
                d.line((x0, yc, ax, ay), fill=(20, 20, 20), width=3)
            d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), fill=(255, 210, 0), outline=(20, 20, 20), width=2)
    for text, p in step.inline:
        x, y = px(p)
        box(text, x, y + int(26 * k), "c")
    canvas.save(img_path, optimize=True)


def render(step):
    _clear("COL_step")
    _clear("COL_studio")
    objs = []
    for o, role, m in step.items:
        n = o.copy()                       # linked mesh data: cheap
        n.data = o.data.copy()
        n.matrix_world = m
        n.hide_render = False
        U.collection("COL_step").objects.link(n)
        U.set_material(n, mat(role))
        objs.append(n)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    for _, p in step.labels + step.inline:
        pts.append(p)
    bb = (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts),
          min(p.z for p in pts), max(p.z for p in pts))
    floor = step.floor if step.floor is not None else min((o.matrix_world @ Vector(c)).z for o in objs for c in o.bound_box) - 0.05
    S.build(bb, floor)
    # the studio lights are tuned for the whole engine (span ~330 mm): they sit at a distance
    # proportional to the scene, so their power has to follow its square
    span = max(bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4])
    for o in U.collection("COL_studio").objects:
        if o.type == 'LIGHT':
            o.data.energy *= (span / 330.0) ** 2
    cam = S.camera(step.cam, bb, step.zoom, lens=step.lens)
    bpy.context.view_layer.update()
    path = os.path.join(OUT, step.name + ".png")
    size = step.size or SIZE
    if DRAFT:
        size = (int(size[0] * 0.6), int(size[1] * 0.6))
    S.render(path, size=size, samples=SAMPLES)
    _callouts(path, step, cam)
    print("rendered", step.name, flush=True)


# ---------------------------------------------------------------------------
# reusable groups
# ---------------------------------------------------------------------------
def rod_group(c):
    return [f"rod_{c}", f"bearing686_{c}", f"bush_small_{c}"]


def piston_group(c):
    return [f"piston_{c}", f"bush_lug_{c}_0", f"bush_lug_{c}_1", f"wristpin_{c}"]


def throw_group(k):
    """Crankpin k (0-based) with both rings."""
    return [f"crankpin_{k+1}", f"crankpin_ring_{k+1}a", f"crankpin_ring_{k+1}b"]


CRANK = (["main_shaft_front", "end_web_front", "segment_12", "segment_23", "segment_34", "end_web_rear", "main_shaft_rear"]
         + sum((throw_group(k) for k in range(C.N_THROWS)), []))
EVEN = [c for c in range(1, C.N_CYL + 1) if C.cyl_bank(c) == "A"]
ODD = [c for c in range(1, C.N_CYL + 1) if C.cyl_bank(c) == "B"]


def crank_module(s, m=I4, role="old"):
    """Crank + all 8 rods + the bank A pistons (the motion-test state)."""
    s.add(CRANK, role, m)
    for c in range(1, C.N_CYL + 1):
        s.add(f"rod_{c}", role, m)
        s.add([f"bearing686_{c}", f"bush_small_{c}"], None, m)
    for c in EVEN:
        s.add(f"piston_{c}", role, m)
        s.add([f"bush_lug_{c}_0", f"bush_lug_{c}_1", f"wristpin_{c}"], None, m)
    return s


def flange_screw_pts(front=True):
    """(tip point, direction) of the 3 main-shaft flange screws at one end."""
    out = []
    for a in C.SHAFT_FLANGE_BOLT_ANGLES:
        if front:
            y, z = polar(C.SHAFT_FLANGE_PCD / 2, a + C.THROW_PIN_A[0])
            out.append((Vector((C.END_WEB_OUTER_X + DX, y, z)), Vector((-1, 0, 0))))
        else:
            y, z = polar(C.SHAFT_FLANGE_PCD / 2, -a + C.THROW_PIN_B[-1])
            out.append((Vector((-C.END_WEB_OUTER_X + DX, y, z)), Vector((1, 0, 0))))
    return out


def end_plate_screw_pts(front=True):
    out = []
    for y, z in CASE_END_SCREWS + BEAM_END_SCREWS:
        if front:
            out.append((Vector((H + C.SCREW_FLOOR, y, z)), Vector((-1, 0, 0))))
        else:
            out.append((Vector((-H - C.SCREW_FLOOR, -y, z)), Vector((1, 0, 0))))
    return out


def bank_screw_pts():
    pts = [(x, C.BLOCK_SCREW_VALLEY_Y) for x in between_x()] + [(x, C.BLOCK_SCREW_END_Y) for x in end_screws_x()]
    return [(bank_pt(x, y, C.FACE_DIST + C.SCREW_FLOOR), -AXIS_A) for x, y in pts]


def head_screw_pts():
    return [(bank_pt(x, y, C.DECK_DIST + C.SCREW_FLOOR), -AXIS_A) for x in between_x() for y in C.HEAD_SCREW_Y]


# ---------------------------------------------------------------------------
# the steps
# ---------------------------------------------------------------------------
def s00_parts():
    s = Step("00_printed_parts")
    rows = [
        [("01_crankcase", "01 crankcase x1"), ("02_valley_beam", "02 valley beam x1")],
        [("03_cylinder_bank", "03 cylinder bank x1"), ("30_cylinder_head_A", "30 head A x1")],
        [("04_end_plate", "04 end plate x2"), ("05_crank_end_web", "05 end web x2"), ("06_crank_segment_90", "06-90 x1"),
         ("07_crank_segment_180", "07-180 x1"), ("08_crank_segment_270", "08-270 x1"),
         ("T12_crank_knob", "T12 hand knob x1")],
        [("09_conrod", "09 rod x8"), ("10_piston", "10 piston x8"), ("P1_proto_crankpin", "P1 crankpin\nx4"),
         ("P1R_proto_spacer_ring", "P1R ring\nx8"), ("P2P_proto_shaft_plug", "P2P plug\nx2"), ("P2_proto_main_shaft", "P2 rear shaft\n(short) x1"),
         ("P2F_proto_main_shaft_front", "P2F front shaft\n(long) x1")],
    ]
    y = 0.0
    for row in rows:
        sizes = []
        for stem, _ in row:
            o = lib("print:" + stem)
            xs = [c[0] for c in o.bound_box]
            ys = [c[1] for c in o.bound_box]
            zs = [c[2] for c in o.bound_box]
            sizes.append((min(xs), max(xs), min(ys), max(ys), min(zs)))
        depth = max(b[3] - b[2] for b in sizes)
        gap = 45.0 if len(row) < 3 else 72.0
        width = sum(b[1] - b[0] for b in sizes) + gap * (len(row) - 1)
        x = -width / 2
        for (stem, text), b in zip(row, sizes):
            m = T(x - b[0], y - depth / 2 - (b[2] + b[3]) / 2, -b[4])
            s.add("print:" + stem, "new", m)
            s.under(text, Vector((x + (b[1] - b[0]) / 2, y - depth - 4.0, 0.0)))
            x += b[1] - b[0] + gap
        y -= depth + 70.0
    s.cam = (0.0, -0.45, 1.0)
    s.zoom = 1.0
    s.floor = 0.0
    s.margin = 0
    s.size = (1900, 1500)
    return s


def s01_inserts_case():
    s = Step("01_inserts_crankcase_beam")
    s.add("crankcase", "old").add("valley_beam", "old")
    lift = 14.0
    for y, z in CASE_END_SCREWS:
        s.insert((H, y, z), (-1, 0, 0), lift)
    for y, z in BEAM_END_SCREWS:
        s.insert((H, y, z), (-1, 0, 0), lift)
    for bank, axis in (("A", AXIS_A), ("B", Vector((0.0, *polar(1.0, C.BANK_B_ANGLE))))):
        for x in end_screws_x():
            s.insert(bank_pt(x, C.BLOCK_SCREW_END_Y, C.FACE_DIST, bank), -axis, lift)
        for x in between_x():
            s.insert(bank_pt(x, C.BLOCK_SCREW_VALLEY_Y, C.FACE_DIST, bank), -axis, lift)
    s.label("Crankcase front end:\n4 inserts\n(4 more at the rear)", Vector((H + lift, CASE_END_SCREWS[0][0], CASE_END_SCREWS[0][1])))
    s.label("Valley beam front end:\n2 inserts\n(2 more at the rear)", Vector((H + lift, BEAM_END_SCREWS[1][0], BEAM_END_SCREWS[1][1])))
    s.label("Crankcase, sloped top face:\n2 inserts, one near each end", bank_pt(end_screws_x()[0], C.BLOCK_SCREW_END_Y, C.FACE_DIST + lift))
    s.label("Valley beam, sloped side:\n3 inserts", bank_pt(between_x()[1], C.BLOCK_SCREW_VALLEY_Y, C.FACE_DIST + lift))
    s.label("Other side: the same\n(2 in the crankcase,\n3 in the valley beam)", bank_pt(between_x()[1], C.BLOCK_SCREW_VALLEY_Y, C.FACE_DIST + lift, "B"))
    s.label("FRONT", Vector((H, 0.0, C.CASE_FLOOR_Z + 6.0)))
    s.cam = (1.0, -0.8, 0.75)
    return s


def s02_inserts_bank():
    s = Step("02_inserts_bank_deck")
    up = RX(-C.BANK_A_ANGLE) @ T(0, 0, 0)          # bank A axis -> +Z (deck up)
    m = up
    s.add("bank_A", "old", m)
    for x in between_x():
        for y in C.HEAD_SCREW_Y:
            p = m @ bank_pt(x, y, C.DECK_DIST)
            s.insert(p, (0, 0, -1), 14.0)
    p0 = m @ bank_pt(between_x()[0], C.HEAD_SCREW_Y[0], C.DECK_DIST + 14.0)
    s.label("6 inserts in the deck\n(the flat top face),\nbetween the bores", p0)
    s.label("Windows = outer side", m @ bank_pt(C.BANK_A_CYL_X[1], C.BLOCK_Y_OUT, 66.0))
    s.label("Small slots = valley side\n(the rails go here)", m @ bank_pt(C.BANK_A_CYL_X[2], C.RAIL_OFFSET, C.DECK_DIST))
    s.cam = (0.7, -1.0, 0.9)
    return s


def s03_inserts_web():
    s = Step("03_inserts_end_web")
    # front end web, flange face (+X) turned up
    m = RY(-90) @ T(-(C.END_WEB_OUTER_X + DX), 0, 0)
    s.add("end_web_front", "old", m)
    for p, d in flange_screw_pts(True):
        s.insert(m @ p, (0, 0, -1), 12.0)
    q = m @ flange_screw_pts(True)[0][0]
    s.label("3 inserts in the 3 small\nholes of the flat face", q + Vector((0, 0, 12.0)))
    py, pz = polar(C.CRANK_R, C.THROW_PIN_A[0])
    s.label("This bigger hole is for\nthe crankpin screw.\nNo insert here", m @ Vector((C.END_WEB_OUTER_X + DX, py, pz)))
    s.label("Do both end webs\nthe same way", m @ Vector((C.END_WEB_OUTER_X + DX - 6.0, *polar(C.WEB_CW_R - 2.0, C.THROW_PIN_A[0] + 180.0))))
    s.cam = (0.8, -1.0, 1.0)
    s.zoom = 0.8
    return s


def _flat_rod(c):
    """Rod c lying flat, fluted face up, big end at the origin, small end towards +Y."""
    p = pin_c(C.cyl_throw(c))
    xr = cyl_x_pos(c) + DX
    return RY(-90) @ RX(90.0 - rod_angle(c)) @ T(-xr, -p.y, -p.z)


def s04_rod():
    s = Step("04_rod_bearing_bushing")
    c = 2
    m = _flat_rod(c)
    s.add(f"rod_{c}", "old", m)
    s.add(f"bearing686_{c}", None, T(0, 0, 16) @ m)
    s.add(f"bush_small_{c}", None, T(0, 0, 14) @ m)
    s.label("686 bearing:\nclamp it in, flush\nwith both faces", top_of(f"bearing686_{c}", T(0, 0, 16) @ m))
    s.label("Bronze bushing: thin ring of\nsuper glue round its MIDDLE,\npush in from the grooved side,\ncentre it, wipe off extra glue", top_of(f"bush_small_{c}", T(0, 0, 14) @ m))
    s.label("09 con-rod, groove side up", centre(f"rod_{c}", m))
    s.cam = (0.9, -1.0, 0.85)
    s.zoom = 1.15
    return s


def _upright(c):
    """Piston c upright (bank axis -> +Z), wrist pin at the origin."""
    w = wrist(c)
    return RX(-C.bank_angle(C.cyl_bank(c))) @ T(-w.x, -w.y, -w.z)


def s05_piston():
    s = Step("05_piston_bushings")
    c = 2
    m = _upright(c)
    s.add(f"piston_{c}", "old", m)
    s.add(f"bush_lug_{c}_0", None, T(0, 0, 14) @ m)
    s.add(f"bush_lug_{c}_1", None, T(0, 0, -14) @ m)
    s.label("Bushing 1: glue on its middle,\npush in from the top, flush", centre(f"bush_lug_{c}_0", T(0, 0, 14) @ m))
    s.label("Bushing 2: same, from\nthe bottom, flush", centre(f"bush_lug_{c}_1", T(0, 0, -14) @ m))
    s.label("10 piston", m @ (wrist(c) + Vector((C.PISTON_DIA / 2, 0, 0))))
    s.label("Guide lug (the small\ntube on the side)", m @ (wrist(c) + BANK_A @ Vector((0, C.RAIL_OFFSET, 5.0))))
    s.cam = (1.0, 0.75, 0.55)
    s.zoom = 1.0
    s.floor = -40.0
    return s


def s06_piston_on_rod():
    s = Step("06_piston_on_rod")
    c = 2
    m = _upright(c)
    s.add(f"piston_{c}", "old", m)
    s.add([f"bush_lug_{c}_0", f"bush_lug_{c}_1"], None, m)
    s.add(f"rod_{c}", "old", m)
    s.add([f"bearing686_{c}", f"bush_small_{c}"], None, m)
    s.add(f"wristpin_{c}", None, T(34, 0, 0) @ m)
    s.label("3 x 20 mm dowel pin (wrist pin):\nthrough the piston, the rod's\nbushing, and the piston again", centre(f"wristpin_{c}", T(34, 0, 0) @ m))
    s.label("Pin ends up 12 mm deep\non both sides (centred)", m @ (wrist(c) + Vector((C.PISTON_DIA / 2, 0, 0))))
    s.label("Rod small end sits\nbetween the two bosses", m @ (wrist(c) + Vector((0, 0, 0)) - AXIS_A * 9.0))
    s.label("Guide lug: this side will face\nthe MIDDLE of the engine", m @ (wrist(c) + BANK_A @ Vector((0, C.RAIL_OFFSET, C.LUG_TOP))))
    s.cam = (1.0, -0.55, 0.38)
    s.zoom = 1.05
    return s


def s07_pin_loading():
    s = Step("07_crankpin_loading")
    k = 0
    s.add(f"crankpin_{k+1}", "new")
    for c, dx in ((1, 17.0), (2, -17.0)):
        s.add(f"rod_{c}", "old", T(dx, 0, 0))
        s.add([f"bearing686_{c}", f"bush_small_{c}"], None, T(dx, 0, 0))
    s.add(f"crankpin_ring_{k+1}a", "new", T(31.0, 0, 0))
    s.add(f"crankpin_ring_{k+1}b", "new", T(-31.0, 0, 0))
    p = pin_c(k)
    s.label("P1 crankpin", p + Vector((0, 0, 3.5)))
    s.label("Front rod (odd cylinder)\nslides on first...", centre("bearing686_1", T(17.0, 0, 0)) + Vector((0, 0, 9.5)))
    s.label("...then a P1R ring", centre(f"crankpin_ring_{k+1}a", T(31.0, 0, 0)))
    s.label("Rear rod (even cylinder)", centre("bearing686_2", T(-17.0, 0, 0)) + Vector((0, 0, 9.5)))
    s.label("P1R ring", centre(f"crankpin_ring_{k+1}b", T(-31.0, 0, 0)))
    s.label("Flat on each pin end", p + Vector((C.PIN_LEN / 2 - 3.0, *polar(3.0, C.THROW_PIN_A[k]))))
    s.cam = (0.3, -1.0, 0.45)
    s.zoom = 1.1
    return s


def _exploded_crank(gap):
    """[(names, x offset, role)] for the crank chain spread along X, front first."""
    groups = [["main_shaft_front"], ["end_web_front"]]
    segs = ["segment_12", "segment_23", "segment_34"]
    for k in range(C.N_THROWS):
        groups.append(throw_group(k) + rod_group(2 * k + 1) + rod_group(2 * k + 2))
        groups.append([segs[k]] if k < len(segs) else ["end_web_rear"])
    groups.append(["main_shaft_rear"])
    mid = (len(groups) - 1) / 2
    return [(g, (mid - i) * gap) for i, g in enumerate(groups)]


def s08_crank_exploded():
    s = Step("08_crank_order")
    names = ["P2F front shaft\n(the long one)", "05 end web", "Pin 1:\nrods 1 + 2", "06-90", "Pin 2:\nrods 3 + 4", "07-180",
             "Pin 3:\nrods 5 + 6", "08-270", "Pin 4:\nrods 7 + 8", "05 end web", "P2 rear shaft\n(the short one)"]
    for i, ((g, dx), text) in enumerate(zip(_exploded_crank(30.0), names)):
        m = T(dx, 0, 0)
        for n in g:
            if n.startswith(("rod_",)):
                s.add(n, "dark", m)
            elif n.startswith(("bearing", "bush")):
                s.add(n, None, m)
            else:
                s.add(n, "new" if n.startswith("segment") else "old", m)
        cx = centre(g[0], m).x
        s.under(text, Vector((cx, 0.0, -34.0 if i % 2 == 0 else -62.0)))
    s.under("FRONT  >>>", Vector((centre("main_shaft_front", T(5 * 30.0, 0, 0)).x - 12.0, 0, 44.0)))
    s.under("<<<  REAR", Vector((centre("main_shaft_rear", T(-5 * 30.0, 0, 0)).x + 12.0, 0, 44.0)))
    s.cam = (0.10, -1.0, 0.30)
    s.zoom = 1.12
    s.floor = -95.0
    s.margin = 0
    s.size = (2000, 900)
    return s


def s09_joint():
    s = Step("09_crank_joint")
    # segment 06-90 with pin 2 going into its rear (engraved) face, screw from the front face.
    # The rods and rings that are on the pin by now are left out so the joint can be seen.
    k = 1
    s.add("segment_12", "old")
    pull = T(-24.0, 0, 0)
    s.add(f"crankpin_{k+1}", "new", pull)
    p = pin_c(k)
    x_front = C.THROW_X[0] - C.THROW_INNER / 2 + DX
    x_rear = x_front - C.SEGMENT_LEN
    s.screw((x_front - C.WEB_T + 2.0, p.y, p.z), (-1, 0, 0), 36.0)
    s.label("M3 x 8 screw: down the round\nhole in the FRONT face,\ninto the end of the pin", Vector((x_front + 36.0 - 2.0, p.y, p.z)))
    s.label("Crankpin: presses into the\nD-shaped hole in the REAR face", centre(f"crankpin_{k+1}", pull))
    s.label("REAR face = the face with\nthe engraved number", Vector((x_rear, *polar(C.WEB_HUB_R - 4.0, C.THROW_PIN_A[1] + 180.0))))
    s.label("Flat on the pin end faces\nAWAY from the middle\nof the crank", p + Vector((-24.0 + C.PIN_LEN / 2 - 2.0, *polar(3.0, C.THROW_PIN_A[k]))))
    s.label("(rods and rings on the pin\nare not drawn here)", centre(f"crankpin_{k+1}", pull) + Vector((-C.PIN_LEN / 2, 0, 0)))
    s.cam = (-0.42, -1.0, 0.75)
    s.zoom = 1.0
    return s


def s10_crank_done():
    s = Step("10_crank_assembled")
    s.add(CRANK, "old")
    for c in range(1, C.N_CYL + 1):
        s.add(f"rod_{c}", "dark")
        s.add([f"bearing686_{c}", f"bush_small_{c}"], None)
    for p, d in flange_screw_pts(True):
        s.screw(p + Vector((C.SHAFT_FLANGE_T, 0, 0)), d, 16.0)
    s.label("3 screws through the flange\ninto the end web inserts\n(3 more at the rear)", flange_screw_pts(True)[0][0] + Vector((C.SHAFT_FLANGE_T + 22.0, 0, 0)))
    s.label("FRONT:\nlong shaft", Vector((C.SHAFT_END_X_FRONT + DX, 0, 0)))
    s.label("REAR:\nshort shaft", Vector((-C.SHAFT_END_X + DX, 0, 0)))
    for k, t in enumerate(("06-90", "07-180", "08-270")):
        s.label(t, Vector((C.THROW_X[k] - C.CYL_PITCH / 2 + DX, 0, C.JOURNAL_R)))
    s.label("Rods 1, 3, 5, 7 point to one side,\n2, 4, 6, 8 to the other", centre("bush_small_7"))
    s.cam = (0.45, -1.0, 0.55)
    s.zoom = 1.35
    return s


def s11_into_case():
    s = Step("11_crank_into_crankcase")
    s.add("crankcase", "old")
    crank_module(s, T(0, 0, 85.0), "new")
    s.label("Lower the crank straight down\ninto the open top", Vector((0.0, 0.0, 85.0 + C.JOURNAL_R)))
    s.label("Bank A pistons (2, 4, 6, 8)\nhang out on this side", wrist(6) + Vector((0, 0, 85.0)))
    s.label("Bare rods (1, 3, 5, 7)\nstick out on the other side", wrist(3) + Vector((0, 0, 85.0)))
    s.label("01 crankcase", Vector((H, CASE_END_SCREWS[0][0], CASE_END_SCREWS[0][1])))
    s.label("FRONT", Vector((H, 0.0, C.CASE_FLOOR_Z + 5.0)))
    s.cam = (1.0, -0.85, 0.5)
    return s


def s12_beam():
    s = Step("12_valley_beam")
    s.add("crankcase", "old")
    crank_module(s)
    s.add("valley_beam", "new", T(150.0, 0, 0))
    s.label("02 valley beam slides in\nfrom the FRONT, between\nthe two rows of rods", Vector((150.0 + H, 0.0, 40.0)))
    s.label("Push until it is flush\nwith both ends", Vector((H, 20.0, 30.0)))
    s.cam = (1.0, -0.85, 0.6)
    return s


def s13_end_plates():
    s = Step("13_end_plates")
    s.add(["crankcase", "valley_beam"], "old")
    crank_module(s)
    s.add("end_plate_front", "new", T(62.0, 0, 0))
    s.add("bearing608_front", None, T(34.0, 0, 0))
    s.add("end_plate_rear", "new", T(-62.0, 0, 0))
    s.add("bearing608_rear", None, T(-34.0, 0, 0))
    for p, d in end_plate_screw_pts(True):
        s.screw(p + Vector((62.0, 0, 0)), d, 30.0)
    for p, d in end_plate_screw_pts(False):
        s.screw(p + Vector((-62.0, 0, 0)), d, 30.0)
    s.label("608 bearing: press it into the\nINSIDE of the end plate first", centre("bearing608_front", T(34.0, 0, 0)) + Vector((0, 0, 11.0)))
    s.label("04 end plate", Vector((C.END_PLATE_OUTER_X + 62.0, -30.0, 20.0)))
    s.label("6 screws per plate:\n4 into the crankcase,\n2 into the valley beam", end_plate_screw_pts(True)[0][0] + Vector((62.0 + 30.0, 0, 0)))
    s.label("Same at the rear", Vector((-C.END_PLATE_OUTER_X - 62.0, 30.0, 30.0)))
    s.cam = (1.0, -0.9, 0.45)
    s.zoom = 1.05
    return s


def _core_in_case(s):
    s.add(["crankcase", "valley_beam", "end_plate_front", "end_plate_rear"], "old")
    s.add(["bearing608_front", "bearing608_rear"])
    crank_module(s)
    return s


def s14_bank():
    s = Step("14_bank_A")
    _core_in_case(s)
    lift = AXIS_A * 62.0
    s.add("bank_A", "new", T(*lift))
    for p, d in bank_screw_pts():
        s.screw(p + lift, d, 62.0)
    s.label("03 cylinder bank: lower it straight\ndown the line of the pistons", bank_pt(C.BANK_A_CYL_X[0], C.BLOCK_Y_OUT, 70.0) + lift)
    s.label("5 screws from the top:\n3 on the valley side,\n2 near the ends", bank_screw_pts()[1][0] + lift + AXIS_A * (62.0 + 11.0))
    s.label("Each piston goes up\ninto its own bore", wrist(4) + AXIS_A * C.PISTON_PIN_TO_CROWN)
    s.label("FRONT", Vector((C.END_PLATE_OUTER_X, 0.0, C.CASE_FLOOR_Z + 5.0)))
    s.cam = (0.8, -1.0, 0.7)
    return s


def s15_rails():
    s = Step("15_rails")
    _core_in_case(s)
    s.add("bank_A", "old")
    for p, d in bank_screw_pts():
        s.screw(p, d, 0.0)
    lift = AXIS_A * 52.0
    for c in EVEN:
        s.add(f"rail_{c}", None, T(*lift))
    s.label("4 rails (3 mm rod, 60 mm long):\ndrop each one into the small slot,\nthrough the piston's two bushings,\ndown into the valley beam",
            bank_pt(cyl_x_pos(2), C.RAIL_OFFSET, C.RAIL_TOP) + lift)
    s.label("Each rail ends up 3 mm\nabove the flat top", bank_pt(cyl_x_pos(8), C.RAIL_OFFSET, C.DECK_DIST))
    s.label("One drop of light oil\non each rail", bank_pt(cyl_x_pos(6), C.RAIL_OFFSET, C.RAIL_TOP - 20.0) + lift)
    s.cam = (0.9, -0.3, 0.8)
    s.zoom = 1.1
    return s


def s16_head():
    s = Step("16_head_A")
    _core_in_case(s)
    s.add("bank_A", "old")
    for c in EVEN:
        s.add(f"rail_{c}")
    lift = AXIS_A * 48.0
    s.add("head_A", "new", T(*lift))
    for p, d in head_screw_pts():
        s.screw(p + lift, d, 40.0)
    s.label("30 head A: the 4 rail tops\ngo into 4 small holes\nunder the head", bank_pt(C.BANK_A_CYL_X[0], C.BLOCK_Y_OUT, C.DECK_DIST + 14.0) + lift)
    s.label("6 screws down through\nthe head into the bank", head_screw_pts()[2][0] + lift + AXIS_A * (40.0 + 11.0))
    s.cam = (0.8, -1.0, 0.7)
    return s


def s17_done():
    s = Step("17_motion_test_done")
    _core_in_case(s)
    s.add(["bank_A", "head_A"], "old")
    for c in EVEN:
        s.add(f"rail_{c}")
    s.add("print:T12_crank_knob", "new", knob_matrix())
    s.label("Turn the crank with\nthe T12 hand knob", Vector((C.SHAFT_END_X_FRONT + DX, 0, 23.0)))
    s.label("Watch the pistons\nthrough the windows", bank_pt(C.BANK_A_CYL_X[1], C.BLOCK_Y_OUT, 66.0))
    s.label("Bare rods 1, 3, 5, 7 lean on\nthe edge of this slot until\nbank B is printed", wrist(1))
    s.cam = (0.6, -1.0, 0.3)
    s.zoom = 1.15
    return s


def knob_matrix():
    """T12 knob (print orientation: disc down, bore up) on the front shaft, disc outwards."""
    o = lib("print:T12_crank_knob")
    xs = [c[0] for c in o.bound_box]
    ys = [c[1] for c in o.bound_box]
    centre_xy = T(-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, 0)
    return T(C.SHAFT_END_X_FRONT + DX + 1.6, 0, 0) @ RY(-90) @ centre_xy


def s18_shaft_plug():
    s = Step("18_shaft_plug")
    s.add("end_web_front", "old")
    # the printed shaft has a socket instead of the spigot: draw the production shaft mesh
    # pulled forward, and the loose plug between it and the web
    s.add("main_shaft_front", "new", T(30.0, 0, 0))
    plug = lib("print:P2P_proto_shaft_plug")
    zs = [c[2] for c in plug.bound_box]
    pm = T(C.END_WEB_OUTER_X + DX + 13.0, 0, 0) @ RY(90) @ T(0, 0, -(min(zs) + max(zs)) / 2)
    s.add("print:P2P_proto_shaft_plug", "new", pm)
    for p, d in flange_screw_pts(True):
        s.screw(p + Vector((C.SHAFT_FLANGE_T + 30.0, 0, 0)), d, 20.0)
    s.label("P2P plug: half goes in the\ncentre hole of the end web,\nhalf in the hole in the shaft", Vector((C.END_WEB_OUTER_X + DX + 13.0, 0, 0)))
    s.label("P2F front shaft", Vector((C.SHAFT_END_X_FRONT + DX + 30.0 - 12.0, 0, 4.0)))
    s.label("3 screws through the flange\ninto the 3 inserts", flange_screw_pts(True)[0][0] + Vector((C.SHAFT_FLANGE_T + 30.0 + 26.0, 0, 0)))
    py, pz = polar(C.CRANK_R, C.THROW_PIN_A[0])
    s.label("The notch in the flange goes\nover the crankpin screw", Vector((C.END_WEB_OUTER_X + DX + 30.0 + C.SHAFT_FLANGE_T, py, pz)))
    s.label("05 end web\n(insert face)", Vector((C.END_WEB_OUTER_X + DX, *polar(C.WEB_CW_R - 3.0, C.THROW_PIN_A[0] + 180.0))))
    s.cam = (0.8, -1.0, 0.5)
    s.zoom = 0.95
    return s


def _all_in_case(s, bank_b_role="old", lift_b=Vector((0, 0, 0))):
    """Both banks' pistons on their rods; bank A complete."""
    _core_in_case(s)
    s.add(["bank_A", "head_A"], "old")
    for c in EVEN:
        s.add(f"rail_{c}")
    for c in ODD:
        s.add(f"piston_{c}", bank_b_role)
        s.add([f"bush_lug_{c}_0", f"bush_lug_{c}_1", f"wristpin_{c}"])
    return s


def s19_bank_b():
    s = Step("19_bank_B")
    _all_in_case(s, "new")
    axis_b = Vector((0.0, *polar(1.0, C.BANK_B_ANGLE)))
    lift = axis_b * 62.0
    s.add("bank_B", "new", T(*lift))
    pts = [(x, C.BLOCK_SCREW_VALLEY_Y) for x in between_x()] + [(x, C.BLOCK_SCREW_END_Y) for x in end_screws_x()]
    for x, y in pts:
        s.screw(bank_pt(x, y, C.FACE_DIST + C.SCREW_FLOOR, "B") + lift, -axis_b, 62.0)
    s.label("Second 03 bank: lower it over\npistons 1, 3, 5, 7", bank_pt(C.BANK_A_CYL_X[-1], C.BLOCK_Y_OUT, 70.0, "B") + lift)
    s.label("5 screws, same as bank A", bank_pt(between_x()[1], C.BLOCK_SCREW_VALLEY_Y, C.FACE_DIST + C.SCREW_FLOOR + 11.0, "B") + lift + axis_b * 62.0)
    s.label("Pistons go on rods\n1, 3, 5, 7 first", wrist(3) + axis_b * C.PISTON_PIN_TO_CROWN)
    s.label("Bank A is already done", bank_pt(C.BANK_A_CYL_X[1], C.HEAD_SCREW_Y[0], C.DECK_DIST + C.HEAD_H))
    s.cam = (0.8, 1.0, 0.7)
    return s


def s20_all_eight():
    s = Step("20_all_eight")
    _all_in_case(s)
    s.add(["bank_B", "head_B"], "old")
    for c in ODD:
        s.add(f"rail_{c}")
    s.add("print:T12_crank_knob", "new", knob_matrix())
    s.label("T12 hand knob on the front shaft:\nturn the crank with it", Vector((C.SHAFT_END_X_FRONT + DX, 0, 23.0)))
    s.label("Bank A: cylinders 2, 4, 6, 8", bank_pt(C.BANK_A_CYL_X[1], C.BLOCK_Y_OUT, 66.0))
    s.label("Bank B: cylinders 1, 3, 5, 7", bank_pt(C.BANK_A_CYL_X[1], C.HEAD_SCREW_Y[0], C.DECK_DIST + C.HEAD_H, "B"))
    s.cam = (1.0, -0.75, 0.45)
    s.zoom = 1.1
    return s


# ---------------------------------------------------------------------------
# part tour: what each part is and which face is which
# ---------------------------------------------------------------------------
FLIP = RX(180.0)


def s30_crankcase_under():
    s = Step("p1_crankcase_underside")
    s.add("crankcase", "new", FLIP)
    hx = C.HALL_X + 1.3
    s.label("REAR: this small pocket is\nunder the REAR end only", FLIP @ Vector((hx, 0.0, C.CASE_FLOOR_Z)))
    s.label("4 holes underneath: screws\nfrom the oil pan go in here\n(later, not for the motion test)", FLIP @ Vector((94.0, 40.0, C.CASE_FLOOR_Z)))
    s.label("FRONT end", FLIP @ Vector((H, 0.0, C.CASE_FLOOR_Z + 12.0)))
    s.label("Crankcase turned upside down:\nthis flat face is its BOTTOM", FLIP @ Vector((0.0, -30.0, C.CASE_FLOOR_Z)))
    s.cam = (-0.55, -0.8, 1.0)
    s.zoom = 1.05
    return s


def s31_beam_faces():
    s = Step("p2_valley_beam_holes")
    s.add("valley_beam", "new")
    xs = C.BANK_A_CYL_X
    s.label("4 SMALLEST holes (3 mm):\nthe rails go in here", bank_pt(xs[1], C.RAIL_OFFSET, C.FACE_DIST))
    s.label("3 medium holes:\nheat inserts", bank_pt(between_x()[1], C.BLOCK_SCREW_VALLEY_Y, C.FACE_DIST))
    s.label("2 big holes, one near each end:\nthe bank's pegs drop in here", bank_pt(xs[0] + 18.0, C.LOCATOR_Y, C.FACE_DIST))
    s.label("The other sloped side has\nthe same holes", bank_pt(xs[3], C.RAIL_OFFSET, C.FACE_DIST, "B"))
    s.cam = tuple(AXIS_A * 1.0 + Vector((0.75, 0.0, 0.3)))
    s.zoom = 1.0
    return s


def s32_bank_under():
    s = Step("p3_bank_underside")
    m = FLIP @ RX(-C.BANK_A_ANGLE)
    s.add("bank_A", "new", m)
    xs = C.BANK_A_CYL_X
    s.label("2 PEGS: this is the BOTTOM.\nIt sits on the crankcase", m @ bank_pt(xs[0] + 18.0, C.LOCATOR_Y, C.FACE_DIST - C.LOCATOR_H))
    s.label("Bores: the pistons come up\nthrough here (chamfered edge\nhelps them find the way in)", m @ bank_pt(xs[2], -12.0, C.FACE_DIST))
    s.label("Screw holes come out here\n(the screws go in from the TOP)", m @ bank_pt(between_x()[0], C.BLOCK_SCREW_VALLEY_Y, C.FACE_DIST))
    s.label("Windows: this side faces OUT", m @ bank_pt(xs[1], C.BLOCK_Y_OUT, 66.0))
    s.label("Lug slots: the rails\nrun up through these", m @ bank_pt(xs[3], C.RAIL_OFFSET, C.FACE_DIST))
    s.cam = (0.55, -1.0, 0.95)
    return s


def s33_head_under():
    s = Step("p4_head_underside")
    m = FLIP @ RX(-C.BANK_A_ANGLE)
    s.add("head_A", "new", m)
    xs = C.BANK_A_CYL_X
    s.label("4 small holes: the rail tops\nfit in here (fits one way only)", m @ bank_pt(xs[1], C.RAIL_OFFSET, C.DECK_DIST))
    s.label("6 screw holes go right\nthrough the head", m @ bank_pt(between_x()[1], C.HEAD_SCREW_Y[0], C.DECK_DIST))
    s.label("Long groove: for LED strips\n(not used, leave it empty)", m @ bank_pt(xs[2], 0.0, C.DECK_DIST))
    s.label("Head turned upside down: this\nflat face sits on the bank's top", m @ bank_pt(xs[3], -25.0, C.DECK_DIST))
    s.cam = (0.55, -1.0, 0.95)
    return s


def _turn_z(c, dy):
    return T(0, dy, 0) @ T(*c) @ RZ(180) @ T(*(-c))


def s34_segment_faces():
    s = Step("p5_segment_faces")
    xf = C.THROW_X[0] - C.THROW_INNER / 2 + DX
    xr = xf - C.SEGMENT_LEN
    c = Vector(((xf + xr) / 2, 0, 0))
    mf = T(0, -34.0, 0)
    mr = _turn_z(c, 34.0)
    s.add("segment_12", "new", mf).add("segment_12", "new", mr)
    s.label("FRONT face (no number)", mf @ Vector((xf, *polar(C.WEB_HUB_R - 3.0, C.THROW_PIN_A[0] + 180.0))))
    s.label("D-shaped hole with ribs inside:\na crankpin is pressed in here", mf @ Vector((xf, *polar(C.CRANK_R, C.THROW_PIN_A[0]))))
    s.label("Round hole: a screw goes down it\ninto the pin held by the OTHER face", mf @ Vector((xf, *polar(C.CRANK_R, C.THROW_PIN_A[1]))))
    s.label("REAR face: has the\nengraved number (06-90)", mr @ Vector((xr, 0.0, 0.0)))
    s.label("Every segment has one D-hole\nand one round hole on EACH face", mr @ Vector((xr, *polar(C.CRANK_R, C.THROW_PIN_A[1]))))
    s.cam = (1.0, 0.0, 0.42)
    s.zoom = 1.0
    return s


def s35_end_web_faces():
    s = Step("p6_end_web_faces")
    xt = C.WEB_FACE_X + DX
    xo = C.END_WEB_OUTER_X + DX
    c = Vector(((xt + xo) / 2, 0, 0))
    mo = T(0, -30.0, 0)
    mt = _turn_z(c, 30.0)
    s.add("end_web_front", "new", mo).add("end_web_front", "new", mt)
    a0 = C.THROW_PIN_A[0]
    s.label("INSERT face: the 3 small holes\nget heat inserts (shaft screws)", mo @ Vector((xo, *polar(C.SHAFT_FLANGE_PCD / 2, C.SHAFT_FLANGE_BOLT_ANGLES[1] + a0))))
    s.label("Bigger hole: the crankpin\nscrew goes through it", mo @ Vector((xo, *polar(C.CRANK_R, a0))))
    s.label("Centre hole: the shaft's\nplug (P2P) fits in here", mo @ Vector((xo, 0.0, 0.0)))
    s.label("Other face: D-shaped hole\nfor the crankpin", mt @ Vector((xt, *polar(C.CRANK_R, a0))))
    s.cam = (1.0, 0.0, 0.42)
    s.zoom = 0.95
    return s


def s36_small_parts():
    s = Step("p7_small_parts")
    lay = RY(90.0)
    rail_flat = RY(90.0) @ RX(-C.BANK_A_ANGLE)
    rows = [
        [("print:09_conrod", I4, "09 con-rod x8\ngrooved side up"), ("print:10_piston", FLIP, "10 piston x8\nlug = small tube"),
         ("print:T12_crank_knob", I4, "T12 hand knob")],
        [("print:P2F_proto_main_shaft_front", lay, "P2F front shaft\n(the LONG one)"), ("print:P2_proto_main_shaft", lay, "P2 rear shaft\n(the short one)"),
         ("print:P2P_proto_shaft_plug", I4, "P2P plug x2"), ("rail_2", rail_flat, "rail 3 x 60\nx4 (8 later)")],
        [("print:P1_proto_crankpin", lay, "P1 crankpin x4\nflat on each end"), ("print:P1R_proto_spacer_ring", I4, "P1R ring x8\n0.75 mm thin")],
    ]
    roles = {"rail_2": "steel", "wristpin_2": "steel", "bush_small_2": "bronze", "bearing686_1": "steel", "bearing608_front": "steel"}
    y = 0.0
    for row in rows:
        objs = []
        for name, rot, text in row:
            o = lib(name) if isinstance(name, str) else name
            pts = [rot @ Vector(c) for c in o.bound_box]
            b = (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts), min(p.z for p in pts))
            role = "brass" if not isinstance(name, str) and o is LIB.get("insert") else ("steel" if not isinstance(name, str) else roles.get(name, "new"))
            objs.append((o, rot, text, b, role))
        depth = max(b[3] - b[2] for *_, b, _ in objs)
        gap = 38.0
        width = sum(b[1] - b[0] for *_, b, _ in objs) + gap * (len(objs) - 1)
        x = -width / 2
        for o, rot, text, b, role in objs:
            m = T(x - b[0], y - depth / 2 - (b[2] + b[3]) / 2, -b[4]) @ rot
            s.items.append((o, role, m))
            s.under(text, Vector((x + (b[1] - b[0]) / 2, y - depth - 3.0, 0.0)))
            x += b[1] - b[0] + gap
        y -= depth + 58.0
    s.cam = (0.0, -0.42, 1.0)
    s.floor = 0.0
    s.margin = 0
    s.size = (1900, 1400)
    return s


def s37_hardware():
    s = Step("p8_hardware")
    flat = RY(90.0)                       # bearing / pin axis X -> Z: lying flat
    items = [("wristpin_2", RZ(90.0), "steel", "dowel pin 3 x 20\n= wrist pin (x4)"),
             ("bush_small_2", flat, "bronze", "bronze bushing\n3 x 5 x 4 (x16)"),
             ("bearing686_1", flat, "steel", "686 bearing\nsmall (x8)"),
             ("bearing608_front", flat, "steel", "608 bearing\nbig (x2)"),
             (insert_mesh(), I4, "brass", "M3 heat\ninsert (x35)"),
             (screw_mesh(), I4, "steel", "M3 x 8\nscrew (x38)")]
    x = 0.0
    for name, rot, role, text in items:
        o = lib(name) if isinstance(name, str) else name
        pts = [rot @ Vector(c) for c in o.bound_box]
        b = (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts), min(p.z for p in pts))
        m = T(x - b[0], -(b[2] + b[3]) / 2, -b[4]) @ rot
        s.items.append((o, role, m))
        s.under(text, Vector((x + (b[1] - b[0]) / 2, -13.0, 0.0)))
        x += b[1] - b[0] + 14.0
    s.cam = (0.0, -0.75, 1.0)
    s.floor = 0.0
    s.margin = 0
    s.size = (1900, 900)
    return s


STEPS = [s00_parts, s01_inserts_case, s02_inserts_bank, s03_inserts_web, s04_rod, s05_piston, s06_piston_on_rod,
         s07_pin_loading, s08_crank_exploded, s09_joint, s10_crank_done, s11_into_case, s12_beam, s13_end_plates,
         s14_bank, s15_rails, s16_head, s17_done, s18_shaft_plug, s19_bank_b, s20_all_eight,
         s30_crankcase_under, s31_beam_faces, s32_bank_under, s33_head_under, s34_segment_faces, s35_end_web_faces, s36_small_parts, s37_hardware]


def main():
    global SAMPLES, DRAFT
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated step numbers, e.g. 07,08")
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    if a.draft:
        SAMPLES, DRAFT = 12, True
    os.makedirs(OUT, exist_ok=True)
    U.reset_scene()
    only = set(a.only.split(",")) if a.only else None
    for fn in STEPS:
        num = fn.__name__[1:3]
        if only and num not in only:
            continue
        render(fn())


if __name__ == "__main__":
    main()
