# Pet Cafe Tycoon: Design Brief

## One-liner
Run a tiny diorama pet cafe floating over a miniature living town. Serve customers and their pets, earn cash, expand, and collect rare pets.

## The look (the main selling point)
- High-angle scriptable camera: drag to pan, scroll/pinch to zoom, limited bounds.
- Whole cafe is a cutaway toy-box diorama; a detailed miniature town fills the background.
- Tilt-shift depth of field, warm lighting, day/night cycle with town lights at night, light weather.
- Tiny characters (customers, staff, pets, and the player) with simple readable walk loops.

## Core loop
1. Customers arrive (with a pet) and walk to a table.
2. Player or staff take orders and serve drinks/treats.
3. Customers pay, rate the visit, and leave.
4. Cash buys new tables, decor, machines, staff, and rooms.
5. Reputation unlocks new pets, floors, and menu items.

## Progression
- Start: one room, 2 tables, 1 counter.
- Mid: more rooms/floors, staff hiring, menu research, pet play area.
- Late: pet mall / district, prestige ("Move to a bigger district", permanent perks).

## Hooks
- Collect and display rare pets (cosmetic + small perks).
- Seasonal events and news ticker with market shocks.
- Visit friends' cafes; shared leaderboard.
- Day-1/3/7 return rewards.

## Monetization (fair, no pay-to-win)
- Cosmetics: decor sets, outfits, pet skins.
- 2x speed time-control pass, extra build slots.
- No paid power that blocks free progress.

## Out of scope for v1
Trading, combat, multiple cafes per player, voice/chat features.

## Platform notes
- Mobile-first UI and touch camera controls.
- All currency and purchases server-authoritative; DataStore saves with autosave.
- Keep part/NPC counts low for mobile performance.

## First slices (each playtestable)
1. **Diorama + camera:** one small cafe room, miniature town backdrop, draggable/zoomable camera.
2. **Walking characters:** a few mini NPCs walking set paths (door, counter, table, exit).
3. **First sale:** customer orders, player serves, cash counter goes up.
4. **First upgrade:** spend cash to add a table.
5. **Save/load:** cash and upgrades persist.
