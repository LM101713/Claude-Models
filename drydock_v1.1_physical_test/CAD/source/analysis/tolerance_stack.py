#!/usr/bin/env python3
"""Monte Carlo tolerance stack for the QuickLock bayonet, P001 vs V1.1.

Every printed surface gets an independent deviation drawn from an ASSUMED distribution for a
tuned Bambu H2C printing PETG with a 0.4 mm nozzle (state of the art for FDM; adjust after the
fit test):
  convex XY surface (plug OD, lug tip, window OD)      radial +0.05 +/- 0.05  (uniform 0 .. +0.10)
  concave XY surface (bore, groove floor, detent crest) radial -0.05 +/- 0.05  (material encroaches)
  axial position of a 45-deg flank (layer quantisation) +/- 0.10 (uniform, 0.20 mm layers)
  droop of a DOWN-facing 45-deg flank into the gap      0 .. 0.10 (uniform)
  Z-seam blob on a perimeter (worst case only, not in the distribution)  +0.10

A 45-deg flank turns a radial deviation into an equal axial one. Down-facing flanks:
  cap lug bearing flank (cap printed face-down)        always
  body lip bearing flank, TOP socket                   yes
  body lip bearing flank, BOTTOM socket                no (faces up)

    python tolerance_stack.py [k_lug_N_per_mm]
"""
import importlib.util, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = {"P001": HERE.parents[1] / "drydock.py", "V1.1": HERE.parent / "drydock_v11.py"}
N = 200_000
rng = np.random.default_rng(7)


def U(a, b):
    return rng.uniform(a, b, N)


def load(name):
    spec = importlib.util.spec_from_file_location("m" + name.replace(".", ""), SRC[name])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m.Params()


def stack(P, k_lug=None, mu=0.25):
    D = P.d()
    cvx = lambda: U(0.0, 0.10)        # convex grows
    ccv = lambda: U(0.0, 0.10)        # concave encroaches (magnitude, reduces clearance)
    zq = lambda: U(-0.10, 0.10)
    droop = lambda: U(0.0, 0.10)
    out = {}
    plug, bore = cvx(), ccv()
    out["radial_fit"] = P.fit_radial - plug - bore
    tip, floor = cvx(), ccv()
    out["lug_tip_clear"] = P.lug_tip_clear - tip - floor
    crest = ccv()
    out["detent_interference"] = P.detent_interference + tip + crest
    for end, lip_down in (("bottom_socket", False), ("top_socket", True)):
        lug_flank = cvx() + droop()                 # lug grows radially -> flank moves toward lip
        lip_flank = ccv() + (droop() if lip_down else 0)
        out[f"bearing_play_{end}"] = P.bearing_play - lug_flank - lip_flank + zq() + zq()
    res = {}
    for k, v in out.items():
        res[k] = dict(nominal=float({"radial_fit": P.fit_radial, "lug_tip_clear": P.lug_tip_clear,
                                      "detent_interference": P.detent_interference}.get(k, P.bearing_play)),
                      p05=float(np.percentile(v, 5)), p50=float(np.percentile(v, 50)),
                      p95=float(np.percentile(v, 95)), worst=float(v.min() if "interference" not in k else v.max()),
                      share_negative=float((v < 0).mean()) if "interference" not in k else None)
    if k_lug:
        ramp = math.atan(math.pi * (P.lug_tip_clear + P.detent_interference) /
                         (2 * math.radians(P.detent_halfwidth_deg) * D["R_g"]))
        di = out["detent_interference"]
        T = P.lug_count * k_lug * di * math.tan(ramp + math.atan(mu)) * D["R_g"] / 1000
        res["detent_torque_Nm"] = dict(p05=float(np.percentile(T, 5)), p50=float(np.percentile(T, 50)),
                                       p95=float(np.percentile(T, 95)), ramp_deg=math.degrees(ramp))
        res["detent_force_per_lug_N"] = dict(p05=float(np.percentile(k_lug * di, 5)),
                                             p50=float(np.percentile(k_lug * di, 50)),
                                             p95=float(np.percentile(k_lug * di, 95)))
    return res


if __name__ == "__main__":
    k = float(sys.argv[1]) if len(sys.argv) > 1 else None
    out = {name: stack(load(name), k) for name in SRC}
    print(json.dumps(out, indent=1))
    (HERE / "tolerance_stack.json").write_text(json.dumps(out, indent=1))
