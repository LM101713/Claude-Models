#!/usr/bin/env python3
"""Review renders of the V1.1 changes (uses the P001 three.js studio in ../render).
    python render_v11.py && node render_v11.mjs"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "render"))
import drydock_v11 as dd
import scenes as sc
from build123d import Pos, Rot, Box
sc.OUT = HERE.parent / "render" / "out"

P = dd.Params(); D = P.d()
parts = dd.build_parts(P, sizes=[P.spool_bore])
lip_t = P.face_thickness - P.window_seat_depth
win_l = Rot(0, 0, P.window_turn_deg) * (Pos(0, 0, -D["cap_out"] + lip_t) * parts["window"])
# cap seen from the inside (plug up), window locked, then cut in half to show the ledge
cap_in = [(parts["cap"], "charcoal", None, None), (win_l, "clear", None, None)]
sc.write_scene("v11_cap_inside", cap_in)
half = Pos(0, -60, 0) * Box(200, 120, 200)
sc.write_scene("v11_cap_section", [(s & half, c, None, None) for s, c, _, _ in cap_in])
# window alone
sc.write_scene("v11_window", [(parts["window"], "clear", None, None)])
# body socket end, outside, showing the detent tongues and moved lock marks
body = parts["body"]
sc.write_scene("v11_body", [(body, "charcoal", None, None)])
# fit-test plate
g, L = parts["fit_gauge"], parts["fit_gauge_len"]
ad = parts["adapters"][P.spool_bore]
items = [(Pos(-58, 0, 0) * g, "charcoal", "Double gauge (both print orientations, vent row)", None),
         (Pos(0, 0, D["cap_out"]) * parts["cap"], "charcoal", "Cap", None)]
for i, (d, tg) in enumerate(parts["fit_tune"].items()):
    items.append((Pos(58, -28 + 56 * i, 0) * tg, "charcoal", f"Detent ring {P.detent_interference + d:.2f} mm", None))
items.append((Pos(-58, 52, 0) * parts["window"], "clear", "Window", None))
items.append((Pos(0, 58, 0) * ad, "orange", "55 mm adapter", None))
sc.write_scene("v11_fitplate", items)
print("ok")
