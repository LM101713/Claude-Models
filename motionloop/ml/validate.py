"""
Engineering validation, run on the actual meshes:

    1. every part is one closed manifold shell
    2. kinematics: rod length held at every angle, stroke, rod angle, transmission angle,
       mirror / shuttle phase relation, peak slider speed and acceleration
    3. full-rotation sweep (both crank wheels): triangle-level intersection test between every
       pair of moving and fixed bodies at every 2 degrees
    4. minimum clearance between every pair over the rotation, and each designed clearance
    5. designed contacts / fits inside the rigid crank and slider assemblies
    6. wall thickness and overhangs in print orientation
    7. simple strength estimates for the weak links
"""

import math
import time

from mathutils import Matrix, Vector

from . import geom as G
from . import parts as PT
from .params import P, D, slider_x, pin_xz


class PMirror(P):
    PHASE_DEG = 180.0


class PShuttle(P):
    PHASE_DEG = 0.0


def bodies(parts, theta, cfg):
    """{body name: [(object, matrix), ...]} at crank angle theta for config 'mirror'/'shuttle'."""
    shuttle = cfg == "shuttle"
    p = PShuttle if shuttle else PMirror
    C = PT.crank_matrix(theta)
    wheel = parts["wheel_shuttle"] if shuttle else parts["wheel_mirror"]
    crank = [(wheel, C), (parts["cheek"], C), (parts["cheek"], C @ PT.cheek_b_basis(shuttle)),
             (parts["cap"], C), (parts["handle"], C), (parts["knob"], C),
             (parts["pin"], C @ PT.knob_pin_basis())]
    SA, SB = PT.slider_matrix(theta, -1, p), PT.slider_matrix(theta, 1, p)
    return {
        "frame": [(parts["frame"], Matrix())],
        "crank": crank,
        "rod_A": [(parts["rod"], PT.rod_matrix(theta, -1, p))],
        "rod_B": [(parts["rod"], PT.rod_matrix(theta, 1, p))],
        "slider_A": [(parts["slider"], SA), (parts["pin"], SA)],
        "slider_B": [(parts["slider"], SB), (parts["pin"], SB)],
    }


PAIRS = [("frame", "crank"), ("frame", "rod_A"), ("frame", "rod_B"), ("frame", "slider_A"),
         ("frame", "slider_B"), ("crank", "rod_A"), ("crank", "rod_B"), ("crank", "slider_A"),
         ("crank", "slider_B"), ("rod_A", "rod_B"), ("rod_A", "slider_A"), ("rod_B", "slider_B"),
         ("rod_A", "slider_B"), ("rod_B", "slider_A"), ("slider_A", "slider_B")]

# designed minimum gap for each pair (the smallest fit between them), mm
EXPECTED = {
    ("frame", "crank"): ((P.BORE_D - P.JOURNAL_D) / 2, "journal in the tower bore (radial)"),
    ("frame", "slider_A"): (P.SLIDE_Z, "slider underside above the plinth / dovetail flank"),
    ("frame", "slider_B"): (P.SLIDE_Z, "slider underside above the plinth / dovetail flank"),
    ("crank", "rod_A"): (P.RUN_DIA / 2, "crank pin in the big-end bore (radial)"),
    ("crank", "rod_B"): (P.RUN_DIA / 2, "crank pin in the big-end bore (radial)"),
    ("rod_A", "slider_A"): (P.RUN_DIA / 2, "wrist pin in the small-end bore (radial)"),
    ("rod_B", "slider_B"): (P.RUN_DIA / 2, "wrist pin in the small-end bore (radial)"),
}


def _local_points(parts, step):
    cache = {}
    for k, ob in parts.items():
        cache[k] = G.surface_points(ob, step)
    return cache


def _body_points(body, pts_cache, parts):
    inv = {id(v): k for k, v in parts.items()}
    out = []
    for ob, M in body:
        out += [M @ q for q in pts_cache[inv[id(ob)]]]
    return out


def kinematics(p, n=720):
    rows = []
    for k in range(n + 1):
        th = 2 * math.pi * k / n
        xa, xb = slider_x(th, -1, p), slider_x(th, 1, p)
        rows.append((math.degrees(th), xa, xb))
    xa = [r[1] for r in rows]
    xb = [r[2] for r in rows]
    # speeds and accelerations per (rad/s) and per (rad/s)^2 by finite differences
    h = 2 * math.pi / n
    va = [(xa[i + 1] - xa[i - 1]) / (2 * h) for i in range(1, n)]
    aa = [(xa[i + 1] - 2 * xa[i] + xa[i - 1]) / h ** 2 for i in range(1, n)]
    beta = math.degrees(math.asin(p.CRANK_R / p.ROD_L))
    return dict(rows=rows, stroke_A=max(xa) - min(xa), stroke_B=max(xb) - min(xb),
                range_A=(min(xa), max(xa)), range_B=(min(xb), max(xb)),
                v_peak=max(abs(v) for v in va), a_peak=max(abs(a) for a in aa),
                beta_max_deg=beta, transmission_min_deg=90 - beta)


def rod_length_check(parts, cfg, n=72):
    """The posed rod must have its bore centres exactly on the crank pin and the wrist pin."""
    p = PShuttle if cfg == "shuttle" else PMirror
    worst = 0.0
    for k in range(n):
        th = 2 * math.pi * k / n
        for side in (-1, 1):
            R = PT.rod_matrix(th, side, p)
            big = R @ Vector((0, 0, 0))
            small = R @ Vector((p.ROD_L, 0, 0))
            px, pz = pin_xz(th, side, p)
            # crank pin centre from the posed cheek geometry
            C = PT.crank_matrix(th)
            if side < 0:
                pin_c = C @ Vector((p.CRANK_R, 0, p.AXLE_Z))
            else:
                pin_c = C @ PT.cheek_b_basis(cfg == "shuttle") @ Vector((p.CRANK_R, 0, p.AXLE_Z))
            wrist = PT.slider_matrix(th, side, p) @ Vector((0, 0, p.AXLE_Z))
            e1 = math.hypot(big.x - pin_c.x, big.z - pin_c.z)
            e2 = math.hypot(small.x - wrist.x, small.z - wrist.z)
            worst = max(worst, e1, e2, abs((small - big).length - p.ROD_L))
    return worst


def sweep(parts, cfg, step_deg=2.0, clear_every=5, pts_cache=None, log=print):
    t0 = time.time()
    res = {pr: dict(hits=0, hit_angles=[], min_gap=99.0, at=None, where=None) for pr in PAIRS}
    frame_tree = G.bvh_of([(parts["frame"], Matrix())])[0]
    n = int(round(360 / step_deg))
    lowest = 99.0
    for k in range(n):
        th = math.radians(k * step_deg)
        B = bodies(parts, th, cfg)
        trees = {"frame": frame_tree}
        for name, lst in B.items():
            if name != "frame":
                trees[name] = G.bvh_of(lst)[0]
        for a, b in PAIRS:
            ov = trees[a].overlap(trees[b])
            if ov:
                res[(a, b)]["hits"] += len(ov)
                res[(a, b)]["hit_angles"].append(k * step_deg)
        if k % clear_every == 0:
            for a, b in PAIRS:
                # sample the moving body against the other body's tree
                src = b if a == "frame" else a
                dst = a if a == "frame" else b
                pts = _body_points(B[src], pts_cache, parts)
                d, where = G.min_dist(pts, trees[dst], limit=6.0)
                r = res[(a, b)]
                if d < r["min_gap"]:
                    r["min_gap"], r["at"], r["where"] = d, k * step_deg, where
            # handle / knob ground clearance
            for ob, M in B["crank"]:
                if ob in (parts["handle"], parts["knob"], parts["pin"]):
                    lowest = min(lowest, min((M @ v.co).z for v in ob.data.vertices))
    log(f"  sweep {cfg}: {n} poses in {time.time() - t0:.0f} s")
    return res, lowest


def designed_contacts(parts):
    """Fits inside rigid sub-assemblies, measured on the meshes at crank angle 0."""
    out = {}
    wheel = parts["wheel_mirror"]
    I = Matrix()
    tw = G.bvh_of([(wheel, I)])[0]
    # cheek A: spigot shoulder seated on the wheel face; spigot clear of the D-hole walls
    lift = Matrix.Translation((0, 0.01, 0))
    tc = G.bvh_of([(parts["cheek"], I)])[0]
    tcl = G.bvh_of([(parts["cheek"], lift)])[0]
    out["cheek_on_wheel_overlap_at_0.01mm_lift"] = len(tw.overlap(tcl))
    out["cheek_to_wheel_min_gap"] = G.min_dist(G.surface_points(parts["cheek"], 0.5), tw, 2.0)[0]
    # spigot side clearance: measure from points on the spigot only (y < 3)
    sp = [q for q in G.surface_points(parts["cheek"], 0.3) if q.y < D["Y_WHEEL"] - 0.05]
    out["spigot_to_dhole_min_gap"] = G.min_dist(sp, tw, 2.0)[0]
    # hex shafts in the cheek sockets (line-to-line press by design)
    for nm, obn, ych in (("cap", "cap", 1), ("handle", "handle", -1)):
        ob = parts[obn]
        hexpts = [q for q in G.surface_points(ob, 0.3) if abs(q.y) < D["Y_CHEEK1"] - 0.25]
        if ych > 0:
            tree = tc
        else:
            tree = G.bvh_of([(parts["cheek"], PT.cheek_b_basis(False))])[0]
        out[f"{nm}_hex_to_socket_min_gap"] = G.min_dist(hexpts, tree, 2.0)[0]
    # wrist pin in the slider (press) and knob pin in the handle (press)
    ts = G.bvh_of([(parts["slider"], I)])[0]
    shank = [q for q in G.surface_points(parts["pin"], 0.3) if q.y > -D["Y_WHEEL"] + 0.05]
    out["wrist_pin_to_slider_bore_min_gap"] = G.min_dist(shank, ts, 2.0)[0]
    th = G.bvh_of([(parts["handle"], I)])[0]
    kp = PT.knob_pin_basis()
    shank_k = [kp @ q for q in G.surface_points(parts["pin"], 0.3)]
    shank_k = [q for q in shank_k if q.y > -D["Y_ARM1"] + 0.05]
    out["knob_pin_to_handle_bore_min_gap"] = G.min_dist(shank_k, th, 2.0)[0]
    # knob sleeve on the knob pin (running)
    tk = G.bvh_of([(parts["knob"], I)])[0]
    pts = [kp @ q for q in G.surface_points(parts["pin"], 0.3)]
    out["knob_sleeve_to_pin_min_gap"] = G.min_dist(pts, tk, 2.0)[0]
    return out


def print_matrices():
    """Assembly / reference frame -> print orientation (z = 0 on the bed)."""
    rx = lambda a: Matrix.Rotation(math.radians(a), 4, "X")  # noqa: E731
    T = Matrix.Translation
    return {
        "frame": Matrix(),
        "wheel_mirror": T((0, 0, D["Y_WHEEL"])) @ rx(90) @ T((0, 0, -P.AXLE_Z)),
        "wheel_shuttle": T((0, 0, D["Y_WHEEL"])) @ rx(90) @ T((0, 0, -P.AXLE_Z)),
        "cheek": T((0, 0, D["Y_CHEEK1"])) @ rx(-90) @ T((0, 0, -P.AXLE_Z)),
        "cap": T((0, 0, D["Y_CAP0"] + P.CAP_T)) @ rx(-90) @ T((0, 0, -P.AXLE_Z)),
        "handle": T((0, 0, D["Y_ARM1"])) @ rx(90) @ T((0, 0, -P.AXLE_Z)),
        "knob": T((0, 0, PT.knob_y()[1])) @ rx(-90) @ T((0, 0, -P.AXLE_Z)),
        "rod": T((0, 0, P.ROD_T / 2)) @ rx(90),
        "slider": T((0, 0, P.SLIDER_Y[1])) @ rx(-90) @ T((0, 0, -P.AXLE_Z)),
        "pin": T((0, 0, D["Y_WRIST_HEAD0"] + P.PIN_HEAD_T)) @ rx(90) @ T((0, 0, -P.AXLE_Z)),
    }


def print_checks(parts):
    out = {}
    PM = print_matrices()
    for k, ob in parts.items():
        M = PM[k]
        v, t = G.world_tris(ob, M)
        zmin = min(q.z for q in v)
        flat, steep = G.overhang_scan(v, t, 45.0, z_bed=zmin)
        th = G.thickness_scan(ob)
        thin = [x for x in th if x[0] < 1.2 - 1e-3]
        out[k] = dict(
            z_min=round(zmin, 4),
            height=round(max(q.z for q in v) - zmin, 2),
            flat_down_mm2=round(sum(a for a, _ in flat), 2),
            steep_down_mm2=round(sum(a for a, _ in steep), 2),
            flat_clusters=[dict(area=round(g["area"], 2), lo=[round(x, 1) for x in g["lo"]],
                                hi=[round(x, 1) for x in g["hi"]]) for g in G.cluster(flat)[:8]],
            steep_clusters=[dict(area=round(g["area"], 2), lo=[round(x, 1) for x in g["lo"]],
                                 hi=[round(x, 1) for x in g["hi"]]) for g in G.cluster(steep)[:8]],
            min_wall=round(min((x[0] for x in th), default=99), 3),
            thin_count=len(thin),
            thin_examples=sorted(thin)[:6],
        )
    return out


def strength(p=P):
    """Hand-calculation estimates for the weak links (PETG, conservative layer-limited
    strengths). Load case: 10 N at the knob with one slider jammed (abuse case)."""
    F_hand = 10.0
    T = F_hand * p.HANDLE_R
    F_rod = T / p.CRANK_R  # worst case: whole torque into one rod at 90 degrees
    s_layer_t = 20.0  # MPa, across-layer tensile (conservative printed PETG)
    s_layer_sh = 15.0  # MPa, across-layer shear
    out = {"load_case": f"{F_hand:.0f} N at the knob, one slider jammed: crank torque "
                        f"{T:.0f} N*mm, rod force {F_rod:.1f} N"}

    def bend(d, arm):
        M = F_rod * arm
        return 32 * M / (math.pi * d ** 3)

    arm_pin = P.AXIAL + P.ROD_T / 2
    out["crank_pin_root_bending_MPa"] = round(bend(p.PIN_D, arm_pin + 0.3), 2)
    out["spigot_root_bending_MPa"] = round(bend(p.SPIGOT_D - 0.4, p.SPIGOT_L / 2), 2)
    out["wrist_pin_bending_MPa"] = round(bend(p.WRIST_D, arm_pin), 2)
    # hex drive in torsion, shear on the layer planes (shaft printed vertically)
    d_in = p.HEX_AF
    tau_hex = 16 * T / (math.pi * d_in ** 3)
    out["hex_torsion_MPa"] = round(tau_hex, 2)
    tau_j = 16 * T / (math.pi * p.JOURNAL_D ** 3)
    out["journal_torsion_MPa"] = round(tau_j, 2)
    # rod (printed flat, along the lines): net section at the small end
    a_small = 2 * (p.ROD_SMALL_R - (p.WRIST_D + p.RUN_DIA) / 2) * p.ROD_T
    out["rod_small_end_net_tension_MPa"] = round(F_rod / a_small, 2)
    I = p.ROD_SHANK_HW[1] * 2 * p.ROD_T ** 3 / 12
    out["rod_euler_buckling_N"] = round(math.pi ** 2 * 2000.0 * I / p.ROD_L ** 2, 0)
    sf = {k: round((s_layer_sh if "torsion" in k else s_layer_t) / v, 1)
          for k, v in out.items() if k.endswith("_MPa") and v > 0}
    out["safety_factors_vs_layer_strength"] = sf
    return out
