# V10 final state (preserved)

The complete F1-style V10 design (CAD, firmware, docs, coupons) is frozen at
commit **`7c6cc96`** on branch `claude/v10-engine-display-model-4r6gjr`,
tagged locally `v10-final`. GitHub refuses tag/branch pushes from this
session, so the commit hash is the anchor: `git checkout 7c6cc96` (or
`git checkout v10-final` in a clone that has the tag) restores it exactly.

Nothing from the V10 is deleted by the V8 redesign: the V8 lives in new files
and a new config, and the shared tooling (fits.py, coupons, checks, BOM,
plates, printcheck, firmware tools) is reused.
