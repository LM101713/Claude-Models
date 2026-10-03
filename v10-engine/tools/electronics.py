"""Electronics data model -> netlist, pin tables and drawings.

Everything about the controller board and the harnesses is defined ONCE here
(parts, pins, nets, wires). This script writes:

  docs/ELECTRONICS_NETLIST.csv          every pin and the net it belongs to
  docs/ELECTRONICS_TABLES.md            connector pin-outs, harness and board tables
  docs/img/controller_schematic.png     net-label schematic of the controller board
  docs/img/wiring_overview.png          harness diagram (what plugs where, lengths)

and checks the model: every net has at least two pins (or is marked NC), no pin
is on two nets, every ESP32 GPIO matches firmware/v10_engine/config.h.

    python tools/electronics.py
"""

import csv
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
IMG = os.path.join(DOCS, "img")

# ---------------------------------------------------------------------------
# parts on the controller board: refdes -> (value / part, description, pins)
# ---------------------------------------------------------------------------
PARTS = {
    "U1": ("ESP32-DevKitC-32E", "controller (Espressif, ESP32-WROOM-32E, 38 pin)",
           ["5V", "GND", "3V3", "IO13", "IO14", "IO18", "IO19", "IO21", "IO22", "IO25", "IO26", "IO27",
            "IO32", "IO33"]),
    "U2": ("Pololu D24V22F5", "5 V 2.5 A step-down regulator", ["VIN", "GND", "VOUT", "EN", "PG"]),
    "U3": ("BTT TMC2209 V1.3", "stepper driver (UART mode)",
           ["EN", "MS1", "MS2", "PDN_UART", "PDN2", "CLK", "STEP", "DIR",
            "VM", "GND_P", "A2", "A1", "B1", "B2", "VIO", "GND_L"]),
    "U4": ("SN74AHCT125N", "3.3 V -> 5 V buffer for the LED data (DIP-14 in a socket)",
           [str(i) for i in range(1, 15)]),
    "Q1": ("2N3904", "NPN, switches the START ring LED", ["E", "B", "C"]),
    "F1": ("Littelfuse RXEF200", "2.0 A resettable fuse (PTC)", ["1", "2"]),
    "D1": ("1N5822", "3 A Schottky: reverse-polarity protection", ["A", "K"]),
    "D2": ("P6KE18A", "18 V TVS: clamps plug-in spikes on the 12 V rail", ["A", "K"]),
    "D3": ("1N5817", "1 A Schottky: stops USB back-feeding the LED rail", ["A", "K"]),
    "C1": ("220 uF 35 V", "electrolytic, 12 V bulk at the driver (low ESR)", ["+", "-"]),
    "C2": ("470 uF 16 V", "electrolytic, 5 V LED rail reservoir", ["+", "-"]),
    "C3": ("100 nF", "ceramic, U4 supply decoupling", ["1", "2"]),
    "C4": ("10 nF", "ceramic, hall input filter", ["1", "2"]),
    "C5": ("100 nF", "ceramic, speed knob filter", ["1", "2"]),
    "R1": ("1 k", "TMC2209 single-wire UART (TX side)", ["1", "2"]),
    "R3": ("10 k", "keeps the driver OFF until the firmware enables it", ["1", "2"]),
    "R4": ("330", "LED data A series resistor", ["1", "2"]),
    "R5": ("330", "LED data B series resistor", ["1", "2"]),
    "R6": ("10 k", "hall sensor pull-up", ["1", "2"]),
    "R7": ("1 k", "Q1 base", ["1", "2"]),
    "R8": ("100 k", "Q1 base pull-down (ring LED off during boot)", ["1", "2"]),
    "J1": ("JST XH 2-pin", "POWER in (from the rocker switch)", ["1", "2"]),
    "J2": ("JST XH 4-pin", "MOTOR", ["1", "2", "3", "4"]),
    "J3": ("JST XH 3-pin", "HALL sensor", ["1", "2", "3"]),
    "J4": ("JST XH 3-pin", "LED strip bank A (cylinders 1-5)", ["1", "2", "3"]),
    "J5": ("JST XH 3-pin", "LED strip bank B (cylinders 6-10)", ["1", "2", "3"]),
    "J6": ("JST XH 3-pin", "SPEED knob", ["1", "2", "3"]),
    "J7": ("JST XH 4-pin", "START button + ring LED", ["1", "2", "3", "4"]),
}

# U4 pin names for the drawing (standard '125 pinout)
U4_NAMES = {"1": "1OE", "2": "1A", "3": "1Y", "4": "2OE", "5": "2A", "6": "2Y", "7": "GND",
            "8": "3Y", "9": "3A", "10": "3OE", "11": "4Y", "12": "4A", "13": "4OE", "14": "VCC"}
U3_HEADER = {"EN": "J1-1", "MS1": "J1-2", "MS2": "J1-3", "PDN_UART": "J1-4", "PDN2": "J1-5", "CLK": "J1-6",
             "STEP": "J1-7", "DIR": "J1-8", "VM": "J2-1", "GND_P": "J2-2", "A2": "J2-3", "A1": "J2-4",
             "B1": "J2-5", "B2": "J2-6", "VIO": "J2-7", "GND_L": "J2-8"}

# ---------------------------------------------------------------------------
# nets: name -> pins ("REF.PIN"). NC_* nets are deliberately unconnected.
# ---------------------------------------------------------------------------
NETS = {
    "12V_IN":   ["J1.1", "F1.1"],
    "12V_F":    ["F1.2", "D1.A"],
    "V12":      ["D1.K", "D2.K", "C1.+", "U3.VM", "U2.VIN", "J7.3"],
    "GND":      ["J1.2", "D2.A", "C1.-", "C2.-", "C3.2", "C4.2", "C5.2", "U1.GND", "U2.GND", "U3.GND_P",
                 "U3.GND_L", "U3.MS1", "U3.MS2", "U3.CLK", "U4.7", "U4.1", "U4.4", "U4.9", "U4.12",
                 "Q1.E", "R8.2", "J3.2", "J4.2", "J5.2", "J6.3", "J7.2"],
    "V5":       ["U2.VOUT", "C2.+", "D3.A", "U4.14", "C3.1", "U4.10", "U4.13", "J4.1", "J5.1"],
    "V5_MCU":   ["D3.K", "U1.5V"],
    "V3":       ["U1.3V3", "U3.VIO", "R3.1", "R6.1", "J3.1", "J6.1"],
    "DRV_EN":   ["U1.IO25", "U3.EN", "R3.2"],
    "STEP":     ["U1.IO26", "U3.STEP"],
    "DIR":      ["U1.IO27", "U3.DIR"],
    "TMC_UART": ["U3.PDN_UART", "U1.IO21", "R1.2"],
    "UART_TX":  ["U1.IO22", "R1.1"],
    "HALL":     ["U1.IO33", "R6.2", "C4.1", "J3.3"],
    "KNOB":     ["U1.IO32", "C5.1", "J6.2"],
    "START":    ["U1.IO14", "J7.1"],
    "RING_PWM": ["U1.IO13", "R7.1"],
    "Q1_BASE":  ["R7.2", "Q1.B", "R8.1"],
    "RING_K":   ["Q1.C", "J7.4"],
    "LEDA_3V":  ["U1.IO18", "U4.2"],
    "LEDA_5V":  ["U4.3", "R4.1"],
    "DATA_A":   ["R4.2", "J4.3"],
    "LEDB_3V":  ["U1.IO19", "U4.5"],
    "LEDB_5V":  ["U4.6", "R5.1"],
    "DATA_B":   ["R5.2", "J5.3"],
    "MOT_A1":   ["U3.A1", "J2.1"],
    "MOT_A2":   ["U3.A2", "J2.2"],
    "MOT_B1":   ["U3.B1", "J2.3"],
    "MOT_B2":   ["U3.B2", "J2.4"],
    "NC_PDN2":  ["U3.PDN2"],
    "NC_3Y":    ["U4.8"],
    "NC_4Y":    ["U4.11"],
    "NC_EN":    ["U2.EN"],
    "NC_PG":    ["U2.PG"],
}

# ---------------------------------------------------------------------------
# harnesses: board connector pin -> off-board part terminal
# (wire, from, to, colour, gauge AWG, signal)
# ---------------------------------------------------------------------------
HARNESS = {
    "W1 POWER (rear panel)": dict(length=250, parts="12 V DC jack (panel), illuminated rocker switch", wires=[
        ("DC jack centre pin (+12 V)", "rocker IN terminal", "red", 20, "+12 V unswitched"),
        ("rocker OUT terminal", "J1-1", "red", 20, "+12 V switched"),
        ("DC jack sleeve (GND)", "J1-2", "black", 20, "ground"),
        ("DC jack sleeve (GND)", "rocker LAMP terminal", "black", 22, "rocker lamp return"),
    ]),
    "W2 MOTOR": dict(length=350, parts="NEMA17 17HS4401S", wires=[
        ("J2-1", "motor black (A+)", "black", 24, "coil A"),
        ("J2-2", "motor green (A-)", "green", 24, "coil A"),
        ("J2-3", "motor red (B+)", "red", 24, "coil B"),
        ("J2-4", "motor blue (B-)", "blue", 24, "coil B"),
    ]),
    "W3 HALL": dict(length=200, parts="DRV5033AJQLPG hall switch (TO-92)", wires=[
        ("J3-1", "sensor pin 1 VCC", "red", 26, "3.3 V"),
        ("J3-2", "sensor pin 2 GND", "black", 26, "ground"),
        ("J3-3", "sensor pin 3 OUT", "white", 26, "LOW = magnet"),
    ]),
    "W4 LED BANK A": dict(length=550, parts="WS2812B strip, 15 LEDs, head A", wires=[
        ("J4-1", "strip +5V pad (data-in end)", "red", 24, "5 V"),
        ("J4-2", "strip GND pad", "black", 24, "ground"),
        ("J4-3", "strip DIN pad", "green", 24, "LED data"),
    ]),
    "W5 LED BANK B": dict(length=550, parts="WS2812B strip, 15 LEDs, head B", wires=[
        ("J5-1", "strip +5V pad (data-in end)", "red", 24, "5 V"),
        ("J5-2", "strip GND pad", "black", 24, "ground"),
        ("J5-3", "strip DIN pad", "green", 24, "LED data"),
    ]),
    "W6 SPEED KNOB": dict(length=250, parts="10 k linear pot, M7 bushing", wires=[
        ("J6-1", "pot terminal 3 (clockwise end)", "red", 26, "3.3 V"),
        ("J6-2", "pot terminal 2 (wiper)", "yellow", 26, "speed signal"),
        ("J6-3", "pot terminal 1 (counter-clockwise end)", "black", 26, "ground"),
    ]),
    "W7 START": dict(length=300, parts="16 mm momentary button, 12 V ring LED", wires=[
        ("J7-1", "button NO terminal", "white", 26, "START (to GND when pressed)"),
        ("J7-2", "button C terminal", "black", 26, "ground"),
        ("J7-3", "button LED + terminal", "red", 26, "+12 V"),
        ("J7-4", "button LED - terminal", "blue", 26, "LED return (switched by Q1)"),
    ]),
}

GPIO_FROM_FIRMWARE = {"PIN_STEP": "IO26", "PIN_DIR": "IO27", "PIN_EN": "IO25", "PIN_TMC_TX": "IO22",
                      "PIN_TMC_RX": "IO21", "PIN_HALL": "IO33", "PIN_POT": "IO32", "PIN_BUTTON": "IO14",
                      "PIN_BUTTON_LED": "IO13", "PIN_LED_A": "IO18", "PIN_LED_B": "IO19"}
GPIO_NET = {"PIN_STEP": "STEP", "PIN_DIR": "DIR", "PIN_EN": "DRV_EN", "PIN_TMC_TX": "UART_TX",
            "PIN_TMC_RX": "TMC_UART", "PIN_HALL": "HALL", "PIN_POT": "KNOB", "PIN_BUTTON": "START",
            "PIN_BUTTON_LED": "RING_PWM", "PIN_LED_A": "LEDA_3V", "PIN_LED_B": "LEDB_3V"}


def check():
    problems = []
    seen = {}
    for net, pins in NETS.items():
        if len(pins) < 2 and not net.startswith("NC_"):
            problems.append(f"net {net} has a single pin")
        for p in pins:
            ref, pin = p.split(".", 1)
            if ref not in PARTS:
                problems.append(f"{p}: unknown part")
            elif pin not in PARTS[ref][2]:
                problems.append(f"{p}: {ref} has no pin {pin}")
            if p in seen:
                problems.append(f"{p} is on nets {seen[p]} and {net}")
            seen[p] = net
    for ref, (_, _, pins) in PARTS.items():
        for pin in pins:
            if f"{ref}.{pin}" not in seen:
                problems.append(f"{ref}.{pin} is not on any net")
    # firmware pins
    cfg = open(os.path.join(ROOT, "firmware", "v10_engine", "config.h")).read()
    for name, gpio in GPIO_FROM_FIRMWARE.items():
        m = re.search(rf"{name}\s*=\s*(\d+);", cfg)
        if not m or f"IO{m.group(1)}" != gpio:
            problems.append(f"firmware {name} = {m.group(1) if m else '?'} but the board uses {gpio}")
        if f"U1.{gpio}" not in NETS[GPIO_NET[name]]:
            problems.append(f"{name}: U1.{gpio} not on net {GPIO_NET[name]}")
    return problems


def write_netlist():
    path = os.path.join(DOCS, "ELECTRONICS_NETLIST.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["net", "part", "pin", "pin name / header", "part value"])
        for net, pins in NETS.items():
            for p in pins:
                ref, pin = p.split(".", 1)
                name = U4_NAMES.get(pin, pin) if ref == "U4" else (U3_HEADER.get(pin, pin) if ref == "U3" else pin)
                w.writerow([net, ref, pin, name, PARTS[ref][0]])
    return path


def write_tables():
    pin_net = {p: n for n, ps in NETS.items() for p in ps}
    L = ["<!-- GENERATED by tools/electronics.py - edit the data model there, not this file -->", ""]
    L += ["## Controller board parts", "", "| Ref | Part | Purpose |", "|---|---|---|"]
    for ref, (val, desc, _) in PARTS.items():
        L.append(f"| {ref} | {val} | {desc} |")
    L += ["", "## ESP32 pin use", "", "| ESP32 pin | Net | Goes to |", "|---|---|---|"]
    for pin in PARTS["U1"][2]:
        net = pin_net[f"U1.{pin}"]
        others = [p for p in NETS[net] if p != f"U1.{pin}"]
        L.append(f"| {pin.replace('IO', 'GPIO')} | {net} | {', '.join(others)} |")
    L += ["", "## TMC2209 module pins (BIGTREETECH V1.3 header numbering)", "",
          "| Module pin | Header | Net |", "|---|---|---|"]
    for pin in PARTS["U3"][2]:
        L.append(f"| {pin} | {U3_HEADER[pin]} | {pin_net[f'U3.{pin}']} |")
    L += ["", "## Board connectors", ""]
    for ref in ("J1", "J2", "J3", "J4", "J5", "J6", "J7"):
        L.append(f"**{ref} - {PARTS[ref][1]}** ({PARTS[ref][0]}, pin 1 marked on the board)")
        L.append("")
        L.append("| Pin | Net |")
        L.append("|---|---|")
        for pin in PARTS[ref][2]:
            L.append(f"| {pin} | {pin_net[f'{ref}.{pin}']} |")
        L.append("")
    L += ["## Harnesses", ""]
    for name, h in HARNESS.items():
        L.append(f"**{name}** - to {h['parts']}, cut length {h['length']} mm")
        L.append("")
        L.append("| From | To | Colour | AWG | Signal |")
        L.append("|---|---|---|---|---|")
        for a, b, col, awg, sig in h["wires"]:
            L.append(f"| {a} | {b} | {col} | {awg} | {sig} |")
        L.append("")
    L += ["## Netlist", "", "| Net | Pins |", "|---|---|"]
    for net, pins in NETS.items():
        L.append(f"| {net} | {', '.join(pins)} |")
    path = os.path.join(DOCS, "ELECTRONICS_TABLES.md")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


# ---------------------------------------------------------------------------
# drawings
# ---------------------------------------------------------------------------
NET_COLOUR = {"V12": "#d62728", "12V_IN": "#d62728", "12V_F": "#d62728", "V5": "#ff7f0e", "V5_MCU": "#ff7f0e",
              "V3": "#9467bd", "GND": "#222222"}


def _ncol(net):
    if net in NET_COLOUR:
        return NET_COLOUR[net]
    if net.startswith("MOT"):
        return "#8c564b"
    if net.startswith(("DATA", "LED")):
        return "#2ca02c"
    if net.startswith("NC_"):
        return "#aaaaaa"
    return "#1f77b4"


def draw_schematic():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    pin_net = {p: n for n, ps in NETS.items() for p in ps}
    # (ref, x, y, left pins, right pins)
    layout = [
        ("U1", 7.0, 10.6, ["5V", "GND", "3V3"], ["IO13", "IO14", "IO18", "IO19", "IO21", "IO22", "IO25", "IO26",
                                                  "IO27", "IO32", "IO33"]),
        ("U3", 15.6, 10.6, ["EN", "MS1", "MS2", "PDN_UART", "PDN2", "CLK", "STEP", "DIR"],
         ["VM", "GND_P", "A2", "A1", "B1", "B2", "VIO", "GND_L"]),
        ("U4", 7.0, 3.6, ["1", "2", "3", "4", "5", "6", "7"], ["14", "13", "12", "11", "10", "9", "8"]),
        ("U2", 16.2, 4.6, ["VIN", "GND"], ["VOUT", "EN", "PG"]),
        ("Q1", 16.2, 1.4, ["B", "E"], ["C"]),
    ]
    fig, ax = plt.subplots(figsize=(17, 11))
    ax.set_xlim(0, 30)
    ax.set_ylim(-1, 15.6)
    ax.axis("off")
    ax.text(0.2, 15.2, "V10 engine - controller board (net-label schematic)", fontsize=16, weight="bold")
    ax.text(0.2, 14.7, "Pins with the same net name are connected. Colours: red 12 V, orange 5 V, purple 3.3 V, "
            "black GND, blue signals, green LED data, brown motor. Generated by tools/electronics.py.",
            fontsize=9, color="#444")
    pitch = 0.42
    for ref, x, y, left, right in layout:
        n = max(len(left), len(right))
        h = n * pitch + 0.5
        w = 4.4 if ref == "U3" else 3.0
        ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.02", fc="#f4f4f8", ec="#333"))
        ax.text(x + w / 2, y + 0.18, f"{ref}  {PARTS[ref][0]}", ha="center", fontsize=10, weight="bold")
        for side, pins in ((-1, left), (1, right)):
            for i, pin in enumerate(pins):
                py = y - 0.45 - i * pitch
                net = pin_net[f"{ref}.{pin}"]
                label = U4_NAMES.get(pin, pin) if ref == "U4" else (f"{pin} ({U3_HEADER[pin]})" if ref == "U3" else pin)
                px = x if side < 0 else x + w
                ax.text(px - side * 0.1, py, label, ha="left" if side < 0 else "right", va="center", fontsize=7.5)
                ax.plot([px, px + side * 0.7], [py, py], color=_ncol(net), lw=2)
                ax.text(px + side * 0.78, py, net, ha="right" if side < 0 else "left", va="center", fontsize=8,
                        color=_ncol(net), weight="bold")
    # small parts as a list with their nets
    small = ["F1", "D1", "D2", "D3", "C1", "C2", "C3", "C4", "C5", "R1", "R3", "R4", "R5", "R6", "R7", "R8"]
    ax.text(21.6, 14.0, "Small parts", fontsize=11, weight="bold")
    yy = 13.5
    for ref in small:
        pins = PARTS[ref][2]
        nets = [pin_net[f"{ref}.{p}"] for p in pins]
        ax.text(21.6, yy, f"{ref}  {PARTS[ref][0]}", fontsize=8.5, weight="bold")
        ax.text(25.7, yy, "  -  ".join(f"{p}: {n}" for p, n in zip(pins, nets)), fontsize=8.5,
                color=_ncol(nets[0] if nets[0] != "GND" else nets[-1]))
        yy -= 0.42
    ax.text(21.6, yy - 0.2, "Connectors (JST XH 2.54 mm)", fontsize=11, weight="bold")
    yy -= 0.7
    for ref in ("J1", "J2", "J3", "J4", "J5", "J6", "J7"):
        pins = PARTS[ref][2]
        ax.text(21.6, yy, f"{ref} {PARTS[ref][1]}", fontsize=8.5, weight="bold")
        yy -= 0.36
        ax.text(21.9, yy, "   ".join(f"{p}:{pin_net[f'{ref}.{p}']}" for p in pins), fontsize=8.2, color="#333")
        yy -= 0.42
    os.makedirs(IMG, exist_ok=True)
    out = os.path.join(IMG, "controller_schematic.png")
    fig.savefig(out, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def draw_wiring():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Rectangle

    sys.path.insert(0, ROOT)
    import config as C
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_aspect("equal")
    x0, x1 = C.BASE_X
    y0, y1 = C.BASE_Y
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#fafafa", ec="#333", lw=2))
    ax.plot([0, 0], [y0, y1], "--", color="#999")
    ax.text(x0 + 4, y1 + 6, "Display base seen from ABOVE (top skin removed).  REAR panel on the left, FRONT on the "
            "right.  Bank A (cyl 1-5) on the -Y side (bottom of the picture).", fontsize=10)
    # engine footprint
    ax.add_patch(Rectangle((-C.END_PLATE_OUTER_X, -52), 2 * C.END_PLATE_OUTER_X, 104, fc="none", ec="#bbb", ls=":"))
    ax.text(-30, -64, "crankcase footprint (on the top skin)", fontsize=8, color="#888")

    def part(x, y, w, h, text, fc="#e8eef8"):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=1", fc=fc, ec="#333"))
        ax.text(x, y, text, ha="center", va="center", fontsize=8.5)

    p = C.PCB
    part(p["x_center"], p["y_center"], p["w"], p["h"], "CONTROLLER BOARD\n70 x 90 mm\nJ1..J7 on the edge", "#fff4d8")
    part(C.MOTOR_FACE_X - 20, 0, 40, 42, "NEMA17\nmotor", "#e0e0e0")
    hall_x = C.HALL_X
    part(hall_x, -24, 22, 9, "hall sensor\n(under rear web)")
    ax.plot([hall_x, hall_x], [-19, -1], color="#9467bd", lw=1, ls=":")
    h = C.HARNESS_HOLE
    ax.add_patch(plt.Circle((h["x"], h["y"]), h["d"] / 2, fc="#ddd", ec="#333"))
    ax.text(h["x"], h["y"] - 16, "LED harness hole\n(under the rear end cover)", fontsize=7.5, ha="center")
    for name, y, _, d in C.CONTROLS:
        part(x0 + 14, y, 18, d + 4, {"dc_jack": "12V jack", "power": "rocker", "speed": "knob",
                                      "start": "START"}[name], "#e8f8e8")
    bx = p["x_center"] - p["w"] / 2
    routes = [
        ("W1 power", [(x0 + 23, 75), (x0 + 30, 75), (x0 + 30, 30), (bx, 30)], "#d62728"),
        ("W6 knob", [(x0 + 23, -20), (bx - 25, -20), (bx - 25, 25), (bx, 25)], "#1f77b4"),
        ("W7 START", [(x0 + 23, -75), (bx - 20, -75), (bx - 20, 21), (bx, 21)], "#1f77b4"),
        ("W2 motor", [(C.MOTOR_FACE_X - 40, 10), (40, 10), (40, 30), (p["x_center"] + p["w"] / 2, 30)], "#8c564b"),
        ("W3 hall", [(hall_x + C.HALL_LEAD_SLOT["dx"], 3), (hall_x + C.HALL_LEAD_SLOT["dx"], 12),
                     (hall_x + C.HALL_LEAD_SLOT["dx"], p["y_center"] - p["h"] / 2)], "#9467bd"),
        ("W4/W5 LEDs", [(h["x"], h["y"] + 6), (h["x"], 40), (bx, 40)], "#2ca02c"),
    ]
    for label, pts, col in routes:
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=col, lw=3, alpha=0.85)
        mx, my = pts[len(pts) // 2]
        ax.text(mx + 2, my + 3, label, color=col, fontsize=9, weight="bold")
    for x in C.TIE_ANCHOR_X:
        ax.plot([x], [C.TIE_ANCHOR_Y], "s", color="#555", ms=5)
    ax.text(C.TIE_ANCHOR_X[0] - 2, C.TIE_ANCHOR_Y - 9, "cable-tie anchors", fontsize=7.5, color="#555")
    lines = [f"{n}: {hh['length']} mm - {hh['parts']}" for n, hh in HARNESS.items()]
    ax.text(x0, y0 - 18, "Harness cut lengths:   " + "   |   ".join(lines[:4]), fontsize=8)
    ax.text(x0, y0 - 28, "                                  " + "   |   ".join(lines[4:]), fontsize=8)
    ax.text(x0, y0 - 40, "LED leads: each strip's lead leaves its head at the rear end on the valley side, runs down "
            "the rear of the V, into the rear end cover through its notch and down through the harness hole.",
            fontsize=8)
    ax.set_xlim(x0 - 10, x1 + 10)
    ax.set_ylim(y0 - 45, y1 + 14)
    ax.axis("off")
    out = os.path.join(IMG, "wiring_overview.png")
    fig.savefig(out, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    probs = check()
    if probs:
        print("ELECTRONICS MODEL PROBLEMS:")
        for p in probs:
            print("  -", p)
        sys.exit(1)
    print("electronics model OK:", len(PARTS), "parts,", len(NETS), "nets")
    for f in (write_netlist(), write_tables(), draw_schematic(), draw_wiring()):
        print("wrote", f)


def draw_board_layout():
    """Suggested component placement on the 70 x 90 mm prototype board (top view,
    component side). Not hole-exact: solder the female headers with the modules
    plugged in, then wire point-to-point per the netlist."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    W, H = 90.0, 70.0
    fig, ax = plt.subplots(figsize=(13, 10.5))
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((0, 0), W, H, fc="#e9f2e1", ec="#333", lw=2))
    for i in range(int(W / 2.54) + 1):
        for j in range(int(H / 2.54) + 1):
            ax.plot(1.27 + i * 2.54, 1.27 + j * 2.54, ".", color="#9db58a", ms=2)
    for cx, cy in ((2.5, 2.5), (W - 2.5, 2.5), (2.5, H - 2.5), (W - 2.5, H - 2.5)):
        ax.add_patch(plt.Circle((cx, cy), 1.6, fc="white", ec="#333"))

    def mod(x, y, w, h, label, fc):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec="#333", lw=1.5, alpha=0.9))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8.5)

    mod(6, 38, 55.0, 28.0, "U1  ESP32-DevKitC-32E\n(2 x 19 female headers)\nUSB end <- left", "#cfe0ff")
    mod(66, 40, 15.2, 20.3, "U3\nTMC2209\nheatsink up\nVM side ->\nright", "#ffd6d6")
    mod(66, 23.5, 17.8, 12.7, "U2 Pololu\nD24V22F5", "#ffe6c7")
    mod(36, 23.5, 19.3, 7.6, "U4 74AHCT125N\n(DIP-14 socket, notch left)", "#e8e8e8")
    mod(10, 23.5, 8, 12, "C2\n470uF", "#f0f0f0")
    mod(22, 23.5, 10, 10, "C1\n220uF\n35V", "#f0f0f0")
    mod(58, 23.5, 6, 9, "F1\nD1\nD2", "#f0f0f0")
    mod(6, 13.5, 78, 7.5, "small parts row:  R1 R3 R4 R5 R6 R7 R8   C3 C4 C5   D3   Q1  (next to the pins they serve)", "#f7f7f7")
    conns = [("J1\nPWR", 2), ("J7\nSTART", 4), ("J6\nKNOB", 3), ("J3\nHALL", 3), ("J4\nLED A", 3),
             ("J5\nLED B", 3), ("J2\nMOTOR", 4)]
    x = 4.0
    for label, n in conns:
        w = n * 2.5 + 2.4
        ax.add_patch(Rectangle((x, 5.0), w, 5.8, fc="white", ec="#333"))
        ax.text(x + w / 2, 7.9, label, ha="center", va="center", fontsize=7)
        ax.plot([x + 1.25 + 1.2], [11.1], "^", color="red", ms=5)
        x += w + 1.8
    ax.text(0, H + 4, "Controller board - suggested layout (70 x 90 mm double-sided prototype board, component side)",
            fontsize=12, weight="bold")
    ax.text(0, -5, "Red triangle = pin 1 of each JST XH header. The connector edge faces the rear panel / harness hole. "
            "Wire point-to-point on the solder side per docs/ELECTRONICS_TABLES.md (net by net, tick each one off).",
            fontsize=8.5)
    ax.text(0, -9, "12 V and motor nets: 20 AWG. 5 V / GND to J4, J5: 22 AWG on the board. Signals: 26-30 AWG. "
            "Keep the motor wires (J2) away from the HALL (J3) and the LED data lines.", fontsize=8.5)
    ax.set_xlim(-3, W + 3)
    ax.set_ylim(-11, H + 7)
    ax.axis("off")
    out = os.path.join(IMG, "controller_board_layout.png")
    fig.savefig(out, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


if __name__ == "__main__":
    print("wrote", draw_board_layout())
