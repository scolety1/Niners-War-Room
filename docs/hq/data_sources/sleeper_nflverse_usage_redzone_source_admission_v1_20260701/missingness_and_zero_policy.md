# Missingness and Zero Policy

This packet treats source missingness conservatively.

## Sleeper Weekly Stats

Sleeper weekly stats receipts showed the requested usage and red-zone fields as sparse per-player keys. The audited fields were observed as present/nonzero values in the sampled responses; the compact receipt did not observe explicit numeric zero values for the audited fields.

Rules:

- Missing field/key means `Not enough information`, not zero.
- A field can be treated as explicit zero only when the source row explicitly returns numeric `0` for that field.
- Missing `rec_rz_tgt`, `rush_rz_att`, `pass_rz_att`, or `rz_att` is not evidence of zero red-zone work.
- Missing `off_snp` is not zero snaps or no role.
- Missing `tm_off_snp` is not a valid team denominator.
- Red-zone opportunities are opportunities, not guaranteed touches.
- `rz_att` is ambiguous until a source-semantics review proves what is included and whether it overlaps with passing/rushing/receiving subcomponents.

## NFLVerse / NFL Usage Overlap

Existing NFL Usage artifacts document player_stats, PBP-derived red-zone fields, and snap-count coverage. Those artifacts can be used as review evidence for future source overlap checks, but this packet does not approve them for production model/training/source-truth use.

## Route Fields

No requested route candidate was present in the sampled Sleeper weekly stats. Local participation data contains play-level route context, but this packet does not admit a compact player-week route denominator. Missing route values remain `Not enough information`.

Routes, TPRR, and YPRR must not be approximated from participation data in this phase. They may be revisited only if a rights-cleared upload or approved compact route source is already available.

## Red-Zone Validation/Fallback

Typed Sleeper red-zone fields (`rec_rz_tgt`, `rush_rz_att`, `pass_rz_att`) are source-admit candidates when coverage and semantics are proven. PBP-derived red-zone counts using `yardline_100 <= 20` may be used as review-only validation/fallback artifacts in a future lane. `rz_att` remains unresolved until its player/team and component semantics are documented.
