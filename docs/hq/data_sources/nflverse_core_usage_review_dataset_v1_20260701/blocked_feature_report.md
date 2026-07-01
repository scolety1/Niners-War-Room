# Blocked Feature Report

Blocked from Core Usage Review Dataset V1:

| Feature family | Reason |
|---|---|
| Current roster/status/availability | Current-only context; requires point-in-time snapshots. |
| Injury/practice context | Current-only and medical/projection-adjacent; excluded. |
| Depth chart context | Current role context; requires historical as-of proof. |
| Schedule/opponent/bye/next game | Current/future context; excluded from historical features. |
| Routes/TPRR/YPRR | No rights-cleared approved compact route source in this phase. |
| `rz_att` | Ambiguous player/team/component semantics. |
| Missing-as-zero derived fields | Explicitly blocked unless source proves numeric zero. |

No blocked family was normalized into the dataset.
