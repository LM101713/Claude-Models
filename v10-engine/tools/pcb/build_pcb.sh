#!/bin/bash
# Build the V8 controller PCB end to end: place (make_board.py) -> autoroute (Freerouting)
# -> import routes, fill GND pours (finish_board.py) -> DRC -> Gerbers + drill + previews.
#   FREEROUTING=/path/to/freerouting-1.9.0.jar tools/pcb/build_pcb.sh
set -e
cd "$(dirname "$0")/../.."
FR=${FREEROUTING:?set FREEROUTING to the freerouting-1.9.0.jar path}
python3 tools/pcb/make_board.py
java -Djava.awt.headless=true -jar "$FR" -de pcb/v8_controller.dsn -do pcb/v8_controller.ses -mp 40 -dct 0 > pcb/freerouting.log 2>&1 || true
python3 tools/pcb/finish_board.py
kicad-cli pcb drc --severity-error --exit-code-violations -o pcb/drc_report.txt pcb/v8_controller.kicad_pcb
mkdir -p pcb/gerbers
kicad-cli pcb export gerbers -l F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o pcb/gerbers/ pcb/v8_controller.kicad_pcb
kicad-cli pcb export drill --format excellon -o pcb/gerbers/ pcb/v8_controller.kicad_pcb
(cd pcb/gerbers && rm -f ../v8_controller_gerbers_JLCPCB.zip && zip -q ../v8_controller_gerbers_JLCPCB.zip *)
kicad-cli pcb export step --subst-models -f -o pcb/v8_controller.step pcb/v8_controller.kicad_pcb
echo "PCB build OK"
