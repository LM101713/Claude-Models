#!/bin/bash
# Build the V8 controller PCB end to end: place (make_board.py) -> route (route.py, our own
# two-layer grid router) -> GND pours (finish_board.py) -> DRC -> Gerbers + drill + STEP.
#   tools/pcb/build_pcb.sh        (needs KiCad 7: apt install kicad kicad-footprints, python3-numpy)
set -e
cd "$(dirname "$0")/../.."
/usr/bin/python3 tools/pcb/make_board.py
/usr/bin/python3 tools/pcb/route.py
/usr/bin/python3 tools/pcb/finish_board.py
/usr/bin/python3 tools/pcb/drc.py
rm -rf pcb/gerbers && mkdir -p pcb/gerbers
kicad-cli pcb export gerbers -l F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o pcb/gerbers/ pcb/v8_controller.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-separate-th -o pcb/gerbers/ pcb/v8_controller.kicad_pcb
(cd pcb/gerbers && rm -f ../v8_controller_gerbers_JLCPCB.zip && zip -q ../v8_controller_gerbers_JLCPCB.zip *)
kicad-cli pcb export step --subst-models -f -o pcb/v8_controller.step pcb/v8_controller.kicad_pcb > /dev/null
tools/pcb/render_pcb.sh
echo "PCB build OK"
