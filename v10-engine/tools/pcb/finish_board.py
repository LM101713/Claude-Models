"""Add ground pours on both layers to the routed board, fill them and save
pcb/v8_controller.kicad_pcb. Run by tools/pcb/build_pcb.sh."""
import os
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(ROOT, "pcb")
MM = pcbnew.FromMM
OX, OY, W, H = 100.0, 100.0, 90.0, 70.0

board = pcbnew.LoadBoard(os.path.join(PCB, "v8_controller_routed.kicad_pcb"))

gnd = board.FindNet("GND")
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetLocalClearance(MM(0.4))
    z.SetMinThickness(MM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.4))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)):
        ol.Append(MM(OX + x), MM(OY + y))
    board.Add(z)

# GND pads join the pour solidly: several sit between tracks where a 2-spoke thermal
# relief can't form. Every GND pad is also track-routed. (A 60 W iron solders these fine.)
for f in board.GetFootprints():
    for pad in f.Pads():
        if pad.GetNetname() == "GND":
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
out = os.path.join(PCB, "v8_controller.kicad_pcb")
board.Save(out)
tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
print(f"wrote {out}: {len(tracks)} track segments, {len(vias)} vias")
