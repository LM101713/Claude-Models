"""
ODD LAYER - utility cutter concept study
Three architectures for an 18 mm snap-off cutter: 01 KEEL, 02 ORBIT, 03 LOOP.

    pip install bpy manifold3d shapely numpy pillow
    python cutter_concepts.py                 # all renders + concept boards
    python cutter_concepts.py --only orbit --shots hero --preview

Concept-stage geometry: form, proportion and visible mechanism only. Not print-ready CAD.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from uc import concepts as C  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--shots", default="")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "renders"))
    ap.add_argument("--no-boards", action="store_true")
    a = ap.parse_args()
    from uc import scene as S
    os.makedirs(a.out, exist_ok=True)
    for f in C.ALL:
        c = f()
        if a.only and c["key"] not in a.only.split(","):
            continue
        S.render_concept(c, a.out, samples=24 if a.preview else 128, scale=0.5 if a.preview else 1.0,
                         shots=a.shots.split(",") if a.shots else None)
    if not a.no_boards and not a.preview:
        from uc import board
        board.make_all(a.out)


if __name__ == "__main__":
    main()
