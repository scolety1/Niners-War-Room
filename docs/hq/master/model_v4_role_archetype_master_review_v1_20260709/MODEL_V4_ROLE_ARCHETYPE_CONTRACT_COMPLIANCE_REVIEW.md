# Model v4 Role Archetype Contract Compliance Review

## Result

`PASS`

## Contract Checks

- Only `role_archetype_receipts` regenerated: pass.
- Review-only status preserved: pass.
- Required schema present: pass.
- Source hash manifest present: pass.
- Row counts documented: pass.
- Duplicate keys absent: pass.
- Leakage/as-of checks passed: pass.
- Identity/missingness checks passed: pass.
- No blocked source required: pass.
- No production/model-use claim introduced: pass.
- No ranking/app/runtime/model behavior changed: pass.
- No canonical `local_exports` write occurred: pass.

## Boundary

The regenerated archetypes are deterministic context buckets from lagged prior-season usage and production fields. They are not future role labels, scouting labels, formula weights, or production model inputs.
