# Player Context Rebuild Apply Summary

Verdict: `YELLOW_PARTIAL_REBUILD_WITH_GATED_ROWS`

The approved binding matrix was applied to the tracked NFLVerse player context display artifact. This lane moved 41 rows from `NEED_IDENTITY_REVIEW` to `SAFE_NOW_DISPLAY_ONLY` for review/display-only identity use.

## Counts

| Metric | Before | After |
| --- | ---: | ---: |
| Artifact rows | 294 | 294 |
| Safe display rows | 240 | 281 |
| Identity-review/gated rows | 54 | 13 |
| Bound rows applied | 0 | 41 |

## Still Gated

Kentrel Bullock and Jamal Haynes remain gated from the binding packet. The 11 non-approved rows also remain gated. See `remaining_gated_rows.csv`.

## Important Caveat

This rebuild applies identity bindings only. It does not backfill raw NFLVerse context for newly bound rows. Missing context remains `Not enough information`, and app lanes must not infer healthy, no-role, zero snaps, confirmed UDFA, clean schedule, recommendations, projections, valuations, or risk from missing values.
