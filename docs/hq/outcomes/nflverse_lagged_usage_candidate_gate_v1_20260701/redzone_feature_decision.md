# Red-Zone Feature Decision

Decision: `PENDING_SOURCE_ADMISSION_OR_DEFINITION_REVIEW`

Red-zone is not categorically unavailable. It belongs in a source-admission and coverage-audit lane.

Candidate mappings if coverage and semantics are proven:

- `rec_rz_tgt`
- `rush_rz_att`
- `pass_rz_att`

`rz_att` remains unresolved until player/team semantics are proven. Do not build it in Core Usage Review Dataset V1.

Plain-language audit rule: rz_att remains unresolved until player/team semantics are proven.

PBP-derived validation/fallback artifacts using `yardline_100 <= 20` are acceptable as review-only validation/fallback artifacts. They still must preserve nulls and source-as-of fields and must not become model input in this lane.
