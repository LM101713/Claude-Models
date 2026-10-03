"""Cross-check the firmware against the CAD model, then run its unit tests.

1. Regenerates firmware/v10_engine/engine_geometry.h from config.py.
2. CAD kinematics: for every cylinder, the crank angle where its piston is
   really at top dead centre (from the slider-crank model the CAD uses) must
   equal the firing angle the firmware lights the LEDs at.
3. CAD solid: the hall magnet pocket in the end web over the sensor must sit
   exactly over it at crank angle HALL_PHI - the firmware takes the magnet
   centre as HALL_PHI after cylinder 1 TDC.
4. Builds and runs firmware/test/test_engine_logic.cpp with the host compiler.

    python tools/check_firmware.py
"""

import math
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import config as C  # noqa: E402
import gen_firmware_config  # noqa: E402


def check_tdc():
    import rods_pistons as rp
    worst = 0.0
    for c in range(1, C.N_CYL + 1):
        best_phi, best_s = None, -1e9
        for i in range(36000):
            phi = i * 0.01
            _, s, _ = rp.slider(c, phi)
            if s > best_s:
                best_s, best_phi = s, phi
        want = C.FIRE_ANGLE[c] % 360.0
        err = (best_phi - want + 180.0) % 360.0 - 180.0
        worst = max(worst, abs(err))
        print(f"  cylinder {c:2d}: CAD TDC at {best_phi:7.2f} deg, firmware fires at {want:6.1f} deg  (diff {err:+.2f})")
    ok = worst < 0.05
    print("  TDC timing:", "OK" if ok else f"MISMATCH {worst:.2f} deg")
    return ok


def check_magnet():
    import cadquery as cq
    import crank
    from common import cyl_x
    lib = crank.build_all()
    name = "end_web_rear" if C.HALL_SENSOR_END == "rear" else "end_web_front"
    web = [s for n, s in crank.placed_parts(lib, C.HALL_PHI) if n == name][0]
    x = C.HALL_X
    r_probe = C.WEB_CW_R - C.MAGNET["h"] / 2               # inside the magnet pocket

    def solid_at(angle_deg):
        a = math.radians(angle_deg)
        y, z = r_probe * math.sin(a), r_probe * math.cos(a)
        probe = cq.Solid.makeSphere(1.0, cq.Vector(x, y, z))
        return web.intersect(probe).Volume() / probe.Volume()

    at_sensor = solid_at(C.HALL_SENSOR_ANGLE)
    # the 6.6 mm pocket spans about +/-8.5 deg at this radius: just beyond it
    # the web must be solid on both sides (pocket really is in the web)
    beside = min(solid_at(C.HALL_SENSOR_ANGLE + d) for d in (-12.0, 12.0))
    ok = at_sensor < 0.05 and beside > 0.9
    print(f"  {name} magnet pocket over the sensor at {C.HALL_PHI:.0f} deg: material fraction {at_sensor:.2f} "
          f"(pocket), 12 deg either side {beside:.2f} (solid web) -> {'OK' if ok else 'WRONG'}")
    return ok


def run_unit_tests():
    cxx = shutil.which("g++") or shutil.which("clang++")
    if not cxx:
        print("  no host C++ compiler - unit tests skipped")
        return True
    src = os.path.join(ROOT, "firmware", "test", "test_engine_logic.cpp")
    inc = os.path.join(ROOT, "firmware", "v10_engine")
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "t")
        b = subprocess.run([cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-I", inc, src, "-o", exe],
                           capture_output=True, text=True)
        if b.returncode:
            print(b.stdout + b.stderr)
            return False
        r = subprocess.run([exe], capture_output=True, text=True)
        print("  " + (r.stdout + r.stderr).strip().replace("\n", "\n  "))
        return r.returncode == 0


if __name__ == "__main__":
    print("generating", gen_firmware_config.build())
    results = [check_tdc(), check_magnet(), run_unit_tests()]
    print("FIRMWARE CHECK:", "PASS" if all(results) else "FAIL")
    sys.exit(0 if all(results) else 1)
