# V10 display engine - owner's guide and maintenance

## Using it

* **Power:** plug the 12 V adapter into the jack at the back, switch the rocker on.
  The engine turns slowly by itself for a few seconds while it finds its
  position (homing), then stops with cylinder 1 at the top. The START ring
  breathes: ready.
* **Start / stop:** press START. The engine spins up gently; the knob sets the
  speed from idle (knob fully down, 20 RPM) to 120 RPM. Press START again for a
  soft stop.
* **The lights:** every cylinder flashes when its piston reaches the top, in the
  real firing order 1-6-5-10-2-7-3-8-4-9, and the glow fades as the piston goes
  down - like the combustion in a real engine.
* **Unattended:** after 5 minutes without anyone touching it the engine settles
  to idle; after 15 minutes it stops and goes to sleep (motor off, lights off,
  START ring breathing slowly). Press START to wake it. Holding START for 2
  seconds sends it to sleep straight away.
* **Show the mechanism:** the side panels, cam covers and end covers are held by
  magnets. Pull them off straight (no tools) to show the pistons, rods and the
  belt; push them back - they only fit one way.

## Do and don't

* Do keep it indoors, out of direct sun, 10-35 C. The printed parts are ASA
  (heat-resistant to about 90 C), but sunlight through a window fades colours
  over years.
* Do switch it off with the rocker before moving it. Carry it by the base, never
  by the exhausts, trumpets or covers.
* Don't turn the crank by hand while the power is on. With the power off you may
  turn it gently by the front pulley (under the front cover) - always clockwise
  seen from the front.
* Don't put anything into the windows or the intake trumpets while it runs.
* Don't use solvents, glass cleaner or polish on the printed parts. A dry or
  slightly damp microfibre cloth is all it needs. Compressed air for dust.
* Use only the supplied 12 V adapter (12 V, at least 2 A, 5.5 x 2.1 mm, centre
  positive). The engine is protected against a reversed plug, but not against
  a 24 V adapter.

## Maintenance schedule

The controller counts running hours. A service technician can read them with
the `status` command on the USB console (see `ELECTRONICS.md`).

| When | What | How |
|---|---|---|
| Every 500 running hours, or once a year | Oil the 10 piston guide rails | Covers off, one drop of light oil (clock or sewing-machine oil) on top of each rail where it enters the head; run 1 minute at idle; wipe off any excess. Never grease. |
| Every 500 h / yearly | Check the belt | Front end cover off. The belt must be centred on both pulleys, no frayed edges. Long strand deflects about 3 mm with a light finger press. |
| Every 500 h / yearly | Dust | Compressed air into the windows and around the trumpets with the power off. |
| Every 2,000 h | Inspection by a service technician | Bearings, bushings and rails checked for play; belt replaced if worn. |

Parts that wear (all replaceable, all off-the-shelf except the printed ones):
GT2 belt (210 mm, or 220 mm), the 30 bronze bushings (3 x 5 x 4 mm), the
ball bearings (608ZZ, 686ZZ), the LED strips. Spares from the maker.

## Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| Nothing at all, rocker not lit | no power | Check the adapter is plugged into the wall and the jack. |
| All lights blink red **1** time, repeating | position sensor did not find the crank | Switch off and on. If it repeats: service. |
| Red **2** blinks | the motor slipped (lost steps) | Something stopped the crank briefly: check nothing touches the moving parts, then press START. If it repeats: belt tension (service). |
| Red **3** blinks | crank did not turn | Jammed or belt off. Switch off, look under the front cover and in the windows, free it, switch on. |
| Red **4** blinks | motor driver problem | Switch off for a minute, switch on. If it repeats: service. |
| Red **5** blinks | power supply dip | Check the adapter and its plug; use the supplied adapter. |
| One bank's lights do not work | LED strip connection | Service. |
| Lights flash at the wrong pistons | timing setting | Service (one command: `trim`). |
| Ticking noise | rail needs oil, or a loose cover | Oil the rails (above); press the covers home. |

After any fault, pressing START clears it: the engine finds its position again
and is ready.

## Moving and shipping

Use the original box and foam. Take the trumpets and the throttle frame off and
pack them separately (they push in and pull out). Covers stay on (magnets).
