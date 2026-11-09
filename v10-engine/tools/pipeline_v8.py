"""One command for the whole V8 kit pipeline, in dependency order, with a log per
step and a non-zero exit on the first failure:

    python tools/pipeline_v8.py              # everything
    python tools/pipeline_v8.py --from skin  # start at a step (params, core, skin, check, printcheck, plates, bom)
    python tools/pipeline_v8.py --quick      # skip the slow mesh sweep and the slicer print check

Steps:
  lint        tools/check_fits.py           no clearance literal outside fits.py (CAD and Blender parts)
  firmware    tools/check_firmware.py       firmware step table vs CAD TDCs, hall pocket, host unit tests
  params      tools/export_params.py        config.py + fits.py -> skin/params.json
  core        tools/export_core_meshes.py   CAD moving core -> skin/core/*.stl (renders + checks)
  skin        tools/skin_blender.py         Blender library -> skin/*.stl, parts.json, SKIN_PRINT_REPORT.md (strict)
  check       tools/skin_check.py           mesh interference, motor travel, 15 deg sweep -> SKIN_CHECK_REPORT.md
  printcheck  tools/printcheck.py           slicer estimates + overhang / bridge check on skin + core STLs
  plates      tools/plates.py               plate 3MFs + PLATES.md
  bom         tools/bom.py, proto_bom.py    BOM.md / PROTO_BOM.md
Logs: logs/pipeline/<step>.log
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "logs", "pipeline")
PY = sys.executable

STEPS = [
    ("lint", [PY, "tools/check_fits.py"]),
    ("firmware", [PY, "tools/check_firmware.py"]),
    ("params", [PY, "tools/export_params.py"]),
    ("core", [PY, "tools/export_core_meshes.py"]),
    ("skin", [PY, "tools/skin_blender.py", "--build", "--export", "--check", "--strict"]),
    ("check", [PY, "tools/skin_check.py", "--step", "15"]),
    ("printcheck", [PY, "tools/printcheck.py"]),
    ("plates", [PY, "tools/plates.py"]),
    ("bom", [PY, "tools/bom.py"]),
    ("proto_bom", [PY, "tools/proto_bom.py"]),
]


def run(name, cmd):
    os.makedirs(LOGS, exist_ok=True)
    log = os.path.join(LOGS, name + ".log")
    t = time.time()
    with open(log, "w") as f:
        r = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    status = "ok" if r.returncode == 0 else f"FAILED (exit {r.returncode})"
    print(f"  {name:10s} {status:20s} {time.time()-t:6.0f}s  logs/pipeline/{name}.log", flush=True)
    if r.returncode != 0:
        with open(log) as f:
            tail = f.read().splitlines()[-15:]
        print("\n".join("    " + l for l in tail))
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="lint", choices=[s for s, _ in STEPS])
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", help="comma-separated step names to run")
    a = ap.parse_args()
    names = [s for s, _ in STEPS]
    todo = names[names.index(a.start):]
    if a.only:
        todo = [s for s in a.only.split(",") if s in names]
    if a.quick:
        todo = [s for s in todo if s != "printcheck"]
    print(f"pipeline ({PY}): " + " -> ".join(todo), flush=True)
    for name, cmd in STEPS:
        if name not in todo:
            continue
        if a.quick and name == "check":
            cmd = cmd + ["--no-sweep"]
        if not run(name, cmd):
            print(f"stopped at {name}", flush=True)
            sys.exit(1)
    print("pipeline complete", flush=True)


if __name__ == "__main__":
    main()
