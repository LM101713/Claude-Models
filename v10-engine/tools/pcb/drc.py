"""Design-rule check of pcb/v8_controller.kicad_pcb (KiCad 7 has no `kicad-cli pcb drc`).
Writes pcb/drc_report.txt; exits 1 on any error-level violation or unconnected item."""
import os
import re
import sys

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
path = os.path.join(ROOT, "pcb", "v8_controller.kicad_pcb")
rep = os.path.join(ROOT, "pcb", "drc_report.txt")
board = pcbnew.LoadBoard(path)
pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(rep).read()
viol = re.search(r"\*\* Found (\d+) DRC violations", txt)
unc = re.search(r"\*\* Found (\d+) unconnected pads", txt)
errors = len(re.findall(r"Severity: error", txt)) - (int(unc.group(1)) if unc else 0)
print(txt.splitlines()[0] if txt else "", "|", viol.group(0) if viol else "?", "|", unc.group(0) if unc else "?", "| error-level:", errors)
sys.exit(1 if errors or (unc and int(unc.group(1))) else 0)
