"""Studio: neutral cyclorama, soft key / fill / rim, Cycles render from the
reference camera directions, side-by-side composite with the reference image."""
import math
import os

import bpy
from mathutils import Vector

from . import bpyutil as U
from . import materials as M

# camera direction (from target towards camera) and up vector - same angles as the CAD renders / reference set
# name: (camera direction from the target, zoom, reference image, target)
# target None = the engine's bounding-box centre; otherwise a named point computed from the placed parts
VIEWS = {
    "ref1_closeup_34_above": ((0.55, -1.0, 0.75), 1.9, "STYLE_ai_01.png", "bank_A_top"),
    "ref2_rear_left_34": ((-1.0, -0.9, 0.45), 1.0, "STYLE_ai_02.png", None),
    "ref3_front_right_34": ((1.0, 0.9, 0.45), 1.0, "STYLE_ai_03.png", None),
    "ref4_side_left": ((0.0, -1.0, 0.12), 1.0, "STYLE_ai_04.png", None),
    "ref5_front": ((1.0, 0.0, 0.15), 1.0, "STYLE_ai_05.png", None),
    "x1_top": ((0.0, 0.0, 1.0), 1.0, None, None),
    "x2_closeup_intake": ((0.6, 0.7, 0.9), 2.0, None, "intake"),
    "x3_closeup_valve_cover": ((0.3, -1.0, 0.55), 2.2, None, "valve_cover_A"),
}


def build(scene_bbox, floor_z):
    sc = bpy.context.scene
    (x0, x1, y0, y1, z0, z1) = scene_bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    size = max(x1 - x0, y1 - y0) * 6
    # cyclorama: floor + curved back wall
    floor = U.box("STUDIO_floor", cx - size, cx + size, cy - size, cy + size, floor_z - 2.0, floor_z, "COL_studio")
    U.set_material(floor, M.backdrop())
    # lights
    def area(name, loc, target, energy, size_):
        bpy.ops.object.light_add(type='AREA', location=loc)
        l = bpy.context.object
        l.name = name
        l.data.energy = energy
        l.data.size = size_
        l.data.shape = 'RECTANGLE'
        l.data.size_y = size_ * 0.6
        d = Vector(target) - Vector(loc)
        l.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        for c in l.users_collection:
            c.objects.unlink(l)
        U.collection("COL_studio").objects.link(l)
        return l
    t = (cx, cy, (z0 + z1) / 2)
    span = max(x1 - x0, y1 - y0, z1 - z0)
    area("LGT_key", (cx + 1.2 * span, cy - 1.6 * span, z1 + 1.4 * span), t, 3.6e6, 1.8 * span)
    area("LGT_fill", (cx - 0.6 * span, cy + 1.8 * span, z1 + 0.6 * span), t, 1.4e6, 2.4 * span)
    area("LGT_rim", (cx - 1.8 * span, cy - 0.8 * span, z1 + 1.0 * span), t, 1.6e6, 0.8 * span)
    area("LGT_top", (cx, cy, z1 + 2.2 * span), t, 1.2e6, 2.5 * span)
    w = bpy.data.worlds.new("studio_world") if sc.world is None else sc.world
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.64, 0.67, 1.0)
    bg.inputs["Strength"].default_value = 0.6
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = 0.4
    sc.render.film_transparent = False
    return floor


def camera(direction, scene_bbox, zoom=1.0, lens=55.0, up=(0, 0, 1), target=None):
    sc = bpy.context.scene
    (x0, x1, y0, y1, z0, z1) = scene_bbox
    target = Vector(target) if target is not None else Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    radius = 0.5 * math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
    d = Vector(direction).normalized()
    fov = 2 * math.atan(18.0 / lens)                     # 36 mm sensor
    dist = radius / math.sin(fov / 2) * 1.05 / zoom
    cam_data = bpy.data.cameras.new("CAM")
    cam_data.lens = lens
    cam_data.clip_end = 100000
    cam = bpy.data.objects.new("CAM_ref", cam_data)
    U.collection("COL_studio").objects.link(cam)
    cam.location = target + d * dist
    look = (target - cam.location)
    cam.rotation_euler = look.to_track_quat('-Z', 'Y' if abs(d.z) < 0.99 else 'X').to_euler()
    sc.camera = cam
    return cam


def render(path, size=(1456, 1086), samples=64):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.render.filepath = path
    sc.render.image_settings.file_format = 'PNG'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    return path


def composite(render_path, ref_path, out_path, label):
    from PIL import Image, ImageDraw
    a = Image.open(render_path).convert("RGB")
    size = a.size
    b = Image.open(ref_path).convert("RGB").resize(size)
    comp = Image.new("RGB", (size[0] * 2 + 20, size[1] + 40), (255, 255, 255))
    comp.paste(a, (0, 40))
    comp.paste(b, (size[0] + 20, 40))
    d = ImageDraw.Draw(comp)
    d.text((10, 12), f"Blender skin - {label}", fill=(0, 0, 0))
    d.text((size[0] + 30, 12), f"reference {os.path.basename(ref_path)} (AI-generated, style only)", fill=(0, 0, 0))
    comp.save(out_path)
    return out_path
