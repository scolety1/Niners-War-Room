# Current-Only Field Exclusion Report

This packet excludes current-only fields from the future Core Usage Review Dataset V1 feature table unless a later point-in-time gate proves historical replay safety.

## Excluded Families

| Family | Exclusion Reason | Required Future Proof |
|---|---|---|
| Current roster/status/availability | Current display context can leak target-season state. | Historical roster/status snapshots with extraction/publication as-of dates and anchor-specific replay proof. |
| Schedule/current context | Next game/opponent/bye can leak target-season schedule information if not anchored. | Schedule publication/as-of proof and target-anchor policy. |
| Injury/practice context | Current injury/practice status is target-time sensitive and can become medical/projection-adjacent. | Point-in-time injury/practice reports, source policy, and medical-risk exclusion checks. |
| Depth chart context | Current role depth can leak post-anchor information. | Point-in-time depth chart snapshots with publication dates. |
| Routes/TPRR/YPRR | No approved compact route denominator in this phase. | Rights-cleared upload or approved route source with player-week denominator and as-of proof. |
| `rz_att` | Semantics are unresolved. | Proof of player/team/component semantics and overlap with typed red-zone fields. |

## Required Display Text

If an excluded family is requested before proof exists, report `Not enough information` or `Excluded by point-in-time policy`.

Do not display missing current-only fields as zero, healthy, clean, no-role, neutral schedule, favorable matchup, low-risk, or safe.
