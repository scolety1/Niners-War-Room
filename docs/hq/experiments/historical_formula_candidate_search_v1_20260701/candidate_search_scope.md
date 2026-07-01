# Candidate Search Scope

Scope follows Historical Formula Tuning Readiness Gate V1:

- Use canonical V3 substrate only.
- Use Source Contract V1 only.
- Use fixed train/validation/holdout split.
- Select from validation only.
- Evaluate holdout once after validation selection.
- Keep candidate families fixed, small, and interpretable.
- Keep null-fenced fields out of the primary pass.
- Use null-fenced fields only in explicitly labeled sensitivity variants.
- Do not use red-zone sidecars, routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, market/ADP/vendor/projection/rank fields, or current-only context.
