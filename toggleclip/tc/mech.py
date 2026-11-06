"""
Mechanism maths for TC-03 (numpy only, no Blender needed).

  * four-bar kinematics: upper jaw (ground) - lever (pivot P) - bail (Q-K) - blade (K, hinge H)
  * the clamp spring: three Euler-Bernoulli beams solved together with unilateral contact
      - upper jaw  (pinned at H and P)
      - bow        (the blade's lower beam, pinned at H and K; the pins' clearances let its
                    ends sit lower than nominal under load)
      - bar        (the blade's upper beam = the clamp face, joined to the bow by two bridges)
    The bar is pushed against the upper jaw through a bag of thickness t.
  * lever torque and thumb force over the closing stroke (virtual work)

Angles: theta = lever opening angle (0 = locked on its stop, positive = lifting the lever).
phi = blade opening angle about H (positive = nose moving down = jaws opening).
"""

import math

import numpy as np

from .params import P, D, bar_face, SLOP_CHAIN, SLOP_H


def rot(v, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])


def q_of(theta):
    """Q in the upper-jaw frame. Lifting the lever turns it clockwise (x right, z up)."""
    px, pz = D["P"]
    v = rot((D["Q"][0] - px, D["Q"][1] - pz), -theta)
    return (px + v[0], pz + v[1])


def k_of(phi):
    hx, hz = D["H"]
    v = rot((D["K"][0] - hx, D["K"][1] - hz), -phi)
    return (hx + v[0], hz + v[1])


def phi_of(theta):
    """Blade angle that keeps |QK| = the link length."""
    L = D["L_LINK"]
    q = q_of(theta)

    def f(phi):
        k = k_of(phi)
        return math.hypot(q[0] - k[0], q[1] - k[1]) - L

    lo, hi = -0.15, 0.6
    flo = f(lo)
    for _ in range(80):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def pose(theta):
    """Placement of the moving parts at lever angle theta (upper jaw = ground)."""
    phi = phi_of(theta)
    q, k = q_of(theta), k_of(phi)
    bail = math.atan2(q[1] - k[1], q[0] - k[0])
    bail0 = math.atan2(D["Q"][1] - D["K"][1], D["Q"][0] - D["K"][0])
    return dict(theta=theta, phi=phi, Q=q, K=k, bail_rot=bail - bail0)


def k_lift(theta):
    """Upward movement of K (towards the upper jaw) relative to the locked pose."""
    return k_of(phi_of(theta))[1] - D["K"][1]


def opening(theta, x):
    """Gap that opens between the clamp faces at station x (rigid jaws, no bag)."""
    return x * math.sin(phi_of(theta))


# =====================================================================================
# Sections
# =====================================================================================


def sections():
    """Second moments of area (mm^4) and section moduli (mm^3)."""
    b = 2 * P.BLADE_HW
    i_bar, i_bow = b * P.BAR_T ** 3 / 12, b * P.BOW_T ** 3 / 12
    W, H = 2 * P.BODY_HW, P.UJ_H
    i_u = W * H ** 3 / 12
    return dict(bar=i_bar, bow=i_bow, upper=i_u, z_bow=b * P.BOW_T ** 2 / 6,
                z_bar=b * P.BAR_T ** 2 / 6, z_upper=W * H ** 2 / 6)


# =====================================================================================
# Three beams with contact
# =====================================================================================

BAG_K = 3.0      # N/mm per mm of clamp length (12 mm wide): a folded film stack, a guess


def _beam_k(EI, h):
    return EI / h ** 3 * np.array([[12, 6 * h, -12, 6 * h], [6 * h, 4 * h * h, -6 * h, 2 * h * h],
                                   [-12, -6 * h, 12, -6 * h], [6 * h, 2 * h * h, -6 * h, 4 * h * h]])


def solve_clamp(t_bag, v_h, v_k, E, h=0.5, k_pen=None, k_bridge=2.0e4, preload=None):
    """Static solution with the lever locked (or at any lever angle, through v_k).

    t_bag   bag thickness between bar and upper jaw (mm, uniform)
    v_h     vertical displacement of the hinge pin seat in the blade (+ = towards upper jaw)
    v_k     vertical displacement of K (the toggle) relative to the locked CAD pose
    Returns forces (N): total clamp, at K (= link tension, vertical), at H; the pressure
    q(x) (N/mm), bending stresses (MPa) and the deflections."""
    if k_pen is None:      # contact stiffness per mm of length: plastic on plastic, or a bag
        k_pen = 3000.0 if t_bag <= 0 else BAG_K
    L = D["K"][0]
    pre0 = P.PRELOAD if preload is None else preload
    n = int(round(L / h))
    x = np.linspace(0, L, n + 1)
    S = sections()
    nn = n + 1
    ib0, ib1 = int(round(P.BAR_X[0] / h)), int(round(P.BAR_X[1] / h))
    nbar = ib1 - ib0 + 1
    N = 4 * nn + 2 * nbar
    K = np.zeros((N, N))
    for off, EI, cnt in ((0, E * S["upper"], nn), (2 * nn, E * S["bow"], nn),
                         (4 * nn, E * S["bar"], nbar)):
        ke = _beam_k(EI, h)
        for e in range(cnt - 1):
            idx = [off + 2 * e + j for j in range(4)]
            K[np.ix_(idx, idx)] += ke

    def wu(i):
        return 2 * i

    def wb(i):
        return 2 * nn + 2 * i

    def wr(i):
        return 4 * nn + 2 * (i - ib0)

    def couple(a, b, kk, Km):
        Km[a, a] += kk
        Km[b, b] += kk
        Km[a, b] -= kk
        Km[b, a] -= kk

    for xb in P.BRIDGES:
        for i in range(int(round((xb - P.BRIDGE_W / 2) / h)), int(round((xb + P.BRIDGE_W / 2) / h)) + 1):
            couple(wr(i), wb(i), k_bridge * h, K)
    fixed = {wu(0): 0.0, wu(n): 0.0, wb(0): v_h, wb(n): v_k}
    fk = np.array(list(fixed))
    fv = np.array([fixed[i] for i in fk])
    free = np.setdiff1d(np.arange(N), fk)
    stations = np.arange(ib0, ib1 + 1)
    pre_s = np.array([bar_face(x[i], pre0) for i in stations])
    active = np.zeros(len(stations), bool)
    pen = np.zeros(len(stations))
    u = np.zeros(N)
    for _ in range(80):
        Kc = K.copy()
        f = np.zeros(N)
        kk = k_pen * h
        for j in np.nonzero(active)[0]:
            a, b = wr(stations[j]), wu(stations[j])
            couple(a, b, kk, Kc)
            f[a] -= kk * (pre_s[j] + t_bag)
            f[b] += kk * (pre_s[j] + t_bag)
        u = np.zeros(N)
        u[fk] = fv
        rhs = f[free] - Kc[np.ix_(free, fk)] @ fv
        u[free] = np.linalg.solve(Kc[np.ix_(free, free)], rhs)
        pen = np.array([pre_s[j] + t_bag + u[wr(i)] - u[wu(i)] for j, i in enumerate(stations)])
        new = pen > 0
        if np.array_equal(new, active):
            break
        active = new
    q = np.where(active, k_pen * np.maximum(pen, 0.0), 0.0)
    xs = x[stations]
    total = float(np.trapezoid(q, xs))
    F_K = float(np.trapezoid(q * xs, xs)) / L
    w_u, w_b = u[0:2 * nn:2], u[2 * nn:4 * nn:2]
    w_r = u[4 * nn::2]

    def mmax(w, EI, xx):
        c = np.gradient(np.gradient(w, xx), xx)
        return float(np.max(np.abs(c[3:-3])) * EI)

    sig = dict(bow=mmax(w_b, E * S["bow"], x) / S["z_bow"],
               bar=mmax(w_r, E * S["bar"], xs) / S["z_bar"],
               upper=mmax(w_u, E * S["upper"], x) / S["z_upper"])
    qn = q[active]
    gap = -pen * (pen < 0)
    return dict(total=total, F_K=F_K, F_H=total - F_K, x=xs, q=q, cover=float(active.mean()),
                uniformity=float(qn.min() / qn.max()) if len(qn) else 0.0,
                stress=sig, w_upper=w_u, w_bow=w_b, w_bar=w_r, x_all=x,
                bar_drop=float(-np.min(w_r)), max_gap=float(gap.max()))


def locked(t_bag, E, slop=1.0, preload=None):
    return solve_clamp(t_bag, -SLOP_H * slop, -SLOP_CHAIN * slop, E, preload=preload)


# =====================================================================================
# Closing stroke
# =====================================================================================


def r_thumb():
    return D["P"][0] - (P.LEVER_REAR + 8.0)


def stroke(t_bag, E, slop=1.0, degs=None):
    """Rows of (theta_deg, F_K, push torque N mm, thumb force N). Positive torque: the user
    has to push the lever down; negative: the toggle pulls it shut on its own."""
    degs = np.linspace(0.0, 60.0, 121) if degs is None else degs
    out = []
    for dg in degs:
        th = math.radians(dg)
        res = solve_clamp(t_bag, -SLOP_H * slop, k_lift(th) - SLOP_CHAIN * slop, E)
        eps = 1e-4
        dk = (k_lift(th + eps) - k_lift(th - eps)) / (2 * eps)
        torque = -res["F_K"] * dk
        out.append((dg, res["F_K"], torque, torque / r_thumb()))
    return np.array(out)
