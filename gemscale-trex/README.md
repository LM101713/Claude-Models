# Gemscale Flexi T-Rex: Blender generator for a fast print-in-place T. rex that chomps

![Gemscale Flexi T-Rex](renders/standard_cover_hero.png)

`gemscale_trex.py` is a single **Blender** script that sculpts a **small, low, fast-printing
T. rex that prints in one piece, fully assembled, with no supports**. It runs its own
printability checks and exports slicer-ready STL and 3MF files. A small three.js studio in
`render/` makes MakerWorld-style 4:3 cover images.

It's the fourth model in the Gemscale series, after the [Flexi Dragon](../gemscale-dragon/),
[Octopus](../gemscale-octopus/) and [Bat](../gemscale-bat/), and uses the same proven
print-in-place joint.

## How it's sculpted

The body is about 70 **metaball "muscle masses"** blended into one smooth organic surface:
- a deep skull with a back plate, snout, cheek muscle, brow horn and nasal ridge
- a thick S-curved neck, a chest, a belly and hips
- a big drumstick thigh, a shin and a long foot, plus the far leg striding forward
- tiny two-part arms
- a tail that's thick at the hips, tapers to a point and is held up

The lower jaw is a separate metaball part. The teeth and claws are half-cones, and the eye
is a dome with a slit pupil.

Every metaball centre lies on the T. rex's mid-plane, and the model is that body **cut in
half along the mid-plane and laid flat on the bed**. A sum of blobs centred on z = 0 gets
thinner as it rises, so the top surface is a pure height field. That means the model *can't*
have an overhang, it prints with no supports, and it's only 11 mm tall, so it prints fast.

| | Mini | Standard |
|---|---|---|
| Size | 105 × 45 × 10 mm | 140 × 60 × 11 mm |
| Joints | 5 | 5 |
| Filament* | ~7 g | ~13 g |
| Print time* | ~25 min | ~40 min |
| Bed | any (A1 mini and up) | any (A1 mini and up) |

\*These are estimates, not slicer output. Filament comes from the solid volume (2 walls, 15 %
infill, PLA). Slice in Bambu Studio for real numbers before you publish them.

![Top view](renders/standard_cover_top.png)

## What it does

- **The jaw chomps.** It's its own hinged part and opens 30°.
- **The head and neck nod** ±15°.
- **The three-part tail wiggles**, ±28° at each joint.

## Quick start

```bash
# with Blender 4.2+ (tested on 5.0)
blender -b -P gemscale_trex.py -- --preset standard --out models
blender -b -P gemscale_trex.py -- --preset mini --keyring --out models
blender -b -P gemscale_trex.py -- --preset standard --clearance 0.4 --out models   # looser joints

# or as plain Python with the bpy module (pip install bpy)
python gemscale_trex.py --preset standard --out models
```

You can also open the script in Blender's **Scripting** tab and press **Run Script**. A
**Gemscale** tab appears in the 3D-viewport sidebar (press N) with Generate and Export buttons.

Options: `--preset mini|standard`, `--clearance 0.35`, `--keyring` (a loop on the tail tip),
`--out DIR`, `--no-check`, `--save file.blend`, and `--preview` (sculpt only, no joints;
useful while editing the anatomy). A full build takes about 30 seconds.

Each run writes `GemscaleTRex_<preset>.stl` / `.3mf` (one object, every part a separate
shell) and a `_report.txt` with the size, estimated filament and all the check results. It
also writes a `.glb` and `_parts.json` for the renderer; these are not committed.

## Ready-to-print files (`models/`)

| File | Use |
|---|---|
| `GemscaleTRex_standard.3mf` | the main model |
| `GemscaleTRex_standard_clearance0p40.3mf` | looser joints for printers that run tight, or for PETG |
| `GemscaleTRex_mini.3mf` | the small, quick version |
| `GemscaleTRex_mini_keyring.3mf` | mini with a keychain loop on the tail |

STL copies are provided too.

## Print settings

- **0.20 mm layers.** The joint heights are snapped to this grid.
- **Supports off**, brim off, 2 walls, 15 % infill. Use PLA or silk PLA.
- Keep part cooling on so the short tongue bridges come out clean.
- After printing, work every joint gently. The first bend frees it. Open the jaw a few times.
- **Two-tone without an AMS:** add a filament change at about **6 mm**. The raised middle of
  the head, body, thigh and tail switches colour, while the jaw and all the thinner edges keep
  the first colour. Dark green first, then lime or yellow, looks great.

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

### The parts and their joints

The sculpted body is split into six parts: head, jaw, body, two tail parts, and the tail tip.
At every joint:

1. **Big round knuckles.** The housing fills the body's width at the pivot, so the next part
   wraps round it in a matching cup and the joint keeps the body's outline.
2. **Exact swept clearance.** The front part loses the swept volume of everything beyond the
   joint (grown by 0.5 mm and rotated through the full swing), so cuts follow the real shapes
   instead of being blunt wedges.
3. **The knob-in-socket hardware** is cut and added last.

### Checks (every run)

1. Every part is a closed, valid manifold, and each part is a single connected piece.
2. Every gap inside a joint is at least the clearance. Unlinked parts are at least 0.4 mm apart.
3. Every joint swings through its full range, carrying everything beyond it, without touching
   anything else.
4. There are no unsupported overhangs steeper than 45° (the model is a height field, so this
   comes out at 0 mm²). The only exceptions are the short tongue bridges of the joints.
5. The model fits the bed with a 5 mm margin.
6. Every housing surrounds its socket.
7. No vertices merge when saved as float32, and every part is watertight as written to the
   STL/3MF.

These are geometric checks. Test-print a model before you publish it. The mini is a quick way
to check your printer's tolerances.

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
