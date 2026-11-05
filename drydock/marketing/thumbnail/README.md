# DRYDOCK MakerWorld thumbnail

- **Figma (editable, in Liam's Drafts):** https://www.figma.com/design/eSb9izjH20tI7Gl75NfFTQ
- `drydock_thumb_render_3840x2160.png`: transparent product render to drop into the Figma layer
  "Product image — REPLACE WITH PHOTO". It is the real DRYDOCK V1.1 CAD (caps locked, 55 mm
  adapters, standard opaque window blank) rising out of a **generic** spool (simple shapes at
  200 mm flanges, 67 mm wide, 55 mm bore). It is not a model of any brand's spool.
- `drydock_thumbnail_preview_1920x1080.png`: local composite showing the finished thumbnail.
- `drydock_thumbnail_preview_320px.png`: the same at MakerWorld card size, as a legibility check.

Regenerate the render (no CAD changes):
```
python thumb_scene.py      # exports the V1.1 assembly GLB from drydock_v11.py
node render_thumb.mjs drydock_thumb_render_3840x2160.png "w=3840&h=2160&spin=52&lift=14&dist=300&el=14&fov=24&tz=86&ox=720&oy=96&bg=none"
```
