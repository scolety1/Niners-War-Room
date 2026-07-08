# Advanced Metrics NGS Implementation Plan

Runtime implementation was deferred in this lane.

Suggested next implementation lane:

`Advanced Metrics Display-Only NGS Development Lab + Data Health V1`

Scope:

1. Add a Development Lab panel titled `Review-only NGS context`.
2. Add Data Health source coverage rows for NGS passing, rushing, and receiving.
3. Optionally add Player Compare side-by-side context after Development Lab/Data Health tests pass.
4. Use only tracked packet artifacts or a separately approved compact display artifact.
5. Do not read outside-repo raw source caches from runtime.
6. Do not alter rankings, model scoring, hidden sort, recommendations, Trading Lab, or Draft Room.

Required tests:

- Development Lab panel contains review-only gate text.
- Data Health NGS rows show safe display counts and threshold caveat.
- No ranking/sort/model/recommendation language introduced.
- Identity-review rows are hidden by default.
