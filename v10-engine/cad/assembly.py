"""Assembly API switch: the active engine's assembly module (see config.py).
Tools import `assembly` and use the same names for either engine."""

from common import C

if C.VARIANT == "v10":
    from assembly_v10 import *  # noqa: F401,F403
    from assembly_v10 import _bb_overlap, _kind, _same_joint  # noqa: F401
else:
    from assembly_v8 import *  # noqa: F401,F403
    from assembly_v8 import _bb_overlap, _kind, _same_joint  # noqa: F401
