# Gemscale Flexi T-Rex: a fast print-in-place T. rex that chomps

![Gemscale Flexi T-Rex](renders/standard_cover_hero.png)

`gemscale_trex.py` is a single Python script that builds a **small, low, fast-printing T. rex
that prints in one piece, fully assembled, with no supports**. It runs its own printability
checks and exports slicer-ready STL and 3MF files. A small three.js studio in `render/` makes
MakerWorld-style 4:3 cover images.

It's the fourth model in the Gemscale series, after the [Flexi Dragon](../gemscale-dragon/),
[Octopus](../gemscale-octopus/) and [Bat](../gemscale-bat/), and uses the same proven
print-in-place joint.

## Why it prints fast

The T. rex prints **lying on its side as a flat profile**: head on the left, tail on the right.
It's only 12 mm tall, so it has very few layers, and everything is built from faceted domes
with vertical lower walls, so nothing needs support.

| | Mini | Standard |
|---|---|---|
| Size | 99 × 47 × 10 mm | 129 × 63 × 12 mm |
| Joints | 6 | 6 |
| Filament* | ~6 g | ~11 g |
| Print time* | ~20 min | ~35 min |
| Bed | any (A1 mini and up) | any (A1 mini and up) |

\*These are estimates, not slicer output. Filament comes from the solid volume (2 walls, 15 %
infill, PLA). Time is scaled from the sliced Gemscale Dragon. Slice in Bambu Studio for real
numbers before you publish them.

![Top view](renders/standard_cover_top.png)

## What it does

- **The jaw chomps.** It's its own hinged part and opens 36°, so the T. rex really bites.
- **The head nods** ±25°.
- **The four-part tail wiggles**, ±30° at each joint.
- **Fun details:** a big slanted eye gem with a slit pupil, sawtooth teeth in the upper and
  lower jaw, a crown tuft, a row of spikes down the back, tiny two-segment arms with claws
  (the classic joke), a thick leg with a three-toed foot, and a nostril.

## Quick start

```bash
pip install -r requirements.txt          # manifold3d, numpy, trimesh (no Blender needed)

python gemscale_trex.py --preset standard --out models
python gemscale_trex.py --preset mini --keyring --out models
python gemscale_trex.py --preset standard --clearance 0.4 --out models   # looser joints
```

Options: `--preset mini|standard`, `--clearance 0.35`, `--keyring` (a loop on the tail tip),
`--bed 256x256`, `--out DIR`, `--no-check`.

Each run writes `GemscaleTRex_<preset>.stl` / `.3mf` (one object, every part a separate
shell) and a `_report.txt` with the size, estimated filament and all the check results. It
also writes a `.glb` and `_parts.json` for the renderer; these are not committed.

## Ready-to-print files (`models/`)

| File | Use |
|---|---|
| `GemscaleTRex_standard.3mf` | the main model |
| `GemscaleTRex_standard_clearance0p40.3mf` | looser joints for printers that run tight, or for PETG |
| `GemscaleTRex_mini.3mf` | the ~20 min version |
| `GemscaleTRex_mini_keyring.3mf` | mini with a keychain loop on the tail |

STL copies are provided too.

## Print settings

- **0.20 mm layers.** The joint heights are snapped to this grid.
- **Supports off**, brim off, 2 walls, 15 % infill. Use PLA or silk PLA.
- Keep part cooling on so the short tongue bridges come out clean.
- After printing, work every joint gently. The first bend frees it. Open the jaw a few times.
- **Two-tone without an AMS:** add a filament change at **4.4 mm** (mini: **3.8 mm**). The tops
  of the big domes, the spikes and the eye switch colour, and the lower walls and the feet keep
  the first colour. Dark green or red first, then orange or yellow, looks great.

---

## How it works

### The joint

Each joint is the Gemscale captured swivel, with the same clearances as the other models:

```
 side view of one joint:                    top view:
          ____                               F | housing ( knob ) <- tongue - R
      ___/    \___  <- 45 deg: no support      | the notch lets the tongue swing
     |   knob     |  <- vertical band
      \___    ___/  <- 45 deg
          \__/        sits on the bed
```

- The front part (**F**) owns a round 12-sided housing with a double-cone socket and a notch.
- The rear part (**R**) owns a knob that sits in the socket, joined to R by a tongue that
  bridges over the notch floor.
- Clearances: 0.35 mm around the knob (settable), 0.40 mm of air under each tongue (two
  layers), 0.40 mm beside the tongue, and 0.50 mm between the housing and the next part's cup.
- R's material is clipped to the angles it can occupy after the whole swing, plus a 5° margin.
  A flat-topped hub under the cup gives the tongue a solid root.

### The parts

Seven parts: body, head, jaw, and four tail parts, each a convex "gem dome" hull with vertical
lower walls and facets leaning in above, so every face leans at most 45° from vertical.

### Checks (every run)

1. Every part is a closed, valid manifold, and each part is a single connected piece.
2. The union of all parts still has one shell per part, so nothing is fused.
3. Every gap inside a joint is at least the clearance. Unlinked parts are at least 0.45 mm apart.
4. Every joint swings through its full range (jaw 36°, neck ±25°, tail ±30°) without touching
   its neighbour.
5. There are no unsupported overhangs steeper than 45°, apart from a few mm² at the eye.
6. The model fits the bed with a 5 mm margin.
7. Every socket keeps at least a 1 mm wall.
8. No vertices merge when the mesh is saved as a float32 STL.

These are geometric checks. Test-print a model before you publish it. The mini is a quick way to
check your printer's tolerances.

## Renders

```bash
cd render && npm install      # three.js + playwright-core; uses the system Chromium
node render.mjs ../models/GemscaleTRex_standard.glb out.png --view hero --scheme jungle
```

Views: `hero`, `top`, `face`, `plate` (on a textured PEI plate) and `promo` (4:3 card with
headline text). Schemes: `jungle`, `lava`, `ice`, `bone`, `galaxy`, `blackgold`. Set
`CHROMIUM=/path/to/chrome` if Chromium isn't at `/opt/pw-browsers/chromium`.

| | |
|---|---|
| ![](renders/standard_cover_face.png) | ![](renders/standard_cover_plate.png) |
| ![](renders/standard_lava_cover_hero.png) | ![](renders/standard_blackgold_cover_hero.png) |
| ![](renders/mini_ice_cover_hero.png) | ![](renders/mini_keyring_cover_top.png) |

See [`MAKERWORLD_LISTING.md`](MAKERWORLD_LISTING.md) for the title, description, tags and
print-profile plan.
