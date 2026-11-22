"""Pictures of the V8 controller PCB: realistic top / bottom artwork (from the Gerber
layers) and a 3D preview with stand-in parts at their real positions (KiCad's 3D part
models are not installed here, so the parts are simple shapes of the right size).

    tools/pcb/render_pcb.sh            (exports the layers with kicad-cli, then runs this
                                        with python3.13 + bpy)
Writes pcb/img/board_top.png, board_bottom.png, pcb_3d.png, pcb_3d_angle.png.
"""
import json
import math
import os
import sys

import bpy
from PIL import Image, ImageChops, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
from skin import bpyutil as U, materials as M, studio as S  # noqa: E402

PCB = os.path.join(ROOT, "pcb")
IMG = os.path.join(PCB, "img")
LAYERS = sys.argv[-1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]) else os.path.join(PCB, "layers")
W, H = 90.0, 70.0
PX = 1800                                     # artwork width in pixels


def layer(name):
    import cairosvg  # noqa: PLC0415
    png = os.path.join(LAYERS, name + ".png")
    cairosvg.svg2png(url=os.path.join(LAYERS, name + ".svg"), write_to=png, output_width=PX, background_color="white")
    im = ImageOps.invert(Image.open(png).convert("L"))      # copper / silk / opening = white
    return im.point(lambda v: 255 if v > 90 else 0)


def artwork(side):
    cu, silk, mask = layer(f"{side}.Cu"), layer(f"{side}.SilkS"), layer(f"{side}.Mask")
    size = cu.size
    edge = Image.new("L", size, 0)
    # the exported page is the board outline; the outline itself is in every layer: drop a 6 px rim
    edge.paste(255, (6, 6, size[0] - 6, size[1] - 6))
    base = Image.new("RGB", size, (14, 74, 38))                  # solder mask green over bare board
    under = Image.new("RGB", size, (30, 112, 56))                # mask over copper: lighter green
    base.paste(under, mask=cu)
    gold = Image.new("RGB", size, (214, 176, 92))                # ENIG / HASL pads where the mask opens
    base.paste(gold, mask=ImageChops.multiply(mask, cu))
    holes = ImageChops.subtract(mask, cu)                        # mask opening with no copper = drill hole
    base.paste((25, 25, 25), mask=holes)
    base.paste((245, 245, 240), mask=ImageChops.subtract(silk, mask))
    out = Image.new("RGB", size, (40, 40, 40))
    out.paste(base, mask=edge)
    if side == "B":
        out = ImageOps.mirror(out)
    return out


def main():
    os.makedirs(IMG, exist_ok=True)
    top, bot = artwork("F"), artwork("B")
    top.save(os.path.join(IMG, "board_top.png"))
    bot.save(os.path.join(IMG, "board_bottom.png"))
    parts = json.load(open(os.path.join(PCB, "footprints.json")))

    U.reset_scene()
    P = M._principled
    mats = dict(
        black=P("pcb_black", (0.02, 0.02, 0.022), roughness=0.45),
        esp=P("pcb_esp", (0.02, 0.02, 0.025), roughness=0.4),
        shield=P("pcb_shield", (0.75, 0.75, 0.78), metallic=1.0, roughness=0.3),
        tmc=P("pcb_tmc", (0.55, 0.05, 0.08), roughness=0.45),
        heatsink=P("pcb_hs", (0.15, 0.15, 0.17), metallic=1.0, roughness=0.4),
        pololu=P("pcb_pololu", (0.03, 0.12, 0.45), roughness=0.45),
        jst=P("pcb_jst", (0.92, 0.9, 0.82), roughness=0.6),
        cap=P("pcb_cap", (0.04, 0.06, 0.25), roughness=0.4),
        captop=P("pcb_captop", (0.7, 0.72, 0.75), metallic=1.0, roughness=0.35),
        res=P("pcb_res", (0.82, 0.72, 0.52), roughness=0.55),
        disc=P("pcb_disc", (0.95, 0.65, 0.12), roughness=0.5),
        fuse=P("pcb_fuse", (0.9, 0.75, 0.1), roughness=0.5),
        band=P("pcb_band", (0.8, 0.8, 0.8), roughness=0.5),
        pin=P("pcb_pin", (0.8, 0.7, 0.4), metallic=1.0, roughness=0.3),
    )

    def tex_mat(name, path):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Roughness"].default_value = 0.35
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path)
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        return m

    # board: top and bottom faces carry the artwork; KiCad y runs down, Blender y up
    bpy.ops.mesh.primitive_plane_add(size=1)
    topf = bpy.context.object
    topf.scale = (W, H, 1)
    topf.location = (W / 2, -H / 2, 1.6)
    topf.data.materials.append(tex_mat("pcb_top", os.path.join(IMG, "board_top.png")))
    bpy.ops.mesh.primitive_plane_add(size=1)
    botf = bpy.context.object
    botf.scale = (W, H, 1)
    botf.rotation_euler = (math.pi, 0, 0)
    botf.location = (W / 2, -H / 2, 0.0)
    botf.data.materials.append(tex_mat("pcb_bot", os.path.join(IMG, "board_bottom.png")))
    core = U.box("pcb_core", 0.02, W - 0.02, -H + 0.02, -0.02, 0.01, 1.59)
    U.set_material(core, P("pcb_fr4", (0.08, 0.3, 0.12), roughness=0.6))

    def box(x0, x1, y0, y1, z0, z1, mat):
        o = U.box("p", x0, x1, -y1, -y0, z0, z1)
        U.set_material(o, mats[mat])
        return o

    def cyl(r, z0, z1, x, y, mat, axis="Z"):
        if axis == "Z":
            o = U.cylinder("c", r, z0, z1, x, -y, segs=48)
        else:                                             # lying along X at height z0 (centre)
            o = U.cylinder("c", r, x - z1 / 2, x + z1 / 2, -y, z0, axis="X", segs=48)
        U.set_material(o, mats[mat])
        U.shade(o)
        return o

    Z = 1.6
    for p in parts:
        ref, pads, x, y = p["ref"], p["pads"], p["x"], p["y"]
        xs = [q[0] for q in pads] or [x]
        ys = [q[1] for q in pads] or [y]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        if ref in ("U1", "U1B", "U3", "U3B"):                         # female socket strips
            box(min(xs) - 1.27, max(xs) + 1.27, cy - 1.27, cy + 1.27, Z, Z + 8.5, "black")
        elif ref == "U2":                                                # wire pads: three short pin stubs
            for q in pads:
                cyl(0.35, Z, Z + 3.0, q[0], q[1], "pin")
        elif ref.startswith("J"):
            n = len(pads)
            if abs(p["rot"]) == 90:
                box(cx - 2.95, cx + 2.95, min(ys) - 2.45, max(ys) + 2.45, Z, Z + 7.0, "jst")
            else:
                box(min(xs) - 2.45, max(xs) + 2.45, cy - 2.35, cy + 3.4, Z, Z + 7.0, "jst")
        elif ref in ("C1", "C2"):
            d = 10.0 if ref == "C1" else 8.0
            hgt = 13.0 if ref == "C1" else 12.0
            cyl(d / 2, Z + 0.5, Z + hgt, cx, cy, "cap")
            cyl(d / 2 - 0.4, Z + hgt, Z + hgt + 0.1, cx, cy, "captop")
        elif ref in ("C3", "C4", "C5"):
            o = U.box("disc", cx - 2.5, cx + 2.5, -cy - 1.25, -cy + 1.25, Z + 1.0, Z + 6.0)
            U.set_material(o, mats["disc"])
        elif ref == "F1":
            o = U.box("fuse", cx - 3.75, cx + 3.75, -cy - 1.5, -cy + 1.5, Z + 1.0, Z + 11.0)
            U.set_material(o, mats["fuse"])
        elif ref.startswith("R"):
            cyl(1.25, Z + 1.3, 6.3, cx, cy, "res", axis="X")
        elif ref.startswith("D"):
            r, L = {"D1": (2.65, 9.5), "D2": (1.8, 7.5), "D3": (1.35, 5.2)}[ref]
            cyl(r, Z + r + 0.1, L, cx, cy, "black", axis="X")
            kx = pads[0][0] if pads else cx                       # cathode band towards pad 1
            bx = cx + (L / 2 - 0.9) * (1 if kx > cx else -1)
            cyl(r + 0.05, Z + r + 0.1, 0.8, bx, cy, "band", axis="X")
        elif ref == "Q1":
            o = U.cylinder("q", 2.4, Z + 1.0, Z + 5.5, cx, -cy, segs=40)
            U.boolean(o, U.box("qcut", cx - 3, cx + 3, -cy + 0.9, -cy + 3, Z, Z + 6))
            U.set_material(o, mats["black"])
    # plug-in modules, raised on their sockets
    esp = [p for p in parts if p["ref"] in ("U1", "U1B")]
    ex = [q[0] for p in esp for q in p["pads"]]
    ey = [q[1] for p in esp for q in p["pads"]]
    zb = Z + 8.5
    box(min(ex) - 3.5, max(ex) + 5.2, min(ey) - 1.25, max(ey) + 1.25, zb, zb + 1.6, "esp")
    box(max(ex) - 15.5, max(ex) + 2.5, min(ey) + 3.0, max(ey) - 3.0, zb + 1.6, zb + 4.6, "shield")
    box(min(ex) - 3.5, min(ex) + 2.0, (min(ey) + max(ey)) / 2 - 4, (min(ey) + max(ey)) / 2 + 4, zb + 1.6, zb + 4.6, "shield")
    tmc = [p for p in parts if p["ref"] in ("U3", "U3B")]
    tx = [q[0] for p in tmc for q in p["pads"]]
    ty = [q[1] for p in tmc for q in p["pads"]]
    box(min(tx) - 1.1, max(tx) + 1.1, min(ty) - 1.25, max(ty) + 1.25, zb, zb + 1.6, "tmc")
    box((min(tx) + max(tx)) / 2 - 4.5, (min(tx) + max(tx)) / 2 + 4.5, (min(ty) + max(ty)) / 2 - 4.5,
        (min(ty) + max(ty)) / 2 + 4.5, zb + 1.6, zb + 6.6, "heatsink")
    box(59.5, 77.3, 34.2, 52.0, Z + 1.0, Z + 2.6, "pololu")            # regulator on foam tape

    bb = (0, W, -H, 0, 0, 20)
    S.build(bb, -0.01)
    span = max(bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4])
    for o in U.collection("COL_studio").objects:          # studio lights are sized for the engine (~330 mm)
        if o.type == 'LIGHT':
            o.data.energy *= (span / 330.0) ** 2
    for name, d, zoom in (("pcb_3d.png", (0.25, -0.75, 1.0), 1.15), ("pcb_3d_angle.png", (0.9, -1.0, 0.6), 1.1)):
        S.camera(d, bb, zoom)
        S.render(os.path.join(IMG, name), size=(1600, 1200), samples=48)
    print("wrote", IMG)


if __name__ == "__main__":
    main()
