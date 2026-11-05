#!/usr/bin/env python3
"""3D linear-elastic FEA of the cap plug (structured hexahedral mesh in cylindrical
coordinates, quadratic elements, scikit-fem). Answers one question the P001 hand calc could
not: how stiff is the plug against three inward lug loads (the detent and pull-off spring),
given that it is anchored to the thick neck?

Model: neck (r 17.7-21.0, z -3.9..0) clamped at z = -3.9 (head treated as rigid);
plug (r 17.7-19.3, z 0..7.3); three lugs (r 19.3-20.5, z 2.4-6.0, +/-6.7 deg).
Load: radial inward traction on each lug tip face (z 3.2-5.2). PETG E = 2000 MPa, nu = 0.38.
Check case: free ring (plug only) vs the Castigliano thin-ring formula used in P001.

    python plug_fea.py [R_s] [plug_wall]
"""
import json, math, sys
import numpy as np
from skfem import (MeshHex, Basis, FacetBasis, ElementHex2, ElementVector, asm, solve,
                   condense, LinearForm)
from skfem.models.elasticity import linear_elasticity, lame_parameters

E, NU = 2000.0, 0.38


def build(r_nodes, z_nodes, nth, active):
    """Tensor grid (r, theta, z) -> hex mesh with periodic theta, keeping active cells."""
    th = np.linspace(0, 2 * np.pi, nth + 1)
    m = MeshHex.init_tensor(np.array(r_nodes), th, np.array(z_nodes))
    R, T, Z = m.p
    p = np.vstack([R * np.cos(T), R * np.sin(T), Z])
    # merge theta = 2pi onto theta = 0
    key = np.round(np.vstack([R, np.mod(T, 2 * np.pi - 1e-9), Z]).T, 6)
    key[np.isclose(T, 2 * np.pi), 1] = 0.0
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    newp = np.zeros((3, len(uniq)))
    newp[:, inv] = p
    t = inv[m.t]
    # cell centres in (r, theta, z) for activity test
    c = m.p[:, m.t].mean(axis=1)
    keep = np.array([active(cr, ct, cz) for cr, ct, cz in c.T])
    t = t[:, keep]
    used = np.unique(t)
    remap = -np.ones(newp.shape[1], dtype=int)
    remap[used] = np.arange(len(used))
    return MeshHex(newp[:, used], remap[t])


def lug_zone(th_deg, half):
    th = np.asarray(th_deg, dtype=float)
    d = np.min([np.abs(((th - c) + 180) % 360 - 180) for c in (0, 120, 240)], axis=0)
    return d <= half


def run(R_s=19.5, fit=0.2, wall=1.6, free_ring=False, nth=54):
    Rp = R_s - fit
    Rpi = Rp - wall
    Rlt = Rp + 1.2
    Rn = 21.0
    lug_half = 6.67
    if free_ring:
        rn = list(np.linspace(Rpi, Rp, 3))
        zn = list(np.linspace(0, 7.3, 8))
        active = lambda r, t, z: True
    else:
        rn = sorted(set([Rpi, (Rpi + Rp) / 2, Rp, (Rp + Rlt) / 2, Rlt, Rn]))
        zn = [-3.9, -2.9, -1.95, -1.0, 0.0, 0.8, 1.6, 2.4, 3.2, 4.2, 5.2, 6.0, 6.65, 7.3]
        def active(r, t, z):
            td = math.degrees(t)
            if z < 0:
                return r < Rn
            if r < Rp:
                return True
            return r < Rlt and 2.4 < z < 6.0 and lug_zone(td, lug_half)
    m = build(rn, zn, nth, active)
    e = ElementVector(ElementHex2())
    ib = Basis(m, e)
    lam, mu = lame_parameters(E, NU)
    K = asm(linear_elasticity(lam, mu), ib)
    # load facets
    if free_ring:
        rload, z0, z1 = Rp, 0.0, 7.3
    else:
        rload, z0, z1 = Rlt, 3.2, 5.2
    def fsel(x):
        r = np.hypot(x[0], x[1]); th = np.degrees(np.arctan2(x[1], x[0])) % 360
        # flat facets sit inside the true radius by the chord sagitta, so allow 0.1 mm
        ok = np.isclose(r, rload, atol=0.1) & (x[2] > z0 - 1e-6) & (x[2] < z1 + 1e-6)
        return ok & lug_zone(th, lug_half + 0.5)
    facets = m.facets_satisfying(fsel)
    fb = FacetBasis(m, e, facets=facets)
    area = asm(LinearForm(lambda v, w: v[0] * 0 + 1.0 * (v[0] * 0 + 1)), FacetBasis(m, ElementVector(ElementHex2()), facets=facets)) if False else None
    @LinearForm
    def trac(v, w):
        x = w.x
        r = np.sqrt(x[0] ** 2 + x[1] ** 2)
        return -(x[0] / r) * v[0] - (x[1] / r) * v[1]          # unit inward pressure
    f = asm(trac, fb)
    # total load per lug for unit pressure = facet area / 3
    from skfem import Functional
    @Functional
    def one(w):
        return 1.0 + 0 * w.x[0]
    A = one.assemble(fb)
    F_lug = A / 3.0
    # constraints
    if free_ring:
        # z fixed on the bottom face; in-plane rigid modes removed by stiff tangential springs
        # at the symmetry lines between loads (60/180/300 deg), where tangential motion is 0
        fixed = ib.get_dofs(lambda x: np.isclose(x[2], 0.0)).nodal["u^3"]
        import scipy.sparse as sp
        X = ib.doflocs
        n1 = ib.nodal_dofs[0]; n2 = ib.nodal_dofs[1]
        th = np.degrees(np.arctan2(X[1, n1], X[0, n1])) % 360
        rows, cols, vals = [], [], []
        kp = 1e7
        for s0 in (60.0, 180.0, 300.0):
            sel = np.where(np.abs(th - s0) < 0.01)[0]
            tx, ty = -math.sin(math.radians(s0)), math.cos(math.radians(s0))
            for i in sel:
                d = [n1[i], n2[i]]; tv = [tx, ty]
                for a_ in range(2):
                    for b_ in range(2):
                        rows.append(d[a_]); cols.append(d[b_]); vals.append(kp * tv[a_] * tv[b_])
        K = K + sp.coo_matrix((vals, (rows, cols)), shape=K.shape).tocsr()
    else:
        fixed = ib.get_dofs(lambda x: np.isclose(x[2], -3.9)).all()
    u = solve(*condense(K, f, D=fixed))
    # mean radial displacement over the loaded facets (lug tip faces)
    @Functional
    def ur(w):
        x = w.x; r = np.sqrt(x[0] ** 2 + x[1] ** 2)
        uu = w["u"]
        return -(uu[0] * x[0] + uu[1] * x[1]) / r
    U = ur.assemble(fb, u=fb.interpolate(u)) / A
    return dict(k_N_per_mm=F_lug / U, compliance_mm_per_N=U / F_lug, F_lug_unit=F_lug,
                nodes=m.p.shape[1], cells=m.t.shape[1])


def thin_ring(R, t, b, n=3, E=E):
    a = math.pi / n; I = b * t ** 3 / 12; N = 4000; s = 0
    for i in range(N):
        ph = (i + .5) * a / N; mm = .5 * (math.cos(ph) / math.sin(a) - 1 / a); s += mm * mm * a / N
    return 2 * R ** 3 * s / (E * I)


if __name__ == "__main__":
    Rs = float(sys.argv[1]) if len(sys.argv) > 1 else 19.5
    wall = float(sys.argv[2]) if len(sys.argv) > 2 else 1.6
    fr = run(Rs, 0.2, wall, free_ring=True)
    an = thin_ring(Rs - 0.2 - wall / 2, wall, 7.3)
    cap = run(Rs, 0.2, wall)
    out = {"free_ring_fea": fr, "free_ring_analytic_compliance": an,
           "anchored_plug_fea": cap, "stiffening_factor": fr["compliance_mm_per_N"] / cap["compliance_mm_per_N"]}
    print(json.dumps(out, indent=1))
