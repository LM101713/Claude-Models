"""Two-layer grid router for the V8 controller board (no external autorouter).

Reads pcb/v8_controller_unrouted.kicad_pcb, routes every net with A* on a 0.25 mm
grid (8 directions per layer, vias between layers), and writes
pcb/v8_controller_routed.kicad_pcb. Clearances are enforced by dilating the copper of
every net into a keep-out map that other nets may not enter.

    python3 tools/pcb/route.py           (system python: needs pcbnew + numpy)
"""
import heapq
import math
import os
import sys

import numpy as np
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB = os.path.join(ROOT, "pcb")
OX, OY, W, H = 100.0, 100.0, 90.0, 70.0
G = 0.25                                   # grid pitch (mm)
CLR = 0.25                                 # copper clearance (mm)
EDGE = 0.6                                 # copper to board edge (mm)
POWER = {"V12": 0.8, "12V_IN": 0.8, "12V_F": 0.8, "V5": 0.7, "V5_MCU": 0.7, "GND": 0.7,
         "MOT_A1": 0.6, "MOT_A2": 0.6, "MOT_B1": 0.6, "MOT_B2": 0.6}
SIG = 0.4
VIA_D, VIA_DRILL = 0.8, 0.4
MAXW = max(POWER.values())
VIA_COST = 12.0
ORDER_FIRST = ["12V_IN", "12V_F", "V12", "V5", "V5_MCU", "MOT_A1", "MOT_A2", "MOT_B1", "MOT_B2"]
ORDER_LAST = ["GND"]

NX, NY = int(round(W / G)) + 1, int(round(H / G)) + 1
FREE, BLOCK = -1, -2


def mm(v):
    return pcbnew.ToMM(v)


def cell(x, y):
    return int(round(x / G)), int(round(y / G))


class Grid:
    def __init__(self):
        # keep-out owner per layer: FREE, BLOCK (several nets / obstacle) or a net code
        self.ko = np.full((2, NX, NY), FREE, dtype=np.int32)
        # via keep-out (dilated wider: a via is fatter than a track)
        self.kov = np.full((NX, NY), FREE, dtype=np.int32)
        xs = np.arange(NX) * G
        ys = np.arange(NY) * G
        self.X, self.Y = np.meshgrid(xs, ys, indexing="ij")
        edge = (self.X < EDGE + MAXW / 2) | (self.X > W - EDGE - MAXW / 2) | (self.Y < EDGE + MAXW / 2) | (self.Y > H - EDGE - MAXW / 2)
        self.ko[:, edge] = BLOCK
        self.kov[edge] = BLOCK

    def _claim(self, arr, mask, net):
        cur = arr[mask]
        cur = np.where((cur == FREE) | (cur == net), net, BLOCK)
        arr[mask] = cur

    def add_disc(self, x, y, r, net, layers=(0, 1)):
        """Copper disc of radius r (mm) of `net` (BLOCK for an obstacle)."""
        R = r + CLR + MAXW / 2
        Rv = r + CLR + VIA_D / 2
        i0, i1 = max(0, int((x - Rv) / G) - 1), min(NX, int((x + Rv) / G) + 2)
        j0, j1 = max(0, int((y - Rv) / G) - 1), min(NY, int((y + Rv) / G) + 2)
        d2 = (self.X[i0:i1, j0:j1] - x) ** 2 + (self.Y[i0:i1, j0:j1] - y) ** 2
        for L in layers:
            sub = self.ko[L, i0:i1, j0:j1]
            self._claim(sub, d2 <= R * R, net)
        self._claim(self.kov[i0:i1, j0:j1], d2 <= Rv * Rv, net)

    def add_segment(self, a, b, w, net, layer):
        (x0, y0), (x1, y1) = a, b
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (G / 2)))
        for k in range(n + 1):
            t = k / n
            self.add_disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w / 2, net, (layer,))

    def ok(self, L, i, j, net):
        v = self.ko[L, i, j]
        return v == FREE or v == net

    def ok_via(self, i, j, net):
        v = self.kov[i, j]
        return (v == FREE or v == net) and self.ok(0, i, j, net) and self.ok(1, i, j, net)


DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))]


def astar(grid, net, sources, targets):
    """sources / targets: sets of (L, i, j). Returns the path as a list of (L, i, j)."""
    tl = list(targets)
    tx = np.array([t[1] for t in tl])
    ty = np.array([t[2] for t in tl])

    def h(i, j):
        return float(np.min(np.maximum(np.abs(tx - i), np.abs(ty - j))))

    openh = []
    g = {}
    parent = {}
    for s in sorted(sources):
        g[s] = 0.0
        heapq.heappush(openh, (h(s[1], s[2]), 0.0, s, None))
    while openh:
        f, gc, node, dprev = heapq.heappop(openh)
        if gc > g.get(node, 1e18):
            continue
        if node in targets:
            path = [node]
            while path[-1] in parent:
                path.append(parent[path[-1]])
            return path[::-1]
        L, i, j = node
        for di, dj, c in DIRS:
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY) or not grid.ok(L, ni, nj, net):
                continue
            if di and dj and not (grid.ok(L, i + di, j, net) and grid.ok(L, i, j + dj, net)):
                continue                                   # no corner cutting past copper
            cost = c + (0.3 if dprev is not None and dprev != (di, dj) else 0.0) + (0.15 if L == 1 else 0.0)
            nn = (L, ni, nj)
            ng = gc + cost
            if ng < g.get(nn, 1e18):
                g[nn] = ng
                parent[nn] = node
                heapq.heappush(openh, (ng + h(ni, nj), ng, nn, (di, dj)))
        if grid.ok_via(i, j, net):
            nn = (1 - L, i, j)
            ng = gc + VIA_COST
            if ng < g.get(nn, 1e18):
                g[nn] = ng
                parent[nn] = node
                heapq.heappush(openh, (ng + h(i, j), ng, nn, None))
    return None


def main():
    board = pcbnew.LoadBoard(os.path.join(PCB, "v8_controller_unrouted.kicad_pcb"))
    grid = Grid()
    pads_by_net = {}
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("H"):                        # mounting holes
            p = fp.GetPosition()
            grid.add_disc(mm(p.x) - OX, mm(p.y) - OY, 3.2 / 2 + 0.6, BLOCK)
            continue
        for pad in fp.Pads():
            p = pad.GetPosition()
            x, y = mm(p.x) - OX, mm(p.y) - OY
            sz = pad.GetSize()
            r = 0.5 * math.hypot(mm(sz.x), mm(sz.y)) if pad.GetShape() == pcbnew.PAD_SHAPE_RECT else 0.5 * max(mm(sz.x), mm(sz.y))
            n = pad.GetNetname()
            code = pad.GetNetCode() if n else BLOCK
            grid.add_disc(x, y, r, code)
            if n:
                pads_by_net.setdefault(n, []).append((x, y, code))
    for n in pads_by_net:
        pads_by_net[n].sort(key=lambda p: (round(p[0], 3), round(p[1], 3)))
    names = sorted(n for n in pads_by_net if len(pads_by_net[n]) > 1)
    rest = sorted([n for n in names if n not in ORDER_FIRST + ORDER_LAST], key=lambda n: -len(pads_by_net[n]))
    order = [n for n in ORDER_FIRST if n in names] + rest + [n for n in ORDER_LAST if n in names]

    segments = []      # (net name, width, layer, (x0,y0), (x1,y1))
    vias = []          # (net name, (x, y))
    failed = []
    for name in order:
        pads = pads_by_net[name]
        code = pads[0][2]
        w = POWER.get(name, SIG)
        # Prim order: always connect the pad nearest to the tree built so far
        tree = {(L, *cell(pads[0][0], pads[0][1])) for L in (0, 1)}
        todo = pads[1:]
        while todo:
            best = min(todo, key=lambda p: (min(math.hypot(p[0] - t[1] * G, p[1] - t[2] * G) for t in tree), p[0], p[1]))
            todo.remove(best)
            tgt = {(L, *cell(best[0], best[1])) for L in (0, 1)}
            path = astar(grid, code, tree, tgt)
            if path is None:
                failed.append((name, best[:2]))
                print(f"  FAILED {name} -> ({best[0]:.1f}, {best[1]:.1f})", flush=True)
                continue
            # split into same-layer chunks (a via between chunks), then each chunk into
            # straight segments between the cells where the direction changes
            chunks = [[path[0]]]
            for a, b in zip(path, path[1:]):
                if a[0] != b[0]:
                    vias.append((name, (a[1] * G, a[2] * G)))
                    grid.add_disc(a[1] * G, a[2] * G, VIA_D / 2, code)
                    chunks.append([b])
                else:
                    chunks[-1].append(b)
            for ch in chunks:
                if len(ch) < 2:
                    continue
                corners = [ch[0]]
                for k in range(1, len(ch) - 1):
                    d0 = (ch[k][1] - ch[k - 1][1], ch[k][2] - ch[k - 1][2])
                    d1 = (ch[k + 1][1] - ch[k][1], ch[k + 1][2] - ch[k][2])
                    if d0 != d1:
                        corners.append(ch[k])
                corners.append(ch[-1])
                for a, b in zip(corners, corners[1:]):
                    pa, pb = (a[1] * G, a[2] * G), (b[1] * G, b[2] * G)
                    segments.append((name, w, a[0], pa, pb))
                    grid.add_segment(pa, pb, w, code, a[0])
            tree |= set(path) | tgt
        print(f"  routed {name} ({len(pads)} pads)", flush=True)

    # remove dead-end stubs: a segment end that touches no pad, via or other segment of its net
    anchors = {}
    for name, pads in pads_by_net.items():
        for x, y, _ in pads:
            anchors.setdefault(name, set()).add((round(x / G), round(y / G), 2))
    for name, (x, y) in vias:
        anchors.setdefault(name, set()).add((round(x / G), round(y / G), 2))
    def cells(a, b):
        n = max(1, int(round(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / G)))
        return {(round((a[0] + (b[0] - a[0]) * k / n) / G), round((a[1] + (b[1] - a[1]) * k / n) / G)) for k in range(n + 1)}

    changed = True
    while changed:
        changed = False
        cover = {}
        for name, w, L, a, b in segments:
            for c in cells(a, b):
                cover[(name, L, *c)] = cover.get((name, L, *c), 0) + 1
        keep = []
        for seg in segments:
            name, w, L, a, b = seg
            dead = False
            for q in (a, b):
                k = (round(q[0] / G), round(q[1] / G))
                if cover[(name, L, *k)] < 2 and (k[0], k[1], 2) not in anchors.get(name, set()):
                    dead = True
            if dead:
                changed = True
            else:
                keep.append(seg)
        segments = keep
    for name, w, L, a, b in segments:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(OX + a[0]), pcbnew.FromMM(OY + a[1])))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(OX + b[0]), pcbnew.FromMM(OY + b[1])))
        t.SetWidth(pcbnew.FromMM(w))
        t.SetLayer(pcbnew.F_Cu if L == 0 else pcbnew.B_Cu)
        t.SetNet(board.FindNet(name))
        board.Add(t)
    for name, (x, y) in vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y)))
        v.SetWidth(pcbnew.FromMM(VIA_D))
        v.SetDrill(pcbnew.FromMM(VIA_DRILL))
        v.SetNet(board.FindNet(name))
        board.Add(v)
    out = os.path.join(PCB, "v8_controller_routed.kicad_pcb")
    board.Save(out)
    print(f"wrote {out}: {len(segments)} segments, {len(vias)} vias, {len(failed)} failed connections")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
