"""Collect everything needed to print and run the fit coupons into ONE folder at
the top of the project, and zip it:

    python tools/package_coupons.py

-> PRINT_THIS_FIRST/  (plate 3MF, every coupon STL, print settings, checklist, shopping list)
-> dist/coupon_batch_C1.zip
Re-run after tools/plates.py so the copies match the current design.
"""
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import part_sources  # noqa: E402

OUT = os.path.join(ROOT, "PRINT_THIS_FIRST")
ZIP = os.path.join(ROOT, "dist", "coupon_batch_C1.zip")
DOCS = ["TEST_CHECKLIST.md", "COUPON_HARDWARE_ORDER.md", "COUPON_PRINT_GUIDE.md"]


def main():
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            if f != "README.md":
                p = os.path.join(OUT, f)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(OUT, "single_coupon_stls"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "stl", "plates", "C1_coupons.3mf"), OUT)
    names = set(f[:-4] for f in os.listdir(os.path.join(ROOT, "stl")) if f.startswith("T") and f.endswith(".stl"))
    names |= set(f[:-4] for f in os.listdir(part_sources.SKIN_DIR) if f.startswith("T") and f.endswith(".stl"))
    for n in sorted(names):
        shutil.copy(part_sources.resolve(n), os.path.join(OUT, "single_coupon_stls", n + ".stl"))
    # T5 tests the D-flat socket with one printed crankpin (PETG)
    shutil.copy(os.path.join(ROOT, "stl", "P1_proto_crankpin.stl"), os.path.join(OUT, "single_coupon_stls", "P1_proto_crankpin_for_T5.stl"))
    for d in DOCS:
        shutil.copy(os.path.join(ROOT, "docs", d), OUT)
    os.makedirs(os.path.dirname(ZIP), exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(OUT):
            for f in files:
                p = os.path.join(base, f)
                z.write(p, os.path.relpath(p, ROOT))
    print(f"PRINT_THIS_FIRST/: plate + {len(names)} coupon STLs + {len(DOCS)} docs; zip {os.path.getsize(ZIP) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
