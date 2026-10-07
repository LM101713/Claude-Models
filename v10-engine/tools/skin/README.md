# Blender skin - how to run it

Everything visible on the V8 display engine is built in Blender by
`tools/skin_blender.py` from `tools/skin/parts/*.py`. Every dimension comes
from `skin/params.json`, which `tools/export_params.py` writes from
`config.py` (variant `v8`) and `fits.py`. The CAD model (`cad/`) stays the
reference and the checker: the moving core (crank, rods, pistons, rails, end
plates, valley beam, bearings, drive, electronics) is still CAD, and
`tools/skin_check.py` runs the interference and full-rotation checks of the
Blender meshes against it.

## What you need

- Blender 4.5 or newer (the boolean solver `MANIFOLD` arrived in 4.5; the
  script falls back to `EXACT` on older builds, which is slower and less
  robust). Any build works: the installed Blender, or the `bpy` Python
  wheel (`pip install bpy`, Python 3.11) - the cloud session used
  bpy 5.0.1 on Python 3.11.15, headless, Cycles on CPU.
- Python packages inside Blender's Python: `trimesh`, `manifold3d`,
  `numpy`, `Pillow`. With the Blender binary:
  `"<blender dir>\4.5\python\bin\python.exe" -m pip install trimesh manifold3d pillow`.
- The CAD environment (CadQuery) only for `tools/export_params.py`,
  `tools/export_core_meshes.py` and `tools/skin_check.py`.

## One command (Windows, from the `v10-engine` folder)

    "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -b -P tools\skin_blender.py -- --all

or, with the `bpy` wheel:

    python tools\skin_blender.py --all

`--all` = `--build --export --check --render`. Steps can be run alone:

| flag | does | writes |
|---|---|---|
| `--build` | builds the 24-part library in Blender (about 40 s) | - |
| `--export` | STLs in print orientation with part numbers, plus engine-frame copies | `skin/<part>.stl`, `skin/assembly/*.stl`, `skin/parts.json` |
| `--check` | watertight / manifold / sliver / min-wall / overhang / plate-fit checks and the fit measurement on the exported STLs | `docs/SKIN_PRINT_REPORT.md` |
| `--render --round N` | studio renders from the reference angles plus close-ups, side by side with `references/STYLE_ai_0N.png` | `renders/skin_roundN/` |

Options: `--views ref1_closeup_34_above,ref4_side_left` (names in
`tools/skin/studio.py`), `--samples 64`, `--size 1456x1086`, `--phi 0`
(crank angle for the damper), `--no-core` (render without the CAD core
meshes). A full 8-view render set at 64 samples takes about 15 minutes on
4 CPU cores; a GPU build of Blender is much faster (set
`sc.cycles.device` in `studio.py`).

## Order of operations after a parameter change

1. `python tools/export_params.py` (CAD env) - rewrites `skin/params.json`.
2. `python tools/export_core_meshes.py` (CAD env) - engine-frame STLs of the
   CAD core into `skin/core/` for the renders.
3. `blender -b -P tools/skin_blender.py -- --all` (or `python tools/skin_blender.py --all`).
4. `python tools/skin_check.py` (CAD env) - mesh interference + 15-degree
   sweep against the CAD core, part-list comparison -> `docs/SKIN_CHECK_REPORT.md`.

## Where the files are

- `tools/skin/bpyutil.py` - primitives (128-segment cylinders), selective
  bevels, lofts, swept tubes, mirror, boolean (MANIFOLD solver), the
  `finalize()` pass (manifold3d merge + 1e-4 mm simplify so STL float32
  rounding cannot open an edge), STL export.
- `tools/skin/fitcut.py` - crush-rib pockets, insert pilots, M3
  clearance / counterbore pairs; every fit cut is logged in `FITS` and
  measured on the exported STL (`tools/skin/measure.py`).
- `tools/skin/parts/` - `block.py` (01, 03), `heads.py` (30, 31, 31B, 32,
  34), `intake.py` (36, 36B, 36C), `exhaust.py` (33, 35), `pan.py` (40, 41,
  42), `front.py` (43, 44, 45, 45B), `stand.py` (46, 47, 48, 49).
- `tools/skin/materials.py`, `tools/skin/studio.py` - palette materials,
  lights, cameras, side-by-side composites.

## Getting the files from the branch

The STLs are committed on branch `claude/v10-engine-display-model-4r6gjr`
in `v10-engine/skin/`. On GitHub open the repository, switch to that branch,
browse to `v10-engine/skin/` and download a file with its "Download raw"
button, or clone the branch:

    git clone -b claude/v10-engine-display-model-4r6gjr <repository url>

## Known limits (honest)

- The skin is parametric CAD-style modelling done in Blender: exact
  cylinders, lofts, bevels and booleans. It has real fillets and drafts, but
  it is not hand sculpting. Where a sculptor would do better is written in
  `docs/VISUAL_REVIEW.md`.
- Text (edition plate, plinth labels) comes from Blender's font tools;
  the font is Blender's default, not the final plate font.
- The 45-degree rule: the check flags faces steeper than 47 degrees from
  vertical; 45-degree chamfers and wedges pass by design.
