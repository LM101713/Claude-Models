#!/usr/bin/env python3
"""Export the real DRYDOCK V1.1 assembly (caps locked, 55 mm adapters, standard opaque window
blank) as a GLB for the thumbnail render. Geometry comes straight from drydock_v11.py."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
V11 = HERE.parents[1] / "v1.1"
sys.path.insert(0, str(V11)); sys.path.insert(0, str(HERE.parents[1] / "render"))
import drydock_v11 as dd
import scenes as sc
sc.OUT = HERE / "out"
P = dd.Params(); D = P.d()
parts = dd.build_parts(P, sizes=[P.spool_bore])
items = []
for s, col, lab in dd.assembly(P, parts, explode=0.0):
    if lab == "window":
        col = "charcoal"          # standard version: opaque blank (no clear filament)
    items.append((s, col, lab, None))
sc.write_scene("drydock_v11_assembly", items)
(sc.OUT / "dims.json").write_text(json.dumps({"L_body": D["L_body"], "cap_out": D["cap_out"], "bore": P.spool_bore, "width": P.spool_width}))
