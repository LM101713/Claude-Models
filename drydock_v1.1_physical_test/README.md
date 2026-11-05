# DRYDOCK V1.1: physical test package

This package covers the first physical prototype tests of DRYDOCK V1.1, the refillable
silica-gel cartridge for the spool hub, on a Bambu Lab H2C.

> **Status: designed and checked in CAD only.** V1.1 passes 21 automated geometry checks.
> **Nothing has been printed, sliced, or opened in Bambu Studio yet.** The 3MF files were
> verified with a Python 3MF reader. All print settings, forces and times in this package
> are estimates until the tests confirm them.

## Start here

1. **Measure your spool first.** Use `DOCUMENTATION/SPOOL_MEASUREMENTS.md`, following
   section A of `DOCUMENTATION/PHYSICAL_TEST_PROTOCOL.md`. About 10 minutes, with no
   printing.
2. **Open `PRINT_FILES/3mf/DD011_plate4_fit_test.3mf` in Bambu Studio.**
   - Choose the H2C and a PETG profile when asked.
   - Press **Arrange**.
   - Assign filaments. A single filament for everything is fine: PETG HF was the setup used.
     Colour doesn't affect fit.
   - Check the settings against `DOCUMENTATION/PRINTING_GUIDE.md`, then slice.

   It is a plain 3MF (geometry + colours), not a Bambu project file, so no settings come
   with it.
3. **Print the fit-test plate:** ≈ 32 g and ≈ 1.5–1.8 h (estimated), no supports.
4. **Run tests B–F** in `DOCUMENTATION/PHYSICAL_TEST_PROTOCOL.md`, filling in its results
   table. It tells you which parameter to change for each failure.
5. **Only then print a full cartridge** (plates 1–3).

## Contents

```
drydock_v1.1_physical_test/
├── README.md                         this file
├── MANIFEST.sha256                   checksum of every file
├── PRINT_FILES/
│   ├── 3mf/DD011_plate4_fit_test.3mf   ← FIRST PRINT (6 test parts)
│   ├── 3mf/DD011_plate1..3, 5          full cartridge plates and the adapter set
│   ├── stl/fit_test/                   the 6 fit-test parts as separate STLs (print orientation)
│   └── stl/full_cartridge/             every V1.1 part as an STL (print orientation)
├── CAD/
│   ├── source/drydock_v11.py           complete parametric CAD source (build123d, Python)
│   ├── source/analysis/                FEA, tolerance-stack and bead-containment scripts + results
│   ├── source/requirements.txt         pip install -r requirements.txt
│   └── step/                           STEP for every part + the locked assembly
└── DOCUMENTATION/
    ├── PRINTING_GUIDE.md               H2C / PETG settings, orientation, estimates
    ├── PHYSICAL_TEST_PROTOCOL.md       tests A–F, results table, cycle log
    ├── SPOOL_MEASUREMENTS.md           blank measurement sheet
    └── reference/                      design review, CAD validation report (21/21), raw JSON
```

## Fit-test plate contents

| Part | Tests |
|---|---|
| Double gauge (2 dots): both body sockets, printed as on the real body, plus a vent row | bayonet fit in both print orientations, click, stop, pull-out, bead containment |
| Detent rings 0.20 mm (1 dot) and 0.40 mm (3 dots) | brackets the 0.30 mm nominal click |
| Cap | mates with all three |
| Window (**optional indicator**, see below) | twist-lock install, removal, 20 N push-in |
| 55 mm adapter | fit and hold in the real spool bore |

## Window = optional indicator

The window part is **always printed and fitted**, because it closes the Ø14 mm hole in each
cap face. Only its *transparency* is optional:

- **No clear filament (default for this test round):** print the window in the same PETG HF
  as everything else. It becomes an opaque **blank**: the same twist-lock, the same
  retention, no colour view. Check bead condition by opening a cap.
- **Indicator wanted later:** print it in clear or translucent PETG, or use the clear-sheet
  carrier (`DD011_C2_film_window_retainer_x2_optional.stl`).

**Never run the cartridge without a window or blank.** The 14 mm hole would let the beads
out.

## Regenerating after a test

```bash
cd CAD/source
pip install -r requirements.txt
python drydock_v11.py --set fit_radial=0.35 --out ../../PRINT_FILES_rev   # example change
```

All dimensions are parameters in `Params` at the top of `drydock_v11.py`. Every rebuild
re-runs the 21 geometry checks and writes a new validation report. Fusion 360, SolidWorks,
Onshape and FreeCAD all open the STEP files as solid bodies. The parametric history lives in
the Python source.

## Source of truth

This package is a copy of `drydock/v1.1/` on branch `claude/drydock-v1.1`
(V1.1 commit `26b1208`). The design files there were not modified to build the package.
