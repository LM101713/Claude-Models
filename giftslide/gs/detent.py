"""
Detent model: flexure stiffness from the real beam section, the deflection the bump needs at
every point of travel (from the real relief profile and bump shape), and the push/pull force.

Model
  Each lid edge carries a fixed-fixed beam (the strip outboard of the flexure slot) with the
  bump at mid-span. Both sides are identical, so the lid stays centred and each beam takes the
  same deflection delta(s).
      F_y  = k * delta                      lateral spring force, per side
      F_x  = 2 F_y (t + mu) / (1 - mu t)    axial force to keep moving, t = d(delta)/ds
  t > 0: the bump is climbing (resists). t < 0: the spring pushes the lid along (the 'snap').
  A small constant drag from the lid's weight is added.
"""

import math

import numpy as np

from .params import P


# ------------------------------------------------------------------ beam section


def beam_polygon(p=P, dy=0.0):
    """Beam cross-section (y, z lid-local) for the +Y side, from the lid section."""
    yi, yf = p.beam_in + dy, p.land_y + dy
    lc = p.land_chamfer
    return np.array([
        (yi, 0.0), (yf - lc, 0.0), (yf, lc), (yf, p.land_h),
        (yf - p.bevel_run, p.bevel_top_z), (yi, p.bevel_top_z),
    ])


def section_props(poly):
    """Area, centroid y, and second moment about the vertical axis through the centroid
    (bending in Y), for a simple polygon."""
    y, z = poly[:, 0], poly[:, 1]
    y1, z1 = np.roll(y, -1), np.roll(z, -1)
    cr = y * z1 - y1 * z
    A = 0.5 * cr.sum()
    cy = (1 / (6 * A)) * ((y + y1) * cr).sum()
    Iyy0 = (1 / 12) * ((y * y + y * y1 + y1 * y1) * cr).sum()   # about z-axis (y=0)
    I = Iyy0 - A * cy * cy
    c = max(y.max() - cy, cy - y.min())
    return abs(A), cy, abs(I), c


def beam(p=P, E=None, fixity=1.0, dy=0.0, slot_dw=0.0):
    """Stiffness k (N/mm per side) and strain per mm of deflection for the fixed-fixed beam.
    fixity scales between pinned-ish (0.25: 48EI/L^3) and fully clamped (1.0: 192EI/L^3)."""
    E = E or p.E_mpa
    A, cy, I, c = section_props(beam_polygon(p, dy))
    L = p.beam_len + slot_dw
    k = fixity * 192 * E * I / L ** 3
    # clamped-clamped: M_max = F L / 8 -> strain = F L c / (8 E I) = 24 delta c / L^2 at full fixity
    strain_per_mm = (k * L / 8) * c / (E * I) if fixity >= 1 else (k * L / 4) * c / (E * I)
    return dict(A=A, I=I, c=c, L=L, k=k, strain_per_mm=strain_per_mm)


# ------------------------------------------------------------------ deflection along travel


def bump_shape(p=P, n=2401):
    hf = 0.5 * p.bump_flat
    u = np.linspace(-p.bump_rear, p.bump_front, n)
    yb = np.where(u >= 0, (p.bump_front - u) / max(p.bump_front_run, 1e-9),
                  (u + p.bump_rear) / max(p.bump_rear_run, 1e-9))
    yb = np.clip(yb, 0, 1) * p.bump_p
    return u, yb


def deflection(p=P, s=None, tray_dy=0.0, lid_dy=0.0):
    """delta(s): beam deflection needed at lid travel s (per side), for a lid centred in the
    groove. tray_dy / lid_dy: printer-variation offsets per side (+ = prints wider)."""
    if s is None:
        s = np.arange(-0.3, p.travel + 3.0, 0.004)
    prof = np.array(p.relief_profile())
    u, yb = bump_shape(p)
    yb_abs = p.land_y + lid_dy + yb
    out = np.empty(len(s))
    for i, si in enumerate(s):
        xc = p.bump_closed_x + si + u
        yc = p.y_g + tray_dy + np.interp(xc, prof[:, 0], prof[:, 1])
        out[i] = max(0.0, float(np.max(yb_abs - yc)))
    return s, out


def entry_deflection(p=P, tray_dy=0.0, lid_dy=0.0):
    """Deflection while the lid is pushed in from outside (bump passing the lead-in and the
    entry zone), as a function of how far the bump is past the stop (tray x of bump centre)."""
    x = np.linspace(p.bump_closed_x + p.travel - 1, p.L + 2.0, 1500)
    s = x - p.bump_closed_x
    return deflection(p, s, tray_dy, lid_dy)


def forces(s, d, k, mu, direction, lid_mass_g=12.0):
    """Axial force (N) needed to move the lid in `direction` (+1 opening, -1 closing)."""
    t = np.gradient(d, s) * direction
    t = np.clip(t, -5, 1 / mu - 1e-3)
    Fy = k * d
    Fx = 2 * Fy * (t + mu) / (1 - mu * t)
    return Fx + mu * lid_mass_g * 9.81e-3


def summary(p=P, tray_dy=0.0, lid_dy=0.0, E=None, mu=None, fixity=1.0):
    E = E or p.E_mpa
    mu = p.mu if mu is None else mu
    b = beam(p, E, fixity, lid_dy)
    s, d = deflection(p, None, tray_dy, lid_dy)
    fo = forces(s, d, b["k"], mu, +1)
    fc = forces(s, d, b["k"], mu, -1)
    zw = min(6.0, p.travel / 2)
    zone_r1 = s < zw
    zone_stop = s > p.travel - zw
    se, de = entry_deflection(p, tray_dy, lid_dy)
    fin = forces(se, de, b["k"], mu, -1)
    d_run = float(np.interp(p.travel - zw - 0.5, s, d))
    contact = s[(d > d_run + 0.03) & zone_stop]
    run = (s > zw + 1.0) & (s < p.travel - zw + 2.0)
    zone_stop = zone_stop & (s < p.travel + 3.0)
    c = p.lid_clear + tray_dy - lid_dy
    run_clear = c + p.relief_d - p.bump_p
    return dict(
        k=b["k"], I=b["I"],
        d_r1=float(d[zone_r1].max()), d_stop=float(d[zone_stop].max()) if zone_stop.any() else 0.0,
        d_entry=float(de.max()),
        F_open_r1=float(fo[zone_r1].max()), F_close_r1=float(fc[zone_r1].max()),
        F_stop=float(fo[zone_stop].max()), F_insert=float(fin.max()),
        F_run=float(fo[run].max()) if run.any() else 0.0,
        travel_to_stop=float(contact[0]) if len(contact) else float("nan"),
        strain_r1=float(d[zone_r1].max() * b["strain_per_mm"]),
        strain_max=float(max(d.max(), de.max()) * b["strain_per_mm"]),
        clear=c, run_clear=run_clear,
        slot_room=p.slot_w - max(d.max(), de.max()),
        curves=dict(s=s, d=d, f_open=fo, f_close=fc, s_in=se, d_in=de, f_in=fin),
    )
