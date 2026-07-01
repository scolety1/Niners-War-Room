# Next Gate Recommendations

## Recommended Next Lane

Create one narrow point-in-time snapshot manifest lane for a single low-risk family before attempting any broad replay work.

Recommended first candidates:

1. `schedule`, because game date/week fields exist but need release/update timestamp and reschedule history.
2. `draft_picks`, because draft event timing can be split into post-draft anchors, but the current packet does not prove as-of publication or replay eligibility.
3. `weekly_rosters`, only if a frozen season-week snapshot source with extraction timestamps can be produced.

## Do Not Start Yet

Do not begin model experiments, training, source-truth promotion, health inference, injury risk, role projection, rank logic, hidden sort, recommendations, trade value, or pick value from these fields.

## Required Before Reconsideration

A future gate must produce timestamped snapshot manifests, anchor-relative row counts, leakage tests, missingness tests, identity exclusions, and explicit approval for the requested use. Display-only status remains the only current approved use where prior packets allow it.
