"""V8 controller board: places every part, assigns the nets, adds the outline,
mounting holes and ground pours, and writes pcb/v8_controller_unrouted.kicad_pcb.
Routing is done by tools/pcb/route.py, then GND pours by finish_board.py (build_pcb.sh).

    /usr/bin/python3 tools/pcb/make_board.py        (system python: needs the pcbnew module)

The circuit is docs/ELECTRONICS_NETLIST.csv minus the LED outputs (decision D77):
U4 (74AHCT125), R4, R5, J4, J5 and their nets are gone. Board size and the 4
mounting holes match the pan floor panel standoffs (skin/params.json:
pan_board_holes, 85 x 65 mm pattern, 90 x 70 board).
"""
import os
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "pcb")
FP = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM
W, H = 90.0, 70.0
OX, OY = 100.0, 100.0          # board origin on the KiCad sheet


board = pcbnew.BOARD()
nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def P(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


def lib_fp(lib, name, ref, value, x, y, rot=0.0, pads=None):
    f = pcbnew.FootprintLoad(os.path.join(FP, lib + ".pretty"), name)
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    f.SetReference(ref)
    f.SetValue(value)
    board.Add(f)
    f.SetPosition(P(x, y))
    if rot:
        f.SetOrientationDegrees(rot)
    for pad in f.Pads():
        n = (pads or {}).get(pad.GetNumber())
        if n:
            pad.SetNet(net(n))
    return f


def header_fp(ref, value, pins, x0, y0, dx, dy, drill=1.0, size=1.7, silk=None):
    """Custom through-hole header: pins = [(number, net or None)], placed from
    (x0, y0) stepping (dx, dy). Square pad 1."""
    f = pcbnew.FOOTPRINT(board)
    f.SetReference(ref)
    f.SetValue(value)
    f.Reference().SetVisible(False)         # these get hand-drawn silkscreen labels instead
    f.Value().SetVisible(False)
    board.Add(f)
    f.SetPosition(P(x0, y0))
    for i, (num, n) in enumerate(pins):
        pad = pcbnew.PAD(f)
        pad.SetNumber(str(num))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetShape(pcbnew.PAD_SHAPE_RECT if i == 0 else pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.VECTOR2I(MM(size), MM(size)))
        pad.SetDrillSize(pcbnew.VECTOR2I(MM(drill), MM(drill)))
        pad.SetLayerSet(pad.PTHMask())
        f.Add(pad)
        pad.SetPos0(pcbnew.VECTOR2I(MM(i * dx), MM(i * dy)))
        pad.SetPosition(P(x0 + i * dx, y0 + i * dy))
        if n:
            pad.SetNet(net(n))
    return f


def silk_text(text, x, y, size=1.0, layer=pcbnew.F_SilkS, rot=0.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(size * 0.15))
    if rot:
        t.SetTextAngleDegrees(rot)
    board.Add(t)


def silk_rect(x0, y0, x1, y1, layer=pcbnew.F_SilkS):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(layer)
        s.SetWidth(MM(0.15))
        board.Add(s)


# ---------------------------------------------------------------- outline
for a, b in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a))
    s.SetEnd(P(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1))
    board.Add(s)
for i, (x, y) in enumerate(((2.5, 2.5), (87.5, 2.5), (2.5, 67.5), (87.5, 67.5))):
    lib_fp("MountingHole", "MountingHole_3.2mm_M3", f"H{i + 1}", "M3", x, y)

# ---------------------------------------------------------------- ESP32-DevKitC-32E (U1)
# two rows of 19, 22.86 mm apart (measured); pin 1 (3V3) at the antenna end. USB end at the left edge.
LEFT = ["V3", None, None, None, None, None, "KNOB", "HALL", "DRV_EN", "STEP", "DIR", "START", None, "GND",
        "RING_PWM", None, None, None, "V5_MCU"]                  # 3V3 EN VP VN 34 35 32 33 25 26 27 14 12 GND 13 SD2 SD3 CMD 5V
RIGHT = ["GND", None, "UART_TX", None, None, "TMC_UART", "GND", None, None, None, None, None, None, None, None,
         None, None, None, None]                                  # GND 23 22 TX RX 21 GND 19 18 5 17 16 4 0 2 15 SD1 SD0 CLK
LNAME = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "D2", "D3", "CMD", "5V"]
RNAME = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4", "0", "2", "15", "D1", "D0", "CLK"]
ESP_ROW = 22.86                       # measured on the real board 2026-11-24 (0.9 in, not 25.4)
ESP_X1, ESP_Y = 52.72, 9.0            # pin 1 position; rows step -2.54 in x towards the USB end
header_fp("U1", "ESP32-DevKitC-32E", [(i + 1, n) for i, n in enumerate(LEFT)], ESP_X1, ESP_Y, -2.54, 0.0)
header_fp("U1B", "ESP32-DevKitC-32E", [(i + 20, n) for i, n in enumerate(RIGHT)], ESP_X1, ESP_Y + ESP_ROW, -2.54, 0.0)
for i in range(19):
    x = ESP_X1 - 2.54 * i
    silk_text(LNAME[i], x, ESP_Y + 2.2, 0.8, rot=90)
    silk_text(RNAME[i], x, ESP_Y + ESP_ROW - 2.2, 0.8, rot=90)
silk_rect(ESP_X1 - 2.54 * 18 - 3.5, ESP_Y - 1.25, ESP_X1 + 5.2, ESP_Y + ESP_ROW + 1.25)
silk_text("ESP32-DevKitC-32E  (USB this end <)", 30.0, ESP_Y + ESP_ROW / 2, 1.1)
silk_text("antenna", ESP_X1 + 4.5, ESP_Y + ESP_ROW / 2, 0.9, rot=90)

# ---------------------------------------------------------------- TMC2209 stepstick (U3)
TX0, TY = 62.0, 6.0
J1 = ["DRV_EN", "GND", "GND", "TMC_UART", None, "GND", "STEP", "DIR"]     # EN MS1 MS2 PDN_UART PDN2 CLK STEP DIR
J2 = ["V12", "GND", "MOT_A2", "MOT_A1", "MOT_B1", "MOT_B2", "V3", "GND"]   # VM GND A2 A1 B1 B2 VIO GND
header_fp("U3", "BTT TMC2209 V1.3", [(i + 1, n) for i, n in enumerate(J1)], TX0, TY, 2.54, 0.0)
header_fp("U3B", "BTT TMC2209 V1.3", [(i + 9, n) for i, n in enumerate(J2)], TX0, TY + 12.7, 2.54, 0.0)
for i, (a, b) in enumerate(zip(["EN", "M1", "M2", "PDN", "PD2", "CLK", "STP", "DIR"], ["VM", "GND", "2B", "2A", "1A", "1B", "VIO", "GND"])):
    silk_text(a, TX0 + 2.54 * i, TY + 2.4, 0.8, rot=90)
    silk_text(b, TX0 + 2.54 * i, TY + 12.7 - 2.4, 0.8, rot=90)
silk_rect(TX0 - 1.8, TY - 1.8, TX0 + 2.54 * 7 + 1.8, TY + 12.7 + 1.8)
silk_text("TMC2209  EN pin here ^", TX0 + 8.9, TY + 6.35, 0.9)

# ---------------------------------------------------------------- Pololu regulator (U2)
# D24V25F5 pin order is not confirmed, so the board does not assume it: three labelled
# pads (12V / GND / 5V) take short wire links from the regulator's own labelled pins
# VIN / GND / VOUT. Its EN / SHDN / PG pins stay unconnected. The regulator sits on the
# outlined area, held by double-sided foam tape.
RX0, RY = 63.27, 30.5
header_fp("U2", "Pololu D24V25F5 5V", [(1, "V12"), (2, "GND"), (3, "V5")], RX0, RY, 2.54, 0.0, drill=1.1, size=2.0)
for i, nm in enumerate(["12V", "GND", "5V"]):
    silk_text(nm, RX0 + 2.54 * i, RY - 2.6, 0.8, rot=90)
silk_text("to VIN GND VOUT", RX0 + 2.54, RY + 2.2, 0.8)
silk_rect(59.5, 34.0, 77.5, 52.0)                       # 17.8 mm square module, taped here
silk_text("Pololu D24V25F5", 68.5, 41.5, 1.0)
silk_text("(foam tape)", 68.5, 43.5, 0.8)

# ---------------------------------------------------------------- connectors (JST XH, vertical)
JST = "Connector_JST"
lib_fp(JST, "JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", "J1", "12V IN", 74.0, 63.0, 0, {"1": "12V_IN", "2": "GND"})
lib_fp(JST, "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical", "J2", "MOTOR", 84.5, 28.0, 90, {"1": "MOT_A1", "2": "MOT_A2", "3": "MOT_B1", "4": "MOT_B2"})
lib_fp(JST, "JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical", "J3", "HALL", 9.0, 63.0, 0, {"1": "V3", "2": "GND", "3": "HALL"})
lib_fp(JST, "JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical", "J6", "KNOB", 22.0, 63.0, 0, {"1": "V3", "2": "KNOB", "3": "GND"})
lib_fp(JST, "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical", "J7", "START", 35.0, 63.0, 0, {"1": "START", "2": "GND", "3": "V12", "4": "RING_K"})
for ref, x, y, txt in (("J1", 75.25, 68.3, "12V IN + -"), ("J3", 11.5, 58.5, "HALL 3V G S"), ("J6", 24.5, 58.5, "KNOB 3V W G"),
                       ("J7", 38.75, 58.5, "START S G 12V LED")):
    silk_text(txt, x, y, 0.9)
silk_text("MOTOR A1 A2 B1 B2", 80.5, 28.0 + 3.75, 0.9, rot=90)

# ---------------------------------------------------------------- power input chain
lib_fp("Capacitor_THT", "C_Disc_D7.5mm_W5.0mm_P5.00mm", "F1", "PPTC 2A", 63.0, 63.0, 0, {"1": "12V_IN", "2": "12V_F"})
lib_fp("Diode_THT", "D_DO-201AD_P15.24mm_Horizontal", "D1", "1N5822", 70.0, 57.0, 180, {"2": "12V_F", "1": "V12"})
lib_fp("Diode_THT", "D_DO-15_P10.16mm_Horizontal", "D2", "P6KE18A", 48.0, 48.0, 0, {"1": "V12", "2": "GND"})
lib_fp("Capacitor_THT", "CP_Radial_D10.0mm_P5.00mm", "C1", "220uF 50V+", 81.0, 53.5, 0, {"1": "V12", "2": "GND"})
lib_fp("Capacitor_THT", "CP_Radial_D8.0mm_P3.50mm", "C2", "470uF 25V+", 81.25, 43.0, 0, {"1": "V5", "2": "GND"})
lib_fp("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm", "C3", "100nF", 3.5, 41.5, 0, {"1": "V5", "2": "GND"})
lib_fp("Diode_THT", "D_DO-41_SOD81_P10.16mm_Horizontal", "D3", "1N5817", 16.0, 41.5, 0, {"2": "V5", "1": "V5_MCU"})

# ---------------------------------------------------------------- small signal parts
RES = ("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal")
lib_fp(*RES, "R1", "1k", 32.0, 41.5, 0, {"1": "UART_TX", "2": "TMC_UART"})
lib_fp(*RES, "R3", "10k", 32.0, 46.0, 0, {"1": "V3", "2": "DRV_EN"})
lib_fp(*RES, "R6", "10k", 4.0, 47.0, 0, {"1": "V3", "2": "HALL"})
lib_fp(*RES, "R7", "1k", 32.0, 50.5, 0, {"1": "RING_PWM", "2": "Q1_BASE"})
lib_fp(*RES, "R8", "100k", 32.0, 55.0, 0, {"1": "Q1_BASE", "2": "GND"})
lib_fp("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm", "C4", "10nF", 4.0, 52.0, 0, {"1": "HALL", "2": "GND"})
lib_fp("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm", "C5", "100nF", 17.0, 52.0, 0, {"1": "KNOB", "2": "GND"})
lib_fp("Package_TO_SOT_THT", "TO-92_Inline_Wide", "Q1", "2N3904", 45.5, 56.0, 0, {"1": "GND", "2": "Q1_BASE", "3": "RING_K"})

silk_text("V8 display engine controller  rev A  2026-11", 45.0, 68.3, 1.0)
for f in board.GetFootprints():                 # the connector labels above replace their references
    if f.GetReference() in ("J1", "J3", "J6", "J7"):
        f.Reference().SetVisible(False)
    if f.GetReference() == "F1":
        f.Reference().SetPosition(P(65.5, 67.3))
    if f.GetReference() == "C1":
        f.Reference().SetPosition(P(83.5, 59.6))
    if f.GetReference() == "D1":
        f.Reference().SetPosition(P(62.4, 57.0))

# ---------------------------------------------------------------- design rules
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(2)
nc = ds.m_NetSettings.m_DefaultNetClass
nc.SetTrackWidth(MM(0.5))
nc.SetClearance(MM(0.25))
nc.SetViaDiameter(MM(0.9))
nc.SetViaDrill(MM(0.45))
ds.m_MinClearance = MM(0.2)
ds.m_TrackMinWidth = MM(0.25)

os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "v8_controller_unrouted.kicad_pcb")
board.Save(path)
print("wrote", path, "nets:", len(nets), "footprints:", len(board.GetFootprints()))
