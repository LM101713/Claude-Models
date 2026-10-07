"""Load skin/params.json - the only source of dimensions for the skin."""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "skin", "params.json")

_D = None


def data():
    global _D
    if _D is None:
        with open(PATH) as f:
            _D = json.load(f)
    return _D


class _Cfg:
    """Attribute access to config values: P.DECK_DIST, P.VC['r'] ..."""
    def __getattr__(self, name):
        d = data()
        if name in d["config"]:
            return d["config"][name]
        if name in d["fits"]:
            return d["fits"][name]
        if name in d["derived"]:
            return d["derived"][name]
        raise AttributeError(name)


P = _Cfg()


def bank_cyl_x(bank):
    return P.BANK_A_CYL_X if bank == "A" else P.BANK_B_CYL_X


def bank_angle(bank):
    return P.bank_angle_A if bank == "A" else P.bank_angle_B


def deg(a):
    return math.radians(a)
