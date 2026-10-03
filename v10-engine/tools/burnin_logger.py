"""Log the 48 h burn-in of several engines at once over USB.

Plug every engine's ESP32 into a powered USB hub, start each engine's burn-in
(hold START while switching on with the knob at maximum, or let this script
send "burnin 48"), then:

    pip install pyserial
    python tools/burnin_logger.py --start 48       # send "burnin 48" to every engine and log
    python tools/burnin_logger.py                   # only log (burn-in already started on the engines)

Writes one CSV per engine to burnin_logs/<port>_<date>.csv (the firmware prints
one line per minute) and a summary when every engine has finished. A unit
passes when it reports "BURN-IN PASSED" with a worst sync error under 3 deg and
no FAULT line. Ctrl+C stops logging (the engines keep running).
"""

import argparse
import datetime
import glob
import os
import re
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pip install pyserial")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS_SYNC_DEG = 3.0


def ports():
    pats = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/cu.usbserial*", "/dev/cu.SLAB*", "/dev/cu.wchusbserial*"]
    found = sorted(p for pat in pats for p in glob.glob(pat))
    if sys.platform.startswith("win"):
        from serial.tools import list_ports
        found = [p.device for p in list_ports.comports()]
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=float, default=0, help="send 'burnin <hours>' to every engine")
    ap.add_argument("--ports", nargs="*", help="serial ports (default: all USB serial ports)")
    a = ap.parse_args()
    plist = a.ports or ports()
    if not plist:
        sys.exit("no engines found on USB")
    os.makedirs(os.path.join(ROOT, "burnin_logs"), exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    units = {}
    for p in plist:
        s = serial.Serial(p, 115200, timeout=0.1)
        name = os.path.basename(p)
        f = open(os.path.join(ROOT, "burnin_logs", f"{name}_{stamp}.csv"), "w")
        units[p] = dict(ser=s, file=f, buf="", done=False, passed=False, faults=[], worst=0.0, last=time.time())
        if a.start:
            s.write(f"burnin {a.start:g}\n".encode())
        print("logging", p)
    try:
        while not all(u["done"] for u in units.values()):
            for p, u in units.items():
                data = u["ser"].read(4096).decode(errors="replace")
                if not data:
                    if time.time() - u["last"] > 180 and not u["done"]:
                        print(f"{p}: no data for 3 min - check USB / power")
                        u["last"] = time.time()
                    continue
                u["last"] = time.time()
                u["buf"] += data
                while "\n" in u["buf"]:
                    line, u["buf"] = u["buf"].split("\n", 1)
                    line = line.strip()
                    u["file"].write(line + "\n")
                    u["file"].flush()
                    m = re.match(r"^\d+,[\d.]+,\d+,([\d.]+),", line)
                    if m:
                        u["worst"] = max(u["worst"], float(m.group(1)))
                    if line.startswith("FAULT"):
                        u["faults"].append(line)
                        print(f"{p}: {line}")
                    if line.startswith("BURN-IN PASSED") or line.startswith("BURN-IN FAILED"):
                        u["done"] = True
                        u["passed"] = line.startswith("BURN-IN PASSED")
                        print(f"{p}: {line}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nstopped logging")
    print("\nSUMMARY")
    for p, u in units.items():
        ok = u["passed"] and not u["faults"] and u["worst"] < PASS_SYNC_DEG
        print(f"  {p}: {'PASS' if ok else 'FAIL' if u['done'] else 'unfinished'}  worst sync {u['worst']:.2f} deg"
              f"  faults {len(u['faults'])}")


if __name__ == "__main__":
    main()
