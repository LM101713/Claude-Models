"""Turntable-style video of the V8 running: the real part meshes (Blender skin +
CAD core), the crank turning, rods and pistons following the slider-crank
kinematics of config.py, the damper turning with the crank.

    python3.13 tools/video.py                       # renders/video/engine_running.mp4
    python3.13 tools/video.py --frames 4 --draft    # quick test

Positions come from the same formulas as cad/assembly_v8.py; nothing is keyframed by hand.
"""
import argparse
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import config as C  # noqa: E402
import skin_blender as SB  # noqa: E402
from skin import bpyutil as U, studio as S  # noqa: E402

OUT = os.path.join(ROOT, "renders", "video")
DX = C.CRANK_DX
CRANK = ("crankpin", "segment", "end_web", "main_shaft")
CUTAWAY = ("bank_A", "head_A", "valve_cover_A", "oil_cap_A", "boot_A", "header_A", "header_plate_A", "collector_A")


def polar(r, deg):
    a = math.radians(deg)
    return r * math.sin(a), r * math.cos(a)


def RX(deg):
    return Matrix.Rotation(math.radians(-deg), 4, 'X')


def T(v):
    return Matrix.Translation(v)


def cyl_x(c):
    k = C.cyl_throw(c)
    return C.BANK_A_CYL_X[k] if C.cyl_bank(c) == "A" else C.BANK_B_CYL_X[k]


def pin_c(c, phi):
    y, z = polar(C.CRANK_R, C.PIN_ANGLE[c] + phi)
    return Vector((cyl_x(c) + DX, y, z))


def wrist(c, phi):
    y, z = polar(C.piston_travel(phi, c), C.bank_angle(C.cyl_bank(c)))
    return Vector((cyl_x(c), y, z))


def rod_angle(c, phi):
    psi = C.bank_angle(C.cyl_bank(c))
    beta = math.radians(C.PIN_ANGLE[c] + phi - psi)
    r, L = C.CRANK_R, C.ROD_LENGTH
    s = r * math.cos(beta) + math.sqrt(L * L - (r * math.sin(beta)) ** 2)
    return psi + math.degrees(math.atan2(-r * math.sin(beta), s - r * math.cos(beta)))


def mover(name):
    """Return f(phi) -> world matrix for a core mesh exported at crank angle 0, or None if static."""
    n = name[len("core_"):]
    if n.startswith(CRANK):
        return lambda phi: RX(phi)
    for pre in ("rod_", "bearing686_", "bush_small_", "piston_", "wristpin_", "bush_lug_"):
        if n.startswith(pre):
            c = int(n[len(pre):].split("_")[0])
            break
    else:
        return None
    if n.startswith("rod_"):
        p0, a0 = pin_c(c, 0.0), rod_angle(c, 0.0)
        return lambda phi: T(pin_c(c, phi)) @ RX(rod_angle(c, phi) - a0) @ T(-p0)
    if n.startswith("bearing686_"):
        p0 = pin_c(c, 0.0)
        return lambda phi: T(pin_c(c, phi) - p0)
    w0 = wrist(c, 0.0)
    if n.startswith("bush_small_"):            # rides on the rod's small end = the wrist pin
        return lambda phi: T(wrist(c, phi) - w0)
    return lambda phi: T(wrist(c, phi) - w0)    # piston, wrist pin, lug bushings slide on the bore axis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=180)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--rpm", type=float, default=40.0)
    a = ap.parse_args()
    fps = 30
    size = (960, 540) if a.draft else (1280, 720)
    samples = 8 if a.draft else 16
    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

    U.reset_scene()
    SB.build_library()
    placed = SB.place_all(0.0, with_core=True)
    objs = [o for _, o, _ in placed]
    movers = [(o, mover(o.name)) for o in objs if o.name.startswith("core_")]
    movers = [(o, f) for o, f in movers if f is not None]
    dampers = [o for o in objs if o.name.startswith("damper")]
    movers += [(o, (lambda phi: RX(phi))) for o in dampers]
    print(f"{len(movers)} moving objects", flush=True)

    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    bb = (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts),
          min(p.z for p in pts), max(p.z for p in pts))
    S.build(bb, bb[4])
    sc = bpy.context.scene
    sc.cycles.use_denoising = True
    centre = Vector(((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, (bb[4] + bb[5]) / 2))
    radius = 0.5 * (Vector((bb[1], bb[3], bb[5])) - Vector((bb[0], bb[2], bb[4]))).length

    cam = S.camera((0.9, -1.0, 0.45), bb, 1.0, lens=50.0)
    dist = (cam.location - centre).length * 1.18
    cut = [o for o in objs if o.name.startswith(CUTAWAY)]
    deg_per_frame = a.rpm * 360.0 / 60.0 / fps
    for i in range(a.frames):
        phi = (i * deg_per_frame) % 720.0
        for o, f in movers:
            o.matrix_world = f(phi)
        # slow camera swing: 50 deg over the clip, from the front-left (bank A windows) round to the front
        t = i / max(1, a.frames - 1)
        half = a.frames // 2
        if i < half:          # outside: swing from the bank A side towards the front
            u = i / max(1, half - 1)
            az, el, k = math.radians(-60.0 + 35.0 * u), math.radians(20.0), 1.0
        else:                 # bank A side opened: look down on the crank, rods and pistons
            u = (i - half) / max(1, a.frames - half - 1)
            az, el, k = math.radians(-78.0 + 22.0 * u), math.radians(32.0), 0.85
        cam.location = centre + k * dist * Vector((math.cos(el) * math.cos(az) * -1.0 * -1.0 * 1.0,
                                                math.cos(el) * math.sin(az), math.sin(el)))
        cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
        # second half: bank A side opened up so the moving crank, rods and pistons show
        for o in cut:
            o.hide_render = i >= a.frames // 2
        bpy.context.view_layer.update()
        S.render(os.path.join(frames_dir, f"f{i:04d}.png"), size=size, samples=samples)
        print(f"frame {i + 1}/{a.frames}", flush=True)

    mp4 = os.path.join(OUT, "engine_running_draft.mp4" if a.draft else "engine_running.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], check=True)
    print("wrote", mp4, flush=True)


if __name__ == "__main__":
    main()
