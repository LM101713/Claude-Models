"""Engine variant switch.

The repository holds two engines that share fits.py, the CAD helpers and all
the tooling:
  v10  - the F1-style V10 (frozen, docs/V10_FINAL.md)      -> config_v10.py
  v8   - the stock-car pushrod V8 (current work)            -> config_v8.py

Which one is active comes from the ENGINE environment variable, else the
ENGINE file next to this script (default v8). Every module does
`import config as C` exactly as before.
"""

import os as _os

_ROOT = _os.path.dirname(_os.path.abspath(__file__))


def _variant():
    v = _os.environ.get("ENGINE", "").strip().lower()
    if not v and _os.path.exists(_os.path.join(_ROOT, "ENGINE")):
        v = open(_os.path.join(_ROOT, "ENGINE")).read().strip().lower()
    return v or "v8"


VARIANT = _variant()
if VARIANT == "v10":
    from config_v10 import *  # noqa: F401,F403
    from config_v10 import _wrap  # noqa: F401
else:
    from config_v8 import *  # noqa: F401,F403
    from config_v8 import _wrap  # noqa: F401

if __name__ == "__main__":
    print(f"engine variant: {VARIANT}")
    self_check(verbose=True)  # noqa: F405
