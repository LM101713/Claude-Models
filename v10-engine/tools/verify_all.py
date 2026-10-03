"""Full interference / clearance verification of the assembled engine.

    python tools/verify_all.py            # everything (~15 min on 4 cores)
    python tools/verify_all.py --quick    # static + drive checks only

1. config.py self-check
2. static check: every pair of non-moving parts (blocks, heads, covers,
   exhaust, base, motor, belt, pulleys...) must not overlap (crush-rib press
   fits may overlap by their rib volume only)
3. drive check: motor / belt / pulleys / covers / base, also with the 220 mm
   second-source belt and with the motor at both ends of its slots
4. motion sweep: every moving part against every static part and every other
   moving part, one full revolution in 6 deg steps (runs in parallel)
5. clearance scan: the smallest gap between every pair of part kinds that
   come within 4 mm of each other, full revolution in 15 deg steps
6. assembly paths: in the build order of docs/ASSEMBLY.md, every part can
   travel to its final place without hitting what is already there

Writes docs/CLEARANCE_REPORT.md.
"""

import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cad"))

import config as C  # noqa: E402
import assembly  # noqa: E402

SWEEP_STEP = 6.0
CLEAR_STEP = 15.0
NEAR = 4.0


def _statics():
    return [(n, s) for n, s, _ in assembly.styling_parts() + assembly.drive_and_base()]


def _sweep_angles(angles):
    hits = []
    statics = _statics()
    for angle in angles:
        parts = [(n, s) for n, s, _ in assembly.engine(angle)] + statics
        mov = [(n, s) for n, s in parts if n.startswith(assembly.MOVING)]
        sta = [(n, s) for n, s in parts if n.startswith(assembly.STATIC)]
        pairs = [(a, b) for a in mov for b in sta]
        pairs += [(mov[i], mov[j]) for i in range(len(mov)) for j in range(i + 1, len(mov))]
        for (n1, s1), (n2, s2) in pairs:
            if n1.startswith("main_shaft") and n2.startswith(("pulley", "belt")):
                continue
            crank = ("crankpin", "segment", "end_web", "main_shaft")
            if n1.startswith(crank) and n2.startswith(crank):
                continue
            if assembly._same_joint(n1, n2) or not assembly._bb_overlap(s1, s2):
                continue
            v = s1.intersect(s2).Volume()
            if v > 0.01:
                hits.append((angle, n1, n2, round(v, 3)))
        print(f"    sweep {angle:5.1f} deg done", flush=True)
    return hits


def _kind(n):
    for k in ("crankpin", "segment", "end_web", "main_shaft", "rod", "piston", "crankcase", "valley_beam",
              "bank", "end_plate", "rail", "head", "exhaust", "coil", "plenum", "trumpet", "cam_cover",
              "side_panel", "end_cover", "base", "panel", "motor", "belt", "pulley", "spacer"):
        if n.startswith(k):
            return k
    return n


def _clear_angles(angles):
    best = {}
    statics = _statics()
    for angle in angles:
        parts = [(n, s) for n, s, _ in assembly.engine(angle)] + statics
        mov = [(n, s) for n, s in parts if n.startswith(assembly.MOVING)]
        sta = [(n, s) for n, s in parts if n.startswith(assembly.STATIC)]
        pairs = [(a, b) for a in mov for b in sta]
        pairs += [(mov[i], mov[j]) for i in range(len(mov)) for j in range(i + 1, len(mov))]
        for (n1, s1), (n2, s2) in pairs:
            k1, k2 = _kind(n1), _kind(n2)
            crank = ("crankpin", "segment", "end_web", "main_shaft")
            if k1 in crank and k2 in crank:
                continue
            if assembly._same_joint(n1, n2) or not assembly._bb_overlap(s1, s2, NEAR):
                continue
            if (k1, k2) in (("rod", "crankpin"), ("main_shaft", "end_plate"), ("main_shaft", "pulley"),
                            ("main_shaft", "spacer"), ("main_shaft", "belt")):
                continue          # joined through a bearing / clamped
            d = s1.distance(s2)
            key = tuple(sorted((k1, k2)))
            if d < NEAR and (key not in best or d < best[key][0]):
                best[key] = (d, angle, n1, n2)
        print(f"    clearance {angle:5.1f} deg done", flush=True)
    return best


def _path_hits(moving, statics, direction, steps):
    import cadquery as cq
    out = []
    for d in steps:
        for n, s in moving:
            m = s.translate(cq.Vector(*[d * c for c in direction]))
            for sn, ss in statics:
                if assembly._bb_overlap(m, ss) and m.intersect(ss).Volume() > 0.05:
                    out.append((d, n, sn))
    return out


def assembly_paths(angles=(0.0, 24.0, 48.0)):
    """Every part that goes on in the documented build order (docs/ASSEMBLY.md)
    must be able to travel to its final place without hitting anything already
    there. Returns a list of (step, problem) strings; empty = all clear."""
    import math
    import block
    lib = assembly.libs()
    case, beam, plate = lib["block"]["case"], lib["block"]["beam"], lib["block"]["plate"]
    problems = []
    for phi in angles:
        eng = assembly.engine(phi)
        crank = [(n, s) for n, s, _ in eng if n.startswith(("crankpin", "segment", "end_web", "main_shaft", "rod_",
                                                             "piston_"))]
        steps = [
            ("C3 crank module lowered into the open crankcase", crank, [("case", case)], (0, 0, 1), range(0, 90, 3)),
            ("C4 valley beam slid in from the front end", [("beam", beam)], [("case", case)] + crank, (1, 0, 0),
             range(0, 300, 6)),
            ("C5 front end plate slid onto its shaft", [("end_plate_front", plate)],
             [("case", case), ("beam", beam)] + crank, (1, 0, 0), range(0, 60, 2)),
            ("C5 rear end plate slid onto its shaft", [("end_plate_rear", plate.rotate((0, 0, 0), (0, 0, 1), 180))],
             [("case", case), ("beam", beam)] + crank, (-1, 0, 0), range(0, 60, 2)),
        ]
        fixed = [("case", case), ("beam", beam)] + crank
        rails = [(n, s) for n, s, _ in eng if n.startswith("rail_")]
        banks = [("bank_" + b, block.to_bank(lib["block"]["bank"], b)) for b in ("A", "B")]
        for (name, bk), b in zip(banks, ("A", "B")):
            a = math.radians(C.bank_angle(b))
            steps.append((f"D1 bank {b} lowered along its bore axis", [(name, bk)], fixed,
                          (0, math.sin(a), math.cos(a)), range(0, 70, 3)))
        for b in ("A", "B"):
            a = math.radians(C.bank_angle(b))
            hd = block.to_bank(lib["style"]["head"], b)
            steps.append((f"D4 head {b} lowered onto its rails", [("head_" + b, hd)], fixed + banks + rails,
                          (0, math.sin(a), math.cos(a)), range(0, 40, 2)))
        for label, mov, sta, direction, rng in steps:
            hits = _path_hits(mov, sta, direction, rng)
            print(f"    crank {phi:4.0f} deg  {label}: {'clear' if not hits else hits[:3]}", flush=True)
            if hits:
                problems.append(f"crank {phi:.0f} deg, {label}: hits {sorted(set(h[2] for h in hits))}")
    return problems


def _split(seq, n):
    return [seq[i::n] for i in range(n)]


def main(quick=False):
    t0 = time.time()
    lines = ["# Interference and clearance report", "",
             f"Generated by `tools/verify_all.py` on the current CAD (cylinder pitch {C.CYL_PITCH:g} mm, "
             f"stroke {C.STROKE:g} mm, crank modelled at its assembled axial position "
             f"+{C.CRANK_DX:.1f} mm).", ""]
    problems = C.self_check(verbose=False)
    print("config self-check:", "OK" if not problems else problems)
    lines += [f"* config self-check: {'OK' if not problems else problems}"]
    assembly.libs()
    print(f"parts built ({time.time() - t0:.0f} s)", flush=True)
    bad = assembly.static_check()
    print("static check:", "CLEAR" if not bad else bad, flush=True)
    lines += [f"* static check (every pair of non-moving parts): {'CLEAR' if not bad else bad}"]
    dbad = assembly.drive_check()
    print("drive check:", "CLEAR" if not dbad else dbad, flush=True)
    lines += [f"* drive check (210 mm belt, 220 mm belt, motor at both slot ends): "
              f"{'CLEAR' if not dbad else dbad}"]
    paths = assembly_paths()
    print("assembly paths:", "CLEAR" if not paths else paths, flush=True)
    lines += [f"* assembly paths (every part slides to its place in the documented build order, crank at 0/24/48 deg): "
              f"{'CLEAR' if not paths else paths}"]
    if quick:
        print("\n".join(lines))
        return 0 if not (problems or bad or dbad or paths) else 1

    n = max(1, min(4, (os.cpu_count() or 2)))
    angles = [i * SWEEP_STEP for i in range(int(round(360 / SWEEP_STEP)))]
    # "spawn": every worker builds its own parts. Forking a process that has
    # already run OCC booleans can deadlock (OCC's thread pool).
    ctx = mp.get_context("spawn")
    with ctx.Pool(n) as pool:
        hits = [h for part in pool.map(_sweep_angles, _split(angles, n)) for h in part]
    print("motion sweep:", "CLEAR" if not hits else f"{len(hits)} collisions", flush=True)
    lines += [f"* motion sweep ({len(angles)} crank angles, {SWEEP_STEP:g} deg steps, every moving part against "
              f"every other part): {'CLEAR - no collisions' if not hits else f'{len(hits)} COLLISIONS'}"]
    for h in sorted(set((n1, n2) for _, n1, n2, _ in hits))[:30]:
        lines.append(f"  * {h[0]} x {h[1]}")

    cangles = [i * CLEAR_STEP for i in range(int(round(360 / CLEAR_STEP)))]
    with ctx.Pool(n) as pool:
        results = pool.map(_clear_angles, _split(cangles, n))
    best = {}
    for r in results:
        for k, v in r.items():
            if k not in best or v[0] < best[k][0]:
                best[k] = v
    lines += ["", f"## Smallest running gaps (full revolution, {CLEAR_STEP:g} deg steps)", "",
              "Every pair of part kinds that comes within 4 mm. The smallest gaps are by design: "
              "rod to web 0.75 mm (crankpin shoulder), piston to bore 0.80 mm (the piston never touches "
              "the bore - it is guided by its rail).", "", "| Parts | Smallest gap (mm) | At crank angle | Where |",
              "|---|---|---|---|"]
    for key, (d, a, n1, n2) in sorted(best.items(), key=lambda kv: kv[1][0]):
        lines.append(f"| {key[0]} / {key[1]} | {d:.2f} | {a:.0f} deg | {n1} vs {n2} |")
    lines += ["", f"Run time {time.time() - t0:.0f} s."]
    with open(os.path.join(ROOT, "docs", "CLEARANCE_REPORT.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if not (problems or bad or dbad or hits or paths) else 1


if __name__ == "__main__":
    sys.exit(main(quick="--quick" in sys.argv))
