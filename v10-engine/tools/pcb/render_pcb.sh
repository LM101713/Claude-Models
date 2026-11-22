#!/bin/bash
# Export the copper / mask / silk layers and render the PCB pictures into pcb/img/.
set -e
cd "$(dirname "$0")/../.."
mkdir -p pcb/layers
for L in F.Cu B.Cu F.SilkS B.SilkS F.Mask B.Mask; do
  kicad-cli pcb export svg -l $L,Edge.Cuts --black-and-white --exclude-drawing-sheet --page-size-mode 2 \
    -o pcb/layers/$L.svg pcb/v8_controller.kicad_pcb > /dev/null
done
/usr/bin/python3 - <<'PY'
import json, pcbnew
b = pcbnew.LoadBoard("pcb/v8_controller.kicad_pcb")
out = []
for f in b.GetFootprints():
    p = f.GetPosition()
    out.append(dict(ref=f.GetReference(), fp=str(f.GetFPID().GetLibItemName()), value=f.GetValue(),
                    x=pcbnew.ToMM(p.x) - 100, y=pcbnew.ToMM(p.y) - 100, rot=f.GetOrientationDegrees(),
                    pads=[[pcbnew.ToMM(q.GetPosition().x) - 100, pcbnew.ToMM(q.GetPosition().y) - 100] for q in f.Pads()]))
json.dump(out, open("pcb/footprints.json", "w"), indent=1)
PY
python3.13 tools/pcb/render_pcb.py pcb/layers
