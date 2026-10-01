# Military tycoon base v2

| File | What it is |
|---|---|
| `military_base.py` | Base generator (400 x 400 walled compound, enterable buildings, production core). Writes `military_base.fbx` + `base_data.lua`. |
| `makers.py` | The six money makers (AmmoPress, FuelRefinery, SupplyDepot, TankFactory, BlackMarket, MissileSilo). Writes `makers.fbx` + `makers_data.lua`. |
| `blocks.py` | Shared geometry builder, palette, and the sanity checks (normals, coplanar faces, triangle report). |
| `fit_base.lua` | Studio command-bar script: fits the imports, colours them, builds collision/ladders/lights, copies the base to every plot, files the makers into `ServerStorage.Makers`. |
| `render_base.py`, `render_makers.py` | Verification renders into `renders/`. |

```
blender --background --python military_base.py
blender --background --python makers.py
blender --background --python render_base.py      # optional: -- map core int_hangar ...
```

## Collision approach
Visual meshes never collide (`CanCollide = false`). Every wall, floor, stair step, railing and
prop that should block the player is written to `base_data.lua` as an axis-aligned box, and
`fit_base.lua` turns each into an invisible anchored Part (option c). Boxes collide exactly with
cheap Box collision, so hollow buildings stay hollow without paying for convex decomposition.

## Studio setup
1. Import `military_base.fbx` with the 3D Importer (keep the default model name `military_base`).
2. Create `ServerStorage > BaseData` (ModuleScript), paste `base_data.lua`.
3. Import `makers.fbx` (model `makers`) and create `ServerStorage > MakersData` with `makers_data.lua`.
4. Make sure each plot is a child of `Workspace.Plots` (a 400 x 400 floor Part, or a Model whose
   PrimaryPart / `Floor` / largest part is the floor; front of the base = the floor's +Z).
5. Paste `fit_base.lua` into the command bar. Re-run it any time; it replaces what it built before.

## Test plan (Play mode)
1. **Output check** – `[FIT] template built: 88 meshes, 20 lights, ~780 collision parts, 4 ladders`,
   `placed on N plot(s)`, six `maker ...` lines, then `[FIT] done`. No `no style for suffix` warnings.
2. **Walk every building** – in and out of: HQ (front door, west side door, both partition doorways
   on each floor), all three barracks (door at each end, climb an upper bunk), hangar (big door,
   side door), garage (all three bays + side door), both bunkers, both guardhouses. You should
   never get stuck on an invisible edge or walk through a wall.
3. **Climb** – HQ stairs to floor 2, then the second flight to the roof (railings stop you falling
   into the stairwell); hangar stairs to the catwalk; core stairs (two flights) to the catwalk
   ring round the hopper; each corner-tower ladder to the cabin (walk off the top of the ladder
   through the gap in the half wall). From a tower window you can drop onto the wall walk – that
   is intentional.
4. **Drive** – spawn the Humvee on the VehiclePad (112, 112), drive +Z to the service road, west to
   the gate road, and out through the gate. Drive one into a garage bay and back out.
5. **Crate** – confirm the crate spawned under the Dropper (0, 29, 0) falls straight onto the
   Collector pad without touching anything (the chute outlet sits just above, at y 31.5).
6. **Lights** – at night (ClockTime 0) every building interior, tower cabin, the gate and the two red
   beacons (stack, HQ mast) are lit; nothing else should cast light.
